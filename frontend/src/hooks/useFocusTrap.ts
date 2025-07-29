'use client';

import { useRef, useEffect } from 'react';

/**
 * Hook to trap focus within a container (for modals, dialogs, etc.)
 * @param active - Whether the focus trap is active
 * @param initialFocusRef - Optional ref to the element that should receive initial focus
 * @returns Ref to attach to the container element
 */
export function useFocusTrap(active: boolean = true, initialFocusRef?: React.RefObject<HTMLElement>) {
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!active) return;
    
    const container = containerRef.current;
    if (!container) return;
    
    // Save the element that had focus before the trap was activated
    const previouslyFocused = document.activeElement as HTMLElement;
    
    // Focus the initial element or the first focusable element
    const setInitialFocus = () => {
      if (initialFocusRef?.current) {
        initialFocusRef.current.focus();
      } else {
        const focusableElements = getFocusableElements(container);
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        } else {
          container.focus();
        }
      }
    };
    
    // Set initial focus
    setInitialFocus();
    
    // Handle tab key to keep focus within the container
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      
      const focusableElements = getFocusableElements(container);
      if (focusableElements.length === 0) return;
      
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };
    
    // Add event listener
    container.addEventListener('keydown', handleKeyDown);
    
    // Cleanup function
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      
      // Restore focus when the trap is deactivated
      if (previouslyFocused && 'focus' in previouslyFocused) {
        previouslyFocused.focus();
      }
    };
  }, [active, initialFocusRef]);
  
  return containerRef;
}

/**
 * Gets all focusable elements within a container
 * @param container - The container element
 * @returns Array of focusable elements
 */
function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const selector = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable]'
  ].join(',');
  
  return Array.from(container.querySelectorAll(selector)) as HTMLElement[];
}