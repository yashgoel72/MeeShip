import { useEffect, useMemo, useState } from "react";
import type { CreditPackId, CreditPackInfo } from "../types";
import { createOrder, getCreditBalance, getCreditPacks, verifyPayment } from "../services/paymentApi";
import { trackEvent } from "../utils/posthog";
import { useAuth } from "../context/AuthContext";

type PaymentStep = "idle" | "loading_packs" | "creating_order" | "opening_checkout" | "verifying" | "success" | "error";

export interface PaymentModalProps {
  open: boolean;
  onClose: () => void;
  defaultPackId?: CreditPackId;
  onSuccess?: () => void;
}

function formatInr(inr: number) {
  try {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(inr);
  } catch {
    return `₹${inr}`;
  }
}

function getPackId(pack: CreditPackInfo): CreditPackId | null {
  const id = String(pack.id);
  if (id === "starter" || id === "pro" || id === "enterprise") return id;
  return null;
}

async function loadRazorpayScript(): Promise<void> {
  if (typeof window === "undefined") return;
  if (window.Razorpay) return;

  const existing = document.querySelector<HTMLScriptElement>('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
  if (existing) {
    await new Promise<void>((resolve, reject) => {
      if (window.Razorpay) return resolve();
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Failed to load Razorpay script")));
    });
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Razorpay script"));
    document.body.appendChild(script);
  });
}

