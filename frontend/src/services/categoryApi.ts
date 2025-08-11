import { apiClient } from '../utils/api';
import { ApiResponse } from '../types';

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  image?: string;
  icon?: string;
  href?: string;
  sort_order: number;
  products_count?: number;
  children?: Category[];
}

export interface CategoryTree extends Category {
  children: CategoryTree[];
}

  // Get all categories
  getCategories: async (): Promise<ApiResponse<Category[]>> => {
    return apiClient.get<Category[]>(&apos;/categories/&apos;);
  },

  // Get category tree (hierarchical)
  getCategoryTree: async (): Promise<ApiResponse<CategoryTree[]>> => {
    return apiClient.get<CategoryTree[]>(&apos;/categories/tree/&apos;);
  },

  // Get featured categories for homepage
  getFeaturedCategories: async (): Promise<ApiResponse<Category[]>> => {
    return apiClient.get<Category[]>(&apos;/categories/featured/&apos;);
  },

  // Get single category by slug
  getCategory: async (slug: string): Promise<ApiResponse<Category>> => {
    return apiClient.get<Category>(`/categories/${slug}/`);
  },

  // Create new category (admin only)
  createCategory: async (data: Partial<Category>): Promise<ApiResponse<Category>> => {
    return apiClient.post<Category>(&apos;/categories/&apos;, data);
  },

  // Update category (admin only)
  updateCategory: async (slug: string, data: Partial<Category>): Promise<ApiResponse<Category>> => {
    return apiClient.patch<Category>(`/categories/${slug}/`, data);
  },

  // Delete category (admin only)
  deleteCategory: async (slug: string): Promise<ApiResponse<void>> => {
    return apiClient.delete<void>(`/categories/${slug}/`);
  },

  // Bulk update category sort orders (admin only)
  bulkUpdateCategories: async (categories: { id: string; sort_order: number }[]): Promise<ApiResponse<{ message: string }>> => {
    return apiClient.post<{ message: string }>('/categories/bulk-update/', { categories });
  },
};