'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAppDispatch, useAppSelector } from '@/hooks/redux';
import { fetchWishlist, removeFromWishlist, clearWishlist } from '@/store/slices/wishlistSlice';
import { addToCart } from '@/store/slices/cartSlice';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/constants';
import toast from 'react-hot-toast';

export function Wishlist() {
  const dispatch = useAppDispatch();
  const { wishlist, loading } = useAppSelector((state) => state.wishlist);
  const [removingItems, setRemovingItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    dispatch(fetchWishlist());
  }, [dispatch]);

  const handleRemoveItem = async (itemId: string) => {
    setRemovingItems(prev => new Set(prev).add(itemId));
    
    try {
      await dispatch(removeFromWishlist(itemId)).unwrap();
      toast.success('Item removed from wishlist');
    } catch (error: any) {
      toast.error(error || 'Failed to remove item');
    } finally {
      setRemovingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  const handleAddToCart = async (productId: string, productName: string) => {
    try {
      await dispatch(addToCart({ productId, quantity: 1 })).unwrap();
      toast.success(`${productName} added to cart`);
    } catch (error: any) {
      toast.error(error || 'Failed to add to cart');
    }
  };

  const handleClearWishlist = async () => {
    if (!wishlist?.items.length) return;
    
    if (window.confirm('Are you sure you want to clear your entire wishlist?')) {
      try {
        await dispatch(clearWishlist()).unwrap();
        toast.success('Wishlist cleared');
      } catch (error: any) {
        toast.error(error || 'Failed to clear wishlist');
      }
    }
  };

  const handleRefresh = async () => {
    try {
      await dispatch(fetchWishlist()).unwrap();
      toast.success('Wishlist refreshed');
    } catch (error: any) {
      toast.error('Failed to refresh wishlist');
    }
  };

  if (loading && !wishlist) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex space-x-4">
                  <div className="h-20 w-20 bg-gray-200 rounded"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            My Wishlist
            {wishlist?.items && (
              <span className="ml-2 text-sm text-gray-500">
                ({wishlist.items.length} {wishlist.items.length === 1 ? 'item' : 'items'})
              </span>
            )}
          </h2>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              loading={loading}
            >
              Refresh
            </Button>
            {wishlist?.items && wishlist.items.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearWishlist}
                className="text-red-600 hover:text-red-700"
              >
                Clear All
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="px-6 py-4">
        {!wishlist?.items || wishlist.items.length === 0 ? (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">Your wishlist is empty</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start adding products you love to your wishlist.
            </p>
            <div className="mt-6">
              <Link href={ROUTES.PRODUCTS}>
                <Button variant="primary">
                  Browse Products
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {wishlist.items.map((item) => (
              <div
                key={item.id}
                className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
              >
                {/* Product Image */}
                <div className="flex-shrink-0">
                  <div className="h-20 w-20 relative">
                    {item.product.images && item.product.images.length > 0 ? (
                      <Image
                        src={item.product.images.find(img => img.is_primary)?.image || item.product.images[0].image}
                        alt={item.product.name}
                        fill
                        className="object-cover rounded-md"
                      />
                    ) : (
                      <div className="h-full w-full bg-gray-200 rounded-md flex items-center justify-center">
                        <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                    )}
                  </div>
                </div>

                {/* Product Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <Link
                        href={item.product.slug ? ROUTES.PRODUCT_DETAIL(item.product.slug) : ROUTES.PRODUCTS}
                        className="text-sm font-medium text-gray-900 hover:text-blue-600 line-clamp-2"
                      >
                        {item.product.name}
                      </Link>
                      <p className="text-sm text-gray-500 mt-1 line-clamp-1">
                        {item.product.short_description}
                      </p>
                      <div className="flex items-center mt-2 space-x-2">
                        <span className="text-lg font-semibold text-gray-900">
                          ${item.product.discount_price || item.product.price}
                        </span>
                        {item.product.discount_price && (
                          <span className="text-sm text-gray-500 line-through">
                            ${item.product.price}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        Added {new Date(item.added_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col space-y-2">
                  <Button
                    size="sm"
                    onClick={() => handleAddToCart(item.product.id, item.product.name)}
                    disabled={!item.product.is_active}
                  >
                    Add to Cart
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRemoveItem(item.id)}
                    loading={removingItems.has(item.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}