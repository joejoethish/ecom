/**
 * React hooks for products data
 */
import { useState, useEffect } from 'react';
import { productsApi, Product, CategoryProductsResponse, SearchProductsResponse } from '@/services/productsApi';

interface UseProductsOptions {
  featured?: boolean;
  autoFetch?: boolean;
}

interface UseProductsReturn {
  products: Product[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useProducts = (options: UseProductsOptions = {}): UseProductsReturn => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await productsApi.getFeaturedProducts();
      if (response.success && response.data) {
        setProducts(response.data);
      } else {
        setError(response.error?.message || 'Failed to fetch products');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (options.autoFetch) {
      fetchProducts();
    }
  }, [options.autoFetch]);

  return {
    products,
    loading,
    error,
    refetch: fetchProducts,
  };
};

interface UseCategoryProductsOptions {
  categorySlug: string;
  filters?: {
    min_price?: number;
    max_price?: number;
    brand?: string;
    sort?: 'name' | 'price_low' | 'price_high' | 'rating' | 'newest';
  };
  autoFetch?: boolean;
}

interface UseCategoryProductsReturn {
  products: Product[];
  category: CategoryProductsResponse['category'] | null;
  totalCount: number;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useCategoryProducts = (options: UseCategoryProductsOptions): UseCategoryProductsReturn => {
  const [products, setProducts] = useState<Product[]>([]);
  const [category, setCategory] = useState<CategoryProductsResponse['category'] | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCategoryProducts = async () => {
    if (!options.categorySlug) return;

    setLoading(true);
    setError(null);

    try {
      const response = await productsApi.getProductsByCategory(options.categorySlug, options.filters);
      if (response.success && response.data) {
        setProducts(response.data.products);
        setCategory(response.data.category);
        setTotalCount(response.data.total_count);
      } else {
        setError(response.error?.message || 'Failed to fetch category products');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (options.autoFetch && options.categorySlug) {
      fetchCategoryProducts();
    }
  }, [options.categorySlug, options.autoFetch, JSON.stringify(options.filters)]);

  return {
    products,
    category,
    totalCount,
    loading,
    error,
    refetch: fetchCategoryProducts,
  };
};

interface UseProductSearchOptions {
  query: string;
  autoFetch?: boolean;
}

interface UseProductSearchReturn {
  products: Product[];
  query: string;
  totalCount: number;
  loading: boolean;
  error: string | null;
  search: (searchQuery: string) => Promise<void>;
}

export const useProductSearch = (options: UseProductSearchOptions): UseProductSearchReturn => {
  const [products, setProducts] = useState<Product[]>([]);
  const [query, setQuery] = useState(options.query);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchProducts = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setProducts([]);
      setTotalCount(0);
      return;
    }

    setLoading(true);
    setError(null);
    setQuery(searchQuery);

    try {
      const response = await productsApi.searchProducts(searchQuery);
      if (response.success && response.data) {
        setProducts(response.data.products);
        setTotalCount(response.data.total_count);
      } else {
        setError(response.error?.message || 'Failed to search products');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (options.autoFetch && options.query) {
      searchProducts(options.query);
    }
  }, [options.query, options.autoFetch]);

  return {
    products,
    query,
    totalCount,
    loading,
    error,
    search: searchProducts,
  };
};