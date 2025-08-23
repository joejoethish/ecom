// Custom hook for authentication

import { useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '@/store';
import { 
  initializeAuth, 
  clearError, 
  loginUser, 
  registerUser, 
  logoutUser, 
  adminLogin,
  fetchUserProfile,
  updateUserProfile 
} from '@/store/slices/authSlice';
import { LoginCredentials, RegisterData } from '@/types';

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

  const login = async (credentials: LoginCredentials) => {
    const result = await dispatch(loginUser(credentials));
    return {
      success: loginUser.fulfilled.match(result),
      error: loginUser.rejected.match(result) ? result.payload as string : null,
    };
  };

  const register = async (userData: RegisterData) => {
    const result = await dispatch(registerUser(userData));
    return {
      success: registerUser.fulfilled.match(result),
      error: registerUser.rejected.match(result) ? result.payload as string : null,
    };
  };

  const logout = async () => {
    await dispatch(logoutUser());
  };

  const adminLoginHandler = async (credentials: LoginCredentials & { rememberMe?: boolean }) => {
    const result = await dispatch(adminLogin(credentials));
    return {
      success: adminLogin.fulfilled.match(result),
      error: adminLogin.rejected.match(result) ? result.payload as string : null,
    };
  };

  const refreshProfile = async () => {
    const result = await dispatch(fetchUserProfile());
    return {
      success: fetchUserProfile.fulfilled.match(result),
      error: fetchUserProfile.rejected.match(result) ? result.payload as string : null,
    };
  };

  const updateProfile = async (userData: Partial<any>) => {
    const result = await dispatch(updateUserProfile(userData));
    return {
      success: updateUserProfile.fulfilled.match(result),
      error: updateUserProfile.rejected.match(result) ? result.payload as string : null,
    };
  };
  
  return {
    ...authState,
    login,
    register,
    logout,
    adminLogin: adminLoginHandler,
    refreshProfile,
    updateProfile,
    clearError: clearAuthError,
    isAdmin: authState.user?.user_type === 'admin' || authState.user?.is_superuser === true,
    isSeller: authState.user?.user_type === 'seller',
    isCustomer: authState.user?.user_type === 'customer',
  };
}