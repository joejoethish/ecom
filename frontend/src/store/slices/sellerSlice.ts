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
    details?: unknown;
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
  &apos;seller/fetchProfile&apos;,
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerProfile>>(&apos;/api/v1/seller/profile/&apos;);
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to fetch seller profile&apos;);
    }
  }
);

export const registerAsSeller = createAsyncThunk(
  &apos;seller/register&apos;,
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

      const response = await axios.post<ApiResponse<SellerProfile>>(&apos;/api/v1/seller/register/&apos;, formData, {
        headers: {
          &apos;Content-Type&apos;: &apos;multipart/form-data&apos;,
        },
      });
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to register as seller&apos;);
    }
  }
);

export const updateSellerProfile = createAsyncThunk(
  &apos;seller/updateProfile&apos;,
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

      const response = await axios.put<ApiResponse<SellerProfile>>(&apos;/api/v1/seller/profile/&apos;, formData, {
        headers: {
          &apos;Content-Type&apos;: &apos;multipart/form-data&apos;,
        },
      });
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to update seller profile&apos;);
    }
  }
);

export const fetchKYCDocuments = createAsyncThunk(
  &apos;seller/fetchKYCDocuments&apos;,
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerKYC[]>>(&apos;/api/v1/seller/kyc/&apos;);
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to fetch KYC documents&apos;);
    }
  }
);

export const uploadKYCDocument = createAsyncThunk(
  &apos;seller/uploadKYCDocument&apos;,
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

      const response = await axios.post<ApiResponse<SellerKYC>>(&apos;/api/v1/seller/kyc/&apos;, formData, {
        headers: {
          &apos;Content-Type&apos;: &apos;multipart/form-data&apos;,
        },
      });
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to upload KYC document&apos;);
    }
  }
);

export const fetchBankAccounts = createAsyncThunk(
  &apos;seller/fetchBankAccounts&apos;,
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerBankAccount[]>>(&apos;/api/v1/seller/bank-accounts/&apos;);
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to fetch bank accounts&apos;);
    }
  }
);

export const addBankAccount = createAsyncThunk(
  &apos;seller/addBankAccount&apos;,
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

      const response = await axios.post<ApiResponse<SellerBankAccount>>(&apos;/api/v1/seller/bank-accounts/&apos;, formData, {
        headers: {
          &apos;Content-Type&apos;: &apos;multipart/form-data&apos;,
        },
      });
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to add bank account&apos;);
    }
  }
);

export const setPrimaryBankAccount = createAsyncThunk(
  &apos;seller/setPrimaryBankAccount&apos;,
  async (accountId: string, { rejectWithValue }) => {
    try {
      const response = await axios.post<ApiResponse<SellerBankAccount>>(`/api/v1/seller/bank-accounts/${accountId}/set_primary/`);
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to set primary bank account&apos;);
    }
  }
);

export const fetchPayoutHistory = createAsyncThunk(
  &apos;seller/fetchPayoutHistory&apos;,
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerPayout[]>>(&apos;/api/v1/seller/payouts/&apos;);
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to fetch payout history&apos;);
    }
  }
);

export const fetchSellerAnalytics = createAsyncThunk(
  &apos;seller/fetchAnalytics&apos;,
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get<ApiResponse<SellerAnalytics>>(&apos;/api/v1/seller/analytics/&apos;);
      return response.data.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.error?.message || &apos;Failed to fetch seller analytics&apos;);
    }
  }
);

// Create the slice
const sellerSlice = createSlice({
  name: &apos;seller&apos;,
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

export default sellerSlice.reducer;