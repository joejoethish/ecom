import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { 
  fetchPaymentMethods, 
  setSelectedPaymentMethod 
} from '@/store/slices/paymentSlice';
import { PaymentMethod } from '@/types';
import Image from 'next/image';

interface PaymentMethodSelectorProps {
  onMethodSelect?: (methodId: string) => void;
}

  const dispatch = useAppDispatch();
    (state: RootState) => state.payments
  );

  useEffect(() => {
    dispatch(fetchPaymentMethods());
  }, [dispatch]);

  const handleMethodSelect = (methodId: string) => {
    dispatch(setSelectedPaymentMethod(methodId));
    if (onMethodSelect) {
      onMethodSelect(methodId);
    }
  };

  // Group payment methods by type for better organization
    (acc, method) => {
      const type = method.method_type;
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(method);
      return acc;
    },
    {} as Record<string, PaymentMethod[]>
  );

    &apos;CARD&apos;: &apos;Credit/Debit Cards&apos;,
    &apos;UPI&apos;: &apos;UPI Payment&apos;,
    &apos;WALLET&apos;: &apos;Digital Wallets&apos;,
    &apos;NETBANKING&apos;: &apos;Net Banking&apos;,
    &apos;COD&apos;: &apos;Cash on Delivery&apos;,
    &apos;GIFT_CARD&apos;: &apos;Gift Cards&apos;,
    &apos;IMPS&apos;: &apos;IMPS Transfer&apos;,
    &apos;RTGS&apos;: &apos;RTGS Transfer&apos;,
    &apos;NEFT&apos;: &apos;NEFT Transfer&apos;,
  };

  if (loading) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="space-y-2">
              <div className="h-10 bg-gray-200 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        <p>Error loading payment methods: {error}</p>
        <button 
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          onClick={() => dispatch(fetchPaymentMethods())}
        >
          Retry
        </button>
      </div>
    );
  }

  if (paymentMethods.length === 0) {
    return (
      <div className="p-4 bg-yellow-50 text-yellow-700 rounded-lg">
        <p>No payment methods available at the moment. Please try again later.</p>
      </div>
    );
  }

  return (
    <div className="payment-methods-container">
      <h3 className="text-lg font-medium mb-4">Select Payment Method</h3>
      
      {Object.entries(groupedMethods).map(([type, methods]) => (
        <div key={type} className="mb-6">
          <h4 className="text-md font-medium mb-2">{methodTypeLabels[type] || type}</h4>
          <div className="space-y-2">
            {methods.map((method) => (
              <div 
                key={method.id}
                className={`
                  p-4 border rounded-lg cursor-pointer transition-all
                  ${selectedPaymentMethod === method.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'}
                `}
                onClick={() => handleMethodSelect(method.id)}
              >
                <div className="flex items-center">
                  <div className="flex-shrink-0 w-8 h-8 mr-3">
                    {method.icon ? (
                      <Image 
                        src={method.icon} 
                        alt={method.name} 
                        width={32} 
                        height={32} 
                        className="object-contain"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-xs">{method.name.substring(0, 2)}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex-grow">
                    <h5 className="font-medium">{method.name}</h5>
                    {method.description && (
                      <p className="text-sm text-gray-500">{method.description}</p>
                    )}
                  </div>
                  <div className="flex-shrink-0">
                    <input
                      type="radio"
                      checked={selectedPaymentMethod === method.id}
                      onChange={() => handleMethodSelect(method.id)}
                      className=&quot;h-5 w-5 text-blue-600&quot;
                    />
                  </div>
                </div>
                
                {method.processing_fee_percentage > 0 || method.processing_fee_fixed > 0 ? (
                  <div className="mt-2 text-xs text-gray-500">
                    Processing fee: 
                    {method.processing_fee_percentage > 0 && (
                      <span> {method.processing_fee_percentage}%</span>
                    )}
                    {method.processing_fee_percentage > 0 && method.processing_fee_fixed > 0 && (
                      <span> + </span>
                    )}
                    {method.processing_fee_fixed > 0 && (
                      <span>${method.processing_fee_fixed.toFixed(2)}</span>
                    )}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default PaymentMethodSelector;