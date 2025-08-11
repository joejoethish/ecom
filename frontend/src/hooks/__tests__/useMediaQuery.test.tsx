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
  return <div data-testid="result">{matches ? 'true' : 'false'}</div>;
}

// Test component for predefined hooks
function TestBreakpoints() {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();
  
  return (
    <div>
      <div data-testid="mobile">{isMobile ? 'true' : 'false'}</div>
      <div data-testid="tablet">{isTablet ? 'true' : 'false'}</div>
      <div data-testid="desktop">{isDesktop ? 'true' : 'false'}</div>
    </div>
  );
}

describe('useMediaQuery', () => {
  it('returns true when media query matches', () => {
    mockMatchMedia(true);
    render(<TestMediaQuery query="(min-width: 768px)" />);
    expect(screen.getByTestId('result')).toHaveTextContent('true');
  });
  
  it('returns false when media query does not match', () => {
    mockMatchMedia(false);
    render(<TestMediaQuery query="(min-width: 768px)" />);
    expect(screen.getByTestId('result')).toHaveTextContent('false');
  });
  
  it('handles window being undefined (SSR)', () => {
    const originalWindow = global.window;
    // Use a safer approach to mock window as undefined
    Object.defineProperty(global, 'window', {
      value: undefined,
      writable: true,
      configurable: true
    });
    
    // Should not throw an error
    render(<TestMediaQuery query="(min-width: 768px)" />);
    expect(screen.getByTestId('result')).toHaveTextContent('false');
    
    // Restore window
    Object.defineProperty(global, 'window', {
      value: originalWindow,
      writable: true,
      configurable: true
    });
  });
});

describe('Breakpoint hooks', () => {
  it('correctly identifies mobile view', () => {
    // Mock mobile view (below md breakpoint)
    mockMatchMedia(false);
    
    render(<TestBreakpoints />);
    
    expect(screen.getByTestId('mobile')).toHaveTextContent('true');
    expect(screen.getByTestId('tablet')).toHaveTextContent('false');
    expect(screen.getByTestId('desktop')).toHaveTextContent('false');
  });
  
  it('correctly identifies tablet view', () => {
    // First mock for md breakpoint (true)
    // Second mock for lg breakpoint (false)
    mockMatchMedia(true);
    window.matchMedia = jest.fn()
      .mockImplementationOnce(query => ({
        matches: query.includes('768px'), // md breakpoint
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
    
    expect(screen.getByTestId('mobile')).toHaveTextContent('false');
    expect(screen.getByTestId('tablet')).toHaveTextContent('true');
    expect(screen.getByTestId('desktop')).toHaveTextContent('false');
  });
  
  it('correctly identifies desktop view', () => {
    // Mock desktop view (above lg breakpoint)
    mockMatchMedia(true);
    
    render(<TestBreakpoints />);
    
    expect(screen.getByTestId('mobile')).toHaveTextContent('false');
    expect(screen.getByTestId('tablet')).toHaveTextContent('false');
    expect(screen.getByTestId('desktop')).toHaveTextContent('true');
  });
});