export default function PaymentModal({ open, onClose, defaultPackId = "starter", onSuccess }: PaymentModalProps) {
  const { refreshCredits } = useAuth();
  const [packs, setPacks] = useState<CreditPackInfo[]>([]);
  const [step, setStep] = useState<PaymentStep>("idle");
  const [error, setError] = useState<string | null>(null);

  const [selectedPackId, setSelectedPackId] = useState<CreditPackId>(defaultPackId);
  const [balance, setBalance] = useState<number | null>(null);

  const selectedPack = useMemo(() => packs.find((p) => getPackId(p) === selectedPackId) ?? null, [packs, selectedPackId]);

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    const run = async () => {
      setError(null);
      setStep("loading_packs");
      try {
        const res = await getCreditPacks();
        if (cancelled) return;
        setPacks(res.packs ?? []);
        setStep("idle");
        trackEvent("credit_packs_loaded");
      } catch (e: any) {
        if (cancelled) return;
        setError(e?.response?.data?.detail?.message || e?.response?.data?.detail || e?.message || "Failed to load credit packs");
        setStep("error");
      }

      try {
        const bal = await getCreditBalance();
        if (cancelled) return;
        setBalance(bal.credits);
      } catch {
        // optional
      }
    };

    run();
    return () => {
      cancelled = true;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setSelectedPackId(defaultPackId);
  }, [defaultPackId, open]);

  const closeDisabled = step === "creating_order" || step === "opening_checkout" || step === "verifying";

  const close = () => {
    if (closeDisabled) return;
    setError(null);
    setStep("idle");
    onClose();
  };

  const startCheckout = async (pack: CreditPackInfo) => {
    const packId = getPackId(pack);
    if (!packId) {
      setError("Invalid pack selected");
      setStep("error");
      return;
    }

    setError(null);
    setStep("creating_order");
    trackEvent("payment_create_order_clicked", { pack_id: packId });

    try {
      const order = await createOrder({ pack_id: packId });

      setStep("opening_checkout");
      await loadRazorpayScript();
      if (!window.Razorpay) throw new Error("Razorpay SDK not available");

      const options: RazorpayOptions = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: "Meesho Image Optimizer",
        description: `${pack.name} • ${pack.credits} credits`,
        order_id: order.order_id,
        prefill: {
          email: order.prefill?.email,
          name: order.prefill?.name ?? undefined,
        },
        notes: order.notes,
        theme: { color: "#ff007f" },
        handler: async (resp: RazorpayPaymentSuccessResponse) => {
          setStep("verifying");
          trackEvent("payment_handler_called", { pack_id: packId });

          try {
            const verified = await verifyPayment({
              razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id,
              razorpay_signature: resp.razorpay_signature,
            });

            if (!verified.success) {
              throw new Error(verified.message || "Payment verification failed");
            }

            const bal = await getCreditBalance();
            setBalance(bal.credits);
            setStep("success");
            
            // Refresh credits in auth context
            await refreshCredits();
            onSuccess?.();
            
            trackEvent("payment_success", {
              pack_id: packId,
              credits_added: verified.credits_added,
              new_balance: verified.new_balance,
            });
          } catch (e: any) {
            setError(e?.response?.data?.detail?.message || e?.response?.data?.detail || e?.message || "Payment verification failed");
            setStep("error");
            trackEvent("payment_failed", { pack_id: packId });
          }
        },
        modal: {
          ondismiss: () => {
            // User closed checkout; do not treat as error.
            setStep((prev) => (prev === "opening_checkout" || prev === "creating_order" ? "idle" : prev));
            trackEvent("payment_checkout_dismissed", { pack_id: packId });
          },
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
      trackEvent("payment_checkout_opened", { pack_id: packId });
    } catch (e: any) {
      setError(e?.response?.data?.detail?.message || e?.response?.data?.detail || e?.message || "Unable to start payment");
      setStep("error");
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center">
      <div className="w-full max-w-lg overflow-hidden rounded-3xl bg-white shadow-2xl ring-1 ring-slate-200">
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 p-5">
          <div>
            <div className="text-lg font-extrabold text-slate-900">Buy Credits</div>
            <div className="mt-1 text-sm text-slate-600">Pay once. Credits are added instantly after verification.</div>
            {typeof balance === "number" && (
              <div className="mt-2 inline-flex items-center rounded-full bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
                Current balance: {balance} credits
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={close}
            disabled={closeDisabled}
            className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50 disabled:opacity-50"
            aria-label="Close payment modal"
          >
            ✕
          </button>
        </div>

        <div className="p-5">
          {step === "loading_packs" ? (
            <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 ring-1 ring-slate-200">Loading packs…</div>
          ) : (
            <div className="grid gap-3">
              {packs.map((p) => {
                const id = getPackId(p);
                if (!id) return null;

                const active = id === selectedPackId;
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setSelectedPackId(id)}
                    className={[
                      "w-full rounded-2xl p-4 text-left ring-1 transition-colors",
                      active ? "bg-meesho/5 ring-meesho" : "bg-white ring-slate-200 hover:bg-slate-50",
                    ].join(" ")}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="text-sm font-extrabold text-slate-900">{p.name}</div>
                        <div className="mt-1 text-xs text-slate-600">{p.credits} credits • ~₹{p.per_image_cost}/image</div>
                      </div>
                      <div className="text-sm font-extrabold text-slate-900">{formatInr(p.price_inr)}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-2xl bg-rose-50 p-4 text-sm text-rose-800 ring-1 ring-rose-200">{error}</div>
          )}

          {step === "success" && selectedPack && (
            <div className="mt-4 rounded-2xl bg-emerald-50 p-4 text-sm text-emerald-800 ring-1 ring-emerald-200">
              Payment verified. Credits were added successfully.
            </div>
          )}

          <div className="mt-5 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={close}
              disabled={closeDisabled}
              className="rounded-2xl px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={() => selectedPack && startCheckout(selectedPack)}
              disabled={!selectedPack || closeDisabled || step === "loading_packs"}
              className="rounded-2xl bg-meesho px-5 py-3 text-sm font-extrabold text-white hover:bg-meesho/90 disabled:opacity-60"
            >
              {step === "creating_order" ? "Creating order…" : step === "verifying" ? "Verifying…" : "Pay with Razorpay"}
            </button>
          </div>

          <div className="mt-4 text-xs text-slate-500">
            Uses Razorpay Checkout. Payments are verified on the server before credits are added.
          </div>
        </div>
      </div>
    </div>
  );
}