'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { announce } from '@/utils/accessibility';

interface AccessibilityContextType {
  highContrast: boolean;
  toggleHighContrast: () => void;
  fontSize: number;
  increaseFontSize: () => void;
  decreaseFontSize: () => void;
  resetFontSize: () => void;
  reduceMotion: boolean;
  toggleReduceMotion: () => void;
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

interface AccessibilityProviderProps {
  children: React.ReactNode;
}

const FONT_SIZE_KEY = 'ecommerce-font-size';
const HIGH_CONTRAST_KEY = 'ecommerce-high-contrast';
const REDUCE_MOTION_KEY = 'ecommerce-reduce-motion';

export function AccessibilityProvider({ children }: AccessibilityProviderProps) {
  const [highContrast, setHighContrast] = useState(false);
  const [fontSize, setFontSize] = useState(16); // Default font size in pixels
  const [reduceMotion, setReduceMotion] = useState(false);
  
  // Initialize from localStorage and system preferences
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    // Load saved preferences
    const savedFontSize = localStorage.getItem(FONT_SIZE_KEY);
    if (savedFontSize) {
      setFontSize(parseInt(savedFontSize, 10));
    }
    
    const savedHighContrast = localStorage.getItem(HIGH_CONTRAST_KEY);
    if (savedHighContrast) {
      setHighContrast(savedHighContrast === 'true');
    } else {
      // Check system preference for high contrast
      const prefersHighContrast = window.matchMedia('(prefers-contrast: more)').matches;
      setHighContrast(prefersHighContrast);
    }
    
    const savedReduceMotion = localStorage.getItem(REDUCE_MOTION_KEY);
    if (savedReduceMotion) {
      setReduceMotion(savedReduceMotion === 'true');
    } else {
      // Check system preference for reduced motion
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      setReduceMotion(prefersReducedMotion);
    }
  }, []);
  
  // Apply high contrast mode
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    if (highContrast) {
      document.documentElement.classList.add('high-contrast');
    } else {
      document.documentElement.classList.remove('high-contrast');
    }
    
    localStorage.setItem(HIGH_CONTRAST_KEY, String(highContrast));
  }, [highContrast]);
  
  // Apply font size
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    document.documentElement.style.fontSize = `${fontSize}px`;
    localStorage.setItem(FONT_SIZE_KEY, String(fontSize));
  }, [fontSize]);
  
  // Apply reduced motion
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    if (reduceMotion) {
      document.documentElement.classList.add('reduce-motion');
    } else {
      document.documentElement.classList.remove('reduce-motion');
    }
    
    localStorage.setItem(REDUCE_MOTION_KEY, String(reduceMotion));
  }, [reduceMotion]);
  
  const toggleHighContrast = () => {
    setHighContrast((prev) => !prev);
  };
  
  const increaseFontSize = () => {
    setFontSize((prev) => Math.min(prev + 1, 24)); // Max font size: 24px
  };
  
  const decreaseFontSize = () => {
    setFontSize((prev) => Math.max(prev - 1, 12)); // Min font size: 12px
  };
  
  const resetFontSize = () => {
    setFontSize(16); // Reset to default
  };
  
  const toggleReduceMotion = () => {
    setReduceMotion((prev) => !prev);
  };
  
  const value = {
    highContrast,
    toggleHighContrast,
    fontSize,
    increaseFontSize,
    decreaseFontSize,
    resetFontSize,
    reduceMotion,
    toggleReduceMotion,
    announce,
  };
  
  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  
  return context;
}