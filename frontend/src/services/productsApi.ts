/**
 * Products API service for dynamic data
 */
import { apiClient } from '@/utils/api';
import { ApiResponse } from '@/types';

export interface Product {
  id: string;
  name: string;
  slug: string;
  price: number;
  discount_price?: number;
  discount_percentage: number;
  image?: string;
  rating: number;
  review_count: number;
  brand: string;
  category: {
    id: number;
    name: string;
    slug: string;
  };
  is_featured?: boolean;
  free_delivery?: boolean;
  exchange_offer?: boolean;
}

export interface ProductsResponse {
  data: Product[];
  total_count: number;
  page: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface CategoryProductsResponse extends ProductsResponse {
  category: {
    id: number;
    name: string;
    slug: string;
    description: string;
  };
}

export interface SearchProductsResponse extends ProductsResponse {
  query: string;
}

export const productsApi = {
  /**
   * Get featured products for homepage
   */
  getFeaturedProducts: async (): Promise<ApiResponse<Product[]>> => {
    return apiClient.get('/products/featured/');
  },

  /**
   * Get products by category
   */
  getProductsByCategory: async (
    categorySlug: string,
    params?: {
      page?: number;
      price_min?: number;
      price_max?: number;
      brand?: string;
      sort?: string;
    }
  ): Promise<ApiResponse<ProductsResponse>> => {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.price_min) queryParams.append('price_min', params.price_min.toString());
    if (params?.price_max) queryParams.append('price_max', params.price_max.toString());
    if (params?.brand) queryParams.append('brand', params.brand);
    if (params?.sort) queryParams.append('sort', params.sort);
    
    const url = `/products/category/${categorySlug}/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(url);
  },

  /**
   * Search products
   */
  searchProducts: async (query: string): Promise<ApiResponse<SearchProductsResponse>> => {
    return apiClient.get(`/products/search/?q=${encodeURIComponent(query)}`);
  },

  /**
   * Get product details by ID
   */
  getProductDetails: async (productId: string): Promise<ApiResponse<Product & {
    description: string;
    images: Array<{
      id: number;
      image: string;
      is_primary: boolean;
    }>;
    features?: string[];
    specifications?: Record<string, string>;
    reviews: Array<{
      id: number;
      user: string;
      rating: number;
      comment: string;
      created_at: string;
    }>;
  }>> => {
    return apiClient.get(`/products/${productId}/`);
  },
};

export default productsApi;