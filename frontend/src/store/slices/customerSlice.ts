// Customer profile Redux slice

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { CustomerProfile, CustomerPreferences, Address, ApiResponse } from '@/types';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';

interface CustomerState {
  profile: CustomerProfile | null;
  addresses: Address[];
  loading: boolean;
  error: string | null;
}

const initialState: CustomerState = {
  profile: null,
  addresses: [],
  loading: false,
  error: null,
};

// Async thunks
export const fetchCustomerProfile = createAsyncThunk(
  'customer/fetchProfile',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(API_ENDPOINTS.CUSTOMER.PROFILE);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to fetch profile');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch profile');
    }
  }
);

export const updateCustomerProfile = createAsyncThunk(
  'customer/updateProfile',
  async (profileData: Partial<CustomerProfile>, { rejectWithValue }) => {
    try {
      const response = await apiClient.put(API_ENDPOINTS.CUSTOMER.PROFILE, profileData);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to update profile');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update profile');
    }
  }
);

export const updateCustomerPreferences = createAsyncThunk(
  'customer/updatePreferences',
  async (preferences: CustomerPreferences, { rejectWithValue }) => {
    try {
      const response = await apiClient.put(API_ENDPOINTS.CUSTOMER.PREFERENCES, preferences);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to update preferences');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update preferences');
    }
  }
);

export const fetchCustomerAddresses = createAsyncThunk(
  'customer/fetchAddresses',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(API_ENDPOINTS.CUSTOMER.ADDRESSES);
      
      if (response.success && response.data) {
        return response.data.results || response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to fetch addresses');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch addresses');
    }
  }
);

export const createCustomerAddress = createAsyncThunk(
  'customer/createAddress',
  async (addressData: Omit<Address, 'id'>, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(API_ENDPOINTS.CUSTOMER.ADDRESSES, addressData);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to create address');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create address');
    }
  }
);

export const updateCustomerAddress = createAsyncThunk(
  'customer/updateAddress',
  async ({ id, addressData }: { id: string; addressData: Partial<Address> }, { rejectWithValue }) => {
    try {
      const response = await apiClient.put(API_ENDPOINTS.CUSTOMER.ADDRESS_DETAIL(id), addressData);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to update address');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update address');
    }
  }
);

export const deleteCustomerAddress = createAsyncThunk(
  'customer/deleteAddress',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.CUSTOMER.ADDRESS_DETAIL(id));
      
      if (response.success) {
        return id;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to delete address');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to delete address');
    }
  }
);

const customerSlice = createSlice({
  name: 'customer',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Profile
      .addCase(fetchCustomerProfile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCustomerProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.profile = action.payload;
        state.error = null;
      })
      .addCase(fetchCustomerProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Update Profile
      .addCase(updateCustomerProfile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateCustomerProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.profile = action.payload;
        state.error = null;
      })
      .addCase(updateCustomerProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Update Preferences
      .addCase(updateCustomerPreferences.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateCustomerPreferences.fulfilled, (state, action) => {
        state.loading = false;
        if (state.profile) {
          state.profile.preferences = action.payload;
        }
        state.error = null;
      })
      .addCase(updateCustomerPreferences.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Fetch Addresses
      .addCase(fetchCustomerAddresses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCustomerAddresses.fulfilled, (state, action) => {
        state.loading = false;
        state.addresses = action.payload;
        state.error = null;
      })
      .addCase(fetchCustomerAddresses.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Create Address
      .addCase(createCustomerAddress.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createCustomerAddress.fulfilled, (state, action) => {
        state.loading = false;
        state.addresses.push(action.payload);
        state.error = null;
      })
      .addCase(createCustomerAddress.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Update Address
      .addCase(updateCustomerAddress.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateCustomerAddress.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.addresses.findIndex(addr => addr.id === action.payload.id);
        if (index !== -1) {
          state.addresses[index] = action.payload;
        }
        state.error = null;
      })
      .addCase(updateCustomerAddress.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Delete Address
      .addCase(deleteCustomerAddress.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteCustomerAddress.fulfilled, (state, action) => {
        state.loading = false;
        state.addresses = state.addresses.filter(addr => addr.id !== action.payload);
        state.error = null;
      })
      .addCase(deleteCustomerAddress.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = customerSlice.actions;
export default customerSlice.reducer;