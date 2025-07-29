'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../../store';
import {
  trackShipment,
  fetchUserShipments,
  setCurrentShipment,
  clearError
} from '../../store/slices/shippingSlice';
import { Shipment, ShipmentStatus } from '../../types/shipping';
import TrackingTimeline from './TrackingTimeline';

interface OrderTrackingInterfaceProps {
  orderId?: string;
  trackingNumber?: string;
  showSearch?: boolean;
  className?: string;
}

const OrderTrackingInterface: React.FC<OrderTrackingInterfaceProps> = ({
  orderId,
  trackingNumber,
  showSearch = true,
  className = ''
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const { currentShipment, shipments, loading, error } = useSelector(
    (state: RootState) => state.shipping
  );

  const [searchQuery, setSearchQuery] = useState(trackingNumber || '');
  const [searchType, setSearchType] = useState<'tracking' | 'order'>('tracking');

  useEffect(() => {
    if (trackingNumber) {
      handleTrackShipment(trackingNumber);
    } else if (orderId) {
      // Find shipment by order ID from existing shipments or fetch user shipments
      const existingShipment = shipments.find(s => s.order === orderId);
      if (existingShipment) {
        dispatch(setCurrentShipment(existingShipment));
      } else {
        dispatch(fetchUserShipments());
      }
    }

    return () => {
      dispatch(clearError());
    };
  }, [dispatch, trackingNumber, orderId]);

  useEffect(() => {
    if (orderId && shipments.length > 0) {
      const shipment = shipments.find(s => s.order === orderId);
      if (shipment) {
        dispatch(setCurrentShipment(shipment));
      }
    }
  }, [dispatch, orderId, shipments]);

  const handleTrackShipment = async (query: string) => {
    if (!query.trim()) return;

    try {
      await dispatch(trackShipment(query.trim())).unwrap();
    } catch (error) {
      console.error('Failed to track shipment:', error);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      handleTrackShipment(searchQuery.trim());
    }
  };

  const getStatusColor = (status: ShipmentStatus) => {
    switch (status) {
      case 'DELIVERED':
        return 'text-green-600 bg-green-100';
      case 'SHIPPED':
      case 'IN_TRANSIT':
      case 'OUT_FOR_DELIVERY':
        return 'text-blue-600 bg-blue-100';
      case 'PROCESSING':
        return 'text-yellow-600 bg-yellow-100';
      case 'CANCELLED':
      case 'RETURNED':
        return 'text-red-600 bg-red-100';
      case 'FAILED_DELIVERY':
        return 'text-orange-600 bg-orange-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: ShipmentStatus) => {
    switch (status) {
      case 'DELIVERED':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'SHIPPED':
      case 'IN_TRANSIT':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
            <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707L16 7.586A1 1 0 0015.414 7H14z" />
          </svg>
        );
      case 'OUT_FOR_DELIVERY':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
      case 'PROCESSING':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
          </svg>
        );
      case 'CANCELLED':
      case 'RETURNED':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAddress = (address: any) => {
    if (typeof address === 'string') {
      return address;
    }
    const parts = [
      address.address_line_1,
      address.address_line_2,
      address.city,
      address.state,
      address.postal_code
    ].filter(Boolean);
    return parts.join(', ');
  };

  return (
    <div className={`order-tracking-interface ${className}`}>
      {showSearch && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-semibold mb-4">Track Your Order</h2>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex space-x-4">
              <div className="flex-1">
                <label htmlFor="search-query" className="block text-sm font-medium text-gray-700 mb-2">
                  Enter Tracking Number or Order ID
                </label>
                <input
                  id="search-query"
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g., TRK123456789 or ORD123456"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={loading || !searchQuery.trim()}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <div className="flex items-center">
                      <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                      Tracking...
                    </div>
                  ) : (
                    'Track'
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {currentShipment && (
        <div className="space-y-6">
          {/* Shipment Overview */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Shipment Details</h3>
              <div className={`px-3 py-1 rounded-full text-sm font-medium flex items-center ${getStatusColor(currentShipment.status)}`}>
                {getStatusIcon(currentShipment.status)}
                <span className="ml-2">{currentShipment.status_display}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Tracking Information</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tracking Number:</span>
                    <span className="font-medium">{currentShipment.tracking_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Shipping Partner:</span>
                    <span className="font-medium">{currentShipment.shipping_partner_name}</span>
                  </div>
                  {currentShipment.estimated_delivery_date && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Estimated Delivery:</span>
                      <span className="font-medium">
                        {new Date(currentShipment.estimated_delivery_date).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                  {currentShipment.delivery_slot_display && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Delivery Slot:</span>
                      <span className="font-medium">{currentShipment.delivery_slot_display}</span>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Delivery Address</h4>
                <div className="text-sm text-gray-600">
                  <p>{formatAddress(currentShipment.shipping_address)}</p>
                </div>
              </div>
            </div>

            {currentShipment.shipping_cost > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Shipping Cost:</span>
                  <span className="font-medium text-lg">₹{currentShipment.shipping_cost}</span>
                </div>
              </div>
            )}
          </div>

          {/* Tracking Timeline */}
          <TrackingTimeline 
            shipment={currentShipment}
            className="bg-white border border-gray-200 rounded-lg p-6"
          />
        </div>
      )}

      {loading && !currentShipment && (
        <div className="bg-white border border-gray-200 rounded-lg p-8">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Loading tracking information...</p>
          </div>
        </div>
      )}

      {!loading && !currentShipment && !error && showSearch && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8">
          <div className="text-center">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-gray-600">Enter a tracking number or order ID to view shipment details</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderTrackingInterface;