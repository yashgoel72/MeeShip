import { apiRequest } from "./api";
import type {
  CreateOrderRequest,
  CreateOrderResponse,
  CreditBalanceResponse,
  CreditPacksResponse,
  OrderHistoryResponse,
  VerifyPaymentRequest,
  VerifyPaymentResponse,
} from "../types";

export async function getCreditPacks(): Promise<CreditPacksResponse> {
  const res = await apiRequest<CreditPacksResponse>("/api/payments/packs", {
    method: "GET",
  });
  return res.data;
}

export async function createOrder(
  data: CreateOrderRequest
): Promise<CreateOrderResponse> {
  const res = await apiRequest<CreateOrderResponse>("/api/payments/create-order", {
    method: "POST",
    data,
  });
  return res.data;
}

export async function verifyPayment(
  data: VerifyPaymentRequest
): Promise<VerifyPaymentResponse> {
  const res = await apiRequest<VerifyPaymentResponse>("/api/payments/verify", {
    method: "POST",
    data,
  });
  return res.data;
}

export async function getCreditBalance(): Promise<CreditBalanceResponse> {
  const res = await apiRequest<CreditBalanceResponse>("/api/payments/balance", {
    method: "GET",
  });
  return res.data;
}

export async function getOrderHistory(params?: {
  limit?: number;
  offset?: number;
}): Promise<OrderHistoryResponse> {
  const res = await apiRequest<OrderHistoryResponse>("/api/payments/orders", {
    method: "GET",
    params,
  });
  return res.data;
}