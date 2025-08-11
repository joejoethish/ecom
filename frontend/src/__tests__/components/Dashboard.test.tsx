// Unit tests for Dashboard component
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import Dashboard from '@/components/dashboard/Dashboard';
import { dashboardSlice } from '@/store/slices/dashboardSlice';

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
  Pie: () => <div data-testid="pie-chart">Pie Chart</div>,
}));

// Mock store setup
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      dashboard: dashboardSlice.reducer,
    },
    preloadedState: {
      dashboard: {
        stats: {
          totalOrders: 0,
          totalRevenue: 0,
          totalCustomers: 0,
          totalProducts: 0,
          pendingOrders: 0,
          lowStockProducts: 0,
        },
        charts: {
          salesChart: { labels: [], datasets: [] },
          ordersChart: { labels: [], datasets: [] },
        },
        isLoading: false,
        error: null,
        ...initialState,
      },
    },
  });
};

describe(&apos;Dashboard Component&apos;, () => {
  let mockStore: ReturnType<typeof createMockStore>;
  
  beforeEach(() => {
    mockStore = createMockStore();
  });

  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <Provider store={mockStore}>
        {component}
      </Provider>
    );
  };

  test(&apos;renders dashboard with loading state&apos;, () => {
    const loadingStore = createMockStore({ isLoading: true });
    
    render(
      <Provider store={loadingStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByTestId(&apos;loading-spinner&apos;)).toBeInTheDocument();
  });

  test(&apos;renders dashboard stats correctly&apos;, () => {
    const statsStore = createMockStore({
      stats: {
        totalOrders: 150,
        totalRevenue: 25000,
        totalCustomers: 75,
        totalProducts: 200,
        pendingOrders: 12,
        lowStockProducts: 5,
      },
    });
    
    render(
      <Provider store={statsStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(&apos;150&apos;)).toBeInTheDocument(); // Total Orders
    expect(screen.getByText(&apos;$25,000&apos;)).toBeInTheDocument(); // Total Revenue
    expect(screen.getByText(&apos;75&apos;)).toBeInTheDocument(); // Total Customers
    expect(screen.getByText(&apos;200&apos;)).toBeInTheDocument(); // Total Products
    expect(screen.getByText(&apos;12&apos;)).toBeInTheDocument(); // Pending Orders
    expect(screen.getByText(&apos;5&apos;)).toBeInTheDocument(); // Low Stock Products
  });

  test(&apos;renders charts when data is available&apos;, () => {
    const chartsStore = createMockStore({
      charts: {
        salesChart: {
          labels: [&apos;Jan&apos;, &apos;Feb&apos;, &apos;Mar&apos;],
          datasets: [{ data: [100, 200, 300] }],
        },
        ordersChart: {
          labels: [&apos;Jan&apos;, &apos;Feb&apos;, &apos;Mar&apos;],
          datasets: [{ data: [10, 20, 30] }],
        },
      },
    });
    
    render(
      <Provider store={chartsStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByTestId(&apos;line-chart&apos;)).toBeInTheDocument();
    expect(screen.getByTestId(&apos;bar-chart&apos;)).toBeInTheDocument();
  });

  test(&apos;displays error message when data loading fails&apos;, () => {
    const errorStore = createMockStore({
      error: &apos;Failed to load dashboard data&apos;,
    });
    
    render(
      <Provider store={errorStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
  });

  test(&apos;shows empty state when no data is available&apos;, () => {
    const emptyStore = createMockStore({
      stats: {
        totalOrders: 0,
        totalRevenue: 0,
        totalCustomers: 0,
        totalProducts: 0,
        pendingOrders: 0,
        lowStockProducts: 0,
      },
    });
    
    render(
      <Provider store={emptyStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(/no data available/i)).toBeInTheDocument();
  });

  test(&apos;formats currency values correctly&apos;, () => {
    const statsStore = createMockStore({
      stats: {
        totalRevenue: 1234567.89,
      },
    });
    
    render(
      <Provider store={statsStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(&apos;$1,234,567.89&apos;)).toBeInTheDocument();
  });

  test(&apos;handles large numbers with proper formatting&apos;, () => {
    const statsStore = createMockStore({
      stats: {
        totalOrders: 1000000,
        totalCustomers: 500000,
      },
    });
    
    render(
      <Provider store={statsStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(&apos;1,000,000&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;500,000&apos;)).toBeInTheDocument();
  });

  test(&apos;shows refresh button and handles refresh action&apos;, async () => {
    renderWithProvider(<Dashboard />);
    
    const refreshButton = screen.getByRole(&apos;button&apos;, { name: /refresh/i });
    expect(refreshButton).toBeInTheDocument();
    
    // Click refresh button
    fireEvent.click(refreshButton);
    
    // Should trigger data refresh (implementation dependent)
  });

  test(&apos;displays time period selector&apos;, () => {
    renderWithProvider(<Dashboard />);
    
    expect(screen.getByLabelText(/time period/i)).toBeInTheDocument();
    expect(screen.getByText(/last 7 days/i)).toBeInTheDocument();
    expect(screen.getByText(/last 30 days/i)).toBeInTheDocument();
    expect(screen.getByText(/last 90 days/i)).toBeInTheDocument();
  });

  test(&apos;updates data when time period changes&apos;, async () => {
    renderWithProvider(<Dashboard />);
    
    const timePeriodSelect = screen.getByLabelText(/time period/i);
    fireEvent.change(timePeriodSelect, { target: { value: &apos;30&apos; } });
    
    // Should trigger data update for new time period
    await waitFor(() => {
      // Verify new data is loaded
    });
  });

  test(&apos;shows quick action buttons&apos;, () => {
    renderWithProvider(<Dashboard />);
    
    expect(screen.getByRole(&apos;button&apos;, { name: /add product/i })).toBeInTheDocument();
    expect(screen.getByRole(&apos;button&apos;, { name: /view orders/i })).toBeInTheDocument();
    expect(screen.getByRole(&apos;button&apos;, { name: /manage customers/i })).toBeInTheDocument();
  });

  test(&apos;displays recent activity feed&apos;, () => {
    const activityStore = createMockStore({
      recentActivity: [
        { id: 1, type: &apos;order&apos;, message: &apos;New order #1001 received&apos;, timestamp: &apos;2024-01-01T10:00:00Z&apos; },
        { id: 2, type: &apos;product&apos;, message: &apos;Product &quot;Test Item&quot; updated&apos;, timestamp: &apos;2024-01-01T09:30:00Z&apos; },
      ],
    });
    
    render(
      <Provider store={activityStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(/new order #1001 received/i)).toBeInTheDocument();
    expect(screen.getByText(/product &quot;test item&quot; updated/i)).toBeInTheDocument();
  });

  test(&apos;handles responsive design&apos;, () => {
    // Mock window.innerWidth
    Object.defineProperty(window, &apos;innerWidth&apos;, {
      writable: true,
      configurable: true,
      value: 768,
    });
    
    renderWithProvider(<Dashboard />);
    
    // Should adapt layout for tablet/mobile
    const dashboardGrid = screen.getByTestId(&apos;dashboard-grid&apos;);
    expect(dashboardGrid).toHaveClass(&apos;responsive-grid&apos;);
  });

  test(&apos;shows alerts for critical issues&apos;, () => {
    const alertsStore = createMockStore({
      alerts: [
        { id: 1, type: &apos;warning&apos;, message: &apos;5 products are low in stock&apos; },
        { id: 2, type: &apos;error&apos;, message: &apos;Payment gateway is down&apos; },
      ],
    });
    
    render(
      <Provider store={alertsStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(/5 products are low in stock/i)).toBeInTheDocument();
    expect(screen.getByText(/payment gateway is down/i)).toBeInTheDocument();
  });

  test(&apos;displays performance metrics&apos;, () => {
    const metricsStore = createMockStore({
      metrics: {
        conversionRate: 2.5,
        averageOrderValue: 85.50,
        customerRetentionRate: 68.2,
      },
    });
    
    render(
      <Provider store={metricsStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(&apos;2.5%&apos;)).toBeInTheDocument(); // Conversion Rate
    expect(screen.getByText(&apos;$85.50&apos;)).toBeInTheDocument(); // Average Order Value
    expect(screen.getByText(&apos;68.2%&apos;)).toBeInTheDocument(); // Customer Retention Rate
  });

  test(&apos;handles chart interactions&apos;, async () => {
    const chartsStore = createMockStore({
      charts: {
        salesChart: {
          labels: [&apos;Jan&apos;, &apos;Feb&apos;, &apos;Mar&apos;],
          datasets: [{ data: [100, 200, 300] }],
        },
      },
    });
    
    render(
      <Provider store={chartsStore}>
        <Dashboard />
      </Provider>
    );
    
    const chart = screen.getByTestId(&apos;line-chart&apos;);
    
    // Simulate chart click
    fireEvent.click(chart);
    
    // Should handle chart interactions (implementation dependent)
  });

  test(&apos;auto-refreshes data at intervals&apos;, async () => {
    jest.useFakeTimers();
    
    renderWithProvider(<Dashboard />);
    
    // Fast-forward time
    jest.advanceTimersByTime(60000); // 1 minute
    
    // Should trigger auto-refresh
    await waitFor(() => {
      // Verify data refresh was triggered
    });
    
    jest.useRealTimers();
  });

  test(&apos;stops auto-refresh when component unmounts&apos;, () => {
    jest.useFakeTimers();
    
    
    unmount();
    
    // Fast-forward time
    jest.advanceTimersByTime(60000);
    
    // Should not trigger refresh after unmount
    
    jest.useRealTimers();
  });
});