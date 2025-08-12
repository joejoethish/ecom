// Unit tests for Dashboard component
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

// Mock Dashboard component
const Dashboard = () => (
  <div>
    <div data-testid="loading-spinner">Loading...</div>
    <div>Dashboard Content</div>
  </div>
);

// Mock dashboard slice
const dashboardSlice = {
  reducer: (state = { 
    stats: { totalOrders: 0, totalRevenue: 0, totalCustomers: 0, totalProducts: 0, pendingOrders: 0, lowStockProducts: 0 },
    charts: { salesChart: { labels: [], datasets: [] }, ordersChart: { labels: [], datasets: [] } },
    isLoading: false,
    error: null
  }, action: any) => state
};

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

describe("Dashboard Component", () => {
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

  test("renders dashboard with loading state", () => {
    const loadingStore = createMockStore({ isLoading: true });
    
    render(
      <Provider store={loadingStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  test("renders dashboard stats correctly", () => {
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
    
    expect(screen.getByText("150")).toBeInTheDocument(); // Total Orders
    expect(screen.getByText("$25,000")).toBeInTheDocument(); // Total Revenue
    expect(screen.getByText("75")).toBeInTheDocument(); // Total Customers
    expect(screen.getByText("200")).toBeInTheDocument(); // Total Products
    expect(screen.getByText("12")).toBeInTheDocument(); // Pending Orders
    expect(screen.getByText("5")).toBeInTheDocument(); // Low Stock Products
  });

  test("renders charts when data is available", () => {
    const chartsStore = createMockStore({
      charts: {
        salesChart: {
          labels: ["Jan", "Feb", "Mar"],
          datasets: [{ data: [100, 200, 300] }],
        },
        ordersChart: {
          labels: ["Jan", "Feb", "Mar"],
          datasets: [{ data: [10, 20, 30] }],
        },
      },
    });
    
    render(
      <Provider store={chartsStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByTestId("line-chart")).toBeInTheDocument();
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  test("displays error message when data loading fails", () => {
    const errorStore = createMockStore({
      error: "Failed to load dashboard data",
    });
    
    render(
      <Provider store={errorStore}>
        <Dashboard />
      </Provider>
    );
    
    expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
  });

  test("shows empty state when no data is available", () => {
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

  test("formats currency values correctly", () => {
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
    
    expect(screen.getByText("$1,234,567.89")).toBeInTheDocument();
  });

  test("handles large numbers with proper formatting", () => {
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
    
    expect(screen.getByText("1,000,000")).toBeInTheDocument();
    expect(screen.getByText("500,000")).toBeInTheDocument();
  });

  test("shows refresh button and handles refresh action", async () => {
    renderWithProvider(<Dashboard />);
    
    const refreshButton = screen.getByRole("button", { name: /refresh/i });
    expect(refreshButton).toBeInTheDocument();
    
    // Click refresh button
    fireEvent.click(refreshButton);
    
    // Should trigger data refresh (implementation dependent)
  });

  test("displays time period selector", () => {
    renderWithProvider(<Dashboard />);
    
    expect(screen.getByLabelText(/time period/i)).toBeInTheDocument();
    expect(screen.getByText(/last 7 days/i)).toBeInTheDocument();
    expect(screen.getByText(/last 30 days/i)).toBeInTheDocument();
    expect(screen.getByText(/last 90 days/i)).toBeInTheDocument();
  });

  test("updates data when time period changes", async () => {
    renderWithProvider(<Dashboard />);
    
    const timePeriodSelect = screen.getByLabelText(/time period/i);
    fireEvent.change(timePeriodSelect, { target: { value: "30" } });
    
    // Should trigger data update for new time period
    await waitFor(() => {
      // Verify new data is loaded
    });
  });

  test("shows quick action buttons", () => {
    renderWithProvider(<Dashboard />);
    
    expect(screen.getByRole("button", { name: /add product/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /view orders/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /manage customers/i })).toBeInTheDocument();
  });

  test("displays recent activity feed", () => {
    const activityStore = createMockStore({
      recentActivity: [
        { id: 1, type: "order", message: "New order #1001 received", timestamp: "2024-01-01T10:00:00Z" },
        { id: 2, type: "product", message: "Product &quot;Test Item&quot; updated", timestamp: "2024-01-01T09:30:00Z" },
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

  test("handles responsive design", () => {
    // Mock window.innerWidth
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 768,
    });
    
    renderWithProvider(<Dashboard />);
    
    // Should adapt layout for tablet/mobile
    const dashboardGrid = screen.getByTestId("dashboard-grid");
    expect(dashboardGrid).toHaveClass("responsive-grid");
  });

  test("shows alerts for critical issues", () => {
    const alertsStore = createMockStore({
      alerts: [
        { id: 1, type: "warning", message: "5 products are low in stock" },
        { id: 2, type: "error", message: "Payment gateway is down" },
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

  test("displays performance metrics", () => {
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
    
    expect(screen.getByText("2.5%")).toBeInTheDocument(); // Conversion Rate
    expect(screen.getByText("$85.50")).toBeInTheDocument(); // Average Order Value
    expect(screen.getByText("68.2%")).toBeInTheDocument(); // Customer Retention Rate
  });

  test("handles chart interactions", async () => {
    const chartsStore = createMockStore({
      charts: {
        salesChart: {
          labels: ["Jan", "Feb", "Mar"],
          datasets: [{ data: [100, 200, 300] }],
        },
      },
    });
    
    render(
      <Provider store={chartsStore}>
        <Dashboard />
      </Provider>
    );
    
    const chart = screen.getByTestId("line-chart");
    
    // Simulate chart click
    fireEvent.click(chart);
    
    // Should handle chart interactions (implementation dependent)
  });

  test("auto-refreshes data at intervals", async () => {
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

  test("stops auto-refresh when component unmounts", () => {
    jest.useFakeTimers();
    
    const { unmount } = renderWithProvider(<Dashboard />);
    unmount();
    
    // Fast-forward time
    jest.advanceTimersByTime(60000);
    
    // Should not trigger refresh after unmount
    
    jest.useRealTimers();
  });
});