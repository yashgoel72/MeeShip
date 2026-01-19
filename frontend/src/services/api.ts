// Centralized API service for Meesho Image Optimizer
import axios, { AxiosRequestConfig, AxiosResponse } from "axios";

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || "";

export const apiRequest = async <T = any>(
  endpoint: string,
  config: AxiosRequestConfig = {}
): Promise<AxiosResponse<T>> => {
  const token = localStorage.getItem("jwt");
  const headers = {
    ...config.headers,
    Authorization: token ? `Bearer ${token}` : undefined,
  };
  return axios({
    baseURL: API_BASE_URL,
    url: endpoint,
    ...config,
    headers,
  });
};

export const signup = (data: { email: string; password: string; full_name: string }) =>
  apiRequest("/api/auth/signup", { method: "POST", data });

export const login = (data: { email: string; password: string }) =>
  apiRequest("/api/auth/login", { method: "POST", data });

export const requestOtp = (data: { email: string }) =>
  apiRequest("/api/auth/request-otp", { method: "POST", data });

export const loginOtp = (data: { email: string; otp: string }) =>
  apiRequest("/api/auth/login-otp", { method: "POST", data });

export const getMe = () =>
  apiRequest("/api/auth/me", { method: "GET" });

export const uploadImage = (formData: FormData) =>
  apiRequest("/api/images/optimize", { method: "POST", data: formData, headers: { "Content-Type": "multipart/form-data" } });

// === Streaming Optimization Types ===

export type StreamingVariant = {
  index: number;
  tile_index: number;
  variant_index: number;
  variant_type: string;
  url: string;
  tile_name: string;
  variant_label: string;
  completed: number;
  total: number;
  progress: number;
};

export type StreamingStatus = {
  stage: "generating" | "processing" | "uploading";
  progress: number;
  message: string;
};

export type StreamingError = {
  message: string;
  recoverable: boolean;
  variant_index?: number;
  stage_metrics?: Record<string, any>;
};

export type StreamingComplete = {
  id: string;
  total: number;
  successful: number;
  failed: number;
  grid_url: string | null;
  original_url: string | null;
  variant_urls: string[];
  processing_time_ms: number;
  metrics: Record<string, any>;
};

export type StreamingCallbacks = {
  onStatus?: (status: StreamingStatus) => void;
  onVariant?: (variant: StreamingVariant) => void;
  onError?: (error: StreamingError) => void;
  onComplete?: (result: StreamingComplete) => void;
};

/**
 * Mock SSE stream for testing frontend parsing.
 * This simulates the exact format the backend returns.
 */
const mockStreamOptimization = (
  formData: FormData,
  callbacks: StreamingCallbacks
): { abort: () => void } => {
  let aborted = false;
  
  const mockEvents = [
    { event: "status", data: { stage: "generating", progress: 0, message: "Generating your product images with AI..." } },
    { event: "status", data: { stage: "processing", progress: 15, message: "AI generation complete. Creating shipping variants..." } },
    { event: "status", data: { stage: "uploading", progress: 20, message: "Generating and uploading 30 shipping-optimized variants..." } },
  ];
  
  // Add 30 variant events
  const tileNames = ["Hero White", "Styled Neutral Context", "Dramatic Light & Detail", "Secondary Clean Angle", "Dark Luxury Editorial", "Floating / Lightness Shot"];
  const variantTypes = ["hero_compact", "standard", "detail_focus", "dynamic_angle", "warm_minimal"];
  const variantLabels = ["Hero Compact", "Standard Frame", "Detail Focus", "Dynamic Angle", "Warm Minimal"];
  
  let globalIndex = 0;
  for (let tile = 0; tile < 6; tile++) {
    for (let variant = 0; variant < 5; variant++) {
      mockEvents.push({
        event: "variant",
        data: {
          index: globalIndex,
          tile_index: tile,
          variant_index: variant,
          variant_type: variantTypes[variant],
          url: `https://picsum.photos/seed/${globalIndex}/400/600`,
          tile_name: tileNames[tile],
          variant_label: variantLabels[variant],
          completed: globalIndex + 1,
          total: 30,
          progress: 22 + Math.floor((globalIndex / 30) * 73),
        }
      });
      globalIndex++;
    }
  }
  
  // Add complete event
  mockEvents.push({
    event: "complete",
    data: {
      id: "mock-id-12345",
      total: 30,
      successful: 30,
      failed: 0,
      grid_url: "https://picsum.photos/seed/grid/800/1200",
      original_url: "https://picsum.photos/seed/original/400/400",
      variant_urls: Array.from({ length: 30 }, (_, i) => `https://picsum.photos/seed/${i}/400/600`),
      processing_time_ms: 5000,
      metrics: {},
    }
  });
  
  // Emit events with delays
  (async () => {
    for (const evt of mockEvents) {
      if (aborted) break;
      
      await new Promise(r => setTimeout(r, evt.event === "variant" ? 100 : 300));
      
      if (aborted) break;
      
      console.log(`[MOCK SSE] ${evt.event}:`, evt.data);
      
      switch (evt.event) {
        case "status":
          callbacks.onStatus?.(evt.data as StreamingStatus);
          break;
        case "variant":
          callbacks.onVariant?.(evt.data as StreamingVariant);
          break;
        case "complete":
          callbacks.onComplete?.(evt.data as StreamingComplete);
          break;
      }
    }
  })();
  
  return {
    abort: () => { aborted = true; },
  };
};

