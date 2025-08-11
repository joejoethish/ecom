/**
 * Categories API service for dynamic data
 */
import { apiClient } from '@/utils/api';
import { ApiResponse } from '@/types';

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon?: string;
  href?: string;
  product_count: number;
  is_featured?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CategoryFilters {
  category: {
    id: number;
    name: string;
    slug: string;
  };
  brands: Array<{
    name: string;
    count: number;
  }>;
  price_ranges: Array<{
    from: number | null;
    to: number | null;
    label: string;
    count: number;
  }>;
  total_products: number;
}

export const categoriesApi = {
  /**
   * Get featured categories for homepage
   */
  getFeaturedCategories: async (): Promise<ApiResponse<Category[]>> => {
    return apiClient.get(&apos;/categories/featured/&apos;);
  },

  /**
   * Get all categories
   */
  getAllCategories: async (): Promise<ApiResponse<{
    data: Category[];
    total_count: number;
  }>> => {
    return apiClient.get(&apos;/categories/&apos;);
  },

  /**
   * Get category details by slug
   */
  getCategoryDetails: async (slug: string): Promise<ApiResponse<Category & {
    top_brands: Array<{
      name: string;
      count: number;
    }>;
  }>> => {
    return apiClient.get(`/categories/${slug}/`);
  },

  /**
   * Get category filters
   */
  getCategoryFilters: async (slug: string): Promise<ApiResponse<CategoryFilters>> => {
    return apiClient.get(`/categories/${slug}/filters/`);
  },
};

export default categoriesApi;