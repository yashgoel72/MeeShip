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
  const token = localStorage.getItem("jwt");
  const abortController = new AbortController();
  
  // We need to use fetch + ReadableStream since EventSource doesn't support POST
  const url = `${API_BASE_URL}/api/images/optimize-stream`;
  
  fetch(url, {
    method: "POST",
    body: formData,
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
    },
    signal: abortController.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text();
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
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE events from buffer
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer
        
        let currentEvent = "";
        let currentData = "";
        
        for (const line of lines) {
          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            currentData = line.slice(5).trim();
          } else if (line === "" && currentEvent && currentData) {
            // End of event, process it
            try {
              const data = JSON.parse(currentData);
              
              switch (currentEvent) {
                case "status":
                  callbacks.onStatus?.(data as StreamingStatus);
                  break;
                case "variant":
                  callbacks.onVariant?.(data as StreamingVariant);
                  break;
                case "error":
                  callbacks.onError?.(data as StreamingError);
                  break;
                case "complete":
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
