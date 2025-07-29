/**
 * Accessibility utilities
 */

/**
 * Creates props for screen reader only elements
 * @returns CSS properties to visually hide an element while keeping it accessible to screen readers
 */
export function srOnly() {
  return {
    position: 'absolute',
    width: '1px',
    height: '1px',
    padding: '0',
    margin: '-1px',
    overflow: 'hidden',
    clip: 'rect(0, 0, 0, 0)',
    whiteSpace: 'nowrap',
    borderWidth: '0',
  } as const;
}

/**
 * Generates an ARIA label for a button that only has an icon
 * @param action - The action the button performs
 * @returns The ARIA label
 */
export function iconButtonLabel(action: string): string {
  return action;
}

/**
 * Checks if the current environment is using keyboard navigation
 * @returns A function to check if keyboard navigation is active
 */
export function useKeyboardNavigation(): () => boolean {
  if (typeof window === 'undefined') {
    return () => false;
  }
  
  // Add a class to the body when the user is navigating with the keyboard
  const handleFirstTab = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      document.body.classList.add('user-is-tabbing');
      
      window.removeEventListener('keydown', handleFirstTab);
      window.addEventListener('mousedown', handleMouseDown);
    }
  };
  
  const handleMouseDown = () => {
    document.body.classList.remove('user-is-tabbing');
    
    window.removeEventListener('mousedown', handleMouseDown);
    window.addEventListener('keydown', handleFirstTab);
  };
  
  // Set up the listeners
  if (typeof window !== 'undefined' && 
      !document.body.classList.contains('accessibility-listeners-initialized')) {
    window.addEventListener('keydown', handleFirstTab);
    document.body.classList.add('accessibility-listeners-initialized');
  }
  
  return () => document.body.classList.contains('user-is-tabbing');
}

/**
 * Announces a message to screen readers using an ARIA live region
 * @param message - The message to announce
 * @param priority - The priority of the announcement (polite or assertive)
 */
export function announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  if (typeof window === 'undefined') {
    return;
  }
  
  // Create or get the live region element
  let liveRegion = document.getElementById(`accessibility-announce-${priority}`);
  
  if (!liveRegion) {
    liveRegion = document.createElement('div');
    liveRegion.id = `accessibility-announce-${priority}`;
    liveRegion.setAttribute('aria-live', priority);
    liveRegion.setAttribute('aria-relevant', 'additions');
    liveRegion.setAttribute('aria-atomic', 'true');
    
    // Hide it visually
    Object.entries(srOnly()).forEach(([key, value]) => {
      liveRegion!.style[key as any] = value;
    });
    
    document.body.appendChild(liveRegion);
  }
  
  // Update the content to trigger the announcement
  liveRegion.textContent = message;
}