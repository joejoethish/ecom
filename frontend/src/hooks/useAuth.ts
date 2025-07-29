// Custom hook for authentication

import { useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '@/store';
import { initializeAuth, clearError } from '@/store/slices/authSlice';

export function useAuth() {
  const dispatch = useAppDispatch();
  const authState = useAppSelector((state) => state.auth);
  
  useEffect(() => {
    // Initialize auth state when the hook is first used
    dispatch(initializeAuth());
  }, [dispatch]);
  
  const clearAuthError = () => {
    dispatch(clearError());
  };
  
  return {
    ...authState,
    clearError: clearAuthError,
    isAdmin: authState.user?.user_type === 'admin',
    isSeller: authState.user?.user_type === 'seller',
    isCustomer: authState.user?.user_type === 'customer',
  };
}