import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/hooks/redux';
import { addToWishlist, removeFromWishlist, fetchWishlist } from '@/store/slices/wishlistSlice';
import toast from 'react-hot-toast';

export function useWishlist() {
  const dispatch = useAppDispatch();

  const isInWishlist = useCallback((productId: string) => {
    return wishlist?.items.some(item => item.product.id === productId) || false;
  }, [wishlist]);

  const toggleWishlist = useCallback(async (productId: string, productName?: string) => {
    try {
      if (isInWishlist(productId)) {
        const item = wishlist?.items.find(item => item.product.id === productId);
        if (item) {
          await dispatch(removeFromWishlist(item.id)).unwrap();
          toast.success(`${productName || 'Item'} removed from wishlist`);
        }
      } else {
        await dispatch(addToWishlist(productId)).unwrap();
        toast.success(`${productName || 'Item'} added to wishlist`);
      }
    } catch (error: unknown) {
      toast.error(error || 'Failed to update wishlist');
    }
  }, [dispatch, isInWishlist, wishlist]);

  const addToWishlistHandler = useCallback(async (productId: string, productName?: string) => {
    try {
      await dispatch(addToWishlist(productId)).unwrap();
      toast.success(`${productName || 'Item'} added to wishlist`);
    } catch (error: unknown) {
      toast.error(error || 'Failed to add to wishlist');
    }
  }, [dispatch]);

  const removeFromWishlistHandler = useCallback(async (itemId: string, productName?: string) => {
    try {
      await dispatch(removeFromWishlist(itemId)).unwrap();
      toast.success(`${productName || 'Item'} removed from wishlist`);
    } catch (error: unknown) {
      toast.error(error || 'Failed to remove from wishlist');
    }
  }, [dispatch]);

  const refreshWishlist = useCallback(async () => {
    try {
      await dispatch(fetchWishlist()).unwrap();
    } catch (error: unknown) {
      toast.error('Failed to refresh wishlist');
    }
  }, [dispatch]);

  return {
    wishlist,
    loading,
    isInWishlist,
    toggleWishlist,
    addToWishlist: addToWishlistHandler,
    removeFromWishlist: removeFromWishlistHandler,
    refreshWishlist,
  };
}