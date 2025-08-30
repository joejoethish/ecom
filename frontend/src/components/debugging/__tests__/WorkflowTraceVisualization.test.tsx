/**
 * Tests for WorkflowTraceVisualization Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkflowTraceVisualization } from '../WorkflowTraceVisualization';

// Mock ReactFlow
jest.mock('reactflow', () => ({
  __esModule: true,
  default: ({ nodes, edges, children }: any) => (
    <div data-testid="react-flow" data-nodes={JSON.stringify(nodes)} data-edges={JSON.stringify(edges)}>
      React Flow
      {children}
    </div>
  ),
  useNodesState: jest.fn(() => [[], jest.fn(), jest.fn()]),
  useEdgesState: jest.fn(() => [[], jest.fn(), jest.fn()]),
  addEdge: jest.fn(),
  Controls: () => <div data-testid="flow-controls">Controls</div>,
  MiniMap: () => <div data-testid="flow-minimap">MiniMap</div>,
  Background: () => <div data-testid="flow-background">Background</div>,
  Panel: ({ children }: any) => <div data-testid="flow-panel">{children}</div>,
}));

// Mock fetch
global.fetch = jest.fn();

const mockWorkflowTraces = [
  {
    correlationId: 'trace-1',
    workflowType: 'user_login',
    startTime: '2024-01-01T12:00:00Z',
    endTime: '2024-01-01T12:00:02Z',
    status: 'completed' as const,
    totalDuration: 2000,
    steps: [
      {
        id: 'step-1',
        layer: 'frontend' as const,
        component: 'LoginForm',
        operation: 'submit',
        startTime: '2024-01-01T12:00:00Z',
        endTime: '2024-01-01T12:00:01Z',
        duration: 1000,
        status: 'completed' as const,
      },
      {
        id: 'step-2',
        layer: 'api' as const,
        component: 'AuthAPI',
        operation: 'authenticate',
        startTime: '2024-01-01T12:00:01Z',
        endTime: '2024-01-01T12:00:02Z',
        duration: 1000,
        status: 'completed' as const,
      },
    ],
    errors: [],
  },
  {
    correlationId: 'trace-2',
    workflowType: 'product_fetch',
    startTime: '2024-01-01T12:01:00Z',
    status: 'failed' as const,
    steps: [
      {
        id: 'step-3',
        layer: 'frontend' as const,
        component: 'ProductList',
        operation: 'load',
        startTime: '2024-01-01T12:01:00Z',
        status: 'failed' as const,
      },
    ],
    errors: [
      {
        timestamp: '2024-01-01T12:01:00Z',
        component: 'ProductList',
        error: 'Network timeout',
      },
    ],
  },
];

describe('WorkflowTraceVisualization', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ results: mockWorkflowTraces }),
    });
  });

  it('renders loading state initially', () => {
    render(<WorkflowTraceVisualization />);
    
    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
  });

  it('fetches and displays workflow traces', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      expect(screen.getByText('Workflow Traces')).toBeInTheDocument();
    });

    expect(screen.getByText('user_login')).toBeInTheDocument();
    expect(screen.getByText('product_fetch')).toBeInTheDocument();
  });

  it('displays trace status correctly', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('failed')).toBeInTheDocument();
    });
  });

  it('shows correlation IDs', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      expect(screen.getByText('ID: trace-1')).toBeInTheDocument();
      expect(screen.getByText('ID: trace-2')).toBeInTheDocument();
    });
  });

  it('allows filtering by workflow type', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const workflowSelect = screen.getByDisplayValue('All Workflow Types');
      fireEvent.change(workflowSelect, { target: { value: 'user_login' } });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('workflow_type=user_login'),
        expect.any(Object)
      );
    });
  });

  it('allows filtering by status', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const statusSelect = screen.getByDisplayValue('All Statuses');
      fireEvent.change(statusSelect, { target: { value: 'completed' } });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('status=completed'),
        expect.any(Object)
      );
    });
  });

  it('allows filtering by time range', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const timeSelect = screen.getByDisplayValue('Last Hour');
      fireEvent.change(timeSelect, { target: { value: '24h' } });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('time_range=24h'),
        expect.any(Object)
      );
    });
  });

  it('selects trace and shows details', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const traceItem = screen.getByText('user_login').closest('div');
      fireEvent.click(traceItem!);
    });

    expect(screen.getByText('Trace Details')).toBeInTheDocument();
    expect(screen.getByText('trace-1')).toBeInTheDocument();
  });

  it('displays trace duration', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      expect(screen.getByText('2.00s')).toBeInTheDocument();
    });
  });

  it('shows error count for failed traces', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      expect(screen.getByText('1 error(s)')).toBeInTheDocument();
    });
  });

  it('renders ReactFlow visualization when trace is selected', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const traceItem = screen.getByText('user_login').closest('div');
      fireEvent.click(traceItem!);
    });

    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    expect(screen.getByTestId('flow-controls')).toBeInTheDocument();
    expect(screen.getByTestId('flow-minimap')).toBeInTheDocument();
    expect(screen.getByTestId('flow-background')).toBeInTheDocument();
  });

  it('displays step timeline', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const traceItem = screen.getByText('user_login').closest('div');
      fireEvent.click(traceItem!);
    });

    expect(screen.getByText('Step Timeline')).toBeInTheDocument();
    expect(screen.getByText('LoginForm - submit')).toBeInTheDocument();
    expect(screen.getByText('AuthAPI - authenticate')).toBeInTheDocument();
  });

  it('shows errors section for failed traces', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const traceItem = screen.getByText('product_fetch').closest('div');
      fireEvent.click(traceItem!);
    });

    expect(screen.getByText('Errors')).toBeInTheDocument();
    expect(screen.getByText('Network timeout')).toBeInTheDocument();
  });

  it('handles fetch error gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();
  });

  it('shows refresh button', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const refreshButton = screen.getByText('Refresh');
      expect(refreshButton).toBeInTheDocument();
      
      fireEvent.click(refreshButton);
      expect(fetch).toHaveBeenCalledTimes(2); // Initial load + manual refresh
    });
  });

  it('displays trace metadata correctly', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const traceItem = screen.getByText('user_login').closest('div');
      fireEvent.click(traceItem!);
    });

    expect(screen.getByText('Workflow Type:')).toBeInTheDocument();
    expect(screen.getByText('Status:')).toBeInTheDocument();
    expect(screen.getByText('Correlation ID:')).toBeInTheDocument();
    expect(screen.getByText('Duration:')).toBeInTheDocument();
    expect(screen.getByText('Steps:')).toBeInTheDocument();
    expect(screen.getByText('Errors:')).toBeInTheDocument();
  });

  it('shows layer legend in flow panel', async () => {
    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      const traceItem = screen.getByText('user_login').closest('div');
      fireEvent.click(traceItem!);
    });

    expect(screen.getByText('Frontend')).toBeInTheDocument();
    expect(screen.getByText('API')).toBeInTheDocument();
    expect(screen.getByText('Database')).toBeInTheDocument();
  });

  it('handles empty trace list', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ results: [] }),
    });

    render(<WorkflowTraceVisualization />);

    await waitFor(() => {
      expect(screen.getByText('Workflow Traces')).toBeInTheDocument();
    });

    // Should show empty state or no traces
    expect(screen.queryByText('user_login')).not.toBeInTheDocument();
  });
});