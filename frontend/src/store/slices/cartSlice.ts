import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Cart, CartItem, SavedItem, AppliedCoupon } from '@/types';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';

interface CartState {
  items: CartItem[];
  savedItems: SavedItem[];
  appliedCoupons: AppliedCoupon[];
  itemCount: number;
  subtotal: number;
  discountAmount: number;
  totalAmount: number;
  loading: boolean;
  error: string | null;
}

  items: [],
  savedItems: [],
  appliedCoupons: [],
  itemCount: 0,
  subtotal: 0,
  discountAmount: 0,
  totalAmount: 0,
  loading: false,
  error: null,
};

// Async thunks
export const fetchCart = createAsyncThunk(
  'cart/fetchCart',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<Cart>(API_ENDPOINTS.CART.LIST);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to fetch cart&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to fetch cart&apos;);
    }
  }
);

export const addToCart = createAsyncThunk(
  &apos;cart/addToCart&apos;,
  async ({ productId, quantity }: { productId: string; quantity: number }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<CartItem>(API_ENDPOINTS.CART.ADD, {
        product_id: productId,
        quantity,
      });
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to add item to cart&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to add item to cart&apos;);
    }
  }
);

export const updateCartItem = createAsyncThunk(
  &apos;cart/updateCartItem&apos;,
  async ({ itemId, quantity }: { itemId: string; quantity: number }, { rejectWithValue }) => {
    try {
      const response = await apiClient.patch<CartItem>(API_ENDPOINTS.CART.UPDATE(itemId), {
        quantity,
      });
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to update cart item&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to update cart item&apos;);
    }
  }
);

export const removeCartItem = createAsyncThunk(
  &apos;cart/removeCartItem&apos;,
  async (itemId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.CART.REMOVE(itemId));
      
      if (response.success) {
        return itemId;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to remove item from cart&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to remove item from cart&apos;);
    }
  }
);

export const saveForLater = createAsyncThunk(
  &apos;cart/saveForLater&apos;,
  async (itemId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<SavedItem>(`/cart/save-for-later/${itemId}/`);
      
      if (response.success && response.data) {
        return { savedItem: response.data, itemId };
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to save item for later&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to save item for later&apos;);
    }
  }
);

export const moveToCart = createAsyncThunk(
  &apos;cart/moveToCart&apos;,
  async (savedItemId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<CartItem>(`/cart/move-to-cart/${savedItemId}/`);
      
      if (response.success && response.data) {
        return { cartItem: response.data, savedItemId };
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to move item to cart&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to move item to cart&apos;);
    }
  }
);

export const removeSavedItem = createAsyncThunk(
  &apos;cart/removeSavedItem&apos;,
  async (savedItemId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.delete(`/cart/saved-items/${savedItemId}/`);
      
      if (response.success) {
        return savedItemId;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to remove saved item&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to remove saved item&apos;);
    }
  }
);

export const applyCoupon = createAsyncThunk(
  &apos;cart/applyCoupon&apos;,
  async (couponCode: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<AppliedCoupon>('/cart/apply-coupon/', {
        code: couponCode,
      });
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to apply coupon');
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || 'Failed to apply coupon');
    }
  }
);

export const removeCoupon = createAsyncThunk(
  'cart/removeCoupon',
  async (couponId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.delete(`/cart/remove-coupon/${couponId}/`);
      
      if (response.success) {
        return couponId;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to remove coupon');
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || 'Failed to remove coupon');
    }
  }
);

