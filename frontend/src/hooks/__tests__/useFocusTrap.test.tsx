import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { useFocusTrap } from '../useFocusTrap';

// Test component that uses the useFocusTrap hook
function TestComponent({ active = true }: { active?: boolean }) {
  const containerRef = useFocusTrap(active);
  
  return (
    <div ref={containerRef} data-testid="container" tabIndex={-1}>
      <button data-testid="button-1">Button 1</button>
      <button data-testid="button-2">Button 2</button>
      <button data-testid="button-3">Button 3</button>
    </div>
  );
}

describe('useFocusTrap', () => {
  beforeEach(() => {
    // Mock document.activeElement
    Object.defineProperty(document, 'activeElement', {
      writable: true,
      value: document.body,
    });
  });
  
  it('focuses the first focusable element when activated', () => {
    render(<TestComponent />);
    
    const button1 = screen.getByTestId('button-1');
    expect(document.activeElement).toBe(button1);
  });
  
  it('does not trap focus when inactive', () => {
    render(<TestComponent active={false} />);
    
    // Should not focus any element
    expect(document.activeElement).not.toBe(screen.getByTestId('button-1'));
  });
  
  it('traps focus within the container using Tab key', () => {
    render(<TestComponent />);
    
    const button1 = screen.getByTestId('button-1');
    const button2 = screen.getByTestId('button-2');
    const button3 = screen.getByTestId('button-3');
    
    // Initial focus should be on the first button
    expect(document.activeElement).toBe(button1);
    
    // Tab should move to the next button
    fireEvent.keyDown(button1, { key: 'Tab' });
    expect(document.activeElement).toBe(button2);
    
    // Tab again should move to the last button
    fireEvent.keyDown(button2, { key: 'Tab' });
    expect(document.activeElement).toBe(button3);
    
    // Tab from the last button should cycle back to the first
    fireEvent.keyDown(button3, { key: 'Tab' });
    expect(document.activeElement).toBe(button1);
  });
  
  it('handles Shift+Tab to move focus backwards', () => {
    render(<TestComponent />);
    
    const button1 = screen.getByTestId('button-1');
    const button3 = screen.getByTestId('button-3');
    
    // Initial focus should be on the first button
    expect(document.activeElement).toBe(button1);
    
    // Shift+Tab from the first button should cycle to the last
    fireEvent.keyDown(button1, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(button3);
  });
  
  it('focuses the initial element specified by ref', () => {
    // Component with initialFocusRef
    function TestComponentWithInitialFocus() {
      const initialRef = React.useRef<HTMLButtonElement>(null);
      const containerRef = useFocusTrap(true, initialRef as React.RefObject<HTMLElement>);
      
      return (
        <div ref={containerRef} data-testid="container" tabIndex={-1}>
          <button data-testid="button-1">Button 1</button>
          <button data-testid="button-2" ref={initialRef}>Button 2</button>
          <button data-testid="button-3">Button 3</button>
        </div>
      );
    }
    
    render(<TestComponentWithInitialFocus />);
    
    // Initial focus should be on button 2
    expect(document.activeElement).toBe(screen.getByTestId('button-2'));
  });
  
  it('ignores non-Tab key events', () => {
    render(<TestComponent />);
    
    const button1 = screen.getByTestId('button-1');
    
    // Initial focus should be on the first button
    expect(document.activeElement).toBe(button1);
    
    // Other keys should not affect focus
    fireEvent.keyDown(button1, { key: 'Enter' });
    expect(document.activeElement).toBe(button1);
    
    fireEvent.keyDown(button1, { key: 'Escape' });
    expect(document.activeElement).toBe(button1);
  });
});