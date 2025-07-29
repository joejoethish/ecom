import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { 
  createPayment, 
  verifyPayment, 
  getPaymentStatus,
  resetPaymentState
} from '@/store/slices/paymentSlice';
import { CardFormData } from './CreditCardPayment';

interface PaymentProcessorProps {
  orderId: string;
  amount: number;
  onSuccess: (paymentId: string) => void;
  onFailure: (error: string) => void;
  onCancel: () => void;
}

const PaymentProcessor: React.FC<PaymentProcessorProps> = ({
  orderId,
  amount,
  onSuccess,
  onFailure,
  onCancel
}) => {
  const dispatch = useAppDispatch();
  const { 
    selectedCurrency,
    selectedPaymentMethod,
    currentPayment,
    paymentProcessing,
    paymentSuccess,
    paymentError,
    giftCard
  } = useSelector((state: RootState) => state.payments);

  const [paymentInitiated, setPaymentInitiated] = useState(false);
  const [verificationData, setVerificationData] = useState<any>(null);
  const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
      dispatch(resetPaymentState());
    };
  }, [dispatch, statusCheckInterval]);

  // Handle payment success
  useEffect(() => {
    if (paymentSuccess && currentPayment) {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        setStatusCheckInterval(null);
      }
      onSuccess(currentPayment.id);
    }
  }, [paymentSuccess, currentPayment, statusCheckInterval, onSuccess]);

  // Handle payment error
  useEffect(() => {
    if (paymentError && !paymentProcessing) {
      onFailure(paymentError);
    }
  }, [paymentError, paymentProcessing, onFailure]);

  // Process payment with card data
  const processCardPayment = (cardData: CardFormData) => {
    if (!selectedPaymentMethod) return;

    const paymentData = {
      order_id: orderId,
      amount,
      currency_code: selectedCurrency,
      payment_method_id: selectedPaymentMethod,
      metadata: {
        card_last_four: cardData.cardNumber.replace(/\D/g, '').slice(-4),
        card_expiry: `${cardData.expiryMonth}/${cardData.expiryYear.slice(-2)}`,
        cardholder_name: cardData.cardholderName,
        save_card: cardData.saveCard
      }
    };

    dispatch(createPayment(paymentData));
    setPaymentInitiated(true);
  };

  // Process wallet payment
  const processWalletPayment = () => {
    if (!selectedPaymentMethod) return;

    const paymentData = {
      order_id: orderId,
      amount,
      currency_code: selectedCurrency,
      payment_method_id: selectedPaymentMethod,
      metadata: {}
    };

    dispatch(createPayment(paymentData));
    setPaymentInitiated(true);
  };

  // Process gift card payment
  const processGiftCardPayment = (giftCardCode: string) => {
    if (!selectedPaymentMethod) return;

    const paymentData = {
      order_id: orderId,
      amount,
      currency_code: selectedCurrency,
      payment_method_id: selectedPaymentMethod,
      metadata: {
        gift_card_code: giftCardCode
      }
    };

    dispatch(createPayment(paymentData));
    setPaymentInitiated(true);
  };

  // Handle gateway verification
  const handleGatewayVerification = (data: any) => {
    setVerificationData(data);
    
    if (currentPayment) {
      dispatch(verifyPayment({
        payment_id: currentPayment.id,
        gateway_payment_id: data.razorpay_payment_id || data.payment_intent_id || data.id,
        gateway_signature: data.razorpay_signature || data.payment_intent_client_secret || '',
        metadata: {
          razorpay_order_id: data.razorpay_order_id || ''
        }
      }));
    }
  };

  // Start polling for payment status
  const startStatusPolling = () => {
    if (currentPayment && !statusCheckInterval) {
      const interval = setInterval(() => {
        dispatch(getPaymentStatus(currentPayment.id));
      }, 3000); // Check every 3 seconds
      
      setStatusCheckInterval(interval);
    }
  };

  // Render loading state during payment processing
  if (paymentInitiated && paymentProcessing) {
    return (
      <div className="payment-processor p-6 border rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-medium mb-2">Processing Payment</h3>
          <p className="text-gray-500">Please wait while we process your payment...</p>
        </div>
      </div>
    );
  }

  // Render gateway verification UI if needed
  if (verificationData) {
    return (
      <div className="payment-processor p-6 border rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-medium mb-2">Verifying Payment</h3>
          <p className="text-gray-500">Please wait while we verify your payment...</p>
        </div>
      </div>
    );
  }

  // Render success state
  if (paymentSuccess && currentPayment) {
    return (
      <div className="payment-processor p-6 border rounded-lg">
        <div className="text-center">
          <div className="mx-auto mb-4 flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
            <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h3 className="text-lg font-medium text-green-800 mb-2">Payment Successful</h3>
          <p className="text-gray-500 mb-4">Your payment has been processed successfully.</p>
          <p className="text-sm text-gray-500">Payment ID: {currentPayment.id}</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (paymentError) {
    return (
      <div className="payment-processor p-6 border rounded-lg">
        <div className="text-center">
          <div className="mx-auto mb-4 flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </div>
          <h3 className="text-lg font-medium text-red-800 mb-2">Payment Failed</h3>
          <p className="text-gray-500 mb-4">{paymentError}</p>
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => dispatch(resetPaymentState())}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Try Again
            </button>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default PaymentProcessor;