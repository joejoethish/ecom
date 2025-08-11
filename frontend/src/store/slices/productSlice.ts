// Product Redux slice

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Product, Category, PaginatedResponse } from '@/types';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';

interface ProductState {
  products: Product[];
  categories: Category[];
  currentProduct: Product | null;
  loading: boolean;
  error: string | null;
  pagination: {
    count: number;
    next: string | null;
    previous: string | null;
    page_size: number;
    total_pages: number;
    current_page: number;
  } | null;
  filters: {
    category?: string;
    search?: string;
    min_price?: number;
    max_price?: number;
    brand?: string;
    sort?: string;
  };
}

  products: [],
  categories: [],
  currentProduct: null,
  loading: false,
  error: null,
  pagination: null,
  filters: {},
};

// Async thunks
export const fetchProducts = createAsyncThunk(
  'products/fetchProducts',
  async (params: { page?: number; filters?: any } = {}, { rejectWithValue }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) {
        queryParams.append(&apos;page&apos;, params.page.toString());
      }
      
      if (params.filters) {
        Object.entries(params.filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== &apos;&apos;) {
            queryParams.append(key, value.toString());
          }
        });
      }
      
      const url = `${API_ENDPOINTS.PRODUCTS.LIST}?${queryParams.toString()}`;
      const response = await apiClient.get<PaginatedResponse<Product>>(url);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to fetch products&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to fetch products&apos;);
    }
  }
);

export const fetchProductById = createAsyncThunk(
  &apos;products/fetchProductById&apos;,
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<Product>(API_ENDPOINTS.PRODUCTS.DETAIL(id));
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to fetch product&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to fetch product&apos;);
    }
  }
);

export const fetchCategories = createAsyncThunk(
  &apos;products/fetchCategories&apos;,
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<Category[]>(API_ENDPOINTS.PRODUCTS.CATEGORIES);
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to fetch categories&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to fetch categories&apos;);
    }
  }
);

export const searchProducts = createAsyncThunk(
  &apos;products/searchProducts&apos;,
  async (searchQuery: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<PaginatedResponse<Product>>(
        `${API_ENDPOINTS.PRODUCTS.LIST}?search=${encodeURIComponent(searchQuery)}`
      );
      
      if (response.success && response.data) {
        return response.data;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to search products&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to search products&apos;);
    }
  }
);

const productSlice = createSlice({
  name: &apos;products&apos;,
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setFilters: (state, action: PayloadAction<Partial<ProductState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setCurrentProduct: (state, action: PayloadAction<Product | null>) => {
      state.currentProduct = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Products
      .addCase(fetchProducts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.loading = false;
        state.products = action.payload.results;
        state.pagination = action.payload.pagination;
        state.error = null;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Fetch Product by ID
      .addCase(fetchProductById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProductById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentProduct = action.payload;
        state.error = null;
      })
      .addCase(fetchProductById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Fetch Categories
      .addCase(fetchCategories.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchCategories.fulfilled, (state, action) => {
        state.loading = false;
        state.categories = action.payload;
      })
      .addCase(fetchCategories.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Search Products
      .addCase(searchProducts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchProducts.fulfilled, (state, action) => {
        state.loading = false;
        state.products = action.payload.results;
        state.pagination = action.payload.pagination;
        state.error = null;
      })
      .addCase(searchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export default productSlice.reducer;