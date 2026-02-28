import { useState, useEffect, useRef } from "react";
import { 
  unlinkMeeshoAccount, 
  startPlaywrightSession,
  pollPlaywrightSession,
  cancelPlaywrightSession,
  type MeeshoLinkStatus,
  type PlaywrightSessionStatus,
  type PlaywrightStatus
} from "../services/meeshoApi";
import { useMeeshoStore } from "../stores/meeshoStore";
import { trackEvent } from "../utils/posthog";

export interface MeeshoLinkModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type LinkStep = "idle" | "loading" | "starting" | "browser_open" | "logged_in" | "capturing" | "success" | "error" | "session_expired";

const STATUS_MESSAGES: Record<PlaywrightStatus | string, string> = {
  pending: "Logging into Meesho…",
  browser_open: "Filling login form…",
  logged_in: "Login detected! Capturing credentials…",
  capturing: "Capturing session data…",
  completed: "Success! Your account has been linked.",
  failed: "Something went wrong. Please try again.",
  cancelled: "Cancelled by user.",
};

export default function MeeshoLinkModal({ open, onClose, onSuccess }: MeeshoLinkModalProps) {
  const [step, setStep] = useState<LinkStep>("idle");
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<MeeshoLinkStatus | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [playwrightStatus, setPlaywrightStatus] = useState<PlaywrightStatus | null>(null);
  const [linkedSupplierId, setLinkedSupplierId] = useState<string | null>(null);
  const [sessionExpiredMessage, setSessionExpiredMessage] = useState<string | null>(null);
  const [meeshoEmail, setMeeshoEmail] = useState("");
  const [meeshoPassword, setMeeshoPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const pollCancelledRef = useRef(false);

  // Fetch current status from centralized store when modal opens
  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    const fetchStatusAndValidate = async () => {
      setStep("loading");
      setSessionExpiredMessage(null);
      try {
        // Use the centralized store's fetchStatus (deduplicates calls)
        await useMeeshoStore.getState().fetchStatus();
        if (cancelled) return;

        const storeState = useMeeshoStore.getState();
        setStatus(storeState.linked ? {
          linked: true,
          supplier_id: storeState.supplierId,
          linked_at: storeState.linkedAt,
        } : { linked: false, supplier_id: null, linked_at: null });

        // If linked but session invalid, show session_expired step
        if (storeState.linked && storeState.sessionValid === false) {
          setStep("session_expired");
          setSessionExpiredMessage(storeState.sessionExpiredMessage || "Your Meesho session has expired. Please re-link your account.");
          trackEvent("meesho_session_expired_detected");
          return;
        }
        
        setStep("idle");
      } catch (e: unknown) {
        if (cancelled) return;
        setStep("idle");
      }
    };

    fetchStatusAndValidate();
    return () => {
      cancelled = true;
    };
  }, [open]);

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      // Cancel any active session
      if (sessionId && !["completed", "failed", "cancelled"].includes(playwrightStatus || "")) {
        pollCancelledRef.current = true;
        cancelPlaywrightSession(sessionId).catch(() => {});
      }
      setError(null);
      setSessionId(null);
      setPlaywrightStatus(null);
      setLinkedSupplierId(null);
      setSessionExpiredMessage(null);
      setMeeshoEmail("");
      setMeeshoPassword("");
      setShowPassword(false);
      pollCancelledRef.current = false;
    }
  }, [open, sessionId, playwrightStatus]);

  const handleStartBrowser = async () => {
    if (!meeshoEmail || !meeshoPassword) {
      setError("Please enter your Meesho email and password.");
      return;
    }
    setStep("starting");
    setError(null);
    pollCancelledRef.current = false;

    try {
      // Start Playwright session with credentials
      const response = await startPlaywrightSession(meeshoEmail, meeshoPassword);
      setSessionId(response.session_id);
      setPlaywrightStatus("pending");
      setStep("browser_open");

      trackEvent("meesho_browser_started");

      // Poll for completion
      const finalStatus = await pollPlaywrightSession(
        response.session_id,
        (statusUpdate: PlaywrightSessionStatus) => {
          if (pollCancelledRef.current) return;
          setPlaywrightStatus(statusUpdate.status);
          
          // Update step based on playwright status
          if (statusUpdate.status === "browser_open") setStep("browser_open");
          else if (statusUpdate.status === "logged_in") setStep("logged_in");
          else if (statusUpdate.status === "capturing") setStep("capturing");
        }
      );

      if (pollCancelledRef.current) return;

      if (finalStatus.linked && finalStatus.status === "completed") {
        setStep("success");
        setLinkedSupplierId(finalStatus.supplier_id || null);
        trackEvent("meesho_account_linked");

        // Sync centralized store
        useMeeshoStore.getState().markLinked(finalStatus.supplier_id || undefined);

        // Refresh local status display from store
        const storeState = useMeeshoStore.getState();
        setStatus(storeState.linked ? {
          linked: true,
          supplier_id: storeState.supplierId,
          linked_at: storeState.linkedAt,
        } : { linked: false, supplier_id: null, linked_at: null });

        onSuccess?.();

        // Auto-close after success
        setTimeout(() => {
          if (!pollCancelledRef.current) {
            onClose();
          }
        }, 2500);
      } else {
        setStep("error");
        setError(finalStatus.error || "Failed to capture credentials. Please try again.");
      }
    } catch (e: unknown) {
      if (pollCancelledRef.current) return;
      const err = e as { response?: { data?: { detail?: string } }; message?: string };
      setError(err?.response?.data?.detail || err?.message || "Failed to start browser session");
      setStep("error");
    }
  };

  const handleCancel = async () => {
    pollCancelledRef.current = true;
    if (sessionId) {
      await cancelPlaywrightSession(sessionId).catch(() => {});
    }
    setStep("idle");
    setSessionId(null);
    setPlaywrightStatus(null);
  };

  const handleUnlink = async () => {
    setStep("loading");
    setError(null);

    try {
      await unlinkMeeshoAccount();
      trackEvent("meesho_account_unlinked");
      useMeeshoStore.getState().markUnlinked();
      setStatus({ linked: false, supplier_id: null, linked_at: null });
      setStep("idle");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string };
      setError(err?.response?.data?.detail || err?.message || "Failed to unlink account");
      setStep("error");
    }
  };

  if (!open) return null;

  const isLinking = ["starting", "browser_open", "logged_in", "capturing"].includes(step);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-md">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Secure Account Linking</h2>
              <p className="text-sm text-gray-500">One-time login to fetch your shipping rates</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isLinking}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Loading state */}
          {step === "loading" && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-pink-500 border-t-transparent"></div>
            </div>
          )}

          {/* Already linked state */}
          {step === "idle" && status?.linked && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold text-green-800">Account Linked</p>
                    <p className="text-sm text-green-600">
                      Supplier ID: {status.supplier_id}
                      {status.linked_at && (
                        <span className="ml-2">
                          (since {new Date(status.linked_at).toLocaleDateString()})
                        </span>
                      )}
                    </p>
                  </div>
                </div>
              </div>

              <p className="text-sm text-gray-600">
                Your Meesho account is linked. Shipping costs will be automatically calculated for your optimized images.
              </p>

              <button
                onClick={handleUnlink}
                className="w-full py-3 px-4 bg-red-50 text-red-600 font-medium rounded-xl hover:bg-red-100 transition-colors"
              >
                Unlink Account
              </button>
            </div>
          )}

          {/* Success state */}
          {step === "success" && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Account Linked Successfully!</h3>
              <p className="text-gray-600">
                Supplier ID: {linkedSupplierId}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                You can now see exact shipping costs for your products.
              </p>
            </div>
          )}

          {/* Browser session in progress */}
          {isLinking && (
            <div className="space-y-6">
              {/* Progress indicator */}
              <div className="flex items-center justify-center py-4">
                <div className="relative">
                  <div className="animate-spin rounded-full h-16 w-16 border-4 border-pink-200 border-t-pink-500"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    {playwrightStatus === "browser_open" && (
                      <svg className="w-6 h-6 text-pink-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                      </svg>
                    )}
                    {playwrightStatus === "logged_in" && (
                      <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    )}
                    {(playwrightStatus === "capturing" || playwrightStatus === "pending") && (
                      <svg className="w-6 h-6 text-pink-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    )}
                  </div>
                </div>
              </div>

              {/* Status message */}
              <div className="text-center">
                <p className="font-semibold text-gray-800">
                  {STATUS_MESSAGES[playwrightStatus || "pending"]}
                </p>
                {playwrightStatus === "browser_open" && (
                  <p className="text-sm text-gray-500 mt-2">
                    Securely logging into your Meesho account…
                  </p>
                )}
              </div>

              {/* Progress steps */}
              <div className="flex justify-center gap-2">
                {["pending", "browser_open", "logged_in", "capturing"].map((s, i) => {
                  const statuses = ["pending", "browser_open", "logged_in", "capturing"];
                  const currentIndex = statuses.indexOf(playwrightStatus || "pending");
                  const isComplete = i < currentIndex;
                  const isCurrent = i === currentIndex;
                  
                  return (
                    <div
                      key={s}
                      className={`w-3 h-3 rounded-full transition-colors ${
                        isComplete ? "bg-green-500" : isCurrent ? "bg-pink-500 animate-pulse" : "bg-gray-200"
                      }`}
                    />
                  );
                })}
              </div>

              {/* Cancel button */}
              <button
                onClick={handleCancel}
                className="w-full py-3 px-4 bg-gray-100 text-gray-600 font-medium rounded-xl hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Idle state - not linked */}
          {step === "idle" && !status?.linked && (
            <div className="space-y-5">
              {/* How This Works - Visual data flow */}
              <div className="bg-slate-50 rounded-xl p-4 ring-1 ring-slate-200">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">How this works</p>
                <div className="flex items-center justify-between gap-1">
                  <div className="flex flex-col items-center text-center flex-1">
                    <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center mb-1.5">
                      <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
                      </svg>
                    </div>
                    <span className="text-[10px] font-medium text-slate-600">You login</span>
                  </div>
                  <svg className="w-4 h-4 text-slate-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                  <div className="flex flex-col items-center text-center flex-1">
                    <div className="w-9 h-9 rounded-lg bg-amber-100 flex items-center justify-center mb-1.5">
                      <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
                      </svg>
                    </div>
                    <span className="text-[10px] font-medium text-slate-600">We capture session</span>
                  </div>
                  <svg className="w-4 h-4 text-slate-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                  <div className="flex flex-col items-center text-center flex-1">
                    <div className="w-9 h-9 rounded-lg bg-red-100 flex items-center justify-center mb-1.5">
                      <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    </div>
                    <span className="text-[10px] font-medium text-slate-600">Password deleted</span>
                  </div>
                  <svg className="w-4 h-4 text-slate-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                  <div className="flex flex-col items-center text-center flex-1">
                    <div className="w-9 h-9 rounded-lg bg-emerald-100 flex items-center justify-center mb-1.5">
                      <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <span className="text-[10px] font-medium text-slate-600">You're linked!</span>
                  </div>
                </div>
              </div>

              {/* Security assurance - prominent placement above form */}
              <div className="flex items-start gap-2.5 bg-emerald-50 rounded-xl px-3.5 py-3 ring-1 ring-emerald-200">
                <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
                <div>
                  <p className="text-sm font-semibold text-emerald-800">Your password is never stored</p>
                  <p className="text-xs text-emerald-700 mt-0.5">Used once to login, then immediately deleted. Only an encrypted session token is kept.</p>
                </div>
              </div>

              {/* Credentials form */}
              <div className="space-y-3">
                <div>
                  <label htmlFor="meesho-email" className="block text-sm font-medium text-gray-700 mb-1">
                    Meesho Email or Phone
                  </label>
                  <input
                    id="meesho-email"
                    type="email"
                    value={meeshoEmail}
                    onChange={(e) => setMeeshoEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition-colors"
                    autoComplete="email"
                  />
                </div>
                <div>
                  <label htmlFor="meesho-password" className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="meesho-password"
                      type={showPassword ? "text" : "password"}
                      value={meeshoPassword}
                      onChange={(e) => setMeeshoPassword(e.target.value)}
                      placeholder="Enter your Meesho password"
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition-colors pr-12"
                      autoComplete="current-password"
                      onKeyDown={(e) => { if (e.key === "Enter") handleStartBrowser(); }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      tabIndex={-1}
                    >
                      {showPassword ? (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Error inline */}
              {error && (
                <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
              )}

              {/* Link button */}
              <button
                onClick={handleStartBrowser}
                disabled={!meeshoEmail || !meeshoPassword}
                className="w-full py-4 px-4 bg-gradient-to-r from-pink-500 to-purple-600 text-white font-semibold rounded-xl hover:from-pink-600 hover:to-purple-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
                Securely Link Meesho Account
              </button>

              <p className="text-[11px] text-gray-400 text-center">
                🔒 AES-256 encryption · Razorpay-grade security · Takes ~30 seconds
              </p>
            </div>
          )}

          {/* Error state */}
          {step === "error" && (
            <div className="space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold text-red-800">Something went wrong</p>
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setStep("idle")}
                className="w-full py-3 px-4 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Session Expired state */}
          {step === "session_expired" && (
            <div className="space-y-6">
              <div className="bg-amber-50 border border-amber-300 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold text-amber-800">Session Expired</p>
                    <p className="text-sm text-amber-700 mt-1">
                      {sessionExpiredMessage || "Your Meesho session has expired. Meesho sessions typically last 24-48 hours."}
                    </p>
                    {status?.supplier_id && (
                      <p className="text-xs text-amber-600 mt-2">
                        Previously linked: Supplier ID {status.supplier_id}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <p className="text-sm text-gray-600 text-center">
                Re-link your account to continue seeing shipping costs. This takes less than 30 seconds.
              </p>

              {/* Credentials form for re-link */}
              <div className="space-y-3">
                <input
                  type="email"
                  value={meeshoEmail}
                  onChange={(e) => setMeeshoEmail(e.target.value)}
                  placeholder="Meesho email or phone"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors"
                />
                <input
                  type="password"
                  value={meeshoPassword}
                  onChange={(e) => setMeeshoPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-colors"
                  onKeyDown={(e) => { if (e.key === "Enter") handleStartBrowser(); }}
                />
              </div>

              {/* Re-link button */}
              <button
                onClick={handleStartBrowser}
                disabled={!meeshoEmail || !meeshoPassword}
                className="w-full py-4 px-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-semibold rounded-xl hover:from-amber-600 hover:to-orange-600 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Re-link Meesho Account
              </button>

              <button
                onClick={onClose}
                className="w-full py-3 px-4 bg-gray-100 text-gray-600 font-medium rounded-xl hover:bg-gray-200 transition-colors"
              >
                Maybe Later
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
