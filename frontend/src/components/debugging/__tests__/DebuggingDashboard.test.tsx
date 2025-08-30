/**
 * Tests for DebuggingDashboard Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { DebuggingDashboard } from '../DebuggingDashboard';

// Mock the hooks
jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: jest.fn(() => ({
    isConnected: true,
    sendMessage: jest.fn(),
    lastMessage: null,
  })),
}));

jest.mock('@/hooks/useCorrelationId', () => ({
  useCorrelationId: jest.fn(() => ({
    correlationId: 'test-correlation-id-123',
  })),
}));

// Mock the child components
jest.mock('../SystemHealthPanel', () => ({
  SystemHealthPanel: () => <div data-testid="system-health-panel">System Health Panel</div>,
}));

jest.mock('../WorkflowTraceVisualization', () => ({
  WorkflowTraceVisualization: () => <div data-testid="workflow-trace-panel">Workflow Trace Panel</div>,
}));

jest.mock('../DebuggingToolsInterface', () => ({
  DebuggingToolsInterface: () => <div data-testid="debugging-tools-panel">Debugging Tools Panel</div>,
}));

jest.mock('../ErrorAnalysisInterface', () => ({
  ErrorAnalysisInterface: () => <div data-testid="error-analysis-panel">Error Analysis Panel</div>,
}));

const mockStore = configureStore({
  reducer: {
    // Add minimal store structure if needed
  },
});

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <Provider store={mockStore}>
      {component}
    </Provider>
  );
};

describe('DebuggingDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the dashboard with all navigation tabs', () => {
    renderWithProvider(<DebuggingDashboard />);

    expect(screen.getByText('Debug Dashboard')).toBeInTheDocument();
    expect(screen.getByText('System Health')).toBeInTheDocument();
    expect(screen.getByText('Workflow Traces')).toBeInTheDocument();
    expect(screen.getByText('Debug Tools')).toBeInTheDocument();
    expect(screen.getByText('Error Analysis')).toBeInTheDocument();
  });

  it('shows connection status', () => {
    renderWithProvider(<DebuggingDashboard />);

    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('displays correlation ID', () => {
    renderWithProvider(<DebuggingDashboard />);

    expect(screen.getByText(/ID: test-cor/)).toBeInTheDocument();
  });

  it('switches between tabs correctly', () => {
    renderWithProvider(<DebuggingDashboard />);

    // Default tab should be System Health
    expect(screen.getByTestId('system-health-panel')).toBeInTheDocument();

    // Click on Workflow Traces tab
    fireEvent.click(screen.getByText('Workflow Traces'));
    expect(screen.getByTestId('workflow-trace-panel')).toBeInTheDocument();

    // Click on Debug Tools tab
    fireEvent.click(screen.getByText('Debug Tools'));
    expect(screen.getByTestId('debugging-tools-panel')).toBeInTheDocument();

    // Click on Error Analysis tab
    fireEvent.click(screen.getByText('Error Analysis'));
    expect(screen.getByTestId('error-analysis-panel')).toBeInTheDocument();
  });

  it('has refresh data button', () => {
    renderWithProvider(<DebuggingDashboard />);

    const refreshButton = screen.getByText('Refresh Data');
    expect(refreshButton).toBeInTheDocument();
    
    fireEvent.click(refreshButton);
    // Should call sendMessage with refresh_data type
  });

  it('has reset dashboard button', () => {
    renderWithProvider(<DebuggingDashboard />);

    const resetButton = screen.getByText('Reset Dashboard');
    expect(resetButton).toBeInTheDocument();
  });

  it('applies correct styling for active tab', () => {
    renderWithProvider(<DebuggingDashboard />);

    const healthTab = screen.getByText('System Health').closest('button');
    expect(healthTab).toHaveClass('bg-blue-50', 'border-r-2', 'border-blue-500', 'text-blue-700');

    // Switch to another tab
    fireEvent.click(screen.getByText('Workflow Traces'));
    
    const tracesTab = screen.getByText('Workflow Traces').closest('button');
    expect(tracesTab).toHaveClass('bg-blue-50', 'border-r-2', 'border-blue-500', 'text-blue-700');
  });

  it('handles WebSocket disconnection', () => {
    const { useWebSocket } = require('@/hooks/useWebSocket');
    useWebSocket.mockReturnValue({
      isConnected: false,
      sendMessage: jest.fn(),
      lastMessage: null,
    });

    renderWithProvider(<DebuggingDashboard />);

    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('renders with proper accessibility attributes', () => {
    renderWithProvider(<DebuggingDashboard />);

    // Check for proper button roles
    const tabs = screen.getAllByRole('button');
    expect(tabs.length).toBeGreaterThan(0);

    // Check for navigation structure
    const navigation = screen.getByRole('navigation', { hidden: true });
    expect(navigation).toBeInTheDocument();
  });

  it('maintains responsive layout classes', () => {
    renderWithProvider(<DebuggingDashboard />);

    const container = screen.getByText('Debug Dashboard').closest('div');
    expect(container?.parentElement).toHaveClass('w-64', 'bg-white', 'shadow-lg');
  });
});