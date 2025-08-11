import { configureStore, ThunkAction, Action } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

// Import reducers
import authReducer from './slices/authSlice';
import cartReducer from './slices/cartSlice';
import productReducer from './slices/productSlice';
import orderReducer from './slices/orderSlice';
import notificationReducer from './slices/notificationSlice';
import inventoryReducer from './slices/inventorySlice';
import chatReducer from './slices/chatSlice';
import paymentReducer from './slices/paymentSlice';
import shippingReducer from './slices/shippingSlice';
import sellerReducer from './slices/sellerSlice';
import wishlistReducer from './slices/wishlistSlice';
import customerReducer from './slices/customerSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    cart: cartReducer,
    products: productReducer,
    orders: orderReducer,
    notifications: notificationReducer,
    inventory: inventoryReducer,
    chat: chatReducer,
    payments: paymentReducer,
    shipping: shippingReducer,
    seller: sellerReducer,
    wishlist: wishlistReducer,
    customer: customerReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: [&apos;auth/setUser&apos;, &apos;auth/setToken&apos;],
        // Ignore these field paths in all actions
        ignoredActionPaths: [&apos;payload.data&apos;],
        // Ignore these paths in the state
        ignoredPaths: [&apos;auth.user&apos;, &apos;auth.token&apos;],
      },
    }),
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Define reusable AppThunk type for async actions
export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  RootState,
  unknown,
  Action<string>
>;

// Use throughout your app instead of plain `useDispatch` and `useSelector`