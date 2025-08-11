import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  ShippingState,
  DeliverySlot,
  Shipment,
  ShippingRateCalculation,
  ShippingRateResult,
  DeliverySlotAvailability,
  ServiceabilityCheck,
  ShippingAddress
} from '../../types/shipping';
import { shippingApi } from '../../services/shippingApi';

  partners: [],
  serviceableAreas: [],
  deliverySlots: [],
  shipments: [],
  currentShipment: null,
  shippingRates: [],
  selectedDeliverySlot: null,
  selectedShippingAddress: null,
  loading: false,
  error: null,
};

// Async thunks
export const fetchShippingPartners = createAsyncThunk(
  'shipping/fetchPartners',
  async (_, { rejectWithValue }) => {
    try {
      const response = await shippingApi.getShippingPartners();
      return response.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.message || &apos;Failed to fetch shipping partners&apos;);
    }
  }
);

export const checkServiceability = createAsyncThunk(
  &apos;shipping/checkServiceability&apos;,
  async (data: ServiceabilityCheck, { rejectWithValue }) => {
    try {
      const response = await shippingApi.checkServiceability(data.pin_code);
      return response.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.message || &apos;Failed to check serviceability&apos;);
    }
  }
);

export const fetchAvailableDeliverySlots = createAsyncThunk(
  &apos;shipping/fetchAvailableSlots&apos;,
  async (data: DeliverySlotAvailability, { rejectWithValue }) => {
    try {
      const response = await shippingApi.getAvailableDeliverySlots(data);
      return response.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.message || &apos;Failed to fetch delivery slots&apos;);
    }
  }
);

export const calculateShippingRates = createAsyncThunk(
  &apos;shipping/calculateRates&apos;,
  async (data: ShippingRateCalculation, { rejectWithValue }) => {
    try {
      const response = await shippingApi.calculateShippingRates(data);
      return response.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.message || &apos;Failed to calculate shipping rates&apos;);
    }
  }
);

export const trackShipment = createAsyncThunk(
  &apos;shipping/trackShipment&apos;,
  async (trackingNumber: string, { rejectWithValue }) => {
    try {
      const response = await shippingApi.trackShipment(trackingNumber);
      return response.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.message || &apos;Failed to track shipment&apos;);
    }
  }
);

export const fetchUserShipments = createAsyncThunk(
  &apos;shipping/fetchUserShipments&apos;,
  async (_, { rejectWithValue }) => {
    try {
      const response = await shippingApi.getUserShipments();
      return response.data;
    } catch (error: unknown) {
      return rejectWithValue(error.response?.data?.message || &apos;Failed to fetch shipments&apos;);
    }
  }
);

const shippingSlice = createSlice({
  name: &apos;shipping&apos;,
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setSelectedDeliverySlot: (state, action: PayloadAction<DeliverySlot | null>) => {
      state.selectedDeliverySlot = action.payload;
    },
    setSelectedShippingAddress: (state, action: PayloadAction<ShippingAddress | null>) => {
      state.selectedShippingAddress = action.payload;
    },
    clearShippingRates: (state) => {
      state.shippingRates = [];
    },
    clearDeliverySlots: (state) => {
      state.deliverySlots = [];
    },
    setCurrentShipment: (state, action: PayloadAction<Shipment | null>) => {
      state.currentShipment = action.payload;
    },
    resetShippingState: (state) => {
      state.selectedDeliverySlot = null;
      state.selectedShippingAddress = null;
      state.shippingRates = [];
      state.deliverySlots = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch shipping partners
      .addCase(fetchShippingPartners.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchShippingPartners.fulfilled, (state, action) => {
        state.loading = false;
        state.partners = action.payload || [];
      })
      .addCase(fetchShippingPartners.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

      // Check serviceability
      .addCase(checkServiceability.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(checkServiceability.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload && action.payload.serviceable && action.payload.areas) {
          state.serviceableAreas = action.payload.areas;
        }
      })
      .addCase(checkServiceability.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.serviceableAreas = [];
      })

      // Fetch available delivery slots
      .addCase(fetchAvailableDeliverySlots.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAvailableDeliverySlots.fulfilled, (state, action) => {
        state.loading = false;
        state.deliverySlots = action.payload || [];
      })
      .addCase(fetchAvailableDeliverySlots.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.deliverySlots = [];
      })

      // Calculate shipping rates
      .addCase(calculateShippingRates.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(calculateShippingRates.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload) {
          state.shippingRates = Array.isArray(action.payload) ? action.payload : [action.payload];
        } else {
          state.shippingRates = [];
        }
      })
      .addCase(calculateShippingRates.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.shippingRates = [];
      })

      // Track shipment
      .addCase(trackShipment.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(trackShipment.fulfilled, (state, action) => {
        state.loading = false;
        state.currentShipment = action.payload?.shipment || null;
      })
      .addCase(trackShipment.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.currentShipment = null;
      })

      // Fetch user shipments
      .addCase(fetchUserShipments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUserShipments.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload) {
          // Handle both PaginatedResponse<Shipment> and Shipment[] types
          if (Array.isArray(action.payload)) {
            state.shipments = action.payload;
          } else if (action.payload.results) {
            state.shipments = action.payload.results;
          } else {
            state.shipments = [];
          }
        } else {
          state.shipments = [];
        }
      })
      .addCase(fetchUserShipments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  clearError,
  setSelectedDeliverySlot,
  setSelectedShippingAddress,
  clearShippingRates,
  clearDeliverySlots,
  setCurrentShipment,
  resetShippingState,
} = shippingSlice.actions;

export default shippingSlice.reducer;