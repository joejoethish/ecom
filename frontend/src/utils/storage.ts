// Local storage utility functions

import { STORAGE_KEYS } from '@/constants';
import { AuthTokens, User } from '@/types';

// Token management
export const getStoredTokens = (): AuthTokens | null => {
  if (typeof window === 'undefined') return null;
  
  try {
    const access = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    const refresh = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    
    if (access && refresh) {
      return { access, refresh };
    }
  } catch (error) {
    console.error('Error getting stored tokens:', error);
  }
  
  return null;
};

export const setStoredTokens = (tokens: AuthTokens): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh);
  } catch (error) {
    console.error('Error storing tokens:', error);
  }
};

export const removeStoredTokens = (): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  } catch (error) {
    console.error('Error removing tokens:', error);
  }
};

// User management
export const getStoredUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  
  try {
    const userStr = localStorage.getItem(STORAGE_KEYS.USER);
    return userStr ? JSON.parse(userStr) : null;
  } catch (error) {
    console.error('Error getting stored user:', error);
    return null;
  }
};

export const setStoredUser = (user: User): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
  } catch (error) {
    console.error('Error storing user:', error);
  }
};

export const removeStoredUser = (): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(STORAGE_KEYS.USER);
  } catch (error) {
    console.error('Error removing user:', error);
  }
};

// Generic storage functions
export const getStoredItem = <T>(key: string): T | null => {
  if (typeof window === 'undefined') return null;
  
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (error) {
    console.error(`Error getting stored item ${key}:`, error);
    return null;
  }
};

export const setStoredItem = <T>(key: string, value: T): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error storing item ${key}:`, error);
  }
};

export const removeStoredItem = (key: string): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing item ${key}:`, error);
  }
};

// Clear all stored data
export const clearAllStoredData = (): void => {
  if (typeof window === 'undefined') return;
  
  try {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  } catch (error) {
    console.error('Error clearing stored data:', error);
  }
};