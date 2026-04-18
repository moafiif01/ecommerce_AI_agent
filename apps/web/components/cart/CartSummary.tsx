'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { ShoppingCart, X, Trash2 } from 'lucide-react';
import { clearCartItems, getOrCreateCart, removeCartItem } from '@/lib/cart';

interface CartItem {
  id: string;
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  lineTotal: number;
}

interface Cart {
  id: string;
  itemCount: number;
  subtotal: number;
  tax: number;
  shipping: number;
  discount: number;
  total: number;
  items: CartItem[];
}

export function CartSummary() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch cart on component mount
  useEffect(() => {
    fetchCart();
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchCart();
    }
  }, [isOpen]);

  const fetchCart = async () => {
    try {
      const resolvedCart = await getOrCreateCart();
      setCart(resolvedCart);
    } catch (error) {
      console.error('Failed to fetch cart:', error);
    }
  };

  const removeItem = async (itemId: string) => {
    if (!cart) return;

    setIsLoading(true);
    try {
      const updatedCart = await removeCartItem(cart.id, itemId);
      setCart(updatedCart);
    } catch (error) {
      console.error('Failed to remove item:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearCart = async () => {
    if (!window.confirm('Clear all items from cart?')) return;
    if (!cart) return;

    setIsLoading(true);
    try {
      const clearedCart = await clearCartItems(cart.id);
      setCart(clearedCart);
      setIsOpen(false);
    } catch (error) {
      console.error('Failed to clear cart:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const itemCount = cart?.itemCount || 0;

  return (
    <div className="relative">
      {/* Cart Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
      >
        <ShoppingCart className="w-6 h-6" />
        {itemCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {itemCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-gray-900 border dark:border-gray-700 rounded-lg shadow-lg z-50">
          <div className="p-4 border-b dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">Shopping Cart</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Items List */}
          <div className="max-h-64 overflow-y-auto p-4">
            {!cart || itemCount === 0 ? (
              <p className="text-gray-500 text-center py-8">Your cart is empty</p>
            ) : (
              <div className="space-y-3">
                {cart.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-sm truncate">{item.productName}</p>
                      <p className="text-xs text-gray-500">
                        {item.quantity} × ${item.unitPrice.toFixed(2)}
                      </p>
                      <p className="text-sm font-semibold">${item.lineTotal.toFixed(2)}</p>
                    </div>
                    <button
                      onClick={() => removeItem(item.id)}
                      disabled={isLoading}
                      className="p-1 text-gray-500 hover:text-red-500 transition disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Totals */}
          {cart && itemCount > 0 && (
            <>
              <div className="border-t dark:border-gray-700 p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Subtotal:</span>
                  <span>${cart.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Tax (8%):</span>
                  <span>${cart.tax.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Shipping:</span>
                  <span>
                    {cart.shipping === 0 ? (
                      <span className="text-green-600">FREE</span>
                    ) : (
                      `$${cart.shipping.toFixed(2)}`
                    )}
                  </span>
                </div>
                {cart.discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount:</span>
                    <span>-${cart.discount.toFixed(2)}</span>
                  </div>
                )}
                <div className="border-t dark:border-gray-700 pt-2 flex justify-between font-bold text-base">
                  <span>Total:</span>
                  <span>${cart.total.toFixed(2)}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="p-4 border-t dark:border-gray-700 space-y-2">
                <Link
                  href="/checkout"
                  onClick={() => setIsOpen(false)}
                  className="block w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition text-center font-medium"
                >
                  Proceed to Checkout
                </Link>
                <button
                  onClick={clearCart}
                  disabled={isLoading}
                  className="w-full py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition disabled:opacity-50"
                >
                  Clear Cart
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
