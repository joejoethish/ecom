import { useState, useEffect, useCallback } from 'react';
import { categoryApi, Category, CategoryTree } from '../services/categoryApi';

interface UseCategoriesOptions {
  autoFetch?: boolean;
  featured?: boolean;
  tree?: boolean;
}

interface UseCategoriesReturn {
  // Data
  categories: Category[];
  categoryTree: CategoryTree[];
  featuredCategories: Category[];
  
  // Loading states
  loading: boolean;
  
  // Error states
  error: string | null;
  
  // Actions
  fetchCategories: () => Promise<void>;
  fetchCategoryTree: () => Promise<void>;
  fetchFeaturedCategories: () => Promise<void>;
  createCategory: (data: Partial<Category>) => Promise<Category | null>;
  updateCategory: (slug: string, data: Partial<Category>) => Promise<Category | null>;
  deleteCategory: (slug: string) => Promise<boolean>;
  
  // Utilities
  refresh: () => Promise<void>;
  clearError: () => void;
}

export const useCategories = ({
  autoFetch = true,
  featured = false,
  tree = false,
}: UseCategoriesOptions = {}): UseCategoriesReturn => {
  // State
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryTree, setCategoryTree] = useState<CategoryTree[]>([]);
  const [featuredCategories, setFeaturedCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all categories
  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await categoryApi.getCategories();
      
      if (response.success && response.data) {
        setCategories(response.data);
      } else {
        throw new Error(response.error?.message || 'Failed to fetch categories');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch categories';
      setError(errorMessage);
      setCategories([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch category tree
  const fetchCategoryTree = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await categoryApi.getCategoryTree();
      
      if (response.success && response.data) {
        setCategoryTree(response.data);
      } else {
        throw new Error(response.error?.message || 'Failed to fetch category tree');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch category tree';
      setError(errorMessage);
      setCategoryTree([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch featured categories
  const fetchFeaturedCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await categoryApi.getFeaturedCategories();
      
      if (response.success && response.data) {
        setFeaturedCategories(response.data);
      } else {
        throw new Error(response.error?.message || 'Failed to fetch featured categories');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch featured categories';
      setError(errorMessage);
      setFeaturedCategories([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create category
  const createCategory = useCallback(async (data: Partial<Category>): Promise<Category | null> => {
    setError(null);
    
    try {
      const response = await categoryApi.createCategory(data);
      
      if (response.success && response.data) {
        // Refresh categories after creation
        await fetchCategories();
        return response.data;
      } else {
        throw new Error(response.error?.message || 'Failed to create category');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create category';
      setError(errorMessage);
      return null;
    }
  }, [fetchCategories]);

  // Update category
  const updateCategory = useCallback(async (slug: string, data: Partial<Category>): Promise<Category | null> => {
    setError(null);
    
    try {
      const response = await categoryApi.updateCategory(slug, data);
      
      if (response.success && response.data) {
        // Update local state
        setCategories(prev => prev.map(cat => 
          cat.slug === slug ? { ...cat, ...response.data } : cat
        ));
        return response.data;
      } else {
        throw new Error(response.error?.message || 'Failed to update category');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update category';
      setError(errorMessage);
      return null;
    }
  }, []);

  // Delete category
  const deleteCategory = useCallback(async (slug: string): Promise<boolean> => {
    setError(null);
    
    try {
      const response = await categoryApi.deleteCategory(slug);
      
      if (response.success) {
        // Remove from local state
        setCategories(prev => prev.filter(cat => cat.slug !== slug));
        return true;
      } else {
        throw new Error(response.error?.message || 'Failed to delete category');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete category';
      setError(errorMessage);
      return false;
    }
  }, []);

  // Refresh all data
  const refresh = useCallback(async () => {
    const promises = [];
    
    if (featured) {
      promises.push(fetchFeaturedCategories());
    }
    
    if (tree) {
      promises.push(fetchCategoryTree());
    }
    
    if (!featured && !tree) {
      promises.push(fetchCategories());
    }
    
    await Promise.all(promises);
  }, [featured, tree, fetchCategories, fetchCategoryTree, fetchFeaturedCategories]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Effects
  useEffect(() => {
    if (autoFetch) {
      if (featured) {
        fetchFeaturedCategories();
      } else if (tree) {
        fetchCategoryTree();
      } else {
        fetchCategories();
      }
    }
  }, [autoFetch, featured, tree, fetchCategories, fetchCategoryTree, fetchFeaturedCategories]);

  return {
    // Data
    categories,
    categoryTree,
    featuredCategories,
    
    // Loading states
    loading,
    
    // Error states
    error,
    
    // Actions
    fetchCategories,
    fetchCategoryTree,
    fetchFeaturedCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    
    // Utilities
    refresh,
    clearError,
  };
};