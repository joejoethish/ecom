'use client';

import { useState, useEffect } from 'react';

/**
 * Custom hook for responsive design based on media queries
 * @param query - CSS media query string
 * @returns Boolean indicating if the media query matches
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);
  
  useEffect(() => {
    // Check if window is defined (for SSR)
    if (typeof window === 'undefined') {
      return;
    }
    
    // Create media query list
    const mediaQuery = window.matchMedia(query);
    
    // Set initial value
    setMatches(mediaQuery.matches);
    
    // Define listener function
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };
    
    // Add listener
    mediaQuery.addEventListener('change', handleChange);
    
    // Cleanup
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [query]);
  
  return matches;
}

/**
 * Predefined breakpoints for common screen sizes
 */
export const breakpoints = {
  sm: '(min-width: 640px)',
  md: '(min-width: 768px)',
  lg: '(min-width: 1024px)',
  xl: '(min-width: 1280px)',
  '2xl': '(min-width: 1536px)',
} as const;

/**
 * Custom hooks for common breakpoints
 */
export function useIsMobile(): boolean {
  return !useMediaQuery(breakpoints.md);
}

export function useIsTablet(): boolean {
  return useMediaQuery(breakpoints.md) && !useMediaQuery(breakpoints.lg);
}

export function useIsDesktop(): boolean {
  return useMediaQuery(breakpoints.lg);
}

export function useIsLargeDesktop(): boolean {
  return useMediaQuery(breakpoints.xl);
}