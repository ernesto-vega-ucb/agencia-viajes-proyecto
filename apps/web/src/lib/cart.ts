import type { BookingRequestItem } from "../types/domain";

const CART_KEY = "agencia:cart";

export function getCart(): BookingRequestItem[] {
  try {
    const raw = localStorage.getItem(CART_KEY);
    return raw ? (JSON.parse(raw) as BookingRequestItem[]) : [];
  } catch {
    return [];
  }
}

export function addToCart(item: BookingRequestItem): BookingRequestItem[] {
  const cart = getCart();
  cart.push(item);
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  return cart;
}

export function clearCart(): void {
  localStorage.removeItem(CART_KEY);
}