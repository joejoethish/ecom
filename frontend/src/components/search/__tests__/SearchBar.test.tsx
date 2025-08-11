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
jest.mock(&apos;@/utils/api&apos;, () => ({
  apiClient: {
    get: jest.fn(),
  },
}));

// Mock the useDebounce hook
jest.mock(&apos;@/hooks/useDebounce&apos;, () => ({
  useDebounce: (value: string) => value, // Return value immediately for testing
}));

describe(&apos;SearchBar Component&apos;, () => {
  const mockRouter = {
    push: jest.fn(),
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        suggestions: [&apos;smartphone&apos;, &apos;smart tv&apos;, &apos;smartwatch&apos;],
        products: [
          {
            id: &apos;1&apos;,
            name: &apos;Smartphone X&apos;,
            slug: &apos;smartphone-x&apos;,
            price: 999.99,
            image: &apos;smartphone.jpg&apos;,
            category: &apos;Electronics&apos;
          },
          {
            id: &apos;2&apos;,
            name: &apos;Smart TV 55&quot;&apos;,
            slug: &apos;smart-tv-55&apos;,
            price: 699.99,
            image: &apos;tv.jpg&apos;,
            category: &apos;Electronics&apos;
          }
        ]
      }
    });
  });

  test(&apos;renders the search bar correctly&apos;, () => {
    render(<SearchBar />);
    
    expect(screen.getByRole(&apos;combobox&apos;)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(&apos;Search for products...&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(&apos;Search&apos;)).toBeInTheDocument();
  });

  test(&apos;handles input change and shows suggestions&apos;, async () => {
    render(<SearchBar />);
    
    const input = screen.getByRole(&apos;combobox&apos;);
    fireEvent.change(input, { target: { value: &apos;smart&apos; } });
    
    // Wait for suggestions to appear
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(expect.stringContaining(&apos;q=smart&apos;));
    });
    
    // Check if suggestions are displayed
    await waitFor(() => {
      expect(screen.getByText(&apos;Suggestions&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;smartphone&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;smart tv&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;smartwatch&apos;)).toBeInTheDocument();
    });
    
    // Check if product suggestions are displayed
    await waitFor(() => {
      expect(screen.getByText(&apos;Products&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Smartphone X&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Smart TV 55&quot;&apos;)).toBeInTheDocument();
    });
  });

  test(&apos;navigates to search results page on form submission&apos;, async () => {
    render(<SearchBar />);
    
    const input = screen.getByRole(&apos;combobox&apos;);
    fireEvent.change(input, { target: { value: &apos;smart&apos; } });
    
    const form = input.closest(&apos;form&apos;);
    fireEvent.submit(form!);
    
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products?search=smart&apos;);
  });

  test(&apos;navigates to product page when product suggestion is clicked&apos;, async () => {
    render(<SearchBar />);
    
    const input = screen.getByRole(&apos;combobox&apos;);
    fireEvent.change(input, { target: { value: &apos;smart&apos; } });
    
    // Wait for suggestions to appear
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(expect.stringContaining(&apos;q=smart&apos;));
    });
    
    // Click on a product suggestion
    const productSuggestion = await screen.findByText(&apos;Smartphone X&apos;);
    fireEvent.click(productSuggestion);
    
    expect(mockRouter.push).toHaveBeenCalledWith(&apos;/products/smartphone-x&apos;);
  });

  test(&apos;calls onSearch callback when provided&apos;, async () => {
    const mockOnSearch = jest.fn();
    render(<SearchBar onSearch={mockOnSearch} />);
    
    const input = screen.getByRole(&apos;combobox&apos;);
    fireEvent.change(input, { target: { value: &apos;smart&apos; } });
    
    const form = input.closest(&apos;form&apos;);
    fireEvent.submit(form!);
    
    expect(mockOnSearch).toHaveBeenCalledWith(&apos;smart&apos;);
    expect(mockRouter.push).not.toHaveBeenCalled();
  });

  test(&apos;clears search input when clear button is clicked&apos;, async () => {
    render(<SearchBar />);
    
    const input = screen.getByRole(&apos;combobox&apos;);
    fireEvent.change(input, { target: { value: &apos;smart&apos; } });
    
    // Clear button should appear
    const clearButton = screen.getByLabelText(&apos;Clear search&apos;);
    fireEvent.click(clearButton);
    
    expect(input).toHaveValue(&apos;&apos;);
  });

  test(&apos;handles API error gracefully&apos;, async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({
      success: false,
      error: {
        message: &apos;Failed to fetch suggestions&apos;
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