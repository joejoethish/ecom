/**
 * Skeleton loading components for better user experience
 */
import React from 'react';

interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
}

export function Skeleton({ className = '', width, height }: SkeletonProps) {
  const style = {
    width: width || '100%',
    height: height || '1rem'
  };

  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      style={style}
    />
  );
}

export function SkeletonText({ lines = 3, className = '' }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          height="0.75rem"
          width={index === lines - 1 ? '75%' : '100%'}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`p-4 border border-gray-200 rounded-lg ${className}`}>
      <div className="flex items-center space-x-3 mb-4">
        <Skeleton width="3rem" height="3rem" className="rounded-full" />
        <div className="flex-1">
          <Skeleton height="1rem" width="60%" className="mb-2" />
          <Skeleton height="0.75rem" width="40%" />
        </div>
      </div>
      <SkeletonText lines={2} />
    </div>
  );
}

export function SkeletonTable({ 
  rows = 5, 
  columns = 4, 
  className = '' 
}: { 
  rows?: number; 
  columns?: number; 
  className?: string; 
}) {
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Table header */}
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={`header-${index}`} height="1rem" width="80%" />
        ))}
      </div>
      
      {/* Table rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div 
          key={`row-${rowIndex}`} 
          className="grid gap-4" 
          style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton 
              key={`cell-${rowIndex}-${colIndex}`} 
              height="1rem" 
              width={colIndex === 0 ? '100%' : '60%'} 
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonStats({ count = 4, className = '' }: { count?: number; className?: string }) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="p-4 border border-gray-200 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Skeleton width="1.5rem" height="1.5rem" className="rounded" />
            <Skeleton height="0.75rem" width="60%" />
          </div>
          <Skeleton height="2rem" width="40%" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonForm({ fields = 4, className = '' }: { fields?: number; className?: string }) {
  return (
    <div className={`space-y-6 ${className}`}>
      {Array.from({ length: fields }).map((_, index) => (
        <div key={index} className="space-y-2">
          <Skeleton height="0.75rem" width="25%" />
          <Skeleton height="2.5rem" width="100%" className="rounded-md" />
        </div>
      ))}
      <div className="flex justify-end space-x-3 pt-4">
        <Skeleton height="2.5rem" width="5rem" className="rounded-md" />
        <Skeleton height="2.5rem" width="7rem" className="rounded-md" />
      </div>
    </div>
  );
}

export function SkeletonInventoryItem({ className = '' }: { className?: string }) {
  return (
    <tr className={`animate-pulse ${className}`}>
      <td className="px-6 py-4 whitespace-nowrap">
        <Skeleton width="1rem" height="1rem" className="rounded" />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <Skeleton width="2.5rem" height="2.5rem" className="rounded-lg mr-4" />
          <div className="flex-1">
            <Skeleton height="1rem" width="80%" className="mb-1" />
            <Skeleton height="0.75rem" width="60%" />
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <Skeleton height="1rem" width="70%" className="mb-1" />
        <Skeleton height="0.75rem" width="50%" />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="space-y-1">
          <Skeleton height="0.75rem" width="60%" />
          <Skeleton height="0.75rem" width="60%" />
          <Skeleton height="0.75rem" width="60%" />
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <Skeleton height="1.5rem" width="4rem" className="rounded-full" />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <Skeleton height="1rem" width="2rem" />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <Skeleton height="0.75rem" width="4rem" />
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right">
        <div className="flex items-center justify-end space-x-2">
          <Skeleton width="2rem" height="2rem" className="rounded" />
          <Skeleton width="2rem" height="2rem" className="rounded" />
          <Skeleton width="2rem" height="2rem" className="rounded" />
        </div>
      </td>
    </tr>
  );
}

export function SkeletonWarehouseCard({ className = '' }: { className?: string }) {
  return (
    <div className={`p-6 border border-gray-200 rounded-lg animate-pulse ${className}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Skeleton width="2.5rem" height="2.5rem" className="rounded-lg" />
          <div>
            <Skeleton height="1.25rem" width="8rem" className="mb-1" />
            <Skeleton height="0.75rem" width="4rem" />
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <Skeleton width="2rem" height="2rem" className="rounded" />
          <Skeleton width="2rem" height="2rem" className="rounded" />
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-start space-x-2">
          <Skeleton width="1rem" height="1rem" className="rounded mt-0.5" />
          <div className="flex-1 space-y-1">
            <Skeleton height="0.75rem" width="100%" />
            <Skeleton height="0.75rem" width="80%" />
            <Skeleton height="0.75rem" width="60%" />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Skeleton width="1rem" height="1rem" className="rounded" />
          <Skeleton height="0.75rem" width="6rem" />
        </div>

        <div className="flex items-center space-x-2">
          <Skeleton width="1rem" height="1rem" className="rounded" />
          <Skeleton height="0.75rem" width="8rem" />
        </div>

        <div className="flex items-center space-x-2">
          <Skeleton width="1rem" height="1rem" className="rounded" />
          <Skeleton height="0.75rem" width="7rem" />
        </div>

        <div className="flex items-center justify-between pt-2 border-t">
          <Skeleton height="1.25rem" width="3rem" className="rounded-full" />
          <Skeleton height="0.75rem" width="5rem" />
        </div>
      </div>
    </div>
  );
}