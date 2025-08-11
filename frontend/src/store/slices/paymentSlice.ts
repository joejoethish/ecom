// Payment Redux slice

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { 
  Payment, 
  PaymentMethod, 
  Currency, 
  WalletDetails, 
  GiftCard, 
  PaymentFormData,
  PaymentVerificationData,
  PaymentResponse,
  CurrencyConversion
} from '../../types';
import { apiClient } from '../../utils/api';
import { API_ENDPOINTS } from '../../constants';



interface PaymentState {
  paymentMethods: PaymentMethod[];
  currencies: Currency[];
  selectedCurrency: string;
  selectedPaymentMethod: string | null;
  currentPayment: Payment | null;
  wallet: WalletDetails | null;
  giftCard: GiftCard | null;
  loading: boolean;
  error: string | null;
  paymentProcessing: boolean;
  paymentSuccess: boolean;
  paymentError: string | null;
  currencyConversion: CurrencyConversion | null;
}

const initialState: PaymentState = {
  paymentMethods: [],
  currencies: [],
  selectedCurrency: 'USD', // Default currency
  selectedPaymentMethod: null,
  currentPayment: null,
  wallet: null,
  giftCard: null,
  loading: false,
  error: null,
  paymentProcessing: false,
  paymentSuccess: false,
  paymentError: null,
  currencyConversion: null,
};

// Async thunks
export const fetchPaymentMethods = createAsyncThunk(
  'payments/fetchPaymentMethods',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<PaymentMethod[]>(API_ENDPOINTS.PAYMENTS.METHODS);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to fetch payment methods');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch payment methods');
    }
  }
);

export const fetchCurrencies = createAsyncThunk(
  'payments/fetchCurrencies',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<Currency[]>(API_ENDPOINTS.PAYMENTS.CURRENCIES);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to fetch currencies');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch currencies');
    }
  }
);

export const createPayment = createAsyncThunk(
  'payments/createPayment',
  async (paymentData: PaymentFormData, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<PaymentResponse>(API_ENDPOINTS.PAYMENTS.CREATE, paymentData);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to create payment');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create payment');
    }
  }
);

export const verifyPayment = createAsyncThunk(
  'payments/verifyPayment',
  async (verificationData: PaymentVerificationData, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<PaymentResponse>(API_ENDPOINTS.PAYMENTS.VERIFY, verificationData);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to verify payment');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to verify payment');
    }
  }
);

export const getPaymentStatus = createAsyncThunk(
  'payments/getPaymentStatus',
  async (paymentId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<PaymentResponse>(API_ENDPOINTS.PAYMENTS.STATUS(paymentId));
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to get payment status');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to get payment status');
    }
  }
);

export const getWalletDetails = createAsyncThunk(
  'payments/getWalletDetails',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<WalletDetails>(API_ENDPOINTS.PAYMENTS.WALLET);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to get wallet details');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to get wallet details');
    }
  }
);

export const validateGiftCard = createAsyncThunk(
  'payments/validateGiftCard',
  async (code: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<GiftCard>(API_ENDPOINTS.PAYMENTS.GIFT_CARD.VALIDATE, { code });
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Invalid gift card');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to validate gift card');
    }
  }
);

export const convertCurrency = createAsyncThunk(
  'payments/convertCurrency',
  async (data: { from_currency: string; to_currency: string; amount: number }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<CurrencyConversion>(API_ENDPOINTS.PAYMENTS.CONVERT_CURRENCY, data);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || 'Failed to convert currency');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to convert currency');
    }
  }
);

