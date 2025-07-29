'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../../store';
import {
  calculateShippingRates,
  clearShippingRates,
  clearError
} from '../../store/slices/shippingSlice';
import { ShippingRateCalculation, ShippingRateResult } from '../../types/shipping';

interface ShippingCostCalculatorProps {
  sourcePinCode?: string;
  destinationPinCode?: string;
  weight?: number;
  dimensions?: Record<string, any>;
  onRateSelect?: (rate: ShippingRateResult) => void;
  className?: string;
}

const ShippingCostCalculator: React.FC<ShippingCostCalculatorProps> = ({
  sourcePinCode = '',
  destinationPinCode = '',
  weight = 0,
  dimensions = {},
  onRateSelect,
  className = ''
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const { shippingRates, loading, error } = useSelector(
    (state: RootState) => state.shipping
  );

  const [formData, setFormData] = useState<ShippingRateCalculation>({
    source_pin_code: sourcePinCode,
    destination_pin_code: destinationPinCode,
    weight: weight,
    dimensions: dimensions
  });

  const [selectedRate, setSelectedRate] = useState<ShippingRateResult | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      source_pin_code: sourcePinCode,
      destination_pin_code: destinationPinCode,
      weight: weight,
      dimensions: dimensions
    }));
  }, [sourcePinCode, destinationPinCode, weight, dimensions]);

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const handleInputChange = (field: keyof ShippingRateCalculation, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDimensionChange = (dimension: string, value: number) => {
    setFormData(prev => ({
      ...prev,
      dimensions: {
        ...prev.dimensions,
        [dimension]: value
      }
    }));
  };

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.source_pin_code || !formData.destination_pin_code || !formData.weight) {
      return;
    }

    try {
      await dispatch(calculateShippingRates(formData)).unwrap();
      setSelectedRate(null);
    } catch (error) {
      console.error('Failed to calculate shipping rates:', error);
    }
  };

  const handleRateSelect = (rate: ShippingRateResult) => {
    setSelectedRate(rate);
    onRateSelect?.(rate);
  };

  const handleClearRates = () => {
    dispatch(clearShippingRates());
    setSelectedRate(null);
  };

  const formatDeliveryTime = (rate: ShippingRateResult) => {
    if (rate.estimated_delivery_days) {
      return `${rate.estimated_delivery_days} days`;
    } else if (rate.min_delivery_days && rate.max_delivery_days) {
      return `${rate.min_delivery_days}-${rate.max_delivery_days} days`;
    }
    return 'Not specified';
  };

  const isFormValid = formData.source_pin_code && formData.destination_pin_code && formData.weight > 0;

  return (
    <div className={`shipping-cost-calculator ${className}`}>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Calculate Shipping Cost</h3>

        <form onSubmit={handleCalculate} className="space-y-4">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="source-pin" className="block text-sm font-medium text-gray-700 mb-1">
                Source Pin Code
              </label>
              <input
                id="source-pin"
                type="text"
                value={formData.source_pin_code}
                onChange={(e) => handleInputChange('source_pin_code', e.target.value)}
                placeholder="e.g., 110001"
                maxLength={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="destination-pin" className="block text-sm font-medium text-gray-700 mb-1">
                Destination Pin Code
              </label>
              <input
                id="destination-pin"
                type="text"
                value={formData.destination_pin_code}
                onChange={(e) => handleInputChange('destination_pin_code', e.target.value)}
                placeholder="e.g., 400001"
                maxLength={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label htmlFor="weight" className="block text-sm font-medium text-gray-700 mb-1">
              Weight (kg)
            </label>
            <input
              id="weight"
              type="number"
              step="0.1"
              min="0.1"
              value={formData.weight}
              onChange={(e) => handleInputChange('weight', parseFloat(e.target.value) || 0)}
              placeholder="e.g., 1.5"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Advanced Options */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center"
            >
              <svg 
                className={`w-4 h-4 mr-1 transition-transform ${showAdvanced ? 'rotate-90' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Advanced Options
            </button>
          </div>

          {showAdvanced && (
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900">Package Dimensions (cm)</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label htmlFor="length" className="block text-sm font-medium text-gray-700 mb-1">
                    Length
                  </label>
                  <input
                    id="length"
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.dimensions?.length || ''}
                    onChange={(e) => handleDimensionChange('length', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="width" className="block text-sm font-medium text-gray-700 mb-1">
                    Width
                  </label>
                  <input
                    id="width"
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.dimensions?.width || ''}
                    onChange={(e) => handleDimensionChange('width', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="height" className="block text-sm font-medium text-gray-700 mb-1">
                    Height
                  </label>
                  <input
                    id="height"
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.dimensions?.height || ''}
                    onChange={(e) => handleDimensionChange('height', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              type="submit"
              disabled={!isFormValid || loading}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                  Calculating...
                </div>
              ) : (
                'Calculate Rates'
              )}
            </button>
            {shippingRates.length > 0 && (
              <button
                type="button"
                onClick={handleClearRates}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </form>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Shipping Rates Results */}
        {shippingRates.length > 0 && (
          <div className="mt-6">
            <h4 className="font-medium text-gray-900 mb-4">Available Shipping Options</h4>
            <div className="space-y-3">
              {shippingRates.map((rate, index) => (
                <div
                  key={`${rate.shipping_partner.id}-${index}`}
                  className={`border rounded-lg p-4 cursor-pointer transition-all duration-200 ${
                    selectedRate?.shipping_partner.id === rate.shipping_partner.id
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                  onClick={() => handleRateSelect(rate)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                        selectedRate?.shipping_partner.id === rate.shipping_partner.id
                          ? 'border-blue-500 bg-blue-500'
                          : 'border-gray-300'
                      }`}>
                        {selectedRate?.shipping_partner.id === rate.shipping_partner.id && (
                          <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {rate.shipping_partner.name}
                        </p>
                        <p className="text-sm text-gray-600">
                          Delivery: {formatDeliveryTime(rate)}
                        </p>
                        {rate.is_dynamic_rate && (
                          <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full mt-1">
                            Live Rate
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-900">
                        ₹{rate.rate.toFixed(2)}
                      </p>
                      <p className="text-sm text-gray-500">
                        + taxes
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {selectedRate && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">Selected Option:</p>
                    <p className="text-sm text-gray-600">
                      {selectedRate.shipping_partner.name} - ₹{selectedRate.rate.toFixed(2)}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedRate(null)}
                    className="text-sm text-red-600 hover:text-red-700 font-medium"
                  >
                    Clear Selection
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {!loading && shippingRates.length === 0 && !error && isFormValid && (
          <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <p className="text-yellow-700">
                Click "Calculate Rates" to see available shipping options
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShippingCostCalculator;