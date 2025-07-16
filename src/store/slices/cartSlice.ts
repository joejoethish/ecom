// Cart Redux slice

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Cart, CartItem, Product } from '@/types';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';

interface CartState {
  cart: Cart | null;
  items: CartItem[];
  loading: boolean;
  error: string | null;
  totalAmount: number;
  itemCount: number;
}

const initialState: CartState = {
  cart: null,
  items: [],
  loading: false,
  error: null,
  totalAmount: 0,
  itemCount: 0,
};

// Helper function to calculate totals
const calculateTotals = (items: CartItem[]) => {
  const totalAmount = items.reduce((total, item) => {
    const price = item.product.discount_price || item.product.price;
    return total + (price * item.quantity);
  }, 0);
  
  const itemCount = items.reduce((count, item) => count + item.quantity, 0);
  
  return { totalAmount, itemCount };
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
        return rejectWithValue(response.error?.message || 'Failed to fetch cart');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch cart');
    }
  }
);

export const addToCart = createAsyncThunk(
  'cart/addToCart',
  async ({ productId, quantity = 1 }: { productId: string; quantity?: number }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(API_ENDPOINTS.CART.ADD, {
        product_id: productId,
        quantity,
      });
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to add item to cart');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to add item to cart');
    }
  }
);

export const updateCartItem = createAsyncThunk(
  'cart/updateCartItem',
  async ({ itemId, quantity }: { itemId: string; quantity: number }, { rejectWithValue }) => {
    try {
      const response = await apiClient.put(API_ENDPOINTS.CART.UPDATE(itemId), {
        quantity,
      });
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to update cart item');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update cart item');
    }
  }
);

export const removeFromCart = createAsyncThunk(
  'cart/removeFromCart',
  async (itemId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.CART.REMOVE(itemId));
      
      if (response.success) {
        return itemId;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to remove item from cart');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to remove item from cart');
    }
  }
);

export const clearCart = createAsyncThunk(
  'cart/clearCart',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.CART.LIST);
      
      if (response.success) {
        return null;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to clear cart');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to clear cart');
    }
  }
);

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    // Local cart operations for immediate UI feedback
    addItemLocally: (state, action: PayloadAction<{ product: Product; quantity: number }>) => {
      const { product, quantity } = action.payload;
      const existingItem = state.items.find(item => item.product.id === product.id);
      
      if (existingItem) {
        existingItem.quantity += quantity;
      } else {
        const newItem: CartItem = {
          id: `temp-${Date.now()}`,
          product,
          quantity,
          added_at: new Date().toISOString(),
        };
        state.items.push(newItem);
      }
      
      const totals = calculateTotals(state.items);
      state.totalAmount = totals.totalAmount;
      state.itemCount = totals.itemCount;
    },
    updateItemLocally: (state, action: PayloadAction<{ itemId: string; quantity: number }>) => {
      const { itemId, quantity } = action.payload;
      const item = state.items.find(item => item.id === itemId);
      
      if (item) {
        item.quantity = quantity;
        const totals = calculateTotals(state.items);
        state.totalAmount = totals.totalAmount;
        state.itemCount = totals.itemCount;
      }
    },
    removeItemLocally: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter(item => item.id !== action.payload);
      const totals = calculateTotals(state.items);
      state.totalAmount = totals.totalAmount;
      state.itemCount = totals.itemCount;
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
        state.cart = action.payload;
        state.items = action.payload.items;
        const totals = calculateTotals(action.payload.items);
        state.totalAmount = totals.totalAmount;
        state.itemCount = totals.itemCount;
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
        // Refresh cart data
        if (action.payload.cart) {
          state.cart = action.payload.cart;
          state.items = action.payload.cart.items;
          const totals = calculateTotals(action.payload.cart.items);
          state.totalAmount = totals.totalAmount;
          state.itemCount = totals.itemCount;
        }
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
        // Update the specific item
        const updatedItem = action.payload;
        const itemIndex = state.items.findIndex(item => item.id === updatedItem.id);
        if (itemIndex !== -1) {
          state.items[itemIndex] = updatedItem;
          const totals = calculateTotals(state.items);
          state.totalAmount = totals.totalAmount;
          state.itemCount = totals.itemCount;
        }
        state.error = null;
      })
      .addCase(updateCartItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Remove from Cart
      .addCase(removeFromCart.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeFromCart.fulfilled, (state, action) => {
        state.loading = false;
        state.items = state.items.filter(item => item.id !== action.payload);
        const totals = calculateTotals(state.items);
        state.totalAmount = totals.totalAmount;
        state.itemCount = totals.itemCount;
        state.error = null;
      })
      .addCase(removeFromCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Clear Cart
      .addCase(clearCart.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(clearCart.fulfilled, (state) => {
        state.loading = false;
        state.cart = null;
        state.items = [];
        state.totalAmount = 0;
        state.itemCount = 0;
        state.error = null;
      })
      .addCase(clearCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { 
  clearError, 
  addItemLocally, 
  updateItemLocally, 
  removeItemLocally 
} = cartSlice.actions;

export default cartSlice.reducer;