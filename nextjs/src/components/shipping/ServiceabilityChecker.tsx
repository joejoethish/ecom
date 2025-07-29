'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../../store';
import {
  checkServiceability,
  clearError
} from '../../store/slices/shippingSlice';
import { ServiceableArea } from '../../types/shipping';

interface ServiceabilityCheckerProps {
  pinCode?: string;
  onServiceabilityCheck?: (serviceable: boolean, areas?: ServiceableArea[]) => void;
  className?: string;
}

const ServiceabilityChecker: React.FC<ServiceabilityCheckerProps> = ({
  pinCode = '',
  onServiceabilityCheck,
  className = ''
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const { serviceableAreas, loading, error } = useSelector(
    (state: RootState) => state.shipping
  );

  const [inputPinCode, setInputPinCode] = useState(pinCode);
  const [lastCheckedPinCode, setLastCheckedPinCode] = useState('');
  const [serviceabilityResult, setServiceabilityResult] = useState<{
    serviceable: boolean;
    areas: ServiceableArea[];
    pinCode: string;
  } | null>(null);

  useEffect(() => {
    setInputPinCode(pinCode);
    if (pinCode && pinCode !== lastCheckedPinCode) {
      handleCheck(pinCode);
    }
  }, [pinCode]);

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const handleCheck = async (checkPinCode?: string) => {
    const codeToCheck = checkPinCode || inputPinCode;

    if (!codeToCheck || codeToCheck.length !== 6) {
      return;
    }

    setLastCheckedPinCode(codeToCheck);

    try {
      const result = await dispatch(checkServiceability({ pin_code: codeToCheck })).unwrap();

      if (result) {
        const serviceabilityData = {
          serviceable: result.serviceable,
          areas: result.areas || [],
          pinCode: codeToCheck
        };

        setServiceabilityResult(serviceabilityData);
        onServiceabilityCheck?.(result.serviceable, result.areas);
      }
    } catch (error) {
      setServiceabilityResult({
        serviceable: false,
        areas: [],
        pinCode: codeToCheck
      });
      onServiceabilityCheck?.(false, []);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setInputPinCode(value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleCheck();
  };

  const formatDeliveryTime = (area: ServiceableArea) => {
    if (area.min_delivery_days === area.max_delivery_days) {
      return `${area.min_delivery_days} day${area.min_delivery_days > 1 ? 's' : ''}`;
    }
    return `${area.min_delivery_days}-${area.max_delivery_days} days`;
  };

  return (
    <div className={`serviceability-checker ${className}`}>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Check Delivery Availability</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="pin-code" className="block text-sm font-medium text-gray-700 mb-2">
              Enter Pin Code
            </label>
            <div className="flex space-x-3">
              <input
                id="pin-code"
                type="text"
                value={inputPinCode}
                onChange={handleInputChange}
                placeholder="e.g., 110001"
                maxLength={6}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="submit"
                disabled={loading || inputPinCode.length !== 6}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                    Checking...
                  </div>
                ) : (
                  'Check'
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Enter a 6-digit pin code to check delivery availability
            </p>
          </div>
        </form>

        {/* Results */}
        {serviceabilityResult && serviceabilityResult.pinCode === inputPinCode && (
          <div className="mt-6">
            {serviceabilityResult.serviceable ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start">
                  <svg className="w-6 h-6 text-green-500 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <h4 className="text-green-800 font-medium mb-2">
                      Great! We deliver to {serviceabilityResult.pinCode}
                    </h4>

                    {serviceabilityResult.areas.length > 0 && (
                      <div className="space-y-3">
                        <p className="text-green-700 text-sm mb-3">
                          Available delivery options:
                        </p>
                        {serviceabilityResult.areas.map((area, index) => (
                          <div key={area.id} className="bg-white border border-green-200 rounded-lg p-3">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium text-gray-900">
                                  {area.city}, {area.state}
                                </p>
                                <p className="text-sm text-gray-600">
                                  {area.country}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-sm font-medium text-green-600">
                                  {formatDeliveryTime(area)}
                                </p>
                                <p className="text-xs text-gray-500">
                                  delivery time
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <svg className="w-6 h-6 text-red-500 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <h4 className="text-red-800 font-medium mb-2">
                      Sorry, we don't deliver to {serviceabilityResult.pinCode}
                    </h4>
                    <p className="text-red-700 text-sm">
                      This pin code is currently not in our delivery network. Please try a different pin code or contact our support team for assistance.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Quick Tips */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-blue-800 font-medium mb-2 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            Quick Tips
          </h4>
          <ul className="text-blue-700 text-sm space-y-1">
            <li>• Pin codes are 6-digit numbers (e.g., 110001 for New Delhi)</li>
            <li>• Delivery times may vary based on location and shipping partner</li>
            <li>• Some areas may have additional delivery charges</li>
            <li>• Contact support if your area is not serviceable</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ServiceabilityChecker;