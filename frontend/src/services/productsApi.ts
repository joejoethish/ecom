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
  products: Product[];
  total_count: number;
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
    return apiClient.get(&apos;/products/featured/&apos;);
  },

  /**
   * Get products by category
   */
  getProductsByCategory: async (
    categorySlug: string,
    params?: {
      min_price?: number;
      max_price?: number;
      brand?: string;
      sort?: &apos;name&apos; | &apos;price_low&apos; | &apos;price_high&apos; | &apos;rating&apos; | &apos;newest&apos;;
    }
  ): Promise<ApiResponse<CategoryProductsResponse>> => {
    const queryParams = new URLSearchParams();
    
    if (params?.min_price) queryParams.append(&apos;min_price&apos;, params.min_price.toString());
    if (params?.max_price) queryParams.append(&apos;max_price&apos;, params.max_price.toString());
    if (params?.brand) queryParams.append(&apos;brand&apos;, params.brand);
    if (params?.sort) queryParams.append(&apos;sort&apos;, params.sort);
    
    const url = `/products/category/${categorySlug}/${queryParams.toString() ? `?${queryParams.toString()}` : &apos;&apos;}`;
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