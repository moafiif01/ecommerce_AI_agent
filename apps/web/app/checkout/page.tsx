'use client';

import React, { useEffect, useState } from 'react';
import { ChevronLeft, Loader } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';
import { getOrCreateCart } from '@/lib/cart';

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

interface ShippingMethod {
  id: string;
  name: string;
  days: string;
  cost: number;
}

export default function CheckoutPage() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [shippingMethods, setShippingMethods] = useState<ShippingMethod[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    customerEmail: '',
    shippingAddress: '',
    shippingCity: '',
    shippingState: '',
    shippingZip: '',
    shippingCountry: 'US',
    shippingMethod: 'standard',
  });

  useEffect(() => {
    const fetchCheckoutData = async () => {
      setIsLoading(true);
      try {
        const currentCart = await getOrCreateCart();
        setCart(currentCart);

        // Fetch shipping methods
        const shippingResponse = await api.get(
          `/checkout/methods?subtotal=${currentCart?.subtotal || 0}`
        );
        setShippingMethods(shippingResponse.data.methods || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load checkout');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCheckoutData();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleShippingMethodChange = async (methodId: string) => {
    setFormData((prev) => ({
      ...prev,
      shippingMethod: methodId,
    }));

    // Recalculate shipping
    const response = await api.post('/checkout/shipping', {
        subtotal: cart?.subtotal || 0,
        method: methodId,
    });

    if (!response.data?.success) {
      setError('Failed to recalculate shipping');
    }
  };

  const validateForm = (): boolean => {
    if (!formData.customerEmail) return false;
    if (!formData.shippingAddress) return false;
    if (!formData.shippingCity) return false;
    if (!formData.shippingZip) return false;
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      setError('Please fill in all required fields');
      return;
    }

    if (!cart) {
      setError('Cart not found');
      return;
    }

    setIsProcessing(true);
    try {
      // Validate checkout first
      const validateResponse = await api.post('/checkout/validate', {
          cartId: cart.id,
          shippingAddress: `${formData.shippingAddress}, ${formData.shippingCity}, ${formData.shippingState} ${formData.shippingZip}`,
      });

      if (!validateResponse.data?.success) {
        throw new Error(validateResponse.data?.message || 'Validation failed');
      }

      // Process checkout
      const response = await api.post('/checkout/process', {
          cartId: cart.id,
          customerEmail: formData.customerEmail,
          shippingAddress: `${formData.shippingAddress}, ${formData.shippingCity}, ${formData.shippingState} ${formData.shippingZip}`,
          shippingMethod: formData.shippingMethod,
      });

      if (!response.data?.success) {
        throw new Error(response.data?.message || 'Checkout failed');
      }

      const result = response.data;
      setSuccess(true);
      setCart(null);

      // Redirect to order confirmation
      setTimeout(() => {
        window.location.href = '/orders';
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout failed');
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!cart || cart.itemCount === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <h1 className="text-2xl font-bold">Your cart is empty</h1>
        <Link
          href="/"
          className="text-blue-600 hover:underline flex items-center gap-2"
        >
          <ChevronLeft className="w-5 h-5" />
          Continue Shopping
        </Link>
      </div>
    );
  }

  const selectedShippingMethod = shippingMethods.find(
    (m) => m.id === formData.shippingMethod
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <Link href="/" className="flex items-center gap-2 text-blue-600 hover:underline mb-8">
          <ChevronLeft className="w-5 h-5" />
          Back to Shopping
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Checkout Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="space-y-8">
              {error && (
                <div className="p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg text-red-700">
                  {error}
                </div>
              )}

              {/* Shipping Address */}
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
                <h2 className="text-xl font-bold mb-4">Shipping Address</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Email Address *</label>
                    <input
                      type="email"
                      name="customerEmail"
                      value={formData.customerEmail}
                      onChange={handleInputChange}
                      required
                      className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Street Address *</label>
                    <input
                      type="text"
                      name="shippingAddress"
                      value={formData.shippingAddress}
                      onChange={handleInputChange}
                      required
                      className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">City *</label>
                      <input
                        type="text"
                        name="shippingCity"
                        value={formData.shippingCity}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">State/Province *</label>
                      <input
                        type="text"
                        name="shippingState"
                        value={formData.shippingState}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Zip Code *</label>
                      <input
                        type="text"
                        name="shippingZip"
                        value={formData.shippingZip}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Country</label>
                      <select
                        name="shippingCountry"
                        value={formData.shippingCountry}
                        onChange={handleInputChange}
                        className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                      >
                        <option value="US">United States</option>
                        <option value="CA">Canada</option>
                        <option value="GB">United Kingdom</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {/* Shipping Method */}
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
                <h2 className="text-xl font-bold mb-4">Shipping Method</h2>
                <div className="space-y-3">
                  {shippingMethods.map((method) => (
                    <label key={method.id} className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700">
                      <input
                        type="radio"
                        name="shippingMethod"
                        value={method.id}
                        checked={formData.shippingMethod === method.id}
                        onChange={() => handleShippingMethodChange(method.id)}
                        className="w-4 h-4"
                      />
                      <div className="ml-3 flex-1">
                        <p className="font-medium">{method.name}</p>
                        <p className="text-sm text-gray-500">{method.days}</p>
                      </div>
                      <p className="font-bold">
                        {method.cost === 0 ? 'FREE' : `$${method.cost.toFixed(2)}`}
                      </p>
                    </label>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isProcessing}
                className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center justify-center gap-2 font-bold"
              >
                {isProcessing && <Loader className="w-5 h-5 animate-spin" />}
                {isProcessing ? 'Processing...' : 'Place Order'}
              </button>
            </form>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg sticky top-8">
              <h2 className="text-xl font-bold mb-4">Order Summary</h2>

              {/* Items */}
              <div className="space-y-3 mb-4 pb-4 border-b dark:border-gray-700">
                {cart.items.map((item) => (
                  <div key={item.id} className="flex justify-between text-sm">
                    <div>
                      <p className="font-medium truncate">{item.productName}</p>
                      <p className="text-gray-500">{item.quantity} × ${item.unitPrice.toFixed(2)}</p>
                    </div>
                    <p className="font-semibold">${item.lineTotal.toFixed(2)}</p>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Subtotal</span>
                  <span>${cart.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Tax (8%)</span>
                  <span>${cart.tax.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Shipping</span>
                  <span>
                    {selectedShippingMethod?.cost === 0 ? (
                      <span className="text-green-600 font-semibold">FREE</span>
                    ) : (
                      `$${selectedShippingMethod?.cost.toFixed(2) || '0.00'}`
                    )}
                  </span>
                </div>
                {cart.discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount</span>
                    <span>-${cart.discount.toFixed(2)}</span>
                  </div>
                )}
                <div className="border-t dark:border-gray-700 pt-2 flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>${cart.total.toFixed(2)}</span>
                </div>
              </div>

              {success && (
                <div className="mt-4 p-4 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg text-green-700">
                  Order placed successfully! Redirecting...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
