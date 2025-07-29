import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AccessibilityMenu } from '../AccessibilityMenu';
import { AccessibilityProvider } from '@/components/providers/AccessibilityProvider';

// Mock the accessibility utilities
jest.mock('@/utils/accessibility', () => ({
  announce: jest.fn(),
}));

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
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
jest.mock('@/hooks/useFocusTrap', () => ({
  useFocusTrap: jest.fn().mockImplementation(() => React.createRef()),
}));

describe('AccessibilityMenu', () => {
  beforeEach(() => {
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
      },
      writable: true,
    });
    
    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
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
  
  it('renders the accessibility button', () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    expect(screen.getByTestId('eye-icon')).toBeInTheDocument();
    expect(screen.getByLabelText('Accessibility options')).toBeInTheDocument();
  });
  
  it('opens the menu when the button is clicked', () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Initially, the menu should be closed
    expect(screen.queryByText('Accessibility Options')).not.toBeInTheDocument();
    
    // Click the button to open the menu
    fireEvent.click(screen.getByLabelText('Accessibility options'));
    
    // The menu should now be open
    expect(screen.getByText('Accessibility Options')).toBeInTheDocument();
    expect(screen.getByText('Display')).toBeInTheDocument();
    expect(screen.getByText('Text Size')).toBeInTheDocument();
  });
  
  it('closes the menu when the close button is clicked', () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Open the menu
    fireEvent.click(screen.getByLabelText('Accessibility options'));
    expect(screen.getByText('Accessibility Options')).toBeInTheDocument();
    
    // Click the close button
    fireEvent.click(screen.getByLabelText('Close accessibility menu'));
    
    // The menu should now be closed
    expect(screen.queryByText('Accessibility Options')).not.toBeInTheDocument();
  });
  
  it('toggles high contrast mode', () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Open the menu
    fireEvent.click(screen.getByLabelText('Accessibility options'));
    
    // Initially, high contrast should be off
    expect(screen.getByText('High Contrast').nextSibling).toHaveTextContent('Off');
    
    // Click the high contrast button
    fireEvent.click(screen.getByText('High Contrast').closest('button')!);
    
    // High contrast should now be on
    expect(screen.getByText('High Contrast').nextSibling).toHaveTextContent('On');
    
    // Click again to turn it off
    fireEvent.click(screen.getByText('High Contrast').closest('button')!);
    
    // High contrast should now be off again
    expect(screen.getByText('High Contrast').nextSibling).toHaveTextContent('Off');
  });
  
  it('toggles reduced motion', () => {
    render(
      <AccessibilityProvider>
        <AccessibilityMenu />
      </AccessibilityProvider>
    );
    
    // Open the menu
    fireEvent.click(screen.getByLabelText('Accessibility options'));
    
    // Initially, reduced motion should be off
    expect(screen.getByText('Reduce Motion').nextSibling).toHaveTextContent('Off');
    
    // Click the reduced motion button
    fireEvent.click(screen.getByText('Reduce Motion').closest('button')!);
    
    // Reduced motion should now be on
    expect(screen.getByText('Reduce Motion').nextSibling).toHaveTextContent('On');
    
    // Click again to turn it off
    fireEvent.click(screen.getByText('Reduce Motion').closest('button')!);
    
    // Reduced motion should now be off again
    expect(screen.getByText('Reduce Motion').nextSibling).toHaveTextContent('Off');
  });
  
  it('has buttons to adjust font size', () => {
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