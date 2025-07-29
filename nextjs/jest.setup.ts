import '@testing-library/jest-dom';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: (): {
    push: jest.Mock;
    replace: jest.Mock;
    prefetch: jest.Mock;
    back: jest.Mock;
    forward: jest.Mock;
    refresh: jest.Mock;
  } => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
  }),
  useSearchParams: (): {
    get: jest.Mock;
  } => ({
    get: jest.fn(),
  }),
  usePathname: (): string => '/',
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
  },
  success: jest.fn(),
  error: jest.fn(),
  loading: jest.fn(),
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Global test utilities
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
      toHaveClass(...classNames: string[]): R;
      toHaveAttribute(attr: string, value?: string): R;
      toBeDisabled(): R;
      toBeVisible(): R;
      toHaveValue(value: string | number | string[]): R;
    }
  }
}

// Test utility types
export interface MockStore {
  getState: jest.Mock;
  dispatch: jest.Mock;
  subscribe: jest.Mock;
  replaceReducer: jest.Mock;
}

export interface TestComponentProps {
  children?: React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

// Common test utilities
export const createMockRouter = () => ({
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
  pathname: '/',
  query: {},
  asPath: '/',
});

export const createMockSearchParams = (params: Record<string, string> = {}) => ({
  get: jest.fn((key: string) => params[key] || null),
  has: jest.fn((key: string) => key in params),
  getAll: jest.fn((key: string) => params[key] ? [params[key]] : []),
  keys: jest.fn(() => Object.keys(params)),
  values: jest.fn(() => Object.values(params)),
  entries: jest.fn(() => Object.entries(params)),
  forEach: jest.fn(),
  toString: jest.fn(() => new URLSearchParams(params).toString()),
});

// Mock API response helper
export const createMockApiResponse = <T>(data: T, success = true) => ({
  success,
  data: success ? data : undefined,
  error: success ? undefined : {
    message: 'Mock error',
    code: 'MOCK_ERROR',
    status_code: 400,
  },
});

// Mock pagination helper
export const createMockPagination = (overrides: Partial<{
  count: number;
  next: string | null;
  previous: string | null;
  page_size: number;
  total_pages: number;
  current_page: number;
}> = {}) => ({
  count: 0,
  next: null,
  previous: null,
  page_size: 10,
  total_pages: 0,
  current_page: 1,
  ...overrides,
});