const paymentSlice = createSlice({
  name: 'payments',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
      state.paymentError = null;
    },
    resetPaymentState: (state) => {
      state.paymentProcessing = false;
      state.paymentSuccess = false;
      state.paymentError = null;
      state.currentPayment = null;
    },
    setSelectedCurrency: (state, action: PayloadAction<string>) => {
      state.selectedCurrency = action.payload;
    },
    setSelectedPaymentMethod: (state, action: PayloadAction<string | null>) => {
      state.selectedPaymentMethod = action.payload;
    },
    clearGiftCard: (state) => {
      state.giftCard = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Payment Methods
      .addCase(fetchPaymentMethods.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPaymentMethods.fulfilled, (state, action) => {
        state.loading = false;
        state.paymentMethods = action.payload;
        
        // Set default payment method if none selected
        if (!state.selectedPaymentMethod && action.payload.length > 0) {
          state.selectedPaymentMethod = action.payload[0].id;
        }
        
        state.error = null;
      })
      .addCase(fetchPaymentMethods.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Fetch Currencies
      .addCase(fetchCurrencies.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCurrencies.fulfilled, (state, action) => {
        state.loading = false;
        state.currencies = action.payload;
        state.error = null;
      })
      .addCase(fetchCurrencies.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Create Payment
      .addCase(createPayment.pending, (state) => {
        state.paymentProcessing = true;
        state.paymentSuccess = false;
        state.paymentError = null;
      })
      .addCase(createPayment.fulfilled, (state, action) => {
        state.paymentProcessing = false;
        state.paymentSuccess = true;
        state.currentPayment = {
          id: action.payload.payment_id,
          status: action.payload.status,
          amount: action.payload.amount,
          currency: action.payload.currency,
          payment_method: state.paymentMethods.find(m => m.method_type === action.payload.payment_method) || {
            id: '',
            name: action.payload.payment_method,
            method_type: action.payload.payment_method,
            gateway: 'INTERNAL',
            processing_fee_percentage: 0,
            processing_fee_fixed: 0,
            is_active: true
          },
          order_id: '',
          processing_fee: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        state.paymentError = null;
      })
      .addCase(createPayment.rejected, (state, action) => {
        state.paymentProcessing = false;
        state.paymentSuccess = false;
        state.paymentError = action.payload as string;
      })
      
      // Verify Payment
      .addCase(verifyPayment.pending, (state) => {
        state.paymentProcessing = true;
        state.paymentError = null;
      })
      .addCase(verifyPayment.fulfilled, (state, action) => {
        state.paymentProcessing = false;
        state.paymentSuccess = action.payload.status === 'COMPLETED';
        
        if (state.currentPayment) {
          state.currentPayment.status = action.payload.status;
        }
        
        state.paymentError = null;
      })
      .addCase(verifyPayment.rejected, (state, action) => {
        state.paymentProcessing = false;
        state.paymentSuccess = false;
        state.paymentError = action.payload as string;
      })
      
      // Get Payment Status
      .addCase(getPaymentStatus.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getPaymentStatus.fulfilled, (state, action) => {
        state.loading = false;
        
        if (state.currentPayment) {
          state.currentPayment.status = action.payload.status;
        }
        
        state.paymentSuccess = action.payload.status === 'COMPLETED';
        state.error = null;
      })
      .addCase(getPaymentStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Get Wallet Details
      .addCase(getWalletDetails.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getWalletDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.wallet = action.payload;
        state.error = null;
      })
      .addCase(getWalletDetails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Validate Gift Card
      .addCase(validateGiftCard.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(validateGiftCard.fulfilled, (state, action) => {
        state.loading = false;
        state.giftCard = action.payload;
        state.error = null;
      })
      .addCase(validateGiftCard.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.giftCard = null;
      })
      
      // Convert Currency
      .addCase(convertCurrency.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(convertCurrency.fulfilled, (state, action) => {
        state.loading = false;
        state.currencyConversion = action.payload;
        state.error = null;
      })
      .addCase(convertCurrency.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { 
  clearError, 
  resetPaymentState, 
  setSelectedCurrency, 
  setSelectedPaymentMethod,
  clearGiftCard
} = paymentSlice.actions;
export default paymentSlice.reducer;