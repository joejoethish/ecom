'use client';

import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store';
import { fetchWishlist, removeFromWishlist, clearWishlist } from '@/store/slices/wishlistSlice';
import { addToCart } from '@/store/slices/cartSlice';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'react-hot-toast';
import { Heart, ShoppingCart, Trash2, Package } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { formatCurrency } from '@/utils/currency';

export default function WishlistPage() {
  const dispatch = useDispatch();
  const { wishlist, loading, error } = useSelector((state: RootState) => state.wishlist);
  const [removingItems, setRemovingItems] = useState<Set<string>>(new Set());
  const [addingToCart, setAddingToCart] = useState<Set<string>>(new Set());

  useEffect(() => {
    dispatch(fetchWishlist() as any);
  }, [dispatch]);

  const handleRemoveFromWishlist = async (itemId: string) => {
    setRemovingItems(prev => new Set(prev).add(itemId));
    try {
      await dispatch(removeFromWishlist(itemId) as any).unwrap();
      toast.success('Item removed from wishlist');
    } catch (error: any) {
      toast.error(error || 'Failed to remove item from wishlist');
    } finally {
      setRemovingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  const handleAddToCart = async (productId: string) => {
    setAddingToCart(prev => new Set(prev).add(productId));
    try {
      await dispatch(addToCart({ productId: productId, quantity: 1 }) as any).unwrap();
      toast.success('Item added to cart');
    } catch (error: any) {
      toast.error(error || 'Failed to add item to cart');
    } finally {
      setAddingToCart(prev => {
        const newSet = new Set(prev);
        newSet.delete(productId);
        return newSet;
      });
    }
  };

  const handleClearWishlist = async () => {
    if (window.confirm('Are you sure you want to clear your entire wishlist?')) {
      try {
        await dispatch(clearWishlist() as any).unwrap();
        toast.success('Wishlist cleared');
      } catch (error: any) {
        toast.error(error || 'Failed to clear wishlist');
      }
    }
  };

  if (loading && !wishlist) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, index) => (
            <Card key={index} className="overflow-hidden">
              <Skeleton className="h-48 w-full" />
              <CardContent className="p-4">
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-3/4 mb-4" />
                <div className="flex justify-between items-center">
                  <Skeleton className="h-6 w-20" />
                  <div className="flex gap-2">
                    <Skeleton className="h-8 w-8" />
                    <Skeleton className="h-8 w-8" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-6 text-center">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Error Loading Wishlist
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={() => dispatch(fetchWishlist() as any)}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const items = wishlist?.items || [];

  if (items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">My Wishlist</h1>
          <p className="text-gray-600">Save items you love for later</p>
        </div>
        
        <Card className="max-w-md mx-auto">
          <CardContent className="p-6 text-center">
            <Heart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Your wishlist is empty
            </h3>
            <p className="text-gray-600 mb-4">
              Start adding items you love to your wishlist
            </p>
            <Link href="/products">
              <Button>Browse Products</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">My Wishlist</h1>
          <p className="text-gray-600">
            {items.length} {items.length === 1 ? 'item' : 'items'} saved
          </p>
        </div>
        
        {items.length > 0 && (
          <Button
            variant="outline"
            onClick={handleClearWishlist}
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear All
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {items.map((item) => (
          <Card key={item.id} className="overflow-hidden hover:shadow-lg transition-shadow">
            <div className="relative">
              <Link href={`/products/${item.product.id}`}>
                <div className="aspect-square relative bg-gray-100">
                  {item.product.images && item.product.images.length > 0 ? (
                    <Image
                      src={item.product.images[0].image}
                      alt={item.product.images[0].alt_text || item.product.name}
                      fill
                      className="object-cover hover:scale-105 transition-transform duration-200"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <Package className="h-12 w-12 text-gray-400" />
                    </div>
                  )}
                </div>
              </Link>
              
              <Button
                variant="ghost"
                size="sm"
                className="absolute top-2 right-2 bg-white/80 hover:bg-white text-red-600 hover:text-red-700"
                onClick={() => handleRemoveFromWishlist(item.id)}
                disabled={removingItems.has(item.id)}
              >
                <Heart className="h-4 w-4 fill-current" />
              </Button>
            </div>

            <CardContent className="p-4">
              <Link href={`/products/${item.product.id}`}>
                <h3 className="font-semibold text-gray-900 mb-1 hover:text-blue-600 transition-colors line-clamp-2">
                  {item.product.name}
                </h3>
              </Link>
              
              {item.product.brand && (
                <p className="text-sm text-gray-600 mb-2">{item.product.brand}</p>
              )}

              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-gray-900">
                    {formatCurrency(item.product.discount_price || item.product.price)}
                  </span>
                  {item.product.discount_price && (
                    <span className="text-sm text-gray-500 line-through">
                      {formatCurrency(item.product.price)}
                    </span>
                  )}
                </div>
                
                {!item.product.is_active && (
                  <Badge variant="secondary">Out of Stock</Badge>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => handleAddToCart(item.product.id)}
                  disabled={!item.product.is_active || addingToCart.has(item.product.id)}
                  className="flex-1"
                >
                  <ShoppingCart className="h-4 w-4 mr-2" />
                  {addingToCart.has(item.product.id) ? 'Adding...' : 'Add to Cart'}
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRemoveFromWishlist(item.id)}
                  disabled={removingItems.has(item.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}