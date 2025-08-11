// Wishlist Redux slice

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Wishlist, WishlistItem, Product } from '../../types';
import { apiClient } from '../../utils/api';
import { API_ENDPOINTS } from '../../constants';

interface WishlistState {
  wishlist: Wishlist | null;
  loading: boolean;
  error: string | null;
}

const initialState: WishlistState = {
  wishlist: null,
  loading: false,
  error: null,
};

// Async thunks
export const fetchWishlist = createAsyncThunk(
  'wishlist/fetch',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(API_ENDPOINTS.WISHLIST.LIST);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to fetch wishlist');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch wishlist');
    }
  }
);

export const addToWishlist = createAsyncThunk(
  'wishlist/add',
  async (productId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(API_ENDPOINTS.WISHLIST.ADD, {
        product_id: productId,
      });
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to add to wishlist');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to add to wishlist');
    }
  }
);

export const removeFromWishlist = createAsyncThunk(
  'wishlist/remove',
  async (itemId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.WISHLIST.REMOVE(itemId));
      
      if (response.success) {
        return itemId;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to remove from wishlist');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to remove from wishlist');
    }
  }
);

export const clearWishlist = createAsyncThunk(
  'wishlist/clear',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.WISHLIST.CLEAR);
      
      if (response.success) {
        return null;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to clear wishlist');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to clear wishlist');
    }
  }
);

const wishlistSlice = createSlice({
  name: 'wishlist',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Wishlist
      .addCase(fetchWishlist.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchWishlist.fulfilled, (state, action) => {
        state.loading = false;
        state.wishlist = action.payload;
        state.error = null;
      })
      .addCase(fetchWishlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Add to Wishlist
      .addCase(addToWishlist.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addToWishlist.fulfilled, (state, action) => {
        state.loading = false;
        if (state.wishlist) {
          state.wishlist.items.push(action.payload);
        } else {
          state.wishlist = {
            id: 'temp-id',
            items: [action.payload],
            created_at: new Date().toISOString(),
          };
        }
        state.error = null;
      })
      .addCase(addToWishlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Remove from Wishlist
      .addCase(removeFromWishlist.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeFromWishlist.fulfilled, (state, action) => {
        state.loading = false;
        if (state.wishlist) {
          state.wishlist.items = state.wishlist.items.filter(
            item => item.id !== action.payload
          );
        }
        state.error = null;
      })
      .addCase(removeFromWishlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Clear Wishlist
      .addCase(clearWishlist.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(clearWishlist.fulfilled, (state) => {
        state.loading = false;
        if (state.wishlist) {
          state.wishlist.items = [];
        }
        state.error = null;
      })
      .addCase(clearWishlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = wishlistSlice.actions;
export default wishlistSlice.reducer;