// Core type definitions for the ecommerce platform

export interface User {
  id: string;
  username: string;
  email: string;
  user_type: 'customer' | 'seller' | 'admin';
  phone_number?: string;
  is_verified: boolean;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code: string;
    status_code: number;
    details?: any;
  };
}

export interface PaginationInfo {
  count: number;
  next: string | null;
  previous: string | null;
  page_size: number;
  total_pages: number;
  current_page: number;
}

export interface PaginatedResponse<T> {
  pagination: PaginationInfo;
  results: T[];
  success: boolean;
}

export interface Product {
  id: string;
  name: string;
  slug: string;
  description: string;
  short_description: string;
  category: Category;
  brand: string;
  sku: string;
  price: number;
  discount_price?: number;
  is_active: boolean;
  is_featured: boolean;
  weight?: number;
  dimensions: Record<string, any>;
  images: ProductImage[];
  created_at: string;
  updated_at: string;
}

export interface ProductImage {
  id: string;
  image: string;
  alt_text: string;
  is_primary: boolean;
  order: number;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  parent?: Category;
  image?: string;
  is_active: boolean;
  created_at: string;
}

export interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  added_at: string;
}

export interface Cart {
  id: string;
  items: CartItem[];
  created_at: string;
  updated_at: string;
}

export interface Address {
  id: string;
  type: 'HOME' | 'WORK' | 'OTHER';
  first_name: string;
  last_name: string;
  company?: string;
  address_line_1: string;
  address_line_2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone?: string;
  is_default: boolean;
}

export interface Order {
  id: string;
  order_number: string;
  status: 'PENDING' | 'CONFIRMED' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED' | 'RETURNED';
  total_amount: number;
  discount_amount: number;
  tax_amount: number;
  shipping_amount: number;
  shipping_address: Address;
  billing_address: Address;
  payment_method: string;
  payment_status: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  product: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  user_type?: 'customer' | 'seller';
  phone_number?: string;
}

export interface FormErrors {
  [key: string]: string | string[];
}