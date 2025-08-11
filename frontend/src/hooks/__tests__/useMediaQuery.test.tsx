import React from 'react';
import { render, screen } from '@testing-library/react';
import { useMediaQuery, useIsMobile, useIsTablet, useIsDesktop } from '../useMediaQuery';

// Mock matchMedia
function mockMatchMedia(matches: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(), // Deprecated
      removeListener: jest.fn(), // Deprecated
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
}

// Test component for useMediaQuery
function TestMediaQuery({ query }: { query: string }) {
  const matches = useMediaQuery(query);
  return <div data-testid="result">{matches ? &apos;true&apos; : &apos;false&apos;}</div>;
}

// Test component for predefined hooks
function TestBreakpoints() {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();
  
  return (
    <div>
      <div data-testid="mobile">{isMobile ? &apos;true&apos; : &apos;false&apos;}</div>
      <div data-testid="tablet">{isTablet ? &apos;true&apos; : &apos;false&apos;}</div>
      <div data-testid="desktop">{isDesktop ? &apos;true&apos; : &apos;false&apos;}</div>
    </div>
  );
}

describe(&apos;useMediaQuery&apos;, () => {
  it(&apos;returns true when media query matches&apos;, () => {
    mockMatchMedia(true);
    render(<TestMediaQuery query="(min-width: 768px)" />);
    expect(screen.getByTestId(&apos;result&apos;)).toHaveTextContent(&apos;true&apos;);
  });
  
  it(&apos;returns false when media query does not match&apos;, () => {
    mockMatchMedia(false);
    render(<TestMediaQuery query="(min-width: 768px)" />);
    expect(screen.getByTestId(&apos;result&apos;)).toHaveTextContent(&apos;false&apos;);
  });
  
  it(&apos;handles window being undefined (SSR)&apos;, () => {
    const originalWindow = global.window;
    // Use a safer approach to mock window as undefined
    Object.defineProperty(global, &apos;window&apos;, {
      value: undefined,
      writable: true,
      configurable: true
    });
    
    // Should not throw an error
    render(<TestMediaQuery query="(min-width: 768px)" />);
    expect(screen.getByTestId(&apos;result&apos;)).toHaveTextContent(&apos;false&apos;);
    
    // Restore window
    Object.defineProperty(global, &apos;window&apos;, {
      value: originalWindow,
      writable: true,
      configurable: true
    });
  });
});

describe(&apos;Breakpoint hooks&apos;, () => {
  it(&apos;correctly identifies mobile view&apos;, () => {
    // Mock mobile view (below md breakpoint)
    mockMatchMedia(false);
    
    render(<TestBreakpoints />);
    
    expect(screen.getByTestId(&apos;mobile&apos;)).toHaveTextContent(&apos;true&apos;);
    expect(screen.getByTestId(&apos;tablet&apos;)).toHaveTextContent(&apos;false&apos;);
    expect(screen.getByTestId(&apos;desktop&apos;)).toHaveTextContent(&apos;false&apos;);
  });
  
  it(&apos;correctly identifies tablet view&apos;, () => {
    // First mock for md breakpoint (true)
    // Second mock for lg breakpoint (false)
    mockMatchMedia(true);
    window.matchMedia = jest.fn()
      .mockImplementationOnce(query => ({
        matches: query.includes(&apos;768px&apos;), // md breakpoint
        media: query,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }))
      .mockImplementationOnce(query => ({
        matches: false, // lg breakpoint
        media: query,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));
    
    render(<TestBreakpoints />);
    
    expect(screen.getByTestId(&apos;mobile&apos;)).toHaveTextContent(&apos;false&apos;);
    expect(screen.getByTestId(&apos;tablet&apos;)).toHaveTextContent(&apos;true&apos;);
    expect(screen.getByTestId(&apos;desktop&apos;)).toHaveTextContent(&apos;false&apos;);
  });
  
  it(&apos;correctly identifies desktop view&apos;, () => {
    // Mock desktop view (above lg breakpoint)
    mockMatchMedia(true);
    
    render(<TestBreakpoints />);
    
    expect(screen.getByTestId('mobile')).toHaveTextContent('false');
    expect(screen.getByTestId('tablet')).toHaveTextContent('false');
    expect(screen.getByTestId('desktop')).toHaveTextContent('true');
  });
});