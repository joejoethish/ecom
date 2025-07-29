import React from 'react';
import Image from 'next/image';
import { CartItem as CartItemType } from '@/types';
import { useAppDispatch } from '@/hooks/redux';
import { updateCartItem, removeCartItem, saveForLater } from '@/store/slices/cartSlice';

interface CartItemProps {
  item: CartItemType;
}

const CartItem: React.FC<CartItemProps> = ({ item }) => {
  const dispatch = useAppDispatch();

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity > 0) {
      dispatch(updateCartItem({ itemId: item.id, quantity: newQuantity }));
    }
  };

  const handleRemove = () => {
    dispatch(removeCartItem(item.id));
  };

  const handleSaveForLater = () => {
    dispatch(saveForLater(item.id));
  };

  const currentPrice = item.product.discount_price || item.product.price;
  const originalPrice = item.product.price;
  const hasDiscount = item.product.discount_price && item.product.discount_price < item.product.price;

  return (
    <div className="flex items-start gap-4 p-4 border-b border-gray-200 bg-white">
      {/* Product Image */}
      <div className="flex-shrink-0">
        <div className="relative w-20 h-20 rounded-lg overflow-hidden">
          <Image
            src={item.product.images[0]?.image || '/placeholder-product.jpg'}
            alt={item.product.images[0]?.alt_text || item.product.name}
            fill
            className="object-cover"
          />
        </div>
      </div>

      {/* Product Details */}
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
          {item.product.name}
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          Brand: {item.product.brand}
        </p>
        
        {/* Price */}
        <div className="flex items-center gap-2 mt-2">
          <span className="text-lg font-semibold text-gray-900">
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
          {/* Quantity Controls */}
          <div className="flex items-center border border-gray-300 rounded">
            <button
              onClick={() => handleQuantityChange(item.quantity - 1)}
              className="px-3 py-1 text-gray-600 hover:bg-gray-100 transition-colors"
              disabled={item.quantity <= 1}
            >
              -
            </button>
            <span className="px-3 py-1 text-sm font-medium border-x border-gray-300">
              {item.quantity}
            </span>
            <button
              onClick={() => handleQuantityChange(item.quantity + 1)}
              className="px-3 py-1 text-gray-600 hover:bg-gray-100 transition-colors"
            >
              +
            </button>
          </div>

          {/* Action Buttons */}
          <button
            onClick={handleSaveForLater}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Save for Later
          </button>
          <button
            onClick={handleRemove}
            className="text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Remove
          </button>
        </div>
      </div>

      {/* Item Total */}
      <div className="flex-shrink-0 text-right">
        <div className="text-lg font-semibold text-gray-900">
          ₹{(currentPrice * item.quantity).toLocaleString()}
        </div>
        {hasDiscount && (
          <div className="text-sm text-gray-500 line-through">
            ₹{(originalPrice * item.quantity).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
};

export default CartItem;