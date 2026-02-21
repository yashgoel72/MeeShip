/**
 * SessionExpiredAlert Component
 * 
 * A reusable alert component that displays when the Meesho session has expired,
 * prompting the user to re-link their account.
 */

interface SessionExpiredAlertProps {
  /** Callback when user clicks to re-link */
  onRelinkClick?: () => void;
  /** Custom class name */
  className?: string;
  /** Show as compact inline version */
  compact?: boolean;
  /** Custom message (optional) */
  message?: string;
}

export default function SessionExpiredAlert({
  onRelinkClick,
  className = "",
  compact = false,
  message,
}: SessionExpiredAlertProps) {
  if (compact) {
    return (
      <div className={`flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg ${className}`}>
        <svg className="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span className="text-sm text-amber-700">Session expired</span>
        {onRelinkClick && (
          <button
            onClick={onRelinkClick}
            className="text-xs font-medium text-amber-600 hover:text-amber-800 underline ml-auto"
          >
            Re-link
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 p-4 ${className}`}>
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-amber-800">Meesho Session Expired</h3>
          <p className="text-sm text-amber-700 mt-1">
            {message || "Your Meesho session has expired. Sessions typically last 24-48 hours."}
          </p>
          {onRelinkClick && (
            <button
              onClick={onRelinkClick}
              className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-sm font-semibold rounded-lg hover:from-amber-600 hover:to-orange-600 transition-all"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Re-link Account
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
