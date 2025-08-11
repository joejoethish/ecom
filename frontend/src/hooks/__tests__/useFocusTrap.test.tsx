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

describe(&apos;useFocusTrap&apos;, () => {
  beforeEach(() => {
    // Mock document.activeElement
    Object.defineProperty(document, &apos;activeElement&apos;, {
      writable: true,
      value: document.body,
    });
  });
  
  it(&apos;focuses the first focusable element when activated&apos;, () => {
    render(<TestComponent />);
    
    const button1 = screen.getByTestId(&apos;button-1&apos;);
    expect(document.activeElement).toBe(button1);
  });
  
  it(&apos;does not trap focus when inactive&apos;, () => {
    render(<TestComponent active={false} />);
    
    // Should not focus any element
    expect(document.activeElement).not.toBe(screen.getByTestId(&apos;button-1&apos;));
  });
  
  it(&apos;traps focus within the container using Tab key&apos;, () => {
    render(<TestComponent />);
    
    const button1 = screen.getByTestId(&apos;button-1&apos;);
    const button2 = screen.getByTestId(&apos;button-2&apos;);
    const button3 = screen.getByTestId(&apos;button-3&apos;);
    
    // Initial focus should be on the first button
    expect(document.activeElement).toBe(button1);
    
    // Tab should move to the next button
    fireEvent.keyDown(button1, { key: &apos;Tab&apos; });
    expect(document.activeElement).toBe(button2);
    
    // Tab again should move to the last button
    fireEvent.keyDown(button2, { key: &apos;Tab&apos; });
    expect(document.activeElement).toBe(button3);
    
    // Tab from the last button should cycle back to the first
    fireEvent.keyDown(button3, { key: &apos;Tab&apos; });
    expect(document.activeElement).toBe(button1);
  });
  
  it(&apos;handles Shift+Tab to move focus backwards&apos;, () => {
    render(<TestComponent />);
    
    const button1 = screen.getByTestId(&apos;button-1&apos;);
    const button3 = screen.getByTestId(&apos;button-3&apos;);
    
    // Initial focus should be on the first button
    expect(document.activeElement).toBe(button1);
    
    // Shift+Tab from the first button should cycle to the last
    fireEvent.keyDown(button1, { key: &apos;Tab&apos;, shiftKey: true });
    expect(document.activeElement).toBe(button3);
  });
  
  it(&apos;focuses the initial element specified by ref&apos;, () => {
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
    expect(document.activeElement).toBe(screen.getByTestId(&apos;button-2&apos;));
  });
  
  it(&apos;ignores non-Tab key events&apos;, () => {
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