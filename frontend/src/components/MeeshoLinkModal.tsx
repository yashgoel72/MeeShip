import { useState, useEffect, useRef } from "react";
import { 
  unlinkMeeshoAccount, 
  getMeeshoStatus, 
  validateMeeshoSession,
  startPlaywrightSession,
  pollPlaywrightSession,
  cancelPlaywrightSession,
  type MeeshoLinkStatus,
  type PlaywrightSessionStatus,
  type PlaywrightStatus
} from "../services/meeshoApi";
import { trackEvent } from "../utils/posthog";

export interface MeeshoLinkModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type LinkStep = "idle" | "loading" | "starting" | "browser_open" | "logged_in" | "capturing" | "success" | "error" | "session_expired";

const STATUS_MESSAGES: Record<PlaywrightStatus | string, string> = {
  pending: "Starting browser...",
  browser_open: "Browser opened! Please log into your Meesho account.",
  logged_in: "Login detected! Capturing credentials...",
  capturing: "Capturing session data...",
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
  const pollCancelledRef = useRef(false);

  // Fetch current status and validate session when modal opens
  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    const fetchStatusAndValidate = async () => {
      setStep("loading");
      setSessionExpiredMessage(null);
      try {
        const res = await getMeeshoStatus();
        if (cancelled) return;
        setStatus(res);
        
        // If linked, validate that the session is still active
        if (res.linked) {
          const validation = await validateMeeshoSession();
          if (cancelled) return;
          
          if (!validation.valid) {
            setStep("session_expired");
            setSessionExpiredMessage(validation.message || "Your Meesho session has expired. Please re-link your account.");
            trackEvent("meesho_session_expired_detected");
            return;
          }
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
      pollCancelledRef.current = false;
    }
  }, [open, sessionId, playwrightStatus]);

  const handleStartBrowser = async () => {
    setStep("starting");
    setError(null);
    pollCancelledRef.current = false;

    try {
      // Start Playwright session
      const response = await startPlaywrightSession();
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

        // Refresh status
        const newStatus = await getMeeshoStatus();
        setStatus(newStatus);

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
            <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-purple-600 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Link Meesho Account</h2>
              <p className="text-sm text-gray-500">See exact shipping costs for your products</p>
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
                    A browser window has opened. Complete the login in that window.
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
            <div className="space-y-6">
              {/* Info box */}
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-blue-800">How it works</h3>
                    <ol className="text-sm text-blue-700 mt-2 space-y-1.5 list-decimal list-inside">
                      <li>Click "Open Meesho Login" below</li>
                      <li>A browser window will open automatically</li>
                      <li>Log into your Meesho supplier account</li>
                      <li>Your credentials are captured securely</li>
                      <li>The browser closes and you're linked!</li>
                    </ol>
                  </div>
                </div>
              </div>

              {/* Start button */}
              <button
                onClick={handleStartBrowser}
                className="w-full py-4 px-4 bg-gradient-to-r from-pink-500 to-purple-600 text-white font-semibold rounded-xl hover:from-pink-600 hover:to-purple-700 transition-all flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                Open Meesho Login
              </button>

              {/* Security note */}
              <p className="text-xs text-gray-400 text-center">
                🔒 Your credentials are encrypted with AES-256 and never shared with third parties.
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

              {/* Re-link button */}
              <button
                onClick={handleStartBrowser}
                className="w-full py-4 px-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-semibold rounded-xl hover:from-amber-600 hover:to-orange-600 transition-all flex items-center justify-center gap-2"
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
