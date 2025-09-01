import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { useRouter } from 'next/navigation';
import { AuthGuard } from '../AuthGuard';
import authSlice from '@/store/slices/authSlice';
import { User, AuthState } from '@/types';

// Mock Next.js router
jest.mock('next/navigation', () => ({
    useRouter: jest.fn(),
}));

// Mock the Loading component
jest.mock('@/components/ui/Loading', () => ({
    Loading: () => <div data-testid="loading">Loading...</div>,
}));

// Mock the ErrorBoundary component
jest.mock('@/components/ui/ErrorBoundary', () => ({
    ErrorBoundary: ({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) => {
        try {
            return <>{children}</>;
        } catch (error) {
            return fallback || <div data-testid="error-boundary">Error occurred</div>;
        }
    },
}));

// Mock constants
jest.mock('@/constants', () => ({
    ROUTES: {
        HOME: '/',
        LOGIN: '/login',
        DASHBOARD: '/dashboard',
    },
}));

const mockPush = jest.fn();
const mockRouter = {
    push: mockPush,
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
};

// Helper functions for creating mock data
const createMockUser = (overrides: Partial<User> = {}): User => ({
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    user_type: 'customer',
    is_verified: true,
    created_at: '2023-01-01T00:00:00Z',
    ...overrides,
});

const createMockAuthState = (overrides: Partial<AuthState> = {}): AuthState => ({
    user: null,
    tokens: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    ...overrides,
});

describe('AuthGuard', () => {
    let store: any;
    let mockDispatch: jest.Mock;

    beforeEach(() => {
        jest.clearAllMocks();
        mockPush.mockClear();

        (useRouter as jest.Mock).mockReturnValue(mockRouter);

        mockDispatch = jest.fn();

        // Create a mock store
        store = configureStore({
            reducer: {
                auth: authSlice,
            },
            preloadedState: {
                auth: createMockAuthState(),
            },
        });

        // Mock the dispatch function with unwrap method
        store.dispatch = mockDispatch;
    });

    const renderWithProvider = (component: React.ReactElement) => {
        return render(
            <Provider store={store}>
                {component}
            </Provider>
        );
    };

    describe('Initialization', () => {
        it('should dispatch initializeAuth on mount', async () => {
            mockDispatch.mockReturnValue({ unwrap: () => Promise.resolve() });

            renderWithProvider(
                <AuthGuard>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(mockDispatch).toHaveBeenCalled();
            });
        });

        it('should show loading state during initialization', () => {
            mockDispatch.mockReturnValue({ unwrap: () => new Promise(() => { }) });

            renderWithProvider(
                <AuthGuard>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            expect(screen.getByTestId('loading')).toBeInTheDocument();
        });

        it('should handle initialization errors gracefully', async () => {
            const consoleError = jest.spyOn(console, 'error').mockImplementation(() => { });
            mockDispatch.mockReturnValue({
                unwrap: () => Promise.reject(new Error('Init failed'))
            });

            renderWithProvider(
                <AuthGuard>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(consoleError).toHaveBeenCalledWith('Auth initialization failed:', expect.any(Error));
            });

            consoleError.mockRestore();
        });
    });

    describe('Public Access (No Auth Required)', () => {
        beforeEach(() => {
            mockDispatch.mockReturnValue({ unwrap: () => Promise.resolve() });
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState(),
                },
            });
            store.dispatch = mockDispatch;
        });

        it('should render children when no auth is required', async () => {
            renderWithProvider(
                <AuthGuard requireAuth={false}>
                    <div data-testid="public-content">Public Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByTestId('public-content')).toBeInTheDocument();
            });
        });

        it('should render children for unauthenticated users when no auth required', async () => {
            renderWithProvider(
                <AuthGuard>
                    <div data-testid="public-content">Public Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByTestId('public-content')).toBeInTheDocument();
            });
        });
    });

    describe('Protected Routes (Auth Required)', () => {
        beforeEach(() => {
            mockDispatch.mockReturnValue({ unwrap: () => Promise.resolve() });
        });

        it('should redirect unauthenticated users to login', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState(),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true}>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/login');
            });
        });

        it('should render children for authenticated users', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        user: createMockUser(),
                        tokens: { access: 'token', refresh: 'refresh' },
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true}>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByTestId('protected-content')).toBeInTheDocument();
            });
        });

        it('should redirect to custom path when specified', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState(),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true} redirectTo="/custom-login">
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/custom-login');
            });
        });
    });

    describe('Guest Only Routes', () => {
        beforeEach(() => {
            mockDispatch.mockReturnValue({ unwrap: () => Promise.resolve() });
        });

        it('should render children for unauthenticated users', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState(),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireGuest={true}>
                    <div data-testid="guest-content">Guest Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByTestId('guest-content')).toBeInTheDocument();
            });
        });

        it('should redirect authenticated users to home', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        user: createMockUser(),
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireGuest={true}>
                    <div data-testid="guest-content">Guest Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/');
            });
        });

        it('should redirect authenticated users to custom path', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        user: createMockUser(),
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireGuest={true} redirectTo="/dashboard">
                    <div data-testid="guest-content">Guest Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/dashboard');
            });
        });
    });

    describe('User Type Permissions', () => {
        beforeEach(() => {
            mockDispatch.mockReturnValue({ unwrap: () => Promise.resolve() });
        });

        it('should allow access for users with correct user type', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        user: createMockUser({
                            email: 'admin@example.com',
                            user_type: 'admin'
                        }),
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true} allowedUserTypes={['admin', 'seller']}>
                    <div data-testid="admin-content">Admin Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByTestId('admin-content')).toBeInTheDocument();
            });
        });

        it('should show access denied for users with incorrect user type', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        user: createMockUser({
                            email: 'customer@example.com',
                            user_type: 'customer'
                        }),
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true} allowedUserTypes={['admin', 'seller']}>
                    <div data-testid="admin-content">Admin Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByText('Access Denied')).toBeInTheDocument();
                expect(screen.getByText("You don't have permission to access this page.")).toBeInTheDocument();
            });
        });

        it('should redirect users with incorrect user type when redirectTo is specified', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        user: createMockUser({
                            email: 'customer@example.com',
                            user_type: 'customer'
                        }),
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard
                    requireAuth={true}
                    allowedUserTypes={['admin']}
                    redirectTo="/unauthorized"
                >
                    <div data-testid="admin-content">Admin Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/unauthorized');
            });
        });
    });

    describe('Loading States', () => {
        it('should show loading when auth is loading', () => {
            mockDispatch.mockResolvedValue({ unwrap: () => Promise.resolve() });
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({ loading: true }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true}>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            expect(screen.getByTestId('loading')).toBeInTheDocument();
        });

        it('should show custom fallback when provided', () => {
            mockDispatch.mockResolvedValue({ unwrap: () => Promise.resolve() });
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({ loading: true }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard
                    requireAuth={true}
                    fallback={<div data-testid="custom-loading">Custom Loading</div>}
                >
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            expect(screen.getByTestId('custom-loading')).toBeInTheDocument();
        });
    });

    describe('Error Handling', () => {
        beforeEach(() => {
            mockDispatch.mockReturnValue({ unwrap: () => Promise.resolve() });
        });

        it('should show error state when auth fails and auth is required', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        error: 'Authentication failed',
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true}>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByText('Authentication Error')).toBeInTheDocument();
                expect(screen.getByText('Authentication failed')).toBeInTheDocument();
                expect(screen.getByText('Retry')).toBeInTheDocument();
            });
        });

        it('should handle retry button click', async () => {
            // Mock window.location.reload
            const mockReload = jest.fn();
            Object.defineProperty(window, 'location', {
                value: { reload: mockReload },
                writable: true,
            });

            mockDispatch.mockReturnValue({ unwrap: () => Promise.resolve() });

            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        error: 'Authentication failed',
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true}>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                const retryButton = screen.getByText('Retry');
                retryButton.click();
                expect(mockReload).toHaveBeenCalled();
            });
        });

        it('should not show error state when auth is not required', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        error: 'Authentication failed',
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={false}>
                    <div data-testid="public-content">Public Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByTestId('public-content')).toBeInTheDocument();
                expect(screen.queryByText('Authentication Error')).not.toBeInTheDocument();
            });
        });
    });

    describe('Edge Cases', () => {
        beforeEach(() => {
            mockDispatch.mockReturnValue({ unwrap: () => Promise.resolve() });
        });

        it('should handle missing user object when authenticated', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true} allowedUserTypes={['admin']}>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByTestId('protected-content')).toBeInTheDocument();
            });
        });

        it('should handle empty allowedUserTypes array', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        user: createMockUser(),
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            renderWithProvider(
                <AuthGuard requireAuth={true} allowedUserTypes={[]}>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            await waitFor(() => {
                expect(screen.getByTestId('protected-content')).toBeInTheDocument();
            });
        });

        it('should handle rapid state changes without causing issues', async () => {
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState(),
                },
            });
            store.dispatch = mockDispatch;

            const { rerender } = renderWithProvider(
                <AuthGuard requireAuth={true}>
                    <div data-testid="protected-content">Protected Content</div>
                </AuthGuard>
            );

            // Simulate rapid auth state changes
            store = configureStore({
                reducer: { auth: authSlice },
                preloadedState: {
                    auth: createMockAuthState({
                        user: createMockUser(),
                        isAuthenticated: true,
                    }),
                },
            });
            store.dispatch = mockDispatch;

            rerender(
                <Provider store={store}>
                    <AuthGuard requireAuth={true}>
                        <div data-testid="protected-content">Protected Content</div>
                    </AuthGuard>
                </Provider>
            );

            await waitFor(() => {
                expect(screen.getByTestId('protected-content')).toBeInTheDocument();
            });
        });
    });
});