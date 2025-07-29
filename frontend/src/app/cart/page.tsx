'use client';

import { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Button } from '@/components/ui/Button';
import { useAppSelector, useAppDispatch } from '@/store';
import { updateCartItem, removeCartItem, fetchCart } from '@/store/slices/cartSlice';
import Link from 'next/link';
import { ROUTES } from '@/constants';
import toast from 'react-hot-toast';

// Mock cart data for demonstration
const mockCartItems = [
  {
    id: '1',
    product: {
      id: '1',
      name: 'iPhone 15 Pro Max (Natural Titanium, 256GB)',
      brand: 'Apple',
      price: 134900,
      discount_price: 134900,
      image: '/api/placeholder/150/150',
      rating: 4.5,
      reviewCount: 12543
    },
    quantity: 1,
    subtotal: 134900
  },
  {
    id: '2',
    product: {
      id: '2',
      name: 'Samsung Galaxy S24 Ultra (Titanium Black, 512GB)',
      brand: 'Samsung',
      price: 149999,
      discount_price: 129999,
      image: '/api/placeholder/150/150',
      rating: 4.3,
      reviewCount: 8765
    },
    quantity: 2,
    subtotal: 259998
  }
];

export default function CartPage() {
  const dispatch = useAppDispatch();
  const { items, itemCount, totalAmount, loading } = useAppSelector((state) => state.cart);
  const [cartItems, setCartItems] = useState(mockCartItems);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [selectAll, setSelectAll] = useState(false);

  useEffect(() => {
    // In a real app, this would fetch from the API
    // dispatch(fetchCart());
    setCartItems(mockCartItems);
  }, []);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  const handleQuantityChange = async (itemId: string, newQuantity: number) => {
    if (newQuantity < 1) return;
    
    try {
      // Update local state immediately for better UX
      setCartItems(prev => 
        prev.map(item => 
          item.id === itemId 
            ? { ...item, quantity: newQuantity, subtotal: item.product.discount_price * newQuantity }
            : item
        )
      );
      
      // In a real app, this would update via API
      // await dispatch(updateCartItem({ itemId, quantity: newQuantity })).unwrap();
    } catch (error) {
      toast.error('Failed to update quantity');
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    try {
      setCartItems(prev => prev.filter(item => item.id !== itemId));
      // await dispatch(removeCartItem(itemId)).unwrap();
      toast.success('Item removed from cart');
    } catch (error) {
      toast.error('Failed to remove item');
    }
  };

  const handleSelectItem = (itemId: string) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedItems([]);
    } else {
      setSelectedItems(cartItems.map(item => item.id));
    }
    setSelectAll(!selectAll);
  };

  const calculateSelectedTotal = () => {
    return cartItems
      .filter(item => selectedItems.includes(item.id))
      .reduce((total, item) => total + item.subtotal, 0);
  };

  const selectedTotal = calculateSelectedTotal();
  const selectedCount = selectedItems.length;

  if (cartItems.length === 0) {
    return (
      <Layout>
        <div className="bg-gray-50 min-h-screen">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="bg-white rounded-lg shadow-sm p-8 text-center">
              <div className="text-gray-400 mb-4">
                <svg className="w-24 h-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5M7 13l2.5 5m6-5v6a2 2 0 11-4 0v-6m4 0V9a2 2 0 10-4 0v4.01" />
                </svg>
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Your cart is empty</h2>
              <p className="text-gray-600 mb-6">Add items to your cart to see them here</p>
              <Link href={ROUTES.PRODUCTS}>
                <Button size="lg" className="bg-orange-500 hover:bg-orange-600">
                  Continue Shopping
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="bg-gray-50 min-h-screen">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">My Cart ({cartItems.length})</h1>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Cart Items */}
            <div className="lg:col-span-2 space-y-4">
              {/* Select All */}
              <div className="bg-white rounded-lg shadow-sm p-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectAll}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-900">
                    Select All ({cartItems.length} items)
                  </span>
                </label>
              </div>

              {/* Cart Items List */}
              {cartItems.map((item) => (
                <div key={item.id} className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-start space-x-4">
                    {/* Checkbox */}
                    <input
                      type="checkbox"
                      checked={selectedItems.includes(item.id)}
                      onChange={() => handleSelectItem(item.id)}
                      className="mt-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />

                    {/* Product Image */}
                    <div className="w-24 h-24 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                      <img
                        src={item.product.image}
                        alt={item.product.name}
                        className="w-full h-full object-contain"
                      />
                    </div>

                    {/* Product Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between">
                        <div className="flex-1">
                          <p className="text-sm text-gray-500 mb-1">{item.product.brand}</p>
                          <h3 className="text-lg font-medium text-gray-900 mb-2">
                            {item.product.name}
                          </h3>
                          
                          {/* Price */}
                          <div className="flex items-center space-x-2 mb-3">
                            <span className="text-xl font-bold text-gray-900">
                              {formatPrice(item.product.discount_price)}
                            </span>
                            {item.product.price !== item.product.discount_price && (
                              <>
                                <span className="text-sm text-gray-500 line-through">
                                  {formatPrice(item.product.price)}
                                </span>
                                <span className="text-sm text-green-600 font-medium">
                                  {Math.round(((item.product.price - item.product.discount_price) / item.product.price) * 100)}% off
                                </span>
                              </>
                            )}
                          </div>

                          {/* Offers */}
                          <div className="space-y-1 mb-4">
                            <div className="flex items-center text-xs text-green-600">
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Free Delivery
                            </div>
                            <div className="flex items-center text-xs text-blue-600">
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                              </svg>
                              7 days replacement
                            </div>
                          </div>

                          {/* Quantity Controls */}
                          <div className="flex items-center space-x-4">
                            <div className="flex items-center border border-gray-300 rounded">
                              <button
                                onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                                className="px-3 py-1 hover:bg-gray-100 text-gray-600"
                                disabled={item.quantity <= 1}
                              >
                                -
                              </button>
                              <span className="px-4 py-1 border-x border-gray-300 font-medium">
                                {item.quantity}
                              </span>
                              <button
                                onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                                className="px-3 py-1 hover:bg-gray-100 text-gray-600"
                              >
                                +
                              </button>
                            </div>

                            <button
                              onClick={() => handleRemoveItem(item.id)}
                              className="text-sm text-gray-500 hover:text-red-600 font-medium"
                            >
                              Remove
                            </button>

                            <button className="text-sm text-gray-500 hover:text-blue-600 font-medium">
                              Save for later
                            </button>
                          </div>
                        </div>

                        {/* Subtotal */}
                        <div className="text-right">
                          <p className="text-lg font-bold text-gray-900">
                            {formatPrice(item.subtotal)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Order Summary */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm p-6 sticky top-4">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Price Details ({selectedCount} item{selectedCount !== 1 ? 's' : ''})
                </h2>

                <div className="space-y-3 border-b border-gray-200 pb-4 mb-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Price</span>
                    <span className="text-gray-900">{formatPrice(selectedTotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Discount</span>
                    <span className="text-green-600">-{formatPrice(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Delivery Charges</span>
                    <span className="text-green-600">FREE</span>
                  </div>
                </div>

                <div className="flex justify-between text-lg font-semibold text-gray-900 mb-6">
                  <span>Total Amount</span>
                  <span>{formatPrice(selectedTotal)}</span>
                </div>

                <div className="space-y-3">
                  <Button
                    size="lg"
                    className="w-full bg-orange-500 hover:bg-orange-600"
                    disabled={selectedCount === 0}
                  >
                    Place Order
                  </Button>
                  
                  <div className="text-center">
                    <Link href={ROUTES.PRODUCTS}>
                      <Button variant="outline" size="lg" className="w-full">
                        Continue Shopping
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Safe and Secure */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-center text-sm text-gray-600">
                    <svg className="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    Safe and Secure Payments
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}