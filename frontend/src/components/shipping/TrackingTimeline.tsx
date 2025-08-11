'use client';

import React from 'react';
import { Shipment, ShipmentTracking, ShipmentStatus } from '../../types/shipping';

interface TrackingTimelineProps {
  shipment: Shipment;
  className?: string;
}

  shipment,
  className = &apos;&apos;
}) => {
  const getStatusIcon = (status: ShipmentStatus, isActive: boolean = false) => {
    const baseClasses = `w-6 h-6 ${isActive ? &apos;text-white&apos; : &apos;text-gray-400&apos;}`;
    
    switch (status) {
      case &apos;PENDING&apos;:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      case &apos;PROCESSING&apos;:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
          </svg>
        );
      case &apos;SHIPPED&apos;:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
            <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707L16 7.586A1 1 0 0015.414 7H14z" />
          </svg>
        );
      case &apos;IN_TRANSIT&apos;:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
            <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707L16 7.586A1 1 0 0015.414 7H14z" />
          </svg>
        );
      case &apos;OUT_FOR_DELIVERY&apos;:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
      case &apos;DELIVERED&apos;:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case &apos;FAILED_DELIVERY&apos;:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case &apos;RETURNED&apos;:
      case &apos;CANCELLED&apos;:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-4a1 1 0 112 0 1 1 0 01-2 0zm1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getStatusColor = (status: ShipmentStatus, isActive: boolean = false) => {
    if (isActive) {
      switch (status) {
        case &apos;DELIVERED&apos;:
          return &apos;bg-green-500&apos;;
        case &apos;SHIPPED&apos;:
        case &apos;IN_TRANSIT&apos;:
        case &apos;OUT_FOR_DELIVERY&apos;:
          return &apos;bg-blue-500&apos;;
        case &apos;PROCESSING&apos;:
          return &apos;bg-yellow-500&apos;;
        case &apos;CANCELLED&apos;:
        case &apos;RETURNED&apos;:
          return &apos;bg-red-500&apos;;
        case &apos;FAILED_DELIVERY&apos;:
          return &apos;bg-orange-500&apos;;
        default:
          return &apos;bg-gray-500&apos;;
      }
    }
    return &apos;bg-gray-300&apos;;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString(&apos;en-US&apos;, {
        year: &apos;numeric&apos;,
        month: &apos;short&apos;,
        day: &apos;numeric&apos;
      }),
      time: date.toLocaleTimeString(&apos;en-US&apos;, {
        hour: &apos;2-digit&apos;,
        minute: &apos;2-digit&apos;,
        hour12: true
      })
    };
  };

  const getStatusDisplayName = (status: ShipmentStatus) => {
      &apos;PENDING&apos;: &apos;Order Placed&apos;,
      &apos;PROCESSING&apos;: &apos;Processing&apos;,
      &apos;SHIPPED&apos;: &apos;Shipped&apos;,
      &apos;IN_TRANSIT&apos;: &apos;In Transit&apos;,
      &apos;OUT_FOR_DELIVERY&apos;: &apos;Out for Delivery&apos;,
      &apos;DELIVERED&apos;: &apos;Delivered&apos;,
      &apos;FAILED_DELIVERY&apos;: &apos;Delivery Failed&apos;,
      &apos;RETURNED&apos;: &apos;Returned&apos;,
      &apos;CANCELLED&apos;: &apos;Cancelled&apos;
    };
    return statusMap[status] || status;
  };

  // Create a comprehensive timeline including both tracking updates and key shipment events
  const createTimeline = () => {
    const timeline: Array<{
      status: ShipmentStatus;
      status_display: string;
      description: string;
      location?: string;
      timestamp: string;
      isFromTracking: boolean;
    }> = [];

    // Add tracking updates
    if (shipment.tracking_updates && shipment.tracking_updates.length > 0) {
      shipment.tracking_updates.forEach(update => {
        timeline.push({
          status: update.status,
          status_display: update.status_display,
          description: update.description,
          location: update.location,
          timestamp: update.timestamp,
          isFromTracking: true
        });
      });
    }

    // Add key shipment events if not already in tracking updates
    const trackingStatuses = new Set(timeline.map(t => t.status));

    // Add created event
    if (!trackingStatuses.has(&apos;PENDING&apos;)) {
      timeline.push({
        status: &apos;PENDING&apos;,
        status_display: &apos;Order Placed&apos;,
        description: &apos;Your order has been placed and is being prepared for shipment.&apos;,
        timestamp: shipment.created_at,
        isFromTracking: false
      });
    }

    // Add shipped event
    if (shipment.shipped_at && !trackingStatuses.has(&apos;SHIPPED&apos;)) {
      timeline.push({
        status: &apos;SHIPPED&apos;,
        status_display: &apos;Shipped&apos;,
        description: &apos;Your order has been shipped and is on its way.&apos;,
        timestamp: shipment.shipped_at,
        isFromTracking: false
      });
    }

    // Add delivered event
    if (shipment.delivered_at && !trackingStatuses.has(&apos;DELIVERED&apos;)) {
      timeline.push({
        status: &apos;DELIVERED&apos;,
        status_display: &apos;Delivered&apos;,
        description: &apos;Your order has been successfully delivered.&apos;,
        timestamp: shipment.delivered_at,
        isFromTracking: false
      });
    }

    // Sort by timestamp (most recent first)
    return timeline.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  };

  const timeline = createTimeline();
  const currentStatus = shipment.status;

  // Define the standard status progression
    &apos;PENDING&apos;,
    &apos;PROCESSING&apos;, 
    &apos;SHIPPED&apos;,
    &apos;IN_TRANSIT&apos;,
    &apos;OUT_FOR_DELIVERY&apos;,
    &apos;DELIVERED&apos;
  ];

  const getCurrentStatusIndex = () => {
    return statusProgression.indexOf(currentStatus);
  };

  const currentStatusIndex = getCurrentStatusIndex();

  return (
    <div className={`tracking-timeline ${className}`}>
      <h3 className="text-lg font-semibold mb-6">Tracking Timeline</h3>

      {/* Status Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {statusProgression.map((status, index) => {
            const isActive = index <= currentStatusIndex;
            const isCurrent = status === currentStatus;
            
            return (
              <div key={status} className="flex flex-col items-center flex-1">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  isActive ? getStatusColor(status, true) : 'bg-gray-300'
                } ${isCurrent ? 'ring-4 ring-blue-200' : ''}`}>
                  {getStatusIcon(status, isActive)}
                </div>
                <div className="mt-2 text-center">
                  <p className={`text-xs font-medium ${
                    isActive ? 'text-gray-900' : 'text-gray-500'
                  }`}>
                    {getStatusDisplayName(status)}
                  </p>
                </div>
                {index < statusProgression.length - 1 && (
                  <div className={`absolute h-0.5 w-full mt-5 ${
                    index < currentStatusIndex ? 'bg-blue-500' : 'bg-gray-300'
                  }`} style={{ 
                    left: '50%', 
                    right: '-50%',
                    zIndex: -1
                  }} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed Timeline */}
      {timeline.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-4">Detailed History</h4>
          <div className="space-y-4">
            {timeline.map((event, index) => {
              const isLatest = index === 0;
              
              return (
                <div key={`${event.timestamp}-${event.status}`} className="flex items-start">
                  <div className="flex-shrink-0 mr-4">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isLatest ? getStatusColor(event.status, true) : 'bg-gray-300'
                    }`}>
                      {getStatusIcon(event.status, isLatest)}
                    </div>
                    {index < timeline.length - 1 && (
                      <div className="w-0.5 h-8 bg-gray-300 mx-auto mt-2"></div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className={`text-sm font-medium ${
                        isLatest ? 'text-gray-900' : 'text-gray-700'
                      }`}>
                        {event.status_display}
                      </p>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">{date}</p>
                        <p className="text-xs text-gray-500">{time}</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {event.description}
                    </p>
                    {event.location && (
                      <p className="text-xs text-gray-500 mt-1 flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                        {event.location}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {timeline.length === 0 && (
        <div className="text-center py-8">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-600">No tracking information available yet</p>
        </div>
      )}
    </div>
  );
};

export default TrackingTimeline;