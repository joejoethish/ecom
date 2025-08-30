/**
 * Tests for ErrorAnalysisInterface Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ErrorAnalysisInterface } from '../ErrorAnalysisInterface';

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Doughnut: ({ data, options }: any) => (
    <div data-testid="doughnut-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Doughnut Chart
    </div>
  ),
  Bar: ({ data, options }: any) => (
    <div data-testid="bar-chart" data-chart-data={JSON.stringify(data)} data-chart-options={JSON.stringify(options)}>
      Bar Chart
    </div>
  ),
}));

// Mock fetch
global.fetch = jest.fn();

const mockErrorGroups = [
  {
    id: 'error-1',
    errorType: 'TypeError',
    errorMessage: 'Cannot read property of undefined',
    count: 25,
    firstSeen: '2024-01-01T10:00:00Z',
    lastSeen: '2024-01-01T12:00:00Z',
    affectedComponents: ['ProductList', 'CartComponent'],
    severity: 'high' as const,
    status: 'open' as const,
    resolutionSuggestions: [
      {
        type: 'code_fix' as const,
        title: 'Add null check',
        description: 'Add proper null checking before accessing properties',
        priority: 'high' as const,
        estimatedEffort: '1 hour',
        steps: ['Identify the undefined property', 'Add null check', 'Test the fix'],
      },
    ],
    recentOccurrences: [
      {
        id: 'occurrence-1',
        timestamp: '2024-01-01T12:00:00Z',
        correlationId: 'corr-1',
        layer: 'frontend' as const,
        component: 'ProductList',
        stackTrace: 'TypeError: Cannot read property...',
        metadata: {},
      },
    ],
  },
  {
    id: 'error-2',
    errorType: 'NetworkError',
    errorMessage: 'Failed to fetch',
    count: 10,
    firstSeen: '2024-01-01T11:00:00Z',
    lastSeen: '2024-01-01T11:30:00Z',
    affectedComponents: ['ApiClient'],
    severity: 'medium' as const,
    status: 'investigating' as const,
    resolutionSuggestions: [],
    recentOccurrences: [],
  },
];

const mockErrorAnalytics = {
  totalErrors: 35,
  errorsByLayer: {
    frontend: 20,
    api: 10,
    database: 5,
  },
  errorsByType: {
    TypeError: 25,
    NetworkError: 10,
  },
  errorTrends: [
    { date: '2024-01-01', count: 15 },
    { date: '2024-01-02', count: 20 },
  ],
  topComponents: [
    { component: 'ProductList', count: 15 },
    { component: 'CartComponent', count: 10 },
    { component: 'ApiClient', count: 10 },
  ],
};

describe('ErrorAnalysisInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/error-groups/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ results: mockErrorGroups }),
        });
      }
      if (url.includes('/error-analytics/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockErrorAnalytics),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it('renders loading state initially', () => {
    render(<ErrorAnalysisInterface />);
    
    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
  });

  it('fetches and displays error data', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      expect(screen.getByText('Error Analysis')).toBeInTheDocument();
    });

    expect(screen.getByText('Error Groups')).toBeInTheDocument();
    expect(screen.getByText('TypeError')).toBeInTheDocument();
    expect(screen.getByText('NetworkError')).toBeInTheDocument();
  });

  it('displays error analytics overview', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      expect(screen.getByText('35')).toBeInTheDocument(); // Total errors
      expect(screen.getByText('Error Overview')).toBeInTheDocument();
    });
  });

  it('renders analytics charts', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });
  });

  it('displays error groups with correct information', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      expect(screen.getByText('Cannot read property of undefined')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument(); // Error count
      expect(screen.getByText('HIGH')).toBeInTheDocument(); // Severity
      expect(screen.getByText('open')).toBeInTheDocument(); // Status
    });
  });

  it('allows filtering by severity', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const severitySelect = screen.getByDisplayValue('All Severities');
      fireEvent.change(severitySelect, { target: { value: 'high' } });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('severity=high'),
        expect.any(Object)
      );
    });
  });

  it('allows filtering by status', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const statusSelect = screen.getByDisplayValue('All Statuses');
      fireEvent.change(statusSelect, { target: { value: 'open' } });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('status=open'),
        expect.any(Object)
      );
    });
  });

  it('allows filtering by layer', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const layerSelect = screen.getByDisplayValue('All Layers');
      fireEvent.change(layerSelect, { target: { value: 'frontend' } });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('layer=frontend'),
        expect.any(Object)
      );
    });
  });

  it('allows filtering by time range', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const timeSelect = screen.getByDisplayValue('Last 24 Hours');
      fireEvent.change(timeSelect, { target: { value: '7d' } });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('time_range=7d'),
        expect.any(Object)
      );
    });
  });

  it('selects error group and shows details', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const errorGroup = screen.getByText('TypeError').closest('div');
      fireEvent.click(errorGroup!);
    });

    expect(screen.getByText('Trace Details')).toBeInTheDocument();
    expect(screen.getByText('Cannot read property of undefined')).toBeInTheDocument();
  });

  it('displays resolution suggestions', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const errorGroup = screen.getByText('TypeError').closest('div');
      fireEvent.click(errorGroup!);
    });

    expect(screen.getByText('Resolution Suggestions')).toBeInTheDocument();
    expect(screen.getByText('Add null check')).toBeInTheDocument();
    expect(screen.getByText('Add proper null checking before accessing properties')).toBeInTheDocument();
  });

  it('shows recent occurrences', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const errorGroup = screen.getByText('TypeError').closest('div');
      fireEvent.click(errorGroup!);
    });

    expect(screen.getByText('Recent Occurrences')).toBeInTheDocument();
    expect(screen.getByText('ProductList')).toBeInTheDocument();
    expect(screen.getByText('Correlation ID: corr-1')).toBeInTheDocument();
  });

  it('allows updating error status', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ ...mockErrorGroups[0], status: 'investigating' }),
    });

    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const errorGroup = screen.getByText('TypeError').closest('div');
      fireEvent.click(errorGroup!);
    });

    const investigatingButton = screen.getByText('Mark as investigating');
    fireEvent.click(investigatingButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/error-groups/error-1/'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ status: 'investigating' }),
        })
      );
    });
  });

  it('displays correct severity colors', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const highSeverity = screen.getByText('HIGH');
      expect(highSeverity.closest('span')).toHaveClass('text-red-700', 'bg-red-50', 'border-red-200');

      const mediumSeverity = screen.getByText('MEDIUM');
      expect(mediumSeverity.closest('span')).toHaveClass('text-yellow-700', 'bg-yellow-50', 'border-yellow-200');
    });
  });

  it('displays correct status colors', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const openStatus = screen.getByText('open');
      expect(openStatus.closest('span')).toHaveClass('text-red-700', 'bg-red-100');

      const investigatingStatus = screen.getByText('investigating');
      expect(investigatingStatus.closest('span')).toHaveClass('text-yellow-700', 'bg-yellow-100');
    });
  });

  it('shows stack trace in expandable details', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const errorGroup = screen.getByText('TypeError').closest('div');
      fireEvent.click(errorGroup!);
    });

    const stackTraceToggle = screen.getByText('View Stack Trace');
    expect(stackTraceToggle).toBeInTheDocument();
    
    fireEvent.click(stackTraceToggle);
    expect(screen.getByText('TypeError: Cannot read property...')).toBeInTheDocument();
  });

  it('handles fetch error gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();
  });

  it('shows refresh button', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      expect(refreshButton).toBeInTheDocument();
      
      fireEvent.click(refreshButton);
      expect(fetch).toHaveBeenCalledTimes(3); // Initial 2 calls + manual refresh
    });
  });

  it('displays empty state when no error group is selected', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      expect(screen.getByText('Select an error group to view details')).toBeInTheDocument();
    });
  });

  it('shows top components in overview', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      expect(screen.getByText('ProductList')).toBeInTheDocument();
      expect(screen.getByText('CartComponent')).toBeInTheDocument();
      expect(screen.getByText('ApiClient')).toBeInTheDocument();
    });
  });

  it('displays error metadata correctly', async () => {
    render(<ErrorAnalysisInterface />);

    await waitFor(() => {
      const errorGroup = screen.getByText('TypeError').closest('div');
      fireEvent.click(errorGroup!);
    });

    expect(screen.getByText('First Seen:')).toBeInTheDocument();
    expect(screen.getByText('Last Seen:')).toBeInTheDocument();
    expect(screen.getByText('Affected Components:')).toBeInTheDocument();
    expect(screen.getByText('Total Occurrences')).toBeInTheDocument();
  });
});