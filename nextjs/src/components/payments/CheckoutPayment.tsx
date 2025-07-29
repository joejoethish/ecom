import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { fetchPaymentMethods, fetchCurrencies } from '@/store/slices/paymentSlice';
import { PaymentMethod } from '@/types';
import PaymentMethodSelector from './PaymentMethodSelector';
import CurrencySelector from './CurrencySelector';
import CreditCardPayment from './CreditCardPayment';
import WalletPayment from './WalletPayment';
import GiftCardPayment from './GiftCardPayment';
import PaymentProcessor from './PaymentProcessor';
import { CardFormData } from './CreditCardPayment';

interface CheckoutPaymentProps {
  orderId: string;
  amount: number;
  onPaymentSuccess: (paymentId: string) => void;
  onPaymentFailure: (error: string) => void;
  onCancel: () => void;
}

const CheckoutPayment: React.FC<CheckoutPaymentProps> = ({
  orderId,
  amount,
  onPaymentSuccess,
  onPaymentFailure,
  onCancel
}) => {
  const dispatch = useAppDispatch();
  const { 
    paymentMethods, 
    selectedPaymentMethod, 
    selectedCurrency,
    loading 
  } = useSelector((state: RootState) => state.payments);

  const [convertedAmount, setConvertedAmount] = useState(amount);
  const [showPaymentProcessor, setShowPaymentProcessor] = useState(false);
  const [paymentData, setPaymentData] = useState<any>(null);

  useEffect(() => {
    dispatch(fetchPaymentMethods());
    dispatch(fetchCurrencies());
  }, [dispatch]);

  const handleCurrencyChange = (_currency: string, newAmount: number) => {
    setConvertedAmount(newAmount);
  };

  const handlePaymentMethodSelect = (methodId: string) => {
    // Reset payment data when method changes
    setPaymentData(null);
    setShowPaymentProcessor(false);
  };

  const handleCardPayment = (cardData: CardFormData) => {
    setPaymentData({
      type: 'card',
      data: cardData
    });
    setShowPaymentProcessor(true);
  };

  const handleWalletPayment = () => {
    setPaymentData({
      type: 'wallet'
    });
    setShowPaymentProcessor(true);
  };

  const handleGiftCardPayment = (giftCardCode: string) => {
    setPaymentData({
      type: 'gift_card',
      data: { code: giftCardCode }
    });
    setShowPaymentProcessor(true);
  };

  // Get the selected payment method object
  const selectedMethod = paymentMethods.find(method => method.id === selectedPaymentMethod);

  // Render the appropriate payment form based on the selected method
  const renderPaymentForm = () => {
    if (!selectedMethod) return null;

    switch (selectedMethod.method_type) {
      case 'CARD':
        return (
          <CreditCardPayment 
            amount={convertedAmount} 
            onProceed={handleCardPayment} 
          />
        );
      case 'WALLET':
        return (
          <WalletPayment 
            amount={convertedAmount} 
            onProceed={handleWalletPayment} 
          />
        );
      case 'GIFT_CARD':
        return (
          <GiftCardPayment 
            amount={convertedAmount} 
            onProceed={handleGiftCardPayment} 
          />
        );
      case 'COD':
        return (
          <div className="p-4 border rounded-lg">
            <h4 className="text-lg font-medium mb-4">Cash on Delivery</h4>
            <p className="mb-4">You will pay {selectedCurrency} {convertedAmount.toFixed(2)} when your order is delivered.</p>
            <button
              onClick={() => {
                setPaymentData({ type: 'cod' });
                setShowPaymentProcessor(true);
              }}
              className="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Place Order with COD
            </button>
          </div>
        );
      default:
        return (
          <div className="p-4 border rounded-lg">
            <h4 className="text-lg font-medium mb-4">{selectedMethod.name}</h4>
            <p className="mb-4">Please proceed to complete your payment.</p>
            <button
              onClick={() => {
                setPaymentData({ type: selectedMethod.method_type.toLowerCase() });
                setShowPaymentProcessor(true);
              }}
              className="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Proceed to Payment
            </button>
          </div>
        );
    }
  };

  if (loading && paymentMethods.length === 0) {
    return (
      <div className="checkout-payment p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-6 bg-gray-200 rounded w-1/4"></div>
          <div className="h-40 bg-gray-200 rounded"></div>
          <div className="h-40 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-payment">
      {showPaymentProcessor ? (
        <PaymentProcessor
          orderId={orderId}
          amount={convertedAmount}
          onSuccess={onPaymentSuccess}
          onFailure={onPaymentFailure}
          onCancel={() => {
            setShowPaymentProcessor(false);
            setPaymentData(null);
          }}
        />
      ) : (
        <>
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-4">Payment</h2>
            <div className="mb-4">
              <CurrencySelector 
                amount={amount} 
                onCurrencyChange={handleCurrencyChange} 
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-1">
              <PaymentMethodSelector onMethodSelect={handlePaymentMethodSelect} />
            </div>
            
            <div className="md:col-span-2">
              {renderPaymentForm()}
            </div>
          </div>
          
          <div className="mt-6 flex justify-between">
            <button
              onClick={onCancel}
              className="px-6 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
            >
              Back
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default CheckoutPayment;