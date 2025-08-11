import React from 'react';
import Image from 'next/image';
import { SavedItem } from '@/types';
import { useAppDispatch } from '@/hooks/redux';
import { moveToCart, removeSavedItem } from '@/store/slices/cartSlice';

interface SavedItemsProps {
  savedItems: SavedItem[];
}

  const dispatch = useAppDispatch();

  const handleMoveToCart = (savedItemId: string) => {
    dispatch(moveToCart(savedItemId));
  };

  const handleRemove = (savedItemId: string) => {
    dispatch(removeSavedItem(savedItemId));
  };

  if (savedItems.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 text-center">
        <div className="text-gray-400 mb-2">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No saved items</h3>
        <p className="text-gray-500">Items you save for later will appear here</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Saved for Later ({savedItems.length})
        </h2>
      </div>
      
      <div className="divide-y divide-gray-200">
        {savedItems.map((savedItem) => {
          const currentPrice = savedItem.product.discount_price || savedItem.product.price;
          const originalPrice = savedItem.product.price;
          const hasDiscount = savedItem.product.discount_price && savedItem.product.discount_price < savedItem.product.price;

          return (
            <div key={savedItem.id} className="flex items-start gap-4 p-4">
              {/* Product Image */}
              <div className="flex-shrink-0">
                <div className="relative w-16 h-16 rounded-lg overflow-hidden">
                  <Image
                    src={savedItem.product.images[0]?.image || '/placeholder-product.jpg'}
                    alt={savedItem.product.images[0]?.alt_text || savedItem.product.name}
                    fill
                    className="object-cover"
                  />
                </div>
              </div>

              {/* Product Details */}
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
                  {savedItem.product.name}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  Brand: {savedItem.product.brand}
                </p>
                
                {/* Price */}
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-base font-semibold text-gray-900">
                    ₹{currentPrice.toLocaleString()}
                  </span>
                  {hasDiscount && (
                    <>
                      <span className="text-sm text-gray-500 line-through">
                        ₹{originalPrice.toLocaleString()}
                      </span>
                      <span className="text-sm text-green-600 font-medium">
                        {Math.round(((originalPrice - currentPrice) / originalPrice) * 100)}% off
                      </span>
                    </>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-4 mt-3">
                  <button
                    onClick={() => handleMoveToCart(savedItem.id)}
                    className=&quot;px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors&quot;
                  >
                    Move to Cart
                  </button>
                  <button
                    onClick={() => handleRemove(savedItem.id)}
                    className=&quot;text-sm text-red-600 hover:text-red-800 font-medium&quot;
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SavedItems;