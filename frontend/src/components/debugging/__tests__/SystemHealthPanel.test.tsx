/**
 * Tests for SystemHealthPanel Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SystemHealthPanel } from '../SystemHealthPanel';

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }: any) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Line Chart
    </div>
  ),
  Doughnut: ({ data, options }: any) => (
    <div data-testid="doughnut-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Doughnut Chart
    </div>
  ),
}));

// Mock fetch
global.fetch = jest.fn();

const mockSystemMetrics = {
  frontend: {
    status: 'healthy' as const,
    responseTime: 150,
    errorRate: 0.5,
    activeUsers: 25,
    memoryUsage: 128,
  },
  backend: {
    status: 'warning' as const,
    responseTime: 800,
    errorRate: 1.2,
    activeConnections: 45,
    cpuUsage: 65,
  },
  database: {
    status: 'error' as const,
    queryTime: 1200,
    connectionPool: 85,
    slowQueries: 5,
    diskUsage: 78,
  },
  timestamp: '2024-01-01T12:00:00Z',
};

describe('SystemHealthPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSystemMetrics),
    });
  });

  it('renders loading state initially', () => {
    render(<SystemHealthPanel />);
    
    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
  });

  it('fetches and displays system metrics', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      expect(screen.getByText('System Health Monitor')).toBeInTheDocument();
    });

    expect(screen.getByText('Frontend')).toBeInTheDocument();
    expect(screen.getByText('Backend')).toBeInTheDocument();
    expect(screen.getByText('Database')).toBeInTheDocument();
  });

  it('displays correct status indicators', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      expect(screen.getByText('Healthy')).toBeInTheDocument();
      expect(screen.getByText('Warning')).toBeInTheDocument();
      expect(screen.getByText('Error')).toBeInTheDocument();
    });
  });

  it('shows metric values correctly', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      expect(screen.getByText('150.0ms')).toBeInTheDocument(); // Frontend response time
      expect(screen.getByText('800.0ms')).toBeInTheDocument(); // Backend response time
      expect(screen.getByText('1200.0ms')).toBeInTheDocument(); // Database query time
    });
  });

  it('displays system information', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      expect(screen.getByText('25')).toBeInTheDocument(); // Active users
      expect(screen.getByText('45')).toBeInTheDocument(); // Active connections
      expect(screen.getByText('5')).toBeInTheDocument(); // Slow queries
    });
  });

  it('allows changing refresh interval', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      const select = screen.getByDisplayValue('5s refresh');
      fireEvent.change(select, { target: { value: '10000' } });
      expect(select).toHaveValue('10000');
    });
  });

  it('has refresh now button', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh Now');
      expect(refreshButton).toBeInTheDocument();
      
      fireEvent.click(refreshButton);
      expect(fetch).toHaveBeenCalledTimes(2); // Initial load + manual refresh
    });
  });

  it('renders charts when data is available', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
    });
  });

  it('handles fetch error gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<SystemHealthPanel />);

    await waitFor(() => {
      expect(screen.getByText('Error loading system metrics')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();
  });

  it('displays last updated timestamp', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  it('shows progress bars for metrics', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      const progressBars = screen.getAllByRole('progressbar', { hidden: true });
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  it('applies correct color coding for status', async () => {
    render(<SystemHealthPanel />);

    await waitFor(() => {
      const healthyStatus = screen.getByText('Healthy');
      expect(healthyStatus.closest('div')).toHaveClass('text-green-600', 'bg-green-100');

      const warningStatus = screen.getByText('Warning');
      expect(warningStatus.closest('div')).toHaveClass('text-yellow-600', 'bg-yellow-100');

      const errorStatus = screen.getByText('Error');
      expect(errorStatus.closest('div')).toHaveClass('text-red-600', 'bg-red-100');
    });
  });

  it('updates historical data for charts', async () => {
    render(<SystemHealthPanel />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('System Health Monitor')).toBeInTheDocument();
    });

    // Simulate another data fetch (would happen on interval)
    const updatedMetrics = {
      ...mockSystemMetrics,
      frontend: { ...mockSystemMetrics.frontend, responseTime: 200 },
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(updatedMetrics),
    });

    // Trigger manual refresh
    const refreshButton = screen.getByText('Refresh Now');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(screen.getByText('200.0ms')).toBeInTheDocument();
    });
  });

  it('handles HTTP error responses', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
    });

    render(<SystemHealthPanel />);

    await waitFor(() => {
      expect(screen.getByText('Error loading system metrics')).toBeInTheDocument();
      expect(screen.getByText('HTTP error! status: 500')).toBeInTheDocument();
    });
  });
});