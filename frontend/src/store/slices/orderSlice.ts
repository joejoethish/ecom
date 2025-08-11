import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Order, ReturnRequestFormData, OrderTracking } from '@/types';
import { RootState } from '@/store';
import { ROUTES, ORDER_STATUS } from '@/constants';

export interface OrderTrackingEvent {
  status: string;
  message: string;
  location?: string;
  timestamp: string;
}

interface OrderState {
  orders: Order[];
  currentOrder: Order | null;
  loading: boolean;
  error: string | null;
  pagination?: {
    count: number;
    next: string | null;
    previous: string | null;
    page_size: number;
    total_pages: number;
    current_page: number;
  };
  returnRequestLoading?: boolean;
  returnRequestError?: string | null;
}

interface UpdateOrderStatusPayload {
  orderId: string;
  status: string;
  message: string;
  trackingData: unknown;
  timestamp: string;
}

  orders: [],
  currentOrder: null,
  loading: false,
  error: null,
  pagination: {
    count: 0,
    next: null,
    previous: null,
    page_size: 10,
    total_pages: 0,
    current_page: 1,
  },
  returnRequestLoading: false,
  returnRequestError: null,
};

const orderSlice = createSlice({
  name: 'orders',
  initialState,
  reducers: {
    setOrders: (state, action: PayloadAction<Order[]>) => {
      state.orders = action.payload;
      state.loading = false;
      state.error = null;
    },
    setCurrentOrder: (state, action: PayloadAction<Order>) => {
      state.currentOrder = action.payload;
      state.loading = false;
      state.error = null;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.loading = false;
    },
    updateOrderStatus: (state, action: PayloadAction<UpdateOrderStatusPayload>) => {
      
      // Update in orders list
      const orderIndex = state.orders.findIndex((order) => order.id === orderId);
      if (orderIndex !== -1) {
        state.orders[orderIndex].status = status as any;
        
        // Add tracking event
          id: Date.now().toString(),
          status,
          description: message,
          location: trackingData.location,
          created_at: trackingData.timestamp || timestamp,
        };
        
        if (!state.orders[orderIndex].timeline) {
          state.orders[orderIndex].timeline = [];
        }
        
        state.orders[orderIndex].timeline!.unshift(trackingEvent);
      }
      
      // Update current order if it matches
      if (state.currentOrder && state.currentOrder.id === orderId) {
        state.currentOrder.status = status as any;
        
        // Add tracking event
          id: Date.now().toString(),
          status,
          description: message,
          location: trackingData.location,
          created_at: trackingData.timestamp || timestamp,
        };
        
        if (!state.currentOrder.timeline) {
          state.currentOrder.timeline = [];
        }
        
        state.currentOrder.timeline.unshift(trackingEvent);
      }
    },
    clearOrders: (state) => {
      state.orders = [];
      state.currentOrder = null;
      state.loading = false;
      state.error = null;
    },
  },
});

export const {
  setOrders,
  setCurrentOrder,
  setLoading,
  setError,
  updateOrderStatus,
  clearOrders,
} = orderSlice.actions;

// Async thunk actions
export const fetchOrders = createAsyncThunk<Order[], number | undefined, { state: RootState }>(
  &apos;orders/fetchOrders&apos;,
  async (page: number | undefined, { dispatch }) => {
    try {
      dispatch(setLoading(true));
      // API call would go here
      // Use page parameter for pagination if provided
      dispatch(setOrders(orders));
      return orders;
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : &apos;Failed to fetch orders&apos;));
      throw error;
    }
  }
);

export const fetchOrderById = createAsyncThunk<Order, string, { state: RootState }>(
  &apos;orders/fetchOrderById&apos;,
  async (orderId: string, { dispatch }) => {
    try {
      dispatch(setLoading(true));
      // API call would go here
      // Use orderId to fetch the specific order
      dispatch(setCurrentOrder(order));
      return order;
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : &apos;Failed to fetch order&apos;));
      throw error;
    }
  }
);

interface CancelOrderResponse {
  success: boolean;
}

export const cancelOrder = createAsyncThunk<CancelOrderResponse, string, { state: RootState }>(
  &apos;orders/cancelOrder&apos;,
  async (orderId: string, { dispatch }) => {
    try {
      dispatch(setLoading(true));
      // API call would go here
      // Use orderId to cancel the specific order
      // Update order status after cancellation
      return { success: true };
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : &apos;Failed to cancel order&apos;));
      throw error;
    }
  }
);

interface CreateOrderData {
  shipping_address: unknown;
  billing_address: unknown;
  shipping_method: string;
  items: Array<{
    product_id: string;
    quantity: number;
  }>;
}

export const createOrder = createAsyncThunk<Order, CreateOrderData, { state: RootState }>(
  &apos;orders/createOrder&apos;,
  async (orderData: CreateOrderData, { dispatch }) => {
    try {
      dispatch(setLoading(true));
      // API call would go here
        id: &apos;new-order-id&apos;,
        order_number: `ORD-${Date.now()}`,
        status: ORDER_STATUS.PENDING,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        items: orderData.items.map((item) => ({
          id: `item-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          product: {
            id: item.product_id,
            name: &apos;Product Name&apos;,
            slug: &apos;product-name&apos;,
            description: &apos;Product description&apos;,
            short_description: &apos;Short description&apos;,
            category: {
              id: &apos;cat-1&apos;,
              name: &apos;Category&apos;,
              slug: &apos;category&apos;,
              is_active: true,
              created_at: new Date().toISOString(),
            },
            brand: &apos;Brand&apos;,
            sku: &apos;SKU001&apos;,
            price: 100,
            is_active: true,
            is_featured: false,
            dimensions: {},
            images: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          quantity: item.quantity,
          unit_price: 100,
          total_price: 100 * item.quantity,
          status: ORDER_STATUS.PENDING,
          can_return: false
        })),
        shipping_address: orderData.shipping_address,
        billing_address: orderData.billing_address,
        payment_method: &apos;credit_card&apos;,
        payment_status: &apos;pending&apos;,
        shipping_amount: 10,
        tax_amount: 20,
        discount_amount: 0,
        total_amount: 130,
        timeline: []
      };
      
      dispatch(setCurrentOrder(order));
      return order;
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : &apos;Failed to create order&apos;));
      throw error;
    }
  }
);

interface CreateReturnRequestResponse {
  success: boolean;
}

export const createReturnRequest = createAsyncThunk<CreateReturnRequestResponse, ReturnRequestFormData, { state: RootState }>(
  'orders/createReturnRequest',
  async (returnData: ReturnRequestFormData, { dispatch }) => {
    try {
      dispatch(setLoading(true));
      // API call would go here using returnData
      return { success: true };
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to create return request'));
      throw error;
    }
  }
);

export default orderSlice.reducer;