'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { createOrder } from '@/store/slices/orderSlice';
import { CheckoutPayment } from '@/components/payments';
import { PROFILE_ROUTES, ROUTES } from '@/constants';
import { Address } from '@/types';
import { createPartialAddress } from '@/utils/typeGuards';

enum CheckoutStep {
  SHIPPING = 'shipping',
  PAYMENT = 'payment',
  CONFIRMATION = 'confirmation'
}

const CheckoutPage: React.FC = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { items: cartItems } = useSelector((state: RootState) => state.cart);
  const { currentOrder, loading, error } = useSelector((state: RootState) => state.orders);

  const [currentStep, setCurrentStep] = useState<CheckoutStep>(CheckoutStep.SHIPPING);
  const [shippingAddress, setShippingAddress] = useState<Address | null>(null);
  const [billingAddress, setBillingAddress] = useState<Address | null>(null);
  const [shippingMethod, setShippingMethod] = useState<string>('');
  const [paymentId, setPaymentId] = useState<string>('');

  // Redirect to cart if cart is empty
  useEffect(() => {
    if (!cartItems || cartItems.length === 0) {
      router.push(ROUTES.CART);
    }
  }, [cartItems, router]);

  // Handle order creation
  const handleCreateOrder = () => {
    if (!shippingAddress || !shippingMethod) return;

    interface OrderData {
      shipping_address: Address;
      billing_address: Address;
      shipping_method: string;
      items: Array<{
        product_id: string;
        quantity: number;
      }>;
    }

    const orderData: OrderData = {
      shipping_address: shippingAddress,
      billing_address: billingAddress || shippingAddress,
      shipping_method: shippingMethod,
      items: cartItems?.map(item => ({
        product_id: item.product.id,
        quantity: item.quantity
      })) || []
    };

    dispatch(createOrder(orderData));
  };

  // Handle payment success
  const handlePaymentSuccess = (paymentId: string) => {
    setPaymentId(paymentId);
    setCurrentStep(CheckoutStep.CONFIRMATION);
  };

  // Handle payment failure
  const handlePaymentFailure = (error: string) => {
    console.error('Payment failed:', error);
    // Show error message to user
  };

  // Render shipping form
  const renderShippingStep = () => {
    return (
      <div className="shipping-step">
        <h2 className="text-2xl font-bold mb-6">Shipping Information</h2>

        {/* Shipping form would go here */}
        <div className="mb-6 p-4 bg-yellow-50 text-yellow-700 rounded-lg">
          <p>This is a placeholder for the shipping form.</p>
          <p>In a real implementation, this would include address fields, shipping method selection, etc.</p>
        </div>

        {/* For demo purposes, we'll use dummy data */}
        <button
          onClick={() => {
            // Set dummy data
            setShippingAddress(createPartialAddress({
              first_name: 'John',
              last_name: 'Doe',
              address_line_1: '123 Main St',
              city: 'Anytown',
              state: 'CA',
              postal_code: '12345',
              country: 'US'
            }));
            setBillingAddress(createPartialAddress({
              first_name: 'John',
              last_name: 'Doe',
              address_line_1: '123 Main St',
              city: 'Anytown',
              state: 'CA',
              postal_code: '12345',
              country: 'US'
            }));
            setShippingMethod('standard');

            // Create order and proceed to payment
            handleCreateOrder();
            setCurrentStep(CheckoutStep.PAYMENT);
          }}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Continue to Payment
        </button>
      </div>
    );
  };

  // Render payment step
  const renderPaymentStep = () => {
    if (!currentOrder) {
      return (
        <div className="p-4 bg-yellow-50 text-yellow-700 rounded-lg">
          <p>Order information is not available. Please go back to the shipping step.</p>
          <button
            onClick={() => setCurrentStep(CheckoutStep.SHIPPING)}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Back to Shipping
          </button>
        </div>
      );
    }

    return (
      <CheckoutPayment
        orderId={currentOrder.id}
        amount={currentOrder.total_amount}
        onPaymentSuccess={handlePaymentSuccess}
        onPaymentFailure={handlePaymentFailure}
        onCancel={() => setCurrentStep(CheckoutStep.SHIPPING)}
      />
    );
  };

  // Render confirmation step
  const renderConfirmationStep = () => {
    if (!currentOrder) {
      return (
        <div className="p-4 bg-yellow-50 text-yellow-700 rounded-lg">
          <p>Order information is not available.</p>
          <button
            onClick={() => router.push(ROUTES.HOME)}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Return to Home
          </button>
        </div>
      );
    }

    return (
      <div className="confirmation-step">
        <div className="text-center mb-8">
          <div className="mx-auto mb-4 flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
            <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-green-800 mb-2">Order Confirmed!</h2>
          <p className="text-gray-600">Thank you for your purchase.</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
          <h3 className="text-lg font-medium mb-4">Order Summary</h3>
          <div className="mb-4">
            <p className="text-gray-600">Order Number: <span className="font-medium">{currentOrder.order_number}</span></p>
            <p className="text-gray-600">Payment ID: <span className="font-medium">{paymentId}</span></p>
          </div>

          <div className="border-t pt-4 mb-4">
            <h4 className="font-medium mb-2">Items</h4>
            <ul className="space-y-2">
              {currentOrder?.items?.map((item: any) => (
                <li key={item.id} className="flex justify-between">
                  <span>{item.product?.name} × {item.quantity}</span>
                  <span className="font-medium">${item.total_price?.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="border-t pt-4">
            <div className="flex justify-between mb-2">
              <span>Subtotal</span>
              <span>${((currentOrder?.total_amount || 0) - (currentOrder?.shipping_amount || 0) - (currentOrder?.tax_amount || 0) + (currentOrder?.discount_amount || 0)).toFixed(2)}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span>Shipping</span>
              <span>${(currentOrder?.shipping_amount || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span>Tax</span>
              <span>${(currentOrder?.tax_amount || 0).toFixed(2)}</span>
            </div>
            {(currentOrder?.discount_amount || 0) > 0 && (
              <div className="flex justify-between mb-2 text-green-600">
                <span>Discount</span>
                <span>-${(currentOrder?.discount_amount || 0).toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between font-bold text-lg mt-2 pt-2 border-t">
              <span>Total</span>
              <span>${(currentOrder?.total_amount || 0).toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={() => router.push(PROFILE_ROUTES.ORDERS)}
            className="px-6 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
          >
            View Orders
          </button>
          <button
            onClick={() => router.push(ROUTES.HOME)}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Continue Shopping
          </button>
        </div>
      </div>
    );
  };

  // Render based on current step
  const renderCurrentStep = () => {
    switch (currentStep) {
      case CheckoutStep.SHIPPING:
        return renderShippingStep();
      case CheckoutStep.PAYMENT:
        return renderPaymentStep();
      case CheckoutStep.CONFIRMATION:
        return renderConfirmationStep();
      default:
        return renderShippingStep();
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-60 bg-gray-200 rounded"></div>
          <div className="h-40 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="p-4 bg-red-50 text-red-700 rounded-lg">
          <p>Error: {error}</p>
          <button
            onClick={() => router.push(ROUTES.CART)}
            className="mt-4 px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Return to Cart
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Checkout progress */}
      <div className="mb-8">
        <div className="flex items-center justify-center">
          <div className={`step-item ${currentStep === CheckoutStep.SHIPPING ? 'active' : 'completed'}`}>
            <div className="step-circle">1</div>
            <div className="step-text">Shipping</div>
          </div>
          <div className="step-line"></div>
          <div className={`step-item ${currentStep === CheckoutStep.PAYMENT
            ? 'active'
            : currentStep === CheckoutStep.CONFIRMATION
              ? 'completed'
              : ''
            }`}>
            <div className="step-circle">2</div>
            <div className="step-text">Payment</div>
          </div>
          <div className="step-line"></div>
          <div className={`step-item ${currentStep === CheckoutStep.CONFIRMATION ? 'active' : ''}`}>
            <div className="step-circle">3</div>
            <div className="step-text">Confirmation</div>
          </div>
        </div>
      </div>

      {/* Current step content */}
      <div className="max-w-4xl mx-auto">
        {renderCurrentStep()}
      </div>
    </div>
  );
};

export default CheckoutPage;