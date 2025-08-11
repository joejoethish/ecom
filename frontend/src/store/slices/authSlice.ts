// Authentication Redux slice

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { AuthState, User, AuthTokens, LoginCredentials, RegisterData } from '@/types';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';
import { 
  getStoredTokens, 
  getStoredUser, 
  setStoredTokens, 
  setStoredUser, 
  removeStoredTokens, 
  removeStoredUser 
} from '@/utils/storage';

  user: null,
  tokens: null,
  isAuthenticated: false,
  loading: false,
  error: null,
};

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(API_ENDPOINTS.AUTH.LOGIN, credentials);
      
      if (response.success && response.data) {
        setStoredTokens(tokens);
        setStoredUser(user);
        return { user, tokens };
      } else {
        return rejectWithValue(response.error?.message || &apos;Login failed&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Login failed&apos;);
    }
  }
);

export const registerUser = createAsyncThunk(
  &apos;auth/register&apos;,
  async (userData: RegisterData, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(API_ENDPOINTS.AUTH.REGISTER, userData);
      
      if (response.success && response.data) {
        setStoredTokens(tokens);
        setStoredUser(user);
        return { user, tokens };
      } else {
        return rejectWithValue(response.error?.message || &apos;Registration failed&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Registration failed&apos;);
    }
  }
);

export const logoutUser = createAsyncThunk(
  &apos;auth/logout&apos;,
  async () => {
    try {
      const tokens = getStoredTokens();
      if (tokens?.refresh) {
        await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT, {
          refresh: tokens.refresh,
        });
      }
      
      removeStoredTokens();
      removeStoredUser();
      return null;
    } catch (error: unknown) {
      // Even if logout API fails, clear local storage
      removeStoredTokens();
      removeStoredUser();
      return null;
    }
  }
);

export const fetchUserProfile = createAsyncThunk(
  &apos;auth/fetchProfile&apos;,
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(API_ENDPOINTS.AUTH.PROFILE);
      
      if (response.success && response.data) {
        const user = response.data.user;
        setStoredUser(user);
        return user;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to fetch profile&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to fetch profile&apos;);
    }
  }
);

export const updateUserProfile = createAsyncThunk(
  &apos;auth/updateProfile&apos;,
  async (userData: Partial<User>, { rejectWithValue }) => {
    try {
      const response = await apiClient.put(API_ENDPOINTS.AUTH.PROFILE, userData);
      
      if (response.success && response.data) {
        const user = response.data.user;
        setStoredUser(user);
        return user;
      } else {
        return rejectWithValue(response.error?.message || &apos;Failed to update profile&apos;);
      }
    } catch (error: unknown) {
      return rejectWithValue(error.message || &apos;Failed to update profile&apos;);
    }
  }
);

export const initializeAuth = createAsyncThunk(
  &apos;auth/initialize&apos;,
  async (_, { dispatch }) => {
    const tokens = getStoredTokens();
    const user = getStoredUser();
    
    if (tokens && user) {
      // Verify token is still valid by fetching profile
      try {
        await dispatch(fetchUserProfile()).unwrap();
        return { user, tokens };
      } catch (error) {
        // Token is invalid, clear storage
        removeStoredTokens();
        removeStoredUser();
        return null;
      }
    }
    
    return null;
  }
);

const authSlice = createSlice({
  name: &apos;auth&apos;,
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setTokens: (state, action: PayloadAction<AuthTokens>) => {
      state.tokens = action.payload;
      setStoredTokens(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      })
      
      // Register
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      })
      
      // Logout
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.tokens = null;
        state.isAuthenticated = false;
        state.loading = false;
        state.error = null;
      })
      
      // Fetch Profile
      .addCase(fetchUserProfile.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.error = null;
      })
      .addCase(fetchUserProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Update Profile
      .addCase(updateUserProfile.pending, (state) => {
        state.loading = true;
      })
      .addCase(updateUserProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.error = null;
      })
      .addCase(updateUserProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Initialize Auth
      .addCase(initializeAuth.fulfilled, (state, action) => {
        if (action.payload) {
          state.user = action.payload.user;
          state.tokens = action.payload.tokens;
          state.isAuthenticated = true;
        }
        state.loading = false;
      });
  },
});

export default authSlice.reducer;