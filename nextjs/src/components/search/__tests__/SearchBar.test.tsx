import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchBar } from '../SearchBar';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/utils/api';

// Mock the next/navigation router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock the API client
jest.mock('@/utils/api', () => ({
  apiClient: {
    get: jest.fn(),
  },
}));

// Mock the useDebounce hook
jest.mock('@/hooks/useDebounce', () => ({
  useDebounce: (value: any, delay: number) => value, // Return value immediately for testing
}));

describe('SearchBar Component', () => {
  const mockRouter = {
    push: jest.fn(),
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        suggestions: ['smartphone', 'smart tv', 'smartwatch'],
        products: [
          {
            id: '1',
            name: 'Smartphone X',
            slug: 'smartphone-x',
            price: 999.99,
            image: 'smartphone.jpg',
            category: 'Electronics'
          },
          {
            id: '2',
            name: 'Smart TV 55"',
            slug: 'smart-tv-55',
            price: 699.99,
            image: 'tv.jpg',
            category: 'Electronics'
          }
        ]
      }
    });
  });

  test('renders the search bar correctly', () => {
    render(<SearchBar />);
    
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search for products...')).toBeInTheDocument();
    expect(screen.getByLabelText('Search')).toBeInTheDocument();
  });

  test('handles input change and shows suggestions', async () => {
    render(<SearchBar />);
    
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'smart' } });
    
    // Wait for suggestions to appear
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(expect.stringContaining('q=smart'));
    });
    
    // Check if suggestions are displayed
    await waitFor(() => {
      expect(screen.getByText('Suggestions')).toBeInTheDocument();
      expect(screen.getByText('smartphone')).toBeInTheDocument();
      expect(screen.getByText('smart tv')).toBeInTheDocument();
      expect(screen.getByText('smartwatch')).toBeInTheDocument();
    });
    
    // Check if product suggestions are displayed
    await waitFor(() => {
      expect(screen.getByText('Products')).toBeInTheDocument();
      expect(screen.getByText('Smartphone X')).toBeInTheDocument();
      expect(screen.getByText('Smart TV 55"')).toBeInTheDocument();
    });
  });

  test('navigates to search results page on form submission', async () => {
    render(<SearchBar />);
    
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'smart' } });
    
    const form = input.closest('form');
    fireEvent.submit(form!);
    
    expect(mockRouter.push).toHaveBeenCalledWith('/products?search=smart');
  });

  test('navigates to product page when product suggestion is clicked', async () => {
    render(<SearchBar />);
    
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'smart' } });
    
    // Wait for suggestions to appear
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(expect.stringContaining('q=smart'));
    });
    
    // Click on a product suggestion
    const productSuggestion = await screen.findByText('Smartphone X');
    fireEvent.click(productSuggestion);
    
    expect(mockRouter.push).toHaveBeenCalledWith('/products/smartphone-x');
  });

  test('calls onSearch callback when provided', async () => {
    const mockOnSearch = jest.fn();
    render(<SearchBar onSearch={mockOnSearch} />);
    
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'smart' } });
    
    const form = input.closest('form');
    fireEvent.submit(form!);
    
    expect(mockOnSearch).toHaveBeenCalledWith('smart');
    expect(mockRouter.push).not.toHaveBeenCalled();
  });

  test('clears search input when clear button is clicked', async () => {
    render(<SearchBar />);
    
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'smart' } });
    
    // Clear button should appear
    const clearButton = screen.getByLabelText('Clear search');
    fireEvent.click(clearButton);
    
    expect(input).toHaveValue('');
  });

  test('handles API error gracefully', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: false,
      error: {
        message: 'Failed to fetch suggestions'
      }
    });
    
    render(<SearchBar />);
    
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'smart' } });
    
    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText('Failed to fetch suggestions')).toBeInTheDocument();
    });
  });
});