/**
 * Stream optimization with Server-Sent Events.
 * Variants are delivered incrementally as they're generated.
 * 
 * @param formData - FormData with the image file
 * @param callbacks - Event callbacks for status, variants, errors, and completion
 * @returns Abort controller to cancel the stream
 */
export const streamOptimization = (
  formData: FormData,
  callbacks: StreamingCallbacks
): { abort: () => void } => {
  // USE MOCK FOR TESTING - change to false to use real backend
  const USE_MOCK = false;
  if (USE_MOCK) {
    console.log('[SSE] Using MOCK stream for testing');
    return mockStreamOptimization(formData, callbacks);
  }
  
  const token = localStorage.getItem("jwt");
  const abortController = new AbortController();
  
  // We need to use fetch + ReadableStream since EventSource doesn't support POST
  const url = `${API_BASE_URL}/api/images/optimize-stream`;
  
  console.log('[SSE] Starting stream to:', url);
  
  fetch(url, {
    method: "POST",
    body: formData,
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
    },
    signal: abortController.signal,
  })
    .then(async (response) => {
      console.log('[SSE] Response received:', response.status, response.ok);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('[SSE] Error response:', errorText);
        callbacks.onError?.({
          message: `Server error: ${response.status} - ${errorText}`,
          recoverable: false,
        });
        return;
      }
      
      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError?.({
          message: "Failed to get response stream",
          recoverable: false,
        });
        return;
      }
      
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "";
      let currentData = "";
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('[SSE] Stream ended');
          break;
        }
        
        const chunk = decoder.decode(value, { stream: true });
        console.log('[SSE] Raw chunk:', JSON.stringify(chunk));
        buffer += chunk;
        
        // Parse SSE events from buffer - handle both \r\n and \n
        const lines = buffer.replace(/\r\n/g, '\n').split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer
        
        console.log('[SSE] Parsed lines:', lines.length, lines);
        
        for (const line of lines) {
          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
            console.log('[SSE] Got event type:', currentEvent);
          } else if (line.startsWith("data:")) {
            currentData = line.slice(5).trim();
            console.log('[SSE] Got data for event:', currentEvent);
          } else if (line.startsWith(":")) {
            // Comment/ping, ignore
            continue;
          } else if (line === "" && currentEvent && currentData) {
            // End of event, process it
            try {
              const data = JSON.parse(currentData);
              
              switch (currentEvent) {
                case "status":
                  console.log('[SSE] Status event:', data);
                  callbacks.onStatus?.(data as StreamingStatus);
                  break;
                case "variant":
                  console.log('[SSE] Variant event:', data.completed, '/', data.total);
                  callbacks.onVariant?.(data as StreamingVariant);
                  break;
                case "error":
                  console.error('[SSE] Error event:', data);
                  callbacks.onError?.(data as StreamingError);
                  break;
                case "complete":
                  console.log('[SSE] Complete event:', data);
                  callbacks.onComplete?.(data as StreamingComplete);
                  break;
              }
            } catch (e) {
              console.warn("Failed to parse SSE event:", currentEvent, currentData, e);
            }
            
            currentEvent = "";
            currentData = "";
          }
        }
      }
    })
    .catch((error) => {
      if (error.name === "AbortError") {
        console.log("Stream aborted by user");
        return;
      }
      callbacks.onError?.({
        message: `Stream error: ${error.message}`,
        recoverable: false,
      });
    });
  
  return {
    abort: () => abortController.abort(),
  };
};
