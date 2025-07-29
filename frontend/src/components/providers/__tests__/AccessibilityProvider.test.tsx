import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AccessibilityProvider, useAccessibility } from '../AccessibilityProvider';

// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => {
            store[key] = value.toString();
        },
        clear: () => {
            store = {};
        },
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
});

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
    value: (query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    }),
});

// Test component that uses the accessibility context
function TestComponent() {
    const {
        highContrast,
        toggleHighContrast,
        fontSize,
        increaseFontSize,
        decreaseFontSize,
        resetFontSize,
        reduceMotion,
        toggleReduceMotion,
    } = useAccessibility();

    return (
        <div>
            <div data-testid="high-contrast-value">{highContrast ? 'true' : 'false'}</div>
            <div data-testid="font-size-value">{fontSize}</div>
            <div data-testid="reduce-motion-value">{reduceMotion ? 'true' : 'false'}</div>
            <button data-testid="toggle-high-contrast" onClick={toggleHighContrast}>
                Toggle High Contrast
            </button>
            <button data-testid="increase-font-size" onClick={increaseFontSize}>
                Increase Font Size
            </button>
            <button data-testid="decrease-font-size" onClick={decreaseFontSize}>
                Decrease Font Size
            </button>
            <button data-testid="reset-font-size" onClick={resetFontSize}>
                Reset Font Size
            </button>
            <button data-testid="toggle-reduce-motion" onClick={toggleReduceMotion}>
                Toggle Reduce Motion
            </button>
        </div>
    );
}

describe('AccessibilityProvider', () => {
    beforeEach(() => {
        localStorageMock.clear();
        document.documentElement.style.fontSize = '';
        document.documentElement.classList.remove('high-contrast', 'reduce-motion');
    });

    it('provides default accessibility values', () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        expect(screen.getByTestId('high-contrast-value')).toHaveTextContent('false');
        expect(screen.getByTestId('font-size-value')).toHaveTextContent('16');
        expect(screen.getByTestId('reduce-motion-value')).toHaveTextContent('false');
    });

    it('toggles high contrast mode', () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        fireEvent.click(screen.getByTestId('toggle-high-contrast'));
        expect(screen.getByTestId('high-contrast-value')).toHaveTextContent('true');
        expect(document.documentElement.classList.contains('high-contrast')).toBe(true);

        fireEvent.click(screen.getByTestId('toggle-high-contrast'));
        expect(screen.getByTestId('high-contrast-value')).toHaveTextContent('false');
        expect(document.documentElement.classList.contains('high-contrast')).toBe(false);
    });

    it('increases and decreases font size', () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        fireEvent.click(screen.getByTestId('increase-font-size'));
        expect(screen.getByTestId('font-size-value')).toHaveTextContent('17');
        expect(document.documentElement.style.fontSize).toBe('17px');

        fireEvent.click(screen.getByTestId('decrease-font-size'));
        expect(screen.getByTestId('font-size-value')).toHaveTextContent('16');
        expect(document.documentElement.style.fontSize).toBe('16px');
    });

    it('resets font size to default', () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        // Increase font size twice
        fireEvent.click(screen.getByTestId('increase-font-size'));
        fireEvent.click(screen.getByTestId('increase-font-size'));
        expect(screen.getByTestId('font-size-value')).toHaveTextContent('18');

        // Reset to default
        fireEvent.click(screen.getByTestId('reset-font-size'));
        expect(screen.getByTestId('font-size-value')).toHaveTextContent('16');
        expect(document.documentElement.style.fontSize).toBe('16px');
    });

    it('toggles reduced motion', () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        fireEvent.click(screen.getByTestId('toggle-reduce-motion'));
        expect(screen.getByTestId('reduce-motion-value')).toHaveTextContent('true');
        expect(document.documentElement.classList.contains('reduce-motion')).toBe(true);

        fireEvent.click(screen.getByTestId('toggle-reduce-motion'));
        expect(screen.getByTestId('reduce-motion-value')).toHaveTextContent('false');
        expect(document.documentElement.classList.contains('reduce-motion')).toBe(false);
    });

    it('persists settings to localStorage', () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        fireEvent.click(screen.getByTestId('toggle-high-contrast'));
        fireEvent.click(screen.getByTestId('increase-font-size'));
        fireEvent.click(screen.getByTestId('toggle-reduce-motion'));

        expect(localStorageMock.getItem('ecommerce-high-contrast')).toBe('true');
        expect(localStorageMock.getItem('ecommerce-font-size')).toBe('17');
        expect(localStorageMock.getItem('ecommerce-reduce-motion')).toBe('true');
    });
});