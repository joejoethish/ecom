'use client';

import { useEffect } from 'react';
import { useAppDispatch } from '@/store';
import { initializeAuth } from '@/store/slices/authSlice';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const dispatch = useAppDispatch();
  
  useEffect(() => {
    // Initialize authentication state when the app starts
    dispatch(initializeAuth());
  }, [dispatch]);
  
  return <>{children}</>;
}