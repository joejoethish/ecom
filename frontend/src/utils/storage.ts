// Local storage utility functions

import { STORAGE_KEYS } from '@/constants';
import { AuthTokens, User } from '@/types';

// Token management
  if (typeof window === &apos;undefined&apos;) return null;
  
  try {
    const access = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    const refresh = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    
    if (access && refresh) {
      return { access, refresh };
    }
  } catch (error) {
    console.error(&apos;Error getting stored tokens:&apos;, error);
  }
  
  return null;
};

  if (typeof window === &apos;undefined&apos;) return;
  
  try {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh);
  } catch (error) {
    console.error(&apos;Error storing tokens:&apos;, error);
  }
};

  if (typeof window === &apos;undefined&apos;) return;
  
  try {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  } catch (error) {
    console.error(&apos;Error removing tokens:&apos;, error);
  }
};

// User management
  if (typeof window === &apos;undefined&apos;) return null;
  
  try {
    const userStr = localStorage.getItem(STORAGE_KEYS.USER);
    return userStr ? JSON.parse(userStr) : null;
  } catch (error) {
    console.error(&apos;Error getting stored user:&apos;, error);
    return null;
  }
};

  if (typeof window === &apos;undefined&apos;) return;
  
  try {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
  } catch (error) {
    console.error(&apos;Error storing user:&apos;, error);
  }
};

  if (typeof window === &apos;undefined&apos;) return;
  
  try {
    localStorage.removeItem(STORAGE_KEYS.USER);
  } catch (error) {
    console.error(&apos;Error removing user:&apos;, error);
  }
};

// Generic storage functions
  if (typeof window === &apos;undefined&apos;) return null;
  
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (error) {
    console.error(`Error getting stored item ${key}:`, error);
    return null;
  }
};

  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error storing item ${key}:`, error);
  }
};

  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing item ${key}:`, error);
  }
};

// Clear all stored data
  if (typeof window === 'undefined') return;
  
  try {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  } catch (error) {
    console.error('Error clearing stored data:', error);
  }
};