// Helper function to calculate cart totals
const calculateCartTotals = (items: CartItem[]) => {
  const itemCount = items.reduce((total, item) => total + item.quantity, 0);
  const totalAmount = items.reduce((total, item) => {
    const price = item.product.discount_price || item.product.price;
    return total + price * item.quantity;
  }, 0);
  
  return { itemCount, totalAmount };
};

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearCart: (state) => {
      state.items = [];
      state.itemCount = 0;
      state.totalAmount = 0;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Cart
      .addCase(fetchCart.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCart.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.savedItems = action.payload.saved_items || [];
        state.appliedCoupons = action.payload.applied_coupons || [];
        state.subtotal = action.payload.subtotal;
        state.discountAmount = action.payload.discount_amount;
        state.totalAmount = action.payload.total_amount;
        state.itemCount = itemCount;
        state.error = null;
      })
      .addCase(fetchCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Add to Cart
      .addCase(addToCart.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addToCart.fulfilled, (state, action) => {
        state.loading = false;
        
        // Check if item already exists in cart
        const existingItemIndex = state.items.findIndex(
          item => item.product.id === action.payload.product.id
        );
        
        if (existingItemIndex >= 0) {
          // Update existing item
          state.items[existingItemIndex].quantity += action.payload.quantity;
        } else {
          // Add new item
          state.items.push(action.payload);
        }
        
        state.itemCount = itemCount;
        state.totalAmount = totalAmount;
        state.error = null;
      })
      .addCase(addToCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Update Cart Item
      .addCase(updateCartItem.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateCartItem.fulfilled, (state, action) => {
        state.loading = false;
        
        // Update item quantity
        const itemIndex = state.items.findIndex(item => item.id === action.payload.id);
        if (itemIndex >= 0) {
          state.items[itemIndex].quantity = action.payload.quantity;
        }
        
        state.itemCount = itemCount;
        state.totalAmount = totalAmount;
        state.error = null;
      })
      .addCase(updateCartItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Remove Cart Item
      .addCase(removeCartItem.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeCartItem.fulfilled, (state, action) => {
        state.loading = false;
        
        // Remove item from cart
        state.items = state.items.filter(item => item.id !== action.payload);
        
        state.itemCount = itemCount;
        state.totalAmount = totalAmount;
        state.error = null;
      })
      .addCase(removeCartItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Save for Later
      .addCase(saveForLater.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(saveForLater.fulfilled, (state, action) => {
        state.loading = false;
        
        // Remove item from cart and add to saved items
        state.items = state.items.filter(item => item.id !== action.payload.itemId);
        state.savedItems.push(action.payload.savedItem);
        
        state.itemCount = itemCount;
        state.totalAmount = totalAmount;
        state.error = null;
      })
      .addCase(saveForLater.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Move to Cart
      .addCase(moveToCart.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(moveToCart.fulfilled, (state, action) => {
        state.loading = false;
        
        // Remove from saved items and add to cart
        state.savedItems = state.savedItems.filter(item => item.id !== action.payload.savedItemId);
        state.items.push(action.payload.cartItem);
        
        state.itemCount = itemCount;
        state.totalAmount = totalAmount;
        state.error = null;
      })
      .addCase(moveToCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Remove Saved Item
      .addCase(removeSavedItem.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeSavedItem.fulfilled, (state, action) => {
        state.loading = false;
        
        // Remove from saved items
        state.savedItems = state.savedItems.filter(item => item.id !== action.payload);
        state.error = null;
      })
      .addCase(removeSavedItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Apply Coupon
      .addCase(applyCoupon.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(applyCoupon.fulfilled, (state, action) => {
        state.loading = false;
        
        // Add coupon to applied coupons
        state.appliedCoupons.push(action.payload);
        state.discountAmount += action.payload.discount_amount;
        state.totalAmount = state.subtotal - state.discountAmount;
        state.error = null;
      })
      .addCase(applyCoupon.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Remove Coupon
      .addCase(removeCoupon.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeCoupon.fulfilled, (state, action) => {
        state.loading = false;
        
        // Remove coupon from applied coupons
        const removedCoupon = state.appliedCoupons.find(c => c.coupon.id === action.payload);
        if (removedCoupon) {
          state.discountAmount -= removedCoupon.discount_amount;
          state.appliedCoupons = state.appliedCoupons.filter(c => c.coupon.id !== action.payload);
          state.totalAmount = state.subtotal - state.discountAmount;
        }
        state.error = null;
      })
      .addCase(removeCoupon.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export default cartSlice.reducer;