import { renderHook, RenderHookOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { EnhancedStore } from '@reduxjs/toolkit';
import React from 'react';

import { createTestStore } from './test-utils';
import type { RootState } from '@/store';

// Hook testing utilities with proper typing
interface RenderHookWithStoreOptions<TProps> extends Omit<RenderHookOptions<TProps>, 'wrapper'> {
  preloadedState?: Partial<RootState>;
  store?: EnhancedStore;
}

export function renderHookWithStore<TResult, TProps>(
  hook: (props: TProps) => TResult,
  options: RenderHookWithStoreOptions<TProps> = {}
) {
  const {
    preloadedState,
    store = createTestStore({ preloadedState }),
    ...renderOptions
  } = options;

  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(Provider, { store, children });
  }

  return {
    store,
    ...renderHook(hook, { wrapper: Wrapper, ...renderOptions }),
  };
}

// Mock hook implementations
export const createMockUseRouter = (overrides: Record<string, any> = {}) => ({
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
  pathname: '/',
  query: {},
  asPath: '/',
  ...overrides,
});

export const createMockUseSearchParams = (params: Record<string, string> = {}) => ({
  get: jest.fn((key: string) => params[key] || null),
  has: jest.fn((key: string) => key in params),
  getAll: jest.fn((key: string) => params[key] ? [params[key]] : []),
  keys: jest.fn(() => Object.keys(params)),
  values: jest.fn(() => Object.values(params)),
  entries: jest.fn(() => Object.entries(params)),
  forEach: jest.fn(),
  toString: jest.fn(() => new URLSearchParams(params).toString()),
});

// WebSocket mock utilities
export const createMockWebSocketService = (overrides: Record<string, any> = {}) => ({
  connect: jest.fn(),
  disconnect: jest.fn(),
  send: jest.fn(),
  getConnectionState: jest.fn(() => 'CLOSED'),
  onConnectionStateChange: jest.fn(),
  offConnectionStateChange: jest.fn(),
  onMessage: jest.fn(),
  offMessage: jest.fn(),
  ...overrides,
});

// API mock utilities
export const createMockApiService = <T>(
  mockResponses: Record<string, T> = {}
) => {
  const mockFetch = jest.fn();
  
  Object.entries(mockResponses).forEach(([endpoint, response]) => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes(endpoint)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(response),
          status: 200,
          statusText: 'OK',
        });
      }
      return Promise.reject(new Error(`No mock response for ${url}`));
    });
  });

  return mockFetch;
};

// Local storage mock utilities
export const createMockLocalStorage = (initialData: Record<string, string> = {}) => {
  const storage = { ...initialData };
  
  return {
    getItem: jest.fn((key: string) => storage[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      storage[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete storage[key];
    }),
    clear: jest.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key]);
    }),
    key: jest.fn((index: number) => Object.keys(storage)[index] || null),
    get length() {
      return Object.keys(storage).length;
    },
  };
};

// Session storage mock utilities
export const createMockSessionStorage = createMockLocalStorage;

// Intersection Observer mock
export const createMockIntersectionObserver = () => {
  const mockObserver = {
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  };

  global.IntersectionObserver = jest.fn().mockImplementation(() => mockObserver);
  
  return mockObserver;
};

// Resize Observer mock
export const createMockResizeObserver = () => {
  const mockObserver = {
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  };

  global.ResizeObserver = jest.fn().mockImplementation(() => mockObserver);
  
  return mockObserver;
};

// Performance Observer mock
export const createMockPerformanceObserver = () => {
  const mockObserver = {
    observe: jest.fn(),
    disconnect: jest.fn(),
  };

  const MockPerformanceObserver: any = jest.fn().mockImplementation(() => mockObserver);
  MockPerformanceObserver.supportedEntryTypes = [];
  global.PerformanceObserver = MockPerformanceObserver;
  
  return mockObserver;
};

// Media query mock utilities
export const createMockMediaQuery = (matches = false) => ({
  matches,
  media: '(min-width: 768px)',
  onchange: null,
  addListener: jest.fn(),
  removeListener: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
});

// Geolocation mock utilities
export const createMockGeolocation = () => ({
  getCurrentPosition: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn(),
});

// File API mock utilities
export const createMockFile = (
  name: string,
  content: string,
  type = 'text/plain'
): File => {
  const file = new File([content], name, { type });
  return file;
};

export const createMockFileList = (files: File[]): FileList => {
  const fileList = {
    length: files.length,
    item: (index: number) => files[index] || null,
    [Symbol.iterator]: function* () {
      for (const file of files) {
        yield file;
      }
    },
  };
  
  // Add indexed properties
  files.forEach((file, index) => {
    (fileList as any)[index] = file;
  });
  
  return fileList as FileList;
};