import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface InventoryItem {
  productId: string;
  quantity: number;
  lastUpdated: string;
}

interface InventoryState {
  items: Record<string, InventoryItem>;
  loading: boolean;
  error: string | null;
}

interface UpdateInventoryLevelPayload {
  productId: string;
  quantity: number;
  updateType: string;
  data: unknown;
  timestamp: string;
}

  items: {},
  loading: false,
  error: null,
};

const inventorySlice = createSlice({
  name: &apos;inventory&apos;,
  initialState,
  reducers: {
    setInventoryItems: (state, action: PayloadAction<Record<string, InventoryItem>>) => {
      state.items = action.payload;
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
    updateInventoryLevel: (state, action: PayloadAction<UpdateInventoryLevelPayload>) => {
      
      if (state.items[productId]) {
        state.items[productId].quantity = quantity;
        state.items[productId].lastUpdated = timestamp;
      } else {
        state.items[productId] = {
          productId,
          quantity,
          lastUpdated: timestamp,
        };
      }
    },
    clearInventory: (state) => {
      state.items = {};
      state.loading = false;
      state.error = null;
    },
  },
});

export const {
  setInventoryItems,
  setLoading,
  setError,
  updateInventoryLevel,
  clearInventory,
} = inventorySlice.actions;

export default inventorySlice.reducer;