import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';
import {
  SellerProfile,
  SellerKYC,
  SellerBankAccount,
  SellerPayout,
  SellerAnalytics,
  SellerRegistrationData,
  KYCDocumentData,
  BankAccountData
} from '../../types/sellers';

// API Response interface
interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: {
    message: string;
    code: string;
    status_code: number;
    details?: any;
  };
}

// Type guard for File objects
const isFile = (value: unknown): value is File => {
  return value instanceof File;
};

// Define the state interface
interface SellerState {
  profile: SellerProfile | null;
  kycDocuments: SellerKYC[];
  bankAccounts: SellerBankAccount[];
  payouts: SellerPayout[];
  analytics: SellerAnalytics | null;
  loading: boolean;
  error: string | null;
}

// Initial state
const initialState: SellerState = {
  profile: null,
  kycDocuments: [],
  bankAccounts: [],
  payouts: [],
  analytics: null,
  loading: false,
  error: null,
};

// Async thunks
export const fetchSellerProfile = createAsyncThunk(
  'seller/fetchProfile',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerProfile>>('/api/v1/seller/profile/');
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch seller profile');
    }
  }
);

export const registerAsSeller = createAsyncThunk(
  'seller/register',
  async (sellerData: SellerRegistrationData, { rejectWithValue }) => {
    try {
      // Create FormData for file uploads
      const formData = new FormData();
      Object.entries(sellerData).forEach(([key, value]) => {
        if (isFile(value)) {
          formData.append(key, value);
        } else if (value !== undefined && value !== null) {
          formData.append(key, value.toString());
        }
      });

      const response = await axios.post<ApiResponse<SellerProfile>>('/api/v1/seller/register/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to register as seller');
    }
  }
);

export const updateSellerProfile = createAsyncThunk(
  'seller/updateProfile',
  async (profileData: Partial<SellerProfile>, { rejectWithValue }) => {
    try {
      // Create FormData for file uploads
      const formData = new FormData();
      Object.entries(profileData).forEach(([key, value]) => {
        if (isFile(value)) {
          formData.append(key, value);
        } else if (value !== undefined && value !== null) {
          formData.append(key, String(value));
        }
      });

      const response = await axios.put<ApiResponse<SellerProfile>>('/api/v1/seller/profile/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to update seller profile');
    }
  }
);

export const fetchKYCDocuments = createAsyncThunk(
  'seller/fetchKYCDocuments',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerKYC[]>>('/api/v1/seller/kyc/');
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch KYC documents');
    }
  }
);

export const uploadKYCDocument = createAsyncThunk(
  'seller/uploadKYCDocument',
  async (documentData: KYCDocumentData, { rejectWithValue }) => {
    try {
      // Create FormData for file uploads
      const formData = new FormData();
      Object.entries(documentData).forEach(([key, value]) => {
        if (isFile(value)) {
          formData.append(key, value);
        } else if (value !== undefined && value !== null) {
          formData.append(key, value.toString());
        }
      });

      const response = await axios.post<ApiResponse<SellerKYC>>('/api/v1/seller/kyc/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to upload KYC document');
    }
  }
);

export const fetchBankAccounts = createAsyncThunk(
  'seller/fetchBankAccounts',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerBankAccount[]>>('/api/v1/seller/bank-accounts/');
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch bank accounts');
    }
  }
);

export const addBankAccount = createAsyncThunk(
  'seller/addBankAccount',
  async (accountData: BankAccountData, { rejectWithValue }) => {
    try {
      // Create FormData for file uploads
      const formData = new FormData();
      Object.entries(accountData).forEach(([key, value]) => {
        if (isFile(value)) {
          formData.append(key, value);
        } else if (value !== undefined && value !== null) {
          formData.append(key, value.toString());
        }
      });

      const response = await axios.post<ApiResponse<SellerBankAccount>>('/api/v1/seller/bank-accounts/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to add bank account');
    }
  }
);

export const setPrimaryBankAccount = createAsyncThunk(
  'seller/setPrimaryBankAccount',
  async (accountId: string, { rejectWithValue }) => {
    try {
      const response = await axios.post<ApiResponse<SellerBankAccount>>(`/api/v1/seller/bank-accounts/${accountId}/set_primary/`);
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to set primary bank account');
    }
  }
);

export const fetchPayoutHistory = createAsyncThunk(
  'seller/fetchPayoutHistory',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerPayout[]>>('/api/v1/seller/payouts/');
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch payout history');
    }
  }
);

export const fetchSellerAnalytics = createAsyncThunk(
  'seller/fetchAnalytics',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerAnalytics>>('/api/v1/seller/analytics/');
      return response.data.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch seller analytics');
    }
  }
);

// Create the slice
const sellerSlice = createSlice({
  name: 'seller',
  initialState,
  reducers: {
    clearSellerError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch seller profile
      .addCase(fetchSellerProfile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSellerProfile.fulfilled, (state, action: PayloadAction<SellerProfile>) => {
        state.loading = false;
        state.profile = action.payload;
      })
      .addCase(fetchSellerProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Register as seller
      .addCase(registerAsSeller.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerAsSeller.fulfilled, (state, action: PayloadAction<SellerProfile>) => {
        state.loading = false;
        state.profile = action.payload;
      })
      .addCase(registerAsSeller.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Update seller profile
      .addCase(updateSellerProfile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateSellerProfile.fulfilled, (state, action: PayloadAction<SellerProfile>) => {
        state.loading = false;
        state.profile = action.payload;
      })
      .addCase(updateSellerProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Fetch KYC documents
      .addCase(fetchKYCDocuments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchKYCDocuments.fulfilled, (state, action: PayloadAction<SellerKYC[]>) => {
        state.loading = false;
        state.kycDocuments = action.payload;
      })
      .addCase(fetchKYCDocuments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Upload KYC document
      .addCase(uploadKYCDocument.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadKYCDocument.fulfilled, (state, action: PayloadAction<SellerKYC>) => {
        state.loading = false;
        state.kycDocuments = [...state.kycDocuments, action.payload];
      })
      .addCase(uploadKYCDocument.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Fetch bank accounts
      .addCase(fetchBankAccounts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBankAccounts.fulfilled, (state, action: PayloadAction<SellerBankAccount[]>) => {
        state.loading = false;
        state.bankAccounts = action.payload;
      })
      .addCase(fetchBankAccounts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Add bank account
      .addCase(addBankAccount.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addBankAccount.fulfilled, (state, action: PayloadAction<SellerBankAccount>) => {
        state.loading = false;
        state.bankAccounts = [...state.bankAccounts, action.payload];
      })
      .addCase(addBankAccount.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Set primary bank account
      .addCase(setPrimaryBankAccount.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(setPrimaryBankAccount.fulfilled, (state, action: PayloadAction<SellerBankAccount>) => {
        state.loading = false;
        state.bankAccounts = state.bankAccounts.map(account => ({
          ...account,
          is_primary: account.id === action.payload.id
        }));
      })
      .addCase(setPrimaryBankAccount.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Fetch payout history
      .addCase(fetchPayoutHistory.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPayoutHistory.fulfilled, (state, action: PayloadAction<SellerPayout[]>) => {
        state.loading = false;
        state.payouts = action.payload;
      })
      .addCase(fetchPayoutHistory.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Fetch seller analytics
      .addCase(fetchSellerAnalytics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSellerAnalytics.fulfilled, (state, action: PayloadAction<SellerAnalytics>) => {
        state.loading = false;
        state.analytics = action.payload;
      })
      .addCase(fetchSellerAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearSellerError } = sellerSlice.actions;
export default sellerSlice.reducer;