import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AccessibilityMenu } from '../AccessibilityMenu';
import { AccessibilityProvider } from '@/components/providers/AccessibilityProvider';

// Mock the accessibility utilities
jest.mock('@/utils/accessibility', () => ({
  announce: jest.fn(),
}));

// Mock the lucide-react icons
jest.mock(&apos;lucide-react&apos;, () => ({
  Eye: () => <div data-testid="eye-icon">Eye Icon</div>,
  Type: () => <div>Type Icon</div>,
  TypePlus: () => <div>TypePlus Icon</div>,
  TypeMinus: () => <div>TypeMinus Icon</div>,
  Contrast: () => <div>Contrast Icon</div>,
  RotateCcw: () => <div>RotateCcw Icon</div>,
  X: () => <div>X Icon</div>,
  Sparkles: () => <div>Sparkles Icon</div>,
}));

// Mock the useFocusTrap hook
jest.mock(&apos;@/hooks/useFocusTrap&apos;, () => ({
  useFocusTrap: jest.fn().mockImplementation(() => React.createRef()),
}));

describe(&apos;AccessibilityMenu&apos;, () => {
  beforeEach(() => {
    // Mock localStorage
    Object.defineProperty(window, &apos;localStorage&apos;, {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
      },
      writable: true,
    });
    
    // Mock matchMedia
    Object.defineProperty(window, &apos;matchMedia&apos;, {
      value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
      writable: true,
    });
  });
  
  it(&apos;renders the accessibility button&apos;, () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    expect(screen.getByTestId(&apos;eye-icon&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Accessibility options&apos;)).toBeInTheDocument();
  });
  
  it(&apos;opens the menu when the button is clicked&apos;, () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Initially, the menu should be closed
    expect(screen.queryByText(&apos;Accessibility Options&apos;)).not.toBeInTheDocument();
    
    // Click the button to open the menu
    fireEvent.click(screen.getByLabelText(&apos;Accessibility options&apos;));
    
    // The menu should now be open
    expect(screen.getByText(&apos;Accessibility Options&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Display&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Text Size&apos;)).toBeInTheDocument();
  });
  
  it(&apos;closes the menu when the close button is clicked&apos;, () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Open the menu
    fireEvent.click(screen.getByLabelText(&apos;Accessibility options&apos;));
    expect(screen.getByText(&apos;Accessibility Options&apos;)).toBeInTheDocument();
    
    // Click the close button
    fireEvent.click(screen.getByLabelText(&apos;Close accessibility menu&apos;));
    
    // The menu should now be closed
    expect(screen.queryByText(&apos;Accessibility Options&apos;)).not.toBeInTheDocument();
  });
  
  it(&apos;toggles high contrast mode&apos;, () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Open the menu
    fireEvent.click(screen.getByLabelText(&apos;Accessibility options&apos;));
    
    // Initially, high contrast should be off
    expect(screen.getByText(&apos;High Contrast&apos;).nextSibling).toHaveTextContent(&apos;Off&apos;);
    
    // Click the high contrast button
    fireEvent.click(screen.getByText(&apos;High Contrast&apos;).closest(&apos;button&apos;)!);
    
    // High contrast should now be on
    expect(screen.getByText(&apos;High Contrast&apos;).nextSibling).toHaveTextContent(&apos;On&apos;);
    
    // Click again to turn it off
    fireEvent.click(screen.getByText(&apos;High Contrast&apos;).closest(&apos;button&apos;)!);
    
    // High contrast should now be off again
    expect(screen.getByText(&apos;High Contrast&apos;).nextSibling).toHaveTextContent(&apos;Off&apos;);
  });
  
  it(&apos;toggles reduced motion&apos;, () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Open the menu
    fireEvent.click(screen.getByLabelText(&apos;Accessibility options&apos;));
    
    // Initially, reduced motion should be off
    expect(screen.getByText(&apos;Reduce Motion&apos;).nextSibling).toHaveTextContent(&apos;Off&apos;);
    
    // Click the reduced motion button
    fireEvent.click(screen.getByText(&apos;Reduce Motion&apos;).closest(&apos;button&apos;)!);
    
    // Reduced motion should now be on
    expect(screen.getByText(&apos;Reduce Motion&apos;).nextSibling).toHaveTextContent(&apos;On&apos;);
    
    // Click again to turn it off
    fireEvent.click(screen.getByText(&apos;Reduce Motion&apos;).closest(&apos;button&apos;)!);
    
    // Reduced motion should now be off again
    expect(screen.getByText(&apos;Reduce Motion&apos;).nextSibling).toHaveTextContent(&apos;Off&apos;);
  });
  
  it(&apos;has buttons to adjust font size&apos;, () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Open the menu
    fireEvent.click(screen.getByLabelText('Accessibility options'));
    
    // Check that font size buttons exist
    expect(screen.getByLabelText('Decrease font size')).toBeInTheDocument();
    expect(screen.getByLabelText('Increase font size')).toBeInTheDocument();
    expect(screen.getByLabelText('Reset font size')).toBeInTheDocument();
  });
});