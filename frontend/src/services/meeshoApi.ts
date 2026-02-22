/**
 * Meesho Account Linking API Service
 * 
 * Handles all Meesho-related API calls:
 * - Account linking via Playwright browser automation
 * - Shipping cost calculation
 */

import { apiRequest } from './api';

// ============================================================================
// Types
// ============================================================================

export interface MeeshoLinkStatus {
  linked: boolean;
  supplier_id: string | null;
  linked_at: string | null;
  session_valid?: boolean | null;
}

export interface SessionValidationResponse {
  valid: boolean;
  error_code?: 'SESSION_EXPIRED' | 'NOT_LINKED' | 'BOT_DETECTED';
  message?: string;
}

export interface LinkMeeshoRequest {
  supplier_id: string;
  identifier: string;
  connect_sid: string;
  browser_id?: string;
}

export interface LinkMeeshoResponse {
  success: boolean;
  message: string;
  supplier_id?: string;
}

export interface UnlinkMeeshoResponse {
  success: boolean;
  message: string;
}

export interface ShippingCostRequest {
  image_url: string;
  price: number;
  sscat_id?: number;
}

export interface CategoryItem {
  id: number;
  name: string;
  breadcrumb: string;
}

export interface ShippingCostResponse {
  success: boolean;
  price: number;
  shipping_charges: number;
  transfer_price: number;
  commission_fees: number;
  gst: number;
  total_price: number;
  duplicate_pid?: number;
}

export interface ShippingCostError {
  success: false;
  error: string;
  error_code?: 'NOT_LINKED' | 'SESSION_EXPIRED' | 'API_ERROR' | 'REQUEST_ERROR';
}

export type ShippingCostResult = ShippingCostResponse | ShippingCostError;

// Playwright session types
export interface PlaywrightSessionResponse {
  session_id: string;
  status: string;
  message?: string;
}

export type PlaywrightStatus = 
  | 'pending' 
  | 'browser_open' 
  | 'logged_in' 
  | 'capturing' 
  | 'completed' 
  | 'failed' 
  | 'cancelled';

export interface PlaywrightSessionStatus {
  session_id: string;
  status: PlaywrightStatus;
  error?: string;
  linked?: boolean;
  supplier_id?: string;
  message?: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get current Meesho account linking status
 */
export const getMeeshoStatus = async (): Promise<MeeshoLinkStatus> => {
  const response = await apiRequest<MeeshoLinkStatus>('/api/meesho/status', { method: 'GET' });
  return response.data;
};

/**
 * Link a Meesho account with provided credentials
 */
export const linkMeeshoAccount = async (data: LinkMeeshoRequest): Promise<LinkMeeshoResponse> => {
  const response = await apiRequest<LinkMeeshoResponse>('/api/meesho/link', { method: 'POST', data });
  return response.data;
};

/**
 * Unlink the current Meesho account
 */
export const unlinkMeeshoAccount = async (): Promise<UnlinkMeeshoResponse> => {
  const response = await apiRequest<UnlinkMeeshoResponse>('/api/meesho/unlink', { method: 'POST' });
  return response.data;
};

/**
 * Calculate shipping cost for a product
 * 
 * @param price - Product price in INR
 * @param imageUrl - (Optional) Product image URL for duplicate detection
 * @param sscatId - (Optional) Sub-category ID, defaults to 12435
 */
export const getShippingCost = async (price: number, imageUrl?: string, sscatId?: number): Promise<ShippingCostResult> => {
  const response = await apiRequest<ShippingCostResult>('/api/meesho/shipping-cost', {
    method: 'POST',
    data: {
      price,
      image_url: imageUrl || '',
      sscat_id: sscatId,
    },
  });
  return response.data;
};

// ============================================================================
// Categories
// ============================================================================

/**
 * Fetch all Meesho product categories (sub-sub-categories with breadcrumbs).
 * Result is cached in-memory after the first call.
 */
let _categoriesCache: CategoryItem[] | null = null;

export const getCategories = async (): Promise<CategoryItem[]> => {
  if (_categoriesCache) return _categoriesCache;
  const response = await apiRequest<CategoryItem[]>('/api/meesho/categories', {
    method: 'GET',
  });
  _categoriesCache = response.data;
  return _categoriesCache;
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if a shipping cost result is an error
 */
export const isShippingError = (result: ShippingCostResult): result is ShippingCostError => {
  return !result.success;
};

/**
 * Check if error is due to session expiration
 */
export const isSessionExpired = (result: ShippingCostResult): boolean => {
  return isShippingError(result) && result.error_code === 'SESSION_EXPIRED';
};

/**
 * Check if a SessionValidationResponse indicates expired session
 */
export const isSessionExpiredError = (result: SessionValidationResponse): boolean => {
  return !result.valid && result.error_code === 'SESSION_EXPIRED';
};

/**
 * Check if error is due to account not linked
 */
export const isNotLinked = (result: ShippingCostResult): boolean => {
  return isShippingError(result) && result.error_code === 'NOT_LINKED';
};

/**
 * Validate that the Meesho session is still active.
 * Makes a lightweight API call to check if the token is expired.
 */
export const validateMeeshoSession = async (): Promise<SessionValidationResponse> => {
  const response = await apiRequest<SessionValidationResponse>('/api/meesho/validate-session', { method: 'GET' });
  return response.data;
};

// ============================================================================
// Playwright Browser Automation
// ============================================================================

/**
 * Start a Playwright login session with Meesho credentials.
 * The backend will fill the login form automatically and capture session cookies.
 */
export const startPlaywrightSession = async (email: string, password: string): Promise<PlaywrightSessionResponse> => {
  const response = await apiRequest<PlaywrightSessionResponse>('/api/meesho/playwright/start', {
    method: 'POST',
    data: { email, password },
  });
  return response.data;
};

/**
 * Get the status of a Playwright session.
 * Poll this to check if login is complete.
 */
export const getPlaywrightSessionStatus = async (sessionId: string): Promise<PlaywrightSessionStatus> => {
  const response = await apiRequest<PlaywrightSessionStatus>(`/api/meesho/playwright/status/${sessionId}`, { method: 'GET' });
  return response.data;
};

/**
 * Cancel an active Playwright session.
 */
export const cancelPlaywrightSession = async (sessionId: string): Promise<{ success: boolean; message: string }> => {
  const response = await apiRequest<{ success: boolean; message: string }>(`/api/meesho/playwright/cancel/${sessionId}`, { method: 'POST' });
  return response.data;
};

/**
 * Poll a Playwright session until completion or timeout.
 * 
 * @param sessionId - The session ID to poll
 * @param onStatusChange - Callback for status updates
 * @param pollInterval - Interval in ms (default: 2000)
 * @param timeout - Max time in ms (default: 300000 = 5 min)
 */
export const pollPlaywrightSession = async (
  sessionId: string,
  onStatusChange?: (status: PlaywrightSessionStatus) => void,
  pollInterval = 2000,
  timeout = 300000
): Promise<PlaywrightSessionStatus> => {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const status = await getPlaywrightSessionStatus(sessionId);
    
    if (onStatusChange) {
      onStatusChange(status);
    }
    
    // Terminal states
    if (['completed', 'failed', 'cancelled'].includes(status.status)) {
      return status;
    }
    
    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }
  
  // Timeout - cancel session
  await cancelPlaywrightSession(sessionId);
  return {
    session_id: sessionId,
    status: 'failed',
    error: 'Session timed out'
  };
};
