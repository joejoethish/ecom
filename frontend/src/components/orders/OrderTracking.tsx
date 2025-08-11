import React from 'react';
import { useOrderTracking } from '@/hooks/useOrderTracking';

interface OrderTrackingProps {
  orderId: string;
}

/**
 * Real-time order tracking component
 * Shows order status and tracking events with live updates
 */
const OrderTracking: React.FC<OrderTrackingProps> = ({ orderId }) => {
  const { isConnected, trackingEvents, currentStatus, isLoading, error } = useOrderTracking(orderId);
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-6">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Error: </strong>
        <span className="block sm:inline">{error}</span>
      </div>
    );
  }
  
  // Helper function to get status color
  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return 'bg-yellow-500';
      case 'CONFIRMED':
        return 'bg-blue-500';
      case 'PROCESSING':
        return 'bg-purple-500';
      case 'SHIPPED':
        return 'bg-indigo-500';
      case 'OUT_FOR_DELIVERY':
        return 'bg-cyan-500';
      case 'DELIVERED':
        return 'bg-green-500';
      case 'CANCELLED':
        return 'bg-red-500';
      case 'RETURNED':
        return 'bg-orange-500';
      default:
        return 'bg-gray-500';
    }
  };
  
  return (
    <div className="bg-white shadow-md rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Order Tracking</h2>
        <div className="flex items-center">
          <span className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} mr-2`}></span>
          <span className="text-sm text-gray-500">{isConnected ? 'Live Updates' : 'Offline'}</span>
        </div>
      </div>
      
      <div className="mb-6">
        <div className="flex items-center mb-2">
          <span className="text-gray-700 font-medium">Current Status:</span>
          <span className={`ml-2 px-3 py-1 text-white text-sm rounded-full ${getStatusColor(currentStatus)}`}>
            {currentStatus}
          </span>
        </div>
      </div>
      
      <div className="border-t border-gray-200 pt-4">
        <h3 className="text-lg font-medium mb-4">Tracking Timeline</h3>
        
        {trackingEvents.length === 0 ? (
          <p className="text-gray-500">No tracking events available yet.</p>
        ) : (
          <div className="space-y-4">
            {trackingEvents.map((event, index) => (
              <div key={index} className="relative pl-8 pb-4">
                {/* Timeline dot */}
                <div className={`absolute left-0 top-1.5 h-4 w-4 rounded-full ${getStatusColor(event.status)}`}></div>
                
                {/* Timeline line */}
                {index < trackingEvents.length - 1 && (
                  <div className="absolute left-2 top-5 bottom-0 w-0.5 bg-gray-200"></div>
                )}
                
                {/* Event content */}
                <div>
                  <div className="flex items-center">
                    <h4 className="font-medium">{event.status}</h4>
                    <span className="ml-2 text-xs text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-gray-600 mt-1">{event.message}</p>
                  {event.location && (
                    <p className="text-gray-500 text-sm mt-1">Location: {event.location}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderTracking;