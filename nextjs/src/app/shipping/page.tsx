'use client';

import React, { useState } from 'react';
import {
  DeliverySlotSelector,
  ShippingAddressManager,
  OrderTrackingInterface,
  ShippingCostCalculator,
  ServiceabilityChecker
} from '../../components/shipping';
import { Address } from '../../types';

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

const ShippingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'delivery' | 'tracking' | 'calculator' | 'serviceability'>('delivery');
  const [selectedPinCode, setSelectedPinCode] = useState('110001');

  const tabs = [
    { id: 'delivery', label: 'Delivery Options', icon: '🚚' },
    { id: 'tracking', label: 'Order Tracking', icon: '📦' },
    { id: 'calculator', label: 'Shipping Calculator', icon: '💰' },
    { id: 'serviceability', label: 'Check Serviceability', icon: '📍' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Shipping & Delivery</h1>
          <p className="text-gray-600">Manage your delivery preferences, track orders, and calculate shipping costs</p>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'delivery' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Address Selection */}
              <div>
                <ShippingAddressManager
                  addresses={mockAddresses}
                  onAddressSelect={(address) => {
                    if (address) {
                      setSelectedPinCode(address.postal_code);
                    }
                  }}
                  onAddNewAddress={() => alert('Add new address functionality would be implemented here')}
                  onEditAddress={(address) => alert(`Edit address functionality for ${address.id} would be implemented here`)}
                />
              </div>

              {/* Delivery Slot Selection */}
              <div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <DeliverySlotSelector
                    pincode={selectedPinCode}
                    onSelect={(slot) => {
                      console.log('Selected delivery slot:', slot);
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tracking' && (
            <div>
              <OrderTrackingInterface
                showSearch={true}
                className="bg-white"
              />
            </div>
          )}

          {activeTab === 'calculator' && (
            <div className="max-w-4xl">
              <ShippingCostCalculator
                sourcePinCode="110001"
                destinationPinCode={selectedPinCode}
                weight={1.5}
                onRateSelect={(rate) => {
                  console.log('Selected shipping rate:', rate);
                }}
              />
            </div>
          )}

          {activeTab === 'serviceability' && (
            <div className="max-w-2xl">
              <ServiceabilityChecker
                pinCode={selectedPinCode}
                onServiceabilityCheck={(serviceable, areas) => {
                  console.log('Serviceability result:', { serviceable, areas });
                }}
              />
            </div>
          )}
        </div>

        {/* Additional Information */}
        <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-4">Shipping Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-sm">
            <div>
              <h3 className="font-medium text-blue-800 mb-2">Delivery Options</h3>
              <ul className="text-blue-700 space-y-1">
                <li>• Standard Delivery (3-5 days)</li>
                <li>• Express Delivery (1-2 days)</li>
                <li>• Same Day Delivery (selected areas)</li>
                <li>• Scheduled Delivery Slots</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-blue-800 mb-2">Shipping Partners</h3>
              <ul className="text-blue-700 space-y-1">
                <li>• Shiprocket</li>
                <li>• Delhivery</li>
                <li>• Blue Dart</li>
                <li>• DTDC</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-blue-800 mb-2">Payment Options</h3>
              <ul className="text-blue-700 space-y-1">
                <li>• Cash on Delivery</li>
                <li>• Prepaid Orders</li>
                <li>• Digital Wallets</li>
                <li>• UPI Payments</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShippingPage;