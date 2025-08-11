import React from 'react';
import { useInventoryUpdates } from '@/hooks/useInventoryUpdates';

// SVG icon component to replace heroicons
const ExclamationTriangleIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

/**
 * Real-time inventory alerts component
 * Shows low stock alerts with real-time updates
 */
  
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Error: </strong>
        <span className="block sm:inline">{error}</span>
      </div>
    );
  }
  
  return (
    <div className="bg-white shadow-md rounded-lg overflow-hidden">
      <div className="bg-gray-100 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-700">Inventory Alerts</h3>
        <div className="flex items-center">
          <span className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} mr-2`}></span>
          <span className="text-sm text-gray-500">{isConnected ? &apos;Live Updates&apos; : &apos;Offline&apos;}</span>
        </div>
      </div>
      
      {lowStockAlerts.length === 0 ? (
        <div className="p-6 text-center text-gray-500">
          <p>No inventory alerts at this time.</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {lowStockAlerts.map((alert) => (
            <div key={alert.productId} className="p-4 hover:bg-gray-50">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-6 w-6 text-amber-500" />
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-gray-900">{alert.productName}</h4>
                  <div className="mt-1 text-sm text-gray-600">
                    <p>
                      Current stock: <span className="font-medium text-red-600">{alert.currentStock}</span> (below threshold of {alert.threshold})
                    </p>
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    {new Date(alert.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default InventoryAlerts;