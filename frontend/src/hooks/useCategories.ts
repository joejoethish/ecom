/**
 * React hooks for categories data
 */
import { useState, useEffect } from 'react';
import { categoriesApi, Category } from '@/services/categoriesApi';

interface UseCategoriesOptions {
  featured?: boolean;
  autoFetch?: boolean;
}

interface UseCategoriesReturn {
  categories: Category[];
  featuredCategories: Category[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useCategories = (options: UseCategoriesOptions = {}): UseCategoriesReturn => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [featuredCategories, setFeaturedCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCategories = async () => {
    setLoading(true);
    setError(null);

    try {
      if (options.featured) {
        const response = await categoriesApi.getFeaturedCategories();
        if (response.success && response.data) {
          setFeaturedCategories(response.data);
        } else {
          setError(response.error?.message || 'Failed to fetch featured categories');
        }
      } else {
        const response = await categoriesApi.getAllCategories();
        if (response.success && response.data) {
          setCategories(response.data.data);
        } else {
          setError(response.error?.message || 'Failed to fetch categories');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchBothTypes = async () => {
    setLoading(true);
    setError(null);

    try {
      const [featuredResponse, allResponse] = await Promise.all([
        categoriesApi.getFeaturedCategories(),
        categoriesApi.getAllCategories()
      ]);

      if (featuredResponse.success && featuredResponse.data) {
        setFeaturedCategories(featuredResponse.data);
      }

      if (allResponse.success && allResponse.data) {
        setCategories(allResponse.data.data);
      }

      if (!featuredResponse.success || !allResponse.success) {
        setError('Failed to fetch categories');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (options.autoFetch) {
      if (options.featured !== undefined) {
        fetchCategories();
      } else {
        fetchBothTypes();
      }
    }
  }, [options.featured, options.autoFetch]);

  return {
    categories,
    featuredCategories,
    loading,
    error,
    refetch: options.featured !== undefined ? fetchCategories : fetchBothTypes,
  };
};

interface UseCategoryDetailsOptions {
  slug: string;
  autoFetch?: boolean;
}

interface UseCategoryDetailsReturn {
  category: Category | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useCategoryDetails = (options: UseCategoryDetailsOptions): UseCategoryDetailsReturn => {
  const [category, setCategory] = useState<Category | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCategoryDetails = async () => {
    if (!options.slug) return;

    setLoading(true);
    setError(null);

    try {
      const response = await categoriesApi.getCategoryDetails(options.slug);
      if (response.success && response.data) {
        setCategory(response.data);
      } else {
        setError(response.error?.message || 'Failed to fetch category details');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (options.autoFetch && options.slug) {
      fetchCategoryDetails();
    }
  }, [options.slug, options.autoFetch]);

  return {
    category,
    loading,
    error,
    refetch: fetchCategoryDetails,
  };
};