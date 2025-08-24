/**
 * Tests for Route Discovery Dashboard Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RouteDiscoveryDashboard from '../RouteDiscoveryDashboard';
import * as routeDiscoveryApi from '@/services/routeDiscoveryApi';

// Mock the route discovery API
jest.mock('@/services/routeDiscoveryApi');

const mockRouteDiscoveryApi = routeDiscoveryApi as jest.Mocked<typeof routeDiscoveryApi>;

describe('RouteDiscoveryDashboard', () => {
  const mockDiscoveryResults = {
    routes: [
      {
        path: '/',
        type: 'page' as const,
        component: 'HomePage',
        apiCalls: [
          {
            method: 'GET' as const,
            endpoint: '/api/products',
            authentication: true
          }
        ],
        dependencies: []
      },
      {
        path: '/api/users',
        type: 'api' as const,
        component: 'UsersAPI',
        apiCalls: [],
        dependencies: []
      }
    ],
    totalRoutes: 2,
    apiCallsCount: 1,
    lastScanned: '2024-01-01T00:00:00Z',
    scanDuration: 1500
  };

  const mockDependencyMap = {
    frontend_routes: [
      {
        path: '/',
        type: 'page' as const,
        component: 'HomePage',
        apiCalls: [],
        dependencies: []
      }
    ],
    api_endpoints: ['/api/products', '/api/users'],
    dependencies: [
      {
        frontend_route: '/',
        api_endpoint: '/api/products',
        method: 'GET',
        component: 'HomePage'
      }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default successful responses
    mockRouteDiscoveryApi.getRouteDiscoveryResults.mockResolvedValue({
      success: true,
      data: mockDiscoveryResults,
      message: 'Success'
    });

    mockRouteDiscoveryApi.getDependencyMap.mockResolvedValue({
      success: true,
      data: mockDependencyMap,
      message: 'Success'
    });
  });

  it('renders dashboard with initial data', async () => {
    render(<RouteDiscoveryDashboard />);

    // Check if main heading is present
    expect(screen.getByText('Route Discovery Dashboard')).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Total routes
      expect(screen.getByText('1')).toBeInTheDocument(); // API calls count
    });

    // Check if routes are displayed
    expect(screen.getByText('/')).toBeInTheDocument();
    expect(screen.getByText('/api/users')).toBeInTheDocument();
  });

  it('displays route cards with correct information', async () => {
    render(<RouteDiscoveryDashboard />);

    await waitFor(() => {
      expect(screen.getByText('/')).toBeInTheDocument();
    });

    // Check route type badges
    expect(screen.getByText('page')).toBeInTheDocument();
    expect(screen.getByText('api')).toBeInTheDocument();

    // Check component names
    expect(screen.getByText('Component: HomePage')).toBeInTheDocument();
    expect(screen.getByText('Component: UsersAPI')).toBeInTheDocument();

    // Check API calls section
    expect(screen.getByText('API Calls (1)')).toBeInTheDocument();
    expect(screen.getByText('GET')).toBeInTheDocument();
    expect(screen.getByText('/api/products')).toBeInTheDocument();
    expect(screen.getByText('Auth')).toBeInTheDocument();
  });

  it('handles trigger discovery action', async () => {
    mockRouteDiscoveryApi.triggerRouteDiscovery.mockResolvedValue({
      success: true,
      data: mockDiscoveryResults,
      message: 'Discovery completed'
    });

    render(<RouteDiscoveryDashboard />);

    const triggerButton = screen.getByText('Trigger Discovery');
    fireEvent.click(triggerButton);

    // Check loading state
    expect(screen.getByText('Scanning...')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockRouteDiscoveryApi.triggerRouteDiscovery).toHaveBeenCalled();
      expect(screen.getByText('Trigger Discovery')).toBeInTheDocument();
    });
  });

  it('handles validation action', async () => {
    const mockValidationResult = {
      totalRoutes: 10,
      validRoutes: 8,
      invalidRoutes: 2,
      errors: ['Component file not found: /path/to/missing.tsx']
    };

    mockRouteDiscoveryApi.validateRouteDiscovery.mockResolvedValue({
      success: true,
      data: mockValidationResult,
      message: 'Validation completed'
    });

    render(<RouteDiscoveryDashboard />);

    const validateButton = screen.getByText('Validate Routes');
    fireEvent.click(validateButton);

    await waitFor(() => {
      expect(mockRouteDiscoveryApi.validateRouteDiscovery).toHaveBeenCalled();
    });

    // Should switch to validation tab and show results
    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument(); // Total routes
      expect(screen.getByText('8')).toBeInTheDocument(); // Valid routes
      expect(screen.getByText('2')).toBeInTheDocument(); // Invalid routes
      expect(screen.getByText('Component file not found: /path/to/missing.tsx')).toBeInTheDocument();
    });
  });

  it('switches between tabs correctly', async () => {
    render(<RouteDiscoveryDashboard />);

    await waitFor(() => {
      expect(screen.getByText('/')).toBeInTheDocument();
    });

    // Switch to dependencies tab
    const dependenciesTab = screen.getByText('Dependencies');
    fireEvent.click(dependenciesTab);

    await waitFor(() => {
      expect(screen.getByText('Dependency Overview')).toBeInTheDocument();
      expect(screen.getByText('Frontend Routes')).toBeInTheDocument();
      expect(screen.getByText('API Endpoints')).toBeInTheDocument();
    });
  });

  it('displays dependency map correctly', async () => {
    render(<RouteDiscoveryDashboard />);

    // Switch to dependencies tab
    const dependenciesTab = screen.getByText('Dependencies');
    fireEvent.click(dependenciesTab);

    await waitFor(() => {
      expect(screen.getByText('Dependency Overview')).toBeInTheDocument();
      expect(screen.getByText('Route Dependencies')).toBeInTheDocument();
    });

    // Check dependency mapping
    expect(screen.getByText('Component: HomePage')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    mockRouteDiscoveryApi.getRouteDiscoveryResults.mockResolvedValue({
      success: false,
      data: null,
      error: 'Failed to fetch results'
    });

    mockRouteDiscoveryApi.getDependencyMap.mockResolvedValue({
      success: false,
      data: null,
      error: 'Failed to fetch dependencies'
    });

    render(<RouteDiscoveryDashboard />);

    // Should not crash and should handle the error gracefully
    await waitFor(() => {
      expect(screen.getByText('Route Discovery Dashboard')).toBeInTheDocument();
    });
  });

  it('displays error messages when operations fail', async () => {
    mockRouteDiscoveryApi.triggerRouteDiscovery.mockResolvedValue({
      success: false,
      data: null,
      error: 'Discovery failed due to network error'
    });

    render(<RouteDiscoveryDashboard />);

    const triggerButton = screen.getByText('Trigger Discovery');
    fireEvent.click(triggerButton);

    await waitFor(() => {
      expect(screen.getByText('Discovery failed due to network error')).toBeInTheDocument();
    });
  });

  it('shows loading state during operations', async () => {
    // Make the API call hang to test loading state
    mockRouteDiscoveryApi.triggerRouteDiscovery.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );

    render(<RouteDiscoveryDashboard />);

    const triggerButton = screen.getByText('Trigger Discovery');
    fireEvent.click(triggerButton);

    // Should show loading state
    expect(screen.getByText('Scanning...')).toBeInTheDocument();
    expect(triggerButton).toBeDisabled();
  });

  it('formats timestamps correctly', async () => {
    render(<RouteDiscoveryDashboard />);

    await waitFor(() => {
      // Should display formatted timestamp
      expect(screen.getByText(/Last scanned:/)).toBeInTheDocument();
    });
  });
});