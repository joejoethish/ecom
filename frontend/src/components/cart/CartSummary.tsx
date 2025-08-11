import React from 'react';
import Link from 'next/link';
import { ROUTES } from '@/constants';

interface CartSummaryProps {
  itemCount: number;
  subtotal: number;
  discountAmount: number;
  totalAmount: number;
  loading?: boolean;
}

  itemCount,
  subtotal,
  discountAmount,
  totalAmount,
  loading = false
}) => {
  const shippingAmount = subtotal > 500 ? 0 : 50; // Free shipping above ₹500
  const taxAmount = Math.round(totalAmount * 0.18); // 18% GST
  const finalAmount = totalAmount + shippingAmount + taxAmount;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 sticky top-4">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Order Summary</h2>
      </div>
      
      <div className="p-4 space-y-3">
        {/* Items Count */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Items ({itemCount})</span>
          <span className="font-medium">₹{subtotal.toLocaleString()}</span>
        </div>

        {/* Discount */}
        {discountAmount > 0 && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Discount</span>
            <span className="font-medium text-green-600">-₹{discountAmount.toLocaleString()}</span>
          </div>
        )}

        {/* Shipping */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Shipping</span>
          <div className="text-right">
            {shippingAmount === 0 ? (
              <div>
                <span className="font-medium text-green-600">FREE</span>
                <div className="text-xs text-gray-500">Above ₹500</div>
              </div>
            ) : (
              <span className="font-medium">₹{shippingAmount}</span>
            )}
          </div>
        </div>

        {/* Tax */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Tax (GST 18%)</span>
          <span className="font-medium">₹{taxAmount.toLocaleString()}</span>
        </div>

        <hr className="border-gray-200" />

        {/* Total */}
        <div className="flex justify-between text-base font-semibold">
          <span className="text-gray-900">Total</span>
          <span className="text-gray-900">₹{finalAmount.toLocaleString()}</span>
        </div>

        {/* Savings */}
        {discountAmount > 0 && (
          <div className="text-sm text-green-600 font-medium">
            You saved ₹{discountAmount.toLocaleString()} on this order!
          </div>
        )}

        {/* Free Shipping Progress */}
        {subtotal < 500 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-sm text-blue-800 font-medium mb-1">
              Add ₹{(500 - subtotal).toLocaleString()} more for FREE shipping
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min((subtotal / 500) * 100, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Checkout Button */}
      <div className="p-4 border-t border-gray-200">
        <Link href={ROUTES.CHECKOUT}>
          <button
            disabled={itemCount === 0 || loading}
            className="w-full bg-orange-500 text-white py-3 px-4 rounded-lg font-semibold hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? &apos;Processing...&apos; : `Proceed to Checkout (₹${finalAmount.toLocaleString()})`}
          </button>
        </Link>
        
        <div className="mt-2 text-center">
          <Link href={ROUTES.PRODUCTS} className="text-sm text-blue-600 hover:text-blue-800">
            Continue Shopping
          </Link>
        </div>
      </div>

      {/* Security Badge */}
      <div className="px-4 pb-4">
        <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
          <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span>Secure checkout with 256-bit SSL encryption</span>
        </div>
      </div>
    </div>
  );
};

export default CartSummary;