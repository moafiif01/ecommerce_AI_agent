import api from "@/lib/api";
import { Order } from "@/types";

export interface CreateOrderItemInput {
  product_id: string;
  quantity: number;
}

export interface CreateOrderInput {
  customer_email: string;
  shipping_address: string;
  shipping_method?: string;
  shipping_fee?: number;
  items: CreateOrderItemInput[];
}

export async function createOrder(payload: CreateOrderInput) {
  const response = await api.post("/orders/", payload);
  return response.data as { success: boolean; order?: Order; message?: string };
}

export async function trackOrder(orderNumber: string, email?: string) {
  const response = await api.get("/orders/track", {
    params: {
      order_number: orderNumber,
      ...(email ? { email } : {}),
    },
  });

  return response.data as { success: boolean; order?: Order; message?: string };
}

export async function listOrders(email?: string, limit = 20) {
  const response = await api.get("/orders/", {
    params: {
      ...(email ? { email } : {}),
      limit,
    },
  });

  return response.data as {
    success: boolean;
    count: number;
    orders: Order[];
    message?: string;
  };
}

export async function getOrderById(orderId: string) {
  const response = await api.get(`/orders/${orderId}`);
  return response.data as { success: boolean; order?: Order; message?: string };
}

export async function cancelOrder(orderId: string, reason: string) {
  const response = await api.post(`/orders/${orderId}/cancel`, { reason });
  return response.data as { success: boolean; order?: Order; message?: string };
}
