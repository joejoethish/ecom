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

Object.defineProperty(window, &apos;localStorage&apos;, {
    value: localStorageMock,
});

// Mock matchMedia
Object.defineProperty(window, &apos;matchMedia&apos;, {
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
            <div data-testid="high-contrast-value">{highContrast ? &apos;true&apos; : &apos;false&apos;}</div>
            <div data-testid="font-size-value">{fontSize}</div>
            <div data-testid="reduce-motion-value">{reduceMotion ? &apos;true&apos; : &apos;false&apos;}</div>
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

describe(&apos;AccessibilityProvider&apos;, () => {
    beforeEach(() => {
        localStorageMock.clear();
        document.documentElement.style.fontSize = &apos;&apos;;
        document.documentElement.classList.remove(&apos;high-contrast&apos;, &apos;reduce-motion&apos;);
    });

    it(&apos;provides default accessibility values&apos;, () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        expect(screen.getByTestId(&apos;high-contrast-value&apos;)).toHaveTextContent(&apos;false&apos;);
        expect(screen.getByTestId(&apos;font-size-value&apos;)).toHaveTextContent(&apos;16&apos;);
        expect(screen.getByTestId(&apos;reduce-motion-value&apos;)).toHaveTextContent(&apos;false&apos;);
    });

    it(&apos;toggles high contrast mode&apos;, () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        fireEvent.click(screen.getByTestId(&apos;toggle-high-contrast&apos;));
        expect(screen.getByTestId(&apos;high-contrast-value&apos;)).toHaveTextContent(&apos;true&apos;);
        expect(document.documentElement.classList.contains(&apos;high-contrast&apos;)).toBe(true);

        fireEvent.click(screen.getByTestId(&apos;toggle-high-contrast&apos;));
        expect(screen.getByTestId(&apos;high-contrast-value&apos;)).toHaveTextContent(&apos;false&apos;);
        expect(document.documentElement.classList.contains(&apos;high-contrast&apos;)).toBe(false);
    });

    it(&apos;increases and decreases font size&apos;, () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        fireEvent.click(screen.getByTestId(&apos;increase-font-size&apos;));
        expect(screen.getByTestId(&apos;font-size-value&apos;)).toHaveTextContent(&apos;17&apos;);
        expect(document.documentElement.style.fontSize).toBe(&apos;17px&apos;);

        fireEvent.click(screen.getByTestId(&apos;decrease-font-size&apos;));
        expect(screen.getByTestId(&apos;font-size-value&apos;)).toHaveTextContent(&apos;16&apos;);
        expect(document.documentElement.style.fontSize).toBe(&apos;16px&apos;);
    });

    it(&apos;resets font size to default&apos;, () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        // Increase font size twice
        fireEvent.click(screen.getByTestId(&apos;increase-font-size&apos;));
        fireEvent.click(screen.getByTestId(&apos;increase-font-size&apos;));
        expect(screen.getByTestId(&apos;font-size-value&apos;)).toHaveTextContent(&apos;18&apos;);

        // Reset to default
        fireEvent.click(screen.getByTestId(&apos;reset-font-size&apos;));
        expect(screen.getByTestId(&apos;font-size-value&apos;)).toHaveTextContent(&apos;16&apos;);
        expect(document.documentElement.style.fontSize).toBe(&apos;16px&apos;);
    });

    it(&apos;toggles reduced motion&apos;, () => {
        render(
            <AccessibilityProvider>
                <TestComponent />
            </AccessibilityProvider>
        );

        fireEvent.click(screen.getByTestId(&apos;toggle-reduce-motion&apos;));
        expect(screen.getByTestId(&apos;reduce-motion-value&apos;)).toHaveTextContent(&apos;true&apos;);
        expect(document.documentElement.classList.contains(&apos;reduce-motion&apos;)).toBe(true);

        fireEvent.click(screen.getByTestId(&apos;toggle-reduce-motion&apos;));
        expect(screen.getByTestId(&apos;reduce-motion-value&apos;)).toHaveTextContent(&apos;false&apos;);
        expect(document.documentElement.classList.contains(&apos;reduce-motion&apos;)).toBe(false);
    });

    it(&apos;persists settings to localStorage&apos;, () => {
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