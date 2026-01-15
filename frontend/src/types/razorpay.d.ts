export {};

declare global {
  interface RazorpayPaymentSuccessResponse {
    razorpay_payment_id: string;
    razorpay_order_id: string;
    razorpay_signature: string;
  }

  interface RazorpayPrefill {
    name?: string;
    email?: string;
    contact?: string;
  }

  interface RazorpayTheme {
    color?: string;
  }

  interface RazorpayModalOptions {
    ondismiss?: () => void;
  }

  interface RazorpayOptions {
    key: string;
    amount: number;
    currency: string;

    name?: string;
    description?: string;
    order_id: string;

    prefill?: RazorpayPrefill;
    notes?: Record<string, string>;
    theme?: RazorpayTheme;

    handler: (response: RazorpayPaymentSuccessResponse) => void | Promise<void>;
    modal?: RazorpayModalOptions;
  }

  interface RazorpayInstance {
    open: () => void;
  }

  interface RazorpayConstructor {
    new (options: RazorpayOptions): RazorpayInstance;
  }

  interface Window {
    Razorpay?: RazorpayConstructor;
  }
}