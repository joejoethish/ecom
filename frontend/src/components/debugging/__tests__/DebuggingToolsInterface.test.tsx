/**
 * Tests for DebuggingToolsInterface Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DebuggingToolsInterface } from '../DebuggingToolsInterface';

// Mock the correlation ID hook
jest.mock('@/hooks/useCorrelationId', () => ({
  useCorrelationId: jest.fn(() => ({
    correlationId: 'test-correlation-id-123',
  })),
}));

// Mock fetch
global.fetch = jest.fn();

const mockApiEndpoints = [
  {
    path: '/api/v1/products/',
    method: 'GET',
    description: 'List all products',
    parameters: [
      {
        name: 'page',
        type: 'number' as const,
        required: false,
        description: 'Page number',
        example: 1,
      },
    ],
    authentication: true,
    permissions: ['view_products'],
  },
  {
    path: '/api/v1/products/',
    method: 'POST',
    description: 'Create a new product',
    parameters: [
      {
        name: 'name',
        type: 'string' as const,
        required: true,
        description: 'Product name',
        example: 'Test Product',
      },
      {
        name: 'price',
        type: 'number' as const,
        required: true,
        description: 'Product price',
        example: 99.99,
      },
    ],
    authentication: true,
    permissions: ['add_products'],
  },
];

const mockReplayableRequests = [
  {
    correlationId: 'replay-1',
    originalRequest: {
      method: 'GET',
      url: '/api/v1/products/',
      headers: {
        'Content-Type': 'application/json',
      },
    },
  },
  {
    correlationId: 'replay-2',
    originalRequest: {
      method: 'POST',
      url: '/api/v1/products/',
      headers: {
        'Content-Type': 'application/json',
      },
      payload: {
        name: 'Test Product',
        price: 99.99,
      },
    },
  },
];

describe('DebuggingToolsInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock API endpoints fetch
    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api-endpoints/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ results: mockApiEndpoints }),
        });
      }
      if (url.includes('/replayable-requests/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ results: mockReplayableRequests }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it('renders with API Testing tab active by default', async () => {
    render(<DebuggingToolsInterface />);

    expect(screen.getByText('API Testing')).toBeInTheDocument();
    expect(screen.getByText('Request Replay')).toBeInTheDocument();
    expect(screen.getByText('Payload Editor')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('API Endpoint Testing')).toBeInTheDocument();
    });
  });

  it('fetches and displays API endpoints', async () => {
    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      expect(screen.getByText('List all products')).toBeInTheDocument();
      expect(screen.getByText('Create a new product')).toBeInTheDocument();
    });
  });

  it('allows selecting an endpoint', async () => {
    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const endpoint = screen.getByText('List all products').closest('div');
      fireEvent.click(endpoint!);
    });

    const endpointInput = screen.getByDisplayValue('/api/v1/products/');
    expect(endpointInput).toBeInTheDocument();

    const methodSelect = screen.getByDisplayValue('GET');
    expect(methodSelect).toBeInTheDocument();
  });

  it('generates payload for POST endpoints', async () => {
    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const postEndpoint = screen.getByText('Create a new product').closest('div');
      fireEvent.click(postEndpoint!);
    });

    const methodSelect = screen.getByDisplayValue('POST');
    expect(methodSelect).toBeInTheDocument();

    // Should show payload textarea for POST method
    expect(screen.getByPlaceholderText('{}')).toBeInTheDocument();
  });

  it('allows manual endpoint configuration', async () => {
    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const endpointInput = screen.getByPlaceholderText('/api/v1/example');
      fireEvent.change(endpointInput, { target: { value: '/api/v1/custom/' } });
      expect(endpointInput).toHaveValue('/api/v1/custom/');
    });
  });

  it('allows changing HTTP method', async () => {
    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const methodSelect = screen.getByDisplayValue('GET');
      fireEvent.change(methodSelect, { target: { value: 'POST' } });
      expect(methodSelect).toHaveValue('POST');
    });
  });

  it('executes API test', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: () => Promise.resolve({ success: true }),
      headers: new Map([['X-Correlation-ID', 'test-id']]),
    });

    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const executeButton = screen.getByText('Execute Test');
      fireEvent.click(executeButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Test Results')).toBeInTheDocument();
    });
  });

  it('displays test results', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: () => Promise.resolve({ data: 'test response' }),
      headers: new Map([['X-Correlation-ID', 'test-id']]),
    });

    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const endpointInput = screen.getByPlaceholderText('/api/v1/example');
      fireEvent.change(endpointInput, { target: { value: '/api/v1/test/' } });
      
      const executeButton = screen.getByText('Execute Test');
      fireEvent.click(executeButton);
    });

    await waitFor(() => {
      expect(screen.getByText('200')).toBeInTheDocument();
      expect(screen.getByText('OK')).toBeInTheDocument();
    });
  });

  it('switches to Request Replay tab', async () => {
    render(<DebuggingToolsInterface />);

    fireEvent.click(screen.getByText('Request Replay'));

    await waitFor(() => {
      expect(screen.getByText('Recent Requests')).toBeInTheDocument();
    });
  });

  it('displays replayable requests', async () => {
    render(<DebuggingToolsInterface />);

    fireEvent.click(screen.getByText('Request Replay'));

    await waitFor(() => {
      expect(screen.getByText('GET /api/v1/products/')).toBeInTheDocument();
      expect(screen.getByText('POST /api/v1/products/')).toBeInTheDocument();
    });
  });

  it('allows selecting a request for replay', async () => {
    render(<DebuggingToolsInterface />);

    fireEvent.click(screen.getByText('Request Replay'));

    await waitFor(() => {
      const request = screen.getByText('GET /api/v1/products/').closest('div');
      fireEvent.click(request!);
    });

    expect(screen.getByText('Original Request')).toBeInTheDocument();
    expect(screen.getByText('Header Modifications (JSON)')).toBeInTheDocument();
    expect(screen.getByText('Payload Modifications (JSON)')).toBeInTheDocument();
  });

  it('switches to Payload Editor tab', () => {
    render(<DebuggingToolsInterface />);

    fireEvent.click(screen.getByText('Payload Editor'));

    expect(screen.getByText('Payload Editor & Validator')).toBeInTheDocument();
    expect(screen.getByText('JSON Payload')).toBeInTheDocument();
    expect(screen.getByText('Schema Validation')).toBeInTheDocument();
  });

  it('shows payload editor buttons', () => {
    render(<DebuggingToolsInterface />);

    fireEvent.click(screen.getByText('Payload Editor'));

    expect(screen.getByText('Validate JSON')).toBeInTheDocument();
    expect(screen.getByText('Format JSON')).toBeInTheDocument();
    expect(screen.getByText('Minify JSON')).toBeInTheDocument();
  });

  it('handles API test error', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const endpointInput = screen.getByPlaceholderText('/api/v1/example');
      fireEvent.change(endpointInput, { target: { value: '/api/v1/test/' } });
      
      const executeButton = screen.getByText('Execute Test');
      fireEvent.click(executeButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Network Error')).toBeInTheDocument();
    });
  });

  it('disables execute button when no endpoint is provided', async () => {
    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const executeButton = screen.getByText('Execute Test');
      expect(executeButton).toBeDisabled();
    });
  });

  it('shows loading state during API test', async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    (global.fetch as jest.Mock).mockReturnValueOnce(promise);

    render(<DebuggingToolsInterface />);

    await waitFor(() => {
      const endpointInput = screen.getByPlaceholderText('/api/v1/example');
      fireEvent.change(endpointInput, { target: { value: '/api/v1/test/' } });
      
      const executeButton = screen.getByText('Execute Test');
      fireEvent.click(executeButton);
    });

    expect(screen.getByText('Testing...')).toBeInTheDocument();

    // Resolve the promise
    resolvePromise!({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: () => Promise.resolve({}),
      headers: new Map(),
    });

    await waitFor(() => {
      expect(screen.getByText('Execute Test')).toBeInTheDocument();
    });
  });

  it('applies correct tab styling', () => {
    render(<DebuggingToolsInterface />);

    const activeTab = screen.getByText('API Testing');
    expect(activeTab).toHaveClass('border-blue-500', 'text-blue-600');

    const inactiveTab = screen.getByText('Request Replay');
    expect(inactiveTab).toHaveClass('border-transparent', 'text-gray-500');
  });
});