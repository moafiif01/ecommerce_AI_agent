import api from "@/lib/api";

const CART_SESSION_KEY = "guest_cart_session_id";

export interface CartApiResponse {
  success: boolean;
  cart: {
    id: string;
    itemCount: number;
    subtotal: number;
    tax: number;
    shipping: number;
    discount: number;
    total: number;
    items: Array<{
      id: string;
      productId: string;
      productName: string;
      quantity: number;
      unitPrice: number;
      lineTotal: number;
    }>;
  };
}

export interface AddCartItemInput {
  productId: string;
  unitPrice: number;
  quantity?: number;
}

export function getCartSessionId(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const existing = localStorage.getItem(CART_SESSION_KEY);
  if (existing) {
    return existing;
  }

  const generated =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `session-${Date.now()}-${Math.random().toString(36).slice(2)}`;

  localStorage.setItem(CART_SESSION_KEY, generated);
  return generated;
}

export async function getOrCreateCart(): Promise<CartApiResponse["cart"]> {
  const sessionId = getCartSessionId();
  const response = await api.post<CartApiResponse>(`/cart?session_id=${encodeURIComponent(sessionId)}`);
  return response.data.cart;
}

export async function addItemToCart(
  cartId: string,
  productId: string,
  quantity: number,
  unitPrice: number,
): Promise<CartApiResponse["cart"]> {
  const response = await api.post<CartApiResponse>(`/cart/${cartId}/items`, {
    product_id: productId,
    quantity,
    unit_price: unitPrice,
  });
  return response.data.cart;
}

export async function addItemsToCart(
  items: AddCartItemInput[],
): Promise<CartApiResponse["cart"]> {
  const validItems = items.filter((item) => item.productId && item.unitPrice > 0);
  if (validItems.length === 0) {
    throw new Error("No valid products to add to cart");
  }

  const cart = await getOrCreateCart();
  let updatedCart = cart;

  for (const item of validItems) {
    updatedCart = await addItemToCart(
      updatedCart.id,
      item.productId,
      item.quantity ?? 1,
      item.unitPrice,
    );
  }

  return updatedCart;
}

export async function removeCartItem(cartId: string, itemId: string): Promise<CartApiResponse["cart"]> {
  const response = await api.delete<CartApiResponse>(`/cart/${cartId}/items/${itemId}`);
  return response.data.cart;
}

export async function clearCartItems(cartId: string): Promise<CartApiResponse["cart"]> {
  const response = await api.post<CartApiResponse>(`/cart/${cartId}/clear`);
  return response.data.cart;
}
