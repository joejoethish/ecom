import React, { useState } from 'react';
import { AppliedCoupon } from '@/types';
import { useAppDispatch } from '@/hooks/redux';
import { applyCoupon, removeCoupon } from '@/store/slices/cartSlice';

interface CouponSectionProps {
  appliedCoupons: AppliedCoupon[];
  loading?: boolean;
}

const CouponSection: React.FC<CouponSectionProps> = ({ appliedCoupons, loading = false }) => {
  const dispatch = useAppDispatch();
  const [couponCode, setCouponCode] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleApplyCoupon = (e: React.FormEvent) => {
    e.preventDefault();
    if (couponCode.trim()) {
      dispatch(applyCoupon(couponCode.trim()));
      setCouponCode('');
    }
  };

  const handleRemoveCoupon = (couponId: string) => {
    dispatch(removeCoupon(couponId));
  };

  const totalDiscount = appliedCoupons.reduce((total, applied) => total + applied.discount_amount, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <div className="text-green-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </div>
          <h3 className="font-medium text-gray-900">Apply Coupon</h3>
          {totalDiscount > 0 && (
            <span className="text-sm text-green-600 font-medium">
              (₹{totalDiscount.toLocaleString()} saved)
            </span>
          )}
        </div>
        <div className="text-gray-400">
          <svg 
            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-200">
          {/* Applied Coupons */}
          {appliedCoupons.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Applied Coupons</h4>
              <div className="space-y-2">
                {appliedCoupons.map((applied) => (
                  <div key={applied.coupon.id} className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <div className="text-green-600">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {applied.coupon.code}
                        </div>
                        <div className="text-xs text-gray-600">
                          {applied.coupon.name}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-green-600">
                        -₹{applied.discount_amount.toLocaleString()}
                      </span>
                      <button
                        onClick={() => handleRemoveCoupon(applied.coupon.id)}
                        className="text-red-500 hover:text-red-700 p-1"
                        title="Remove coupon"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Apply New Coupon */}
          <form onSubmit={handleApplyCoupon} className="flex gap-2">
            <input
              type="text"
              value={couponCode}
              onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
              placeholder="Enter coupon code"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!couponCode.trim() || loading}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Applying...' : 'Apply'}
            </button>
          </form>

          {/* Popular Coupons */}
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Popular Coupons</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {['SAVE10', 'WELCOME20', 'FIRST50'].map((code) => (
                <button
                  key={code}
                  onClick={() => setCouponCode(code)}
                  className="text-left p-2 border border-gray-200 rounded-md hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  disabled={appliedCoupons.some(applied => applied.coupon.code === code)}
                >
                  <div className="text-sm font-medium text-gray-900">{code}</div>
                  <div className="text-xs text-gray-500">
                    {code === 'SAVE10' && 'Save 10% on orders above ₹500'}
                    {code === 'WELCOME20' && 'Get 20% off on first order'}
                    {code === 'FIRST50' && 'Flat ₹50 off on orders above ₹300'}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CouponSection;