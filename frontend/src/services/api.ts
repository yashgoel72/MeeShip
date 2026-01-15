// Centralized API service for Meesho Image Optimizer
import axios, { AxiosRequestConfig, AxiosResponse } from "axios";

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || "";

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
