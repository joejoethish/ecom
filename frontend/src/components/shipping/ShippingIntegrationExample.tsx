'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store';
import {
  DeliverySlotSelector,
  ShippingAddressManager,
  OrderTrackingInterface,
  ShippingCostCalculator,
  ServiceabilityChecker
} from './index';
import { useShipping } from '../../hooks/useShipping';
import { Address, DeliverySlot, ShippingAddress, ShippingRateResult, ServiceableArea } from '../../types';

// Mock data for demonstration
const mockAddresses: Address[] = [
  {
    id: '1',
    type: 'HOME',
    first_name: 'John',
    last_name: 'Doe',
    address_line_1: '123 Main Street',
    address_line_2: 'Apt 4B',
    city: 'New Delhi',
    state: 'Delhi',
    postal_code: '110001',
    country: 'India',
    phone: '+91 9876543210',
    is_default: true
  },
  {
    id: '2',
    type: 'WORK',
    first_name: 'John',
    last_name: 'Doe',
    address_line_1: '456 Business Park',
    city: 'Gurgaon',
    state: 'Haryana',
    postal_code: '122001',
    country: 'India',
    phone: '+91 9876543210',
    is_default: false
  }
];

interface ShippingIntegrationExampleProps {
  className?: string;
}

const ShippingIntegrationExample: React.FC<ShippingIntegrationExampleProps> = ({
  className = ''
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const shipping = useShipping();
  
  const [currentStep, setCurrentStep] = useState<'address' | 'serviceability' | 'slots' | 'rates' | 'tracking'>('address');
  const [selectedAddress, setSelectedAddress] = useState<Address | null>(null);
  const [selectedPinCode, setSelectedPinCode] = useState('110001');
  const [isServiceable, setIsServiceable] = useState<boolean | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<DeliverySlot | null>(null);
  const [selectedRate, setSelectedRate] = useState<ShippingRateResult | null>(null);
  const [orderData, setOrderData] = useState({
    weight: 1.5,
    dimensions: { length: 10, width: 8, height: 5 },
    sourcePinCode: '110001'
  });

  // Initialize shipping partners on mount
  useEffect(() => {
    shipping.loadShippingPartners();
  }, []);

  const handleAddressSelect = (address: ShippingAddress | null) => {
    if (address) {
      setSelectedPinCode(address.postal_code);
      setCurrentStep('serviceability');
    }
  };

  const handleServiceabilityCheck = (serviceable: boolean, areas?: ServiceableArea[]) => {
    setIsServiceable(serviceable);
    if (serviceable) {
      setCurrentStep('slots');
    }
  };

  const handleSlotSelect = (slot: DeliverySlot) => {
    setSelectedSlot(slot);
    setCurrentStep('rates');
  };

  const handleRateSelect = (rate: ShippingRateResult) => {
    setSelectedRate(rate);
    // Could proceed to checkout or other next steps
  };

  const resetFlow = () => {
    setCurrentStep('address');
    setSelectedAddress(null);
    setIsServiceable(null);
    setSelectedSlot(null);
    setSelectedRate(null);
    shipping.resetState();
  };

  const getStepStatus = (step: string) => {
    const steps = ['address', 'serviceability', 'slots', 'rates', 'tracking'];
    const currentIndex = steps.indexOf(currentStep);
    const stepIndex = steps.indexOf(step);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'upcoming';
  };

  return (
    <div className={`shipping-integration-example ${className}`}>
      <div className="max-w-6xl mx-auto">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[
              { id: 'address', label: 'Address', icon: '📍' },
              { id: 'serviceability', label: 'Check Area', icon: '✅' },
              { id: 'slots', label: 'Delivery Slot', icon: '📅' },
              { id: 'rates', label: 'Shipping Cost', icon: '💰' },
              { id: 'tracking', label: 'Track Order', icon: '📦' }
            ].map((step, index) => {
              const status = getStepStatus(step.id);
              return (
                <div key={step.id} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium ${
                    status === 'completed' ? 'bg-green-500 text-white' :
                    status === 'current' ? 'bg-blue-500 text-white' :
                    'bg-gray-200 text-gray-600'
                  }`}>
                    {status === 'completed' ? '✓' : step.icon}
                  </div>
                  <div className="ml-2">
                    <p className={`text-sm font-medium ${
                      status === 'current' ? 'text-blue-600' : 'text-gray-600'
                    }`}>
                      {step.label}
                    </p>
                  </div>
                  {index < 4 && (
                    <div className={`w-16 h-0.5 mx-4 ${
                      status === 'completed' ? 'bg-green-500' : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="space-y-6">
          {currentStep === 'address' && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Select Delivery Address</h2>
                <button
                  onClick={resetFlow}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Reset Flow
                </button>
              </div>
              <ShippingAddressManager
                addresses={mockAddresses}
                onAddressSelect={handleAddressSelect}
                onAddNewAddress={() => alert('Add new address functionality')}
                onEditAddress={(address) => alert(`Edit address ${address.id}`)}
              />
            </div>
          )}

          {currentStep === 'serviceability' && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">Check Delivery Availability</h2>
              <ServiceabilityChecker
                pinCode={selectedPinCode}
                onServiceabilityCheck={handleServiceabilityCheck}
              />
              {isServiceable === false && (
                <div className="mt-4">
                  <button
                    onClick={() => setCurrentStep('address')}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                  >
                    Choose Different Address
                  </button>
                </div>
              )}
            </div>
          )}

          {currentStep === 'slots' && isServiceable && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">Select Delivery Slot</h2>
              <DeliverySlotSelector
                pincode={selectedPinCode}
                onSelect={handleSlotSelect}
              />
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={() => setCurrentStep('serviceability')}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
                >
                  Back
                </button>
                {selectedSlot && (
                  <button
                    onClick={() => setCurrentStep('rates')}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                  >
                    Continue to Shipping Rates
                  </button>
                )}
              </div>
            </div>
          )}

          {currentStep === 'rates' && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">Calculate Shipping Cost</h2>
              <ShippingCostCalculator
                sourcePinCode={orderData.sourcePinCode}
                destinationPinCode={selectedPinCode}
                weight={orderData.weight}
                dimensions={orderData.dimensions}
                onRateSelect={handleRateSelect}
              />
              <div className="mt-6 flex space-x-3">
                <button
                  onClick={() => setCurrentStep('slots')}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
                >
                  Back
                </button>
                {selectedRate && (
                  <button
                    onClick={() => setCurrentStep('tracking')}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                  >
                    Proceed to Checkout
                  </button>
                )}
              </div>
            </div>
          )}

          {currentStep === 'tracking' && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">Order Tracking</h2>
              <OrderTrackingInterface showSearch={true} />
              <div className="mt-4">
                <button
                  onClick={resetFlow}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Start New Order
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Summary Panel */}
        {(selectedAddress || selectedSlot || selectedRate) && (
          <div className="mt-8 bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Order Summary</h3>
            <div className="space-y-3 text-sm">
              {selectedAddress && (
                <div>
                  <span className="font-medium">Delivery Address:</span>
                  <span className="ml-2">{selectedPinCode}</span>
                </div>
              )}
              {isServiceable !== null && (
                <div>
                  <span className="font-medium">Serviceability:</span>
                  <span className={`ml-2 ${isServiceable ? 'text-green-600' : 'text-red-600'}`}>
                    {isServiceable ? 'Available' : 'Not Available'}
                  </span>
                </div>
              )}
              {selectedSlot && (
                <div>
                  <span className="font-medium">Delivery Slot:</span>
                  <span className="ml-2">{selectedSlot.name} ({selectedSlot.start_time} - {selectedSlot.end_time})</span>
                </div>
              )}
              {selectedRate && (
                <div>
                  <span className="font-medium">Shipping Cost:</span>
                  <span className="ml-2">₹{selectedRate.rate} via {selectedRate.shipping_partner.name}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Display */}
        {shipping.hasError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-red-700">{shipping.error}</p>
              <button
                onClick={shipping.clearErrors}
                className="ml-auto text-red-600 hover:text-red-800"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Loading Overlay */}
        {shipping.isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 flex items-center space-x-3">
              <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full"></div>
              <span>Processing...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShippingIntegrationExample;