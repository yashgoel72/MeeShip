// Shared types/interfaces for Meesho Image Optimizer frontend

export interface User {
  id: string;
  email: string;
  name?: string;
  trialCount: number;
  trial_uploads_remaining?: number;
  isUpgraded: boolean;
  credits?: number;
  creditsExpiresAt?: string | null;
  // Meesho integration fields
  meeshoLinked?: boolean;
  meeshoSupplierId?: string;
  meeshoLinkedAt?: string | null;
}

export interface ImageUploadRequest {
  file: File;
}

export interface ImageUploadResponse {
  imageId: string;
  status: "processing" | "completed" | "failed";
  optimizedUrl?: string;
  savings?: number;
}

export interface DashboardMetrics {
  totalImages: number;
  totalSavings: number;
  trialCount: number;
  isUpgraded: boolean;
}

export interface ImageResult {
  savings: number;
  image_url: string;
  original_url?: string;
  before_size?: number;
  after_size?: number;
  before_res?: string;
  after_res?: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  loading: boolean;
  error: string | null;
}
// Batch A/B Optimization Types

export interface BatchABResult {
  model: string;
  prompt_variant: string;
  metrics: Record<string, unknown> | null;
  optimized_image_b64: string | null;
  error?: string | null;
}

export interface BatchABResponse {
  results: BatchABResult[];
}

//
// Payments / Credits Types (Razorpay)
//

export type CreditPackId = "starter" | "pro" | "enterprise";

export interface CreditPackInfo {
  id: CreditPackId | string;
  name: string;
  credits: number;
  price_inr: number;
  price_paise: number;
  per_image_cost: number;
  validity_days: number;
}

export interface CreditPacksResponse {
  packs: CreditPackInfo[];
}

export interface PrefillInfo {
  email: string;
  name?: string | null;
}

export interface CreateOrderRequest {
  pack_id: CreditPackId;
}

export interface CreateOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  prefill: PrefillInfo;
  notes: Record<string, string>;
}

export interface VerifyPaymentRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface VerifyPaymentResponse {
  success: boolean;
  message: string;
  credits_added: number;
  new_balance: number;
  expires_at?: string | null;
  order_id: string;
}

export interface CreditBalanceResponse {
  credits: number;
  user_id: string;
  expires_at?: string | null;
}

export interface OrderSummary {
  id: string;
  pack_name: string;
  credits: number;
  amount_inr: number;
  status: string;
  created_at: string;
}

export interface OrderHistoryResponse {
  orders: OrderSummary[];
  total: number;
  limit: number;
  offset: number;
}