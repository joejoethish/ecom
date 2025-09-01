import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchAutocomplete } from '../SearchAutocomplete';
import { apiClient } from '@/utils/api';

// Mock the API client
jest.mock('@/utils/api', () => ({
    apiClient: {
        get: jest.fn(),
    },
}));

// Mock Next.js router
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: mockPush,
    }),
}));

// Mock debounce hook
jest.mock('@/hooks/useDebounce', () => ({
    useDebounce: (value: string) => value,
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('SearchAutocomplete', () => {
    const mockOnSelect = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders search input with placeholder', () => {
        render(
            <SearchAutocomplete
                onSelect={mockOnSelect}
                placeholder="Search products..."
            />
        );

        expect(screen.getByPlaceholderText('Search products...')).toBeInTheDocument();
    });

    it('shows loading state when searching', async () => {
        mockApiClient.get.mockImplementation(() => new Promise(() => { })); // Never resolves

        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText('Loading suggestions...')).toBeInTheDocument();
        });
    });

    it('displays suggestions when API returns data', async () => {
        const mockResponse = {
            success: true,
            data: {
                suggestions: ['Test Product', 'Test Category'],
                products: [
                    {
                        id: '1',
                        name: 'Test Product 1',
                        slug: 'test-product-1',
                        price: 29.99,
                        image: 'test-image.jpg',
                        category: 'Electronics'
                    }
                ],
                query: 'test'
            }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText((content, element) => {
                return element?.textContent === 'Test Product';
            })).toBeInTheDocument();
            expect(screen.getByText((content, element) => {
                return element?.textContent === 'Test Category';
            })).toBeInTheDocument();
            expect(screen.getByText((content, element) => {
                return element?.textContent === 'Test Product 1';
            })).toBeInTheDocument();
        });
    });

    it('handles API errors gracefully', async () => {
        const mockResponse = {
            success: false,
            error: {
                message: 'API Error',
                code: 'API_ERROR',
                status_code: 500
            }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText('API Error')).toBeInTheDocument();
        });
    });

    it('calls onSelect when suggestion is clicked', async () => {
        const mockResponse = {
            success: true,
            data: {
                suggestions: ['Test Product'],
                products: [],
                query: 'test'
            }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText((content, element) => {
                return element?.textContent === 'Test Product';
            })).toBeInTheDocument();
        });

        const suggestionElement = screen.getByText((content, element) => {
            return element?.textContent === 'Test Product';
        });
        await userEvent.click(suggestionElement);

        expect(mockOnSelect).toHaveBeenCalledWith({
            id: 'text-Test Product',
            type: 'category',
            name: 'Test Product',
            url: '/products?search=Test%20Product'
        });
    });

    it('supports keyboard navigation', async () => {
        const mockResponse = {
            success: true,
            data: {
                suggestions: ['Test Product 1', 'Test Product 2'],
                products: [],
                query: 'test'
            }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText('Test Product 1')).toBeInTheDocument();
        });

        // Test arrow down navigation
        fireEvent.keyDown(input, { key: 'ArrowDown' });
        expect(input).toHaveAttribute('aria-activedescendant', 'suggestion-0');

        fireEvent.keyDown(input, { key: 'ArrowDown' });
        expect(input).toHaveAttribute('aria-activedescendant', 'suggestion-1');

        // Test Enter key selection
        fireEvent.keyDown(input, { key: 'Enter' });

        expect(mockOnSelect).toHaveBeenCalledWith({
            id: 'text-Test Product 2',
            type: 'category',
            name: 'Test Product 2',
            url: '/products?search=Test%20Product%202'
        });
    });

    it('closes dropdown on Escape key', async () => {
        const mockResponse = {
            success: true,
            data: {
                suggestions: ['Test Product'],
                products: [],
                query: 'test'
            }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText('Test Product')).toBeInTheDocument();
        });

        fireEvent.keyDown(input, { key: 'Escape' });

        expect(input).toHaveAttribute('aria-expanded', 'false');
    });

    it('does not show suggestions for queries less than 2 characters', async () => {
        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 't');

        // Wait a bit to ensure no API call is made
        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 100));
        });

        expect(mockApiClient.get).not.toHaveBeenCalled();
    });

    it('closes dropdown when clicking outside', async () => {
        const mockResponse = {
            success: true,
            data: {
                suggestions: ['Test Product'],
                products: [],
                query: 'test'
            }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        render(
            <div>
                <SearchAutocomplete onSelect={mockOnSelect} />
                <div data-testid="outside">Outside element</div>
            </div>
        );

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText('Test Product')).toBeInTheDocument();
        });

        // Click outside
        await userEvent.click(screen.getByTestId('outside'));

        expect(input).toHaveAttribute('aria-expanded', 'false');
    });

    it('highlights matching text in suggestions', async () => {
        const mockResponse = {
            success: true,
            data: {
                suggestions: ['Test Product'],
                products: [],
                query: 'test'
            }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test');

        await waitFor(() => {
            const highlightedText = screen.getByText('Test Product').querySelector('.font-semibold.text-blue-600');
            expect(highlightedText).toBeInTheDocument();
        });
    });

    it('handles search submission with Enter key when no suggestion is selected', async () => {
        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test query');

        fireEvent.keyDown(input, { key: 'Enter' });

        expect(mockOnSelect).toHaveBeenCalledWith({
            id: 'search-test query',
            type: 'category',
            name: 'test query',
            url: '/products?search=test%20query'
        });
    });

    it('handles search button click', async () => {
        render(<SearchAutocomplete onSelect={mockOnSelect} />);

        const input = screen.getByRole('combobox');
        await userEvent.type(input, 'test query');

        const searchButton = screen.getByRole('button', { name: 'Search' });
        await userEvent.click(searchButton);

        expect(mockOnSelect).toHaveBeenCalledWith({
            id: 'search-test query',
            type: 'category',
            name: 'test query',
            url: '/products?search=test%20query'
        });
    });
});