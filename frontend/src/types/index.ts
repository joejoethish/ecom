// Core type definitions for the ecommerce platform
import { OrderTracking, ReturnRequest, Replacement } from './orders';
export * from './orders';
export * from './payments';
export * from './shipping';

export interface User {
  id: string;
  username: string;
  email: string;
  user_type: 'customer' | 'seller' | 'admin' | 'inventory_manager' | 'warehouse_staff';
  phone_number?: string;
  is_verified: boolean;
  is_email_verified?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  seller_profile?: any;
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

export interface UserSession {
  id: string;
  session_key: string;
  device_info: {
    browser?: string;
    os?: string;
    device?: string;
    user_agent?: string;
  };
  ip_address: string;
  location?: {
    country?: string;
    city?: string;
    region?: string;
  };
  created_at: string;
  last_activity: string;
  is_active: boolean;
  is_current: boolean;
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
  dimensions?: Record<string, any>;
  images: ProductImage[];
  status?: string;
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

export interface SavedItem {
  id: string;
  product: Product;
  saved_at: string;
}

export interface Coupon {
  id: string;
  code: string;
  name: string;
  discount_type: 'PERCENTAGE' | 'FIXED';
  value: number;
  minimum_order_amount: number;
  maximum_discount_amount?: number;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
}

export interface AppliedCoupon {
  coupon: Coupon;
  discount_amount: number;
}

export interface Cart {
  id: string;
  items: CartItem[];
  saved_items: SavedItem[];
  applied_coupons: AppliedCoupon[];
  subtotal: number;
  discount_amount: number;
  total_amount: number;
  created_at: string;
  updated_at: string;
}

export interface Address {
  id: string;
  type: 'HOME' | 'WORK' | 'OTHER' | 'shipping';
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
  timeline?: OrderTracking[];
  return_requests?: ReturnRequest[];
  replacements?: Replacement[];
  tracking_number?: string;
  estimated_delivery_date?: string;
  actual_delivery_date?: string;
  invoice_number?: string;
  has_invoice?: boolean;
  can_cancel?: boolean;
  can_return?: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  product: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
  status?: string;
  is_gift?: boolean;
  gift_message?: string;
  returned_quantity?: number;
  refunded_amount?: number;
  can_return?: boolean;
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

export interface EmailVerificationData {
  token: string;
  success: boolean;
  message: string;
  user?: User;
}

export interface ResendVerificationData {
  success: boolean;
  message: string;
}

export interface FormErrors {
  [key: string]: string | string[];
}

// Wishlist types
export interface WishlistItem {
  id: string;
  product: Product;
  added_at: string;
}

export interface Wishlist {
  id: string;
  items: WishlistItem[];
  created_at: string;
}

// Customer profile types
export interface CustomerProfile {
  id: string;
  user: User;
  date_of_birth?: string;
  gender?: 'M' | 'F' | 'O';
  preferences: {
    newsletter_subscription: boolean;
    sms_notifications: boolean;
    email_notifications: boolean;
    language: string;
    currency: string;
  };
  created_at: string;
  updated_at: string;
}

export interface CustomerPreferences {
  newsletter_subscription: boolean;
  sms_notifications: boolean;
  email_notifications: boolean;
  language: string;
  currency: string;
}

// Review types
export interface ReviewUser {
  id: string;
  username: string;
  full_name: string;
  avatar_url: string;
}

export interface ReviewProduct {
  id: string;
  name: string;
  slug: string;
  primary_image?: {
    id: string;
    image: string;
    alt_text: string;
  };
}

export interface ReviewImage {
  id: string;
  image: string;
  caption: string;
  sort_order: number;
  created_at: string;
}

export interface Review {
  id: string;
  user: ReviewUser;
  product: ReviewProduct;
  rating: number;
  title: string;
  comment: string;
  pros?: string;
  cons?: string;
  is_verified_purchase: boolean;
  status: 'pending' | 'approved' | 'rejected' | 'flagged';
  helpful_count: number;
  not_helpful_count: number;
  helpfulness_score: number;
  images: ReviewImage[];
  user_vote?: 'helpful' | 'not_helpful';
  can_moderate: boolean;
  created_at: string;
  moderated_by?: ReviewUser;
  moderated_at?: string;
  moderation_notes?: string;
}

export interface ReviewCreateData {
  product: string;
  rating: number;
  title: string;
  comment: string;
  pros?: string;
  cons?: string;
  images?: File[];
}

export interface ReviewUpdateData {
  rating?: number;
  title?: string;
  comment?: string;
  pros?: string;
  cons?: string;
  images?: File[];
}

export interface ReviewHelpfulnessVote {
  id: string;
  vote: 'helpful' | 'not_helpful';
  created_at: string;
}

export interface ReviewReport {
  id: string;
  review: Review;
  reporter: ReviewUser;
  reason: 'spam' | 'inappropriate' | 'fake' | 'offensive' | 'irrelevant' | 'other';
  description: string;
  status: 'pending' | 'reviewed' | 'resolved' | 'dismissed';
  reviewed_by?: ReviewUser;
  reviewed_at?: string;
  resolution_notes?: string;
  created_at: string;
}

export interface ReviewAnalytics {
  total_reviews: number;
  average_rating: number;
  rating_distribution: {
    [key: number]: number; // rating -> percentage
  };
  rating_counts: {
    [key: number]: number; // rating -> count
  };
}

export interface ProductReviewSummary {
  product_id: string;
  total_reviews: number;
  average_rating: number;
  rating_distribution: {
    [key: number]: number;
  };
  recent_reviews: Review[];
  verified_purchase_percentage: number;
}

export interface ModerationStats {
  pending_reviews: number;
  flagged_reviews: number;
  pending_reports: number;
  approved_reviews: number;
  rejected_reviews: number;
}

export interface ReviewFilters {
  product?: string;
  status?: string;
  rating?: number;
  verified_only?: boolean;
  my_reviews?: boolean;
  ordering?: string;
}