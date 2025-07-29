'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../../store';
import {
  setSelectedShippingAddress,
  checkServiceability,
  clearError
} from '../../store/slices/shippingSlice';
import { Address, ShippingAddress } from '../../types';

interface ShippingAddressManagerProps {
  addresses: Address[];
  onAddressSelect?: (address: ShippingAddress | null) => void;
  onAddNewAddress?: () => void;
  onEditAddress?: (address: Address) => void;
  className?: string;
}

const ShippingAddressManager: React.FC<ShippingAddressManagerProps> = ({
  addresses,
  onAddressSelect,
  onAddNewAddress,
  onEditAddress,
  className = ''
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const { selectedShippingAddress, serviceableAreas, loading, error } = useSelector(
    (state: RootState) => state.shipping
  );

  const [localSelectedAddress, setLocalSelectedAddress] = useState<Address | null>(null);
  const [serviceabilityStatus, setServiceabilityStatus] = useState<{
    [key: string]: { serviceable: boolean; loading: boolean; error?: string }
  }>({});

  useEffect(() => {
    // Find the default address or the first address
    const defaultAddress = addresses.find(addr => addr.is_default) || addresses[0];
    if (defaultAddress && !localSelectedAddress) {
      handleAddressSelect(defaultAddress);
    }
  }, [addresses]);

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const convertToShippingAddress = (address: Address): ShippingAddress => ({
    first_name: address.first_name,
    last_name: address.last_name,
    company: address.company,
    address_line_1: address.address_line_1,
    address_line_2: address.address_line_2,
    city: address.city,
    state: address.state,
    postal_code: address.postal_code,
    country: address.country,
    phone: address.phone
  });

  const handleAddressSelect = async (address: Address) => {
    setLocalSelectedAddress(address);
    const shippingAddress = convertToShippingAddress(address);
    dispatch(setSelectedShippingAddress(shippingAddress));
    onAddressSelect?.(shippingAddress);

    // Check serviceability for this pin code
    if (address.postal_code) {
      setServiceabilityStatus(prev => ({
        ...prev,
        [address.id]: { serviceable: false, loading: true }
      }));

      try {
        const result = await dispatch(checkServiceability({ pin_code: address.postal_code }));
        if (checkServiceability.fulfilled.match(result)) {
          setServiceabilityStatus(prev => ({
            ...prev,
            [address.id]: { serviceable: true, loading: false }
          }));
        } else {
          setServiceabilityStatus(prev => ({
            ...prev,
            [address.id]: { 
              serviceable: false, 
              loading: false, 
              error: result.payload as string 
            }
          }));
        }
      } catch (error) {
        setServiceabilityStatus(prev => ({
          ...prev,
          [address.id]: { 
            serviceable: false, 
            loading: false, 
            error: 'Failed to check serviceability' 
          }
        }));
      }
    }
  };

  const getAddressTypeIcon = (type: string) => {
    switch (type) {
      case 'HOME':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
          </svg>
        );
      case 'WORK':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2h2zm4-3a1 1 0 00-1 1v1h2V4a1 1 0 00-1-1zm-3 4a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const formatAddress = (address: Address) => {
    const parts = [
      address.address_line_1,
      address.address_line_2,
      address.city,
      address.state,
      address.postal_code
    ].filter(Boolean);
    return parts.join(', ');
  };

  if (!addresses.length) {
    return (
      <div className={`shipping-address-manager ${className}`}>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Delivery Address</h3>
          <div className="text-center py-8">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <p className="text-gray-600 mb-4">No delivery addresses found</p>
            <button
              onClick={onAddNewAddress}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add New Address
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`shipping-address-manager ${className}`}>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Delivery Address</h3>
          <button
            onClick={onAddNewAddress}
            className="text-blue-600 hover:text-blue-700 font-medium text-sm flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add New
          </button>
        </div>

        <div className="space-y-3">
          {addresses.map((address) => {
            const isSelected = localSelectedAddress?.id === address.id;
            const serviceability = serviceabilityStatus[address.id];

            return (
              <div
                key={address.id}
                className={`border rounded-lg p-4 cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => handleAddressSelect(address)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start flex-1">
                    <div className={`w-4 h-4 rounded-full border-2 mr-3 mt-1 flex-shrink-0 ${
                      isSelected
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                    }`}>
                      {isSelected && (
                        <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <div className="text-gray-600 mr-2">
                          {getAddressTypeIcon(address.type)}
                        </div>
                        <span className="font-medium text-gray-900">
                          {address.first_name} {address.last_name}
                        </span>
                        {address.is_default && (
                          <span className="ml-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                            Default
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 text-sm mb-1">
                        {formatAddress(address)}
                      </p>
                      {address.phone && (
                        <p className="text-gray-500 text-sm">
                          Phone: {address.phone}
                        </p>
                      )}

                      {/* Serviceability Status */}
                      {serviceability && (
                        <div className="mt-2">
                          {serviceability.loading ? (
                            <div className="flex items-center text-sm text-gray-500">
                              <div className="animate-spin w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full mr-2"></div>
                              Checking serviceability...
                            </div>
                          ) : serviceability.serviceable ? (
                            <div className="flex items-center text-sm text-green-600">
                              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                              Delivery available
                            </div>
                          ) : (
                            <div className="flex items-center text-sm text-red-600">
                              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                              </svg>
                              {serviceability.error || 'Not serviceable'}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditAddress?.(address);
                    }}
                    className="text-gray-400 hover:text-gray-600 ml-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

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
      </div>
    </div>
  );
};

export default ShippingAddressManager;