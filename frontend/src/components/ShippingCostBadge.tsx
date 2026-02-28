import { useState, useEffect } from "react";
import { getShippingCost, isShippingError, isSessionExpired, type ShippingCostResponse, type ShippingCostResult } from "../services/meeshoApi";
import { useMeeshoStore } from "../stores/meeshoStore";

export interface ShippingCostBadgeProps {
  /** Product selling price in INR */
  sellingPrice: number;
  /** Whether Meesho account is linked (if known) */
  meeshoLinked?: boolean;
  /** Callback when user clicks to link Meesho account */
  onLinkClick?: () => void;
  /** Custom class name */
  className?: string;
  /** Compact mode for smaller displays */
  compact?: boolean;
}

type BadgeState = "loading" | "linked" | "not-linked" | "session-expired" | "error" | "idle";

export default function ShippingCostBadge({
  sellingPrice,
  meeshoLinked,
  onLinkClick,
  className = "",
  compact = false,
}: ShippingCostBadgeProps) {
  const [state, setState] = useState<BadgeState>("idle");
  const [shippingCost, setShippingCost] = useState<ShippingCostResponse | null>(null);
  const storeLinked = useMeeshoStore((s) => s.linked);
  // Prefer prop if explicitly provided, otherwise use centralized store
  const isLinked = meeshoLinked !== undefined ? meeshoLinked : storeLinked;

  // Fetch shipping cost when linked
  useEffect(() => {
    if (!isLinked) {
      setState(isLinked === false ? "not-linked" : "idle");
      return;
    }

    if (!sellingPrice || sellingPrice <= 0) {
      setState("idle");
      return;
    }

    let cancelled = false;

    const fetchCost = async () => {
      setState("loading");
      try {
        const result: ShippingCostResult = await getShippingCost(sellingPrice);
        if (cancelled) return;
        
        // Check for specific error types
        if (isShippingError(result)) {
          if (isSessionExpired(result)) {
            setState("session-expired");
          } else {
            console.error("Shipping cost error:", result.error);
            setState("error");
          }
          return;
        }
        
        setShippingCost(result);
        setState("linked");
      } catch (e: unknown) {
        if (cancelled) return;
        console.error("Failed to fetch shipping cost:", e);
        setState("error");
      }
    };

    fetchCost();
    return () => {
      cancelled = true;
    };
  }, [isLinked, sellingPrice]);

  // Format currency
  const formatInr = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Compact mode
  if (compact) {
    if (state === "loading") {
      return (
        <span className={`inline-flex items-center gap-1 text-xs text-gray-400 ${className}`}>
          <span className="animate-spin h-3 w-3 border border-gray-300 border-t-transparent rounded-full"></span>
        </span>
      );
    }

    if (state === "linked" && shippingCost) {
      return (
        <span className={`inline-flex items-center gap-1 text-xs font-medium text-green-600 ${className}`}>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8" />
          </svg>
          {formatInr(shippingCost.shipping_charges)}
        </span>
      );
    }

    if (state === "not-linked" && onLinkClick) {
      return (
        <button
          onClick={onLinkClick}
          className={`text-xs text-pink-500 hover:text-pink-600 underline ${className}`}
        >
          + Shipping
        </button>
      );
    }

    if (state === "session-expired" && onLinkClick) {
      return (
        <button
          onClick={onLinkClick}
          className={`inline-flex items-center gap-1 text-xs text-amber-600 hover:text-amber-700 ${className}`}
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="underline">Re-link</span>
        </button>
      );
    }

    return null;
  }

  // Full mode
  return (
    <div className={`rounded-lg ${className}`}>
      {/* Loading */}
      {state === "loading" && (
        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
          <span className="animate-spin h-4 w-4 border-2 border-pink-500 border-t-transparent rounded-full"></span>
          <span className="text-sm text-gray-500">Calculating shipping...</span>
        </div>
      )}

      {/* Linked - show shipping cost */}
      {state === "linked" && shippingCost && (
        <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl">
          <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold text-green-700">
                {formatInr(shippingCost.shipping_charges)}
              </span>
              <span className="text-sm text-green-600">shipping</span>
            </div>
            <p className="text-xs text-green-500 truncate">
              For {formatInr(sellingPrice)} selling price
            </p>
          </div>
          {shippingCost.total_price && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Total Price</p>
              <p className="text-sm font-semibold text-gray-700">
                {formatInr(shippingCost.total_price)}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Not linked - CTA */}
      {state === "not-linked" && (
        <button
          onClick={onLinkClick}
          className="w-full flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-pink-50 to-purple-50 border border-pink-200 rounded-xl hover:from-pink-100 hover:to-purple-100 transition-colors group"
        >
          <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <div className="flex-1 text-left">
            <p className="font-semibold text-gray-800">Link Meesho Account</p>
            <p className="text-xs text-gray-500">See exact shipping costs (~₹73 for most products)</p>
          </div>
          <svg className="w-5 h-5 text-gray-400 group-hover:text-pink-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Session Expired - Re-link CTA */}
      {state === "session-expired" && (
        <button
          onClick={onLinkClick}
          className="w-full flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-300 rounded-xl hover:from-amber-100 hover:to-orange-100 transition-colors group"
        >
          <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-500 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="flex-1 text-left">
            <p className="font-semibold text-amber-800">Session Expired</p>
            <p className="text-xs text-amber-600">Your Meesho session has expired. Click to re-link your account.</p>
          </div>
          <svg className="w-5 h-5 text-amber-400 group-hover:text-amber-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      )}

      {/* Error */}
      {state === "error" && (
        <div className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm text-red-600">Unable to fetch shipping cost</span>
          {onLinkClick && (
            <button onClick={onLinkClick} className="text-xs text-red-500 underline ml-auto">
              Re-link
            </button>
          )}
        </div>
      )}
    </div>
  );
}
