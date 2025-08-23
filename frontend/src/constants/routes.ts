/**
 * Centralized route definitions for the application
 */

// Main routes
export const MAIN_ROUTES = {
  HOME: '/',
  PRODUCTS: '/products',
  PRODUCT_DETAIL: (slug: string) => `/products/${slug}`,
  CART: '/cart',
  CHECKOUT: '/checkout',
  SEARCH: '/search',
  ABOUT: '/about',
  CONTACT: '/contact',
  TERMS: '/terms',
  PRIVACY: '/privacy',
  FAQ: '/faq',
} as const;

// Authentication routes
export const AUTH_ROUTES = {
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  FORGOT_PASSWORD: '/auth/forgot-password',
  RESET_PASSWORD: '/auth/reset-password',
  VERIFY_EMAIL: '/auth/verify-email',
} as const;

// User profile routes
export const PROFILE_ROUTES = {
  DASHBOARD: '/profile',
  ORDERS: '/profile/orders',
  ORDER_DETAIL: (id: string) => `/profile/orders/${id}`,
  ADDRESSES: '/profile/addresses',
  WISHLIST: '/profile/wishlist',
  SETTINGS: '/profile/settings',
  NOTIFICATIONS: '/profile/notifications',
} as const;

// Admin routes
export const ADMIN_ROUTES = {
  DASHBOARD: '/admin',
  LOGIN: '/admin/login',
  SESSIONS: '/admin/sessions',
  ANALYTICS: '/admin/analytics',
  ORDERS: '/admin/orders',
  ORDER_DETAIL: (id: string) => `/admin/orders/${id}`,
  PRODUCTS: '/admin/products',
  PRODUCT_EDIT: (id: string) => `/admin/products/${id}/edit`,
  PRODUCT_CREATE: '/admin/products/create',
  CUSTOMERS: '/admin/customers',
  CUSTOMER_DETAIL: (id: string) => `/admin/customers/${id}`,
  CONTENT: '/admin/content',
  REPORTS: '/admin/reports',
  SYSTEM: '/admin/system',
  NOTIFICATIONS: '/admin/notifications',
  SETTINGS: '/admin/settings',
} as const;

// Seller routes
export const SELLER_ROUTES = {
  DASHBOARD: '/seller/dashboard',
  PRODUCTS: '/seller/products',
  PRODUCT_EDIT: (id: string) => `/seller/products/${id}/edit`,
  PRODUCT_CREATE: '/seller/products/create',
  ORDERS: '/seller/orders',
  ORDER_DETAIL: (id: string) => `/seller/orders/${id}`,
  PROFILE: '/seller/profile',
  KYC: '/seller/kyc',
  BANK_ACCOUNTS: '/seller/bank-accounts',
  PAYOUTS: '/seller/payouts',
  ANALYTICS: '/seller/analytics',
  SETTINGS: '/seller/settings',
} as const;

// Human-readable labels for routes
export const ROUTE_LABELS: Record<string, string> = {
  '/': 'Home',
  '/products': 'Products',
  '/cart': 'Shopping Cart',
  '/checkout': 'Checkout',
  '/search': 'Search',
  '/about': 'About Us',
  '/contact': 'Contact Us',
  '/terms': 'Terms of Service',
  '/privacy': 'Privacy Policy',
  '/faq': 'FAQ',
  
  '/auth/login': 'Login',
  '/auth/register': 'Register',
  '/auth/forgot-password': 'Forgot Password',
  '/auth/reset-password': 'Reset Password',
  '/auth/verify-email': 'Verify Email',
  
  '/profile': 'My Account',
  '/profile/orders': 'My Orders',
  '/profile/addresses': 'My Addresses',
  '/profile/wishlist': 'My Wishlist',
  '/profile/settings': 'Account Settings',
  '/profile/notifications': 'Notifications',
  
  '/admin': 'Admin Dashboard',
  '/admin/login': 'Admin Login',
  '/admin/sessions': 'Session Management',
  '/admin/analytics': 'Analytics',
  '/admin/orders': 'Orders Management',
  '/admin/products': 'Products Management',
  '/admin/products/create': 'Create Product',
  '/admin/customers': 'Customers Management',
  '/admin/content': 'Content Management',
  '/admin/reports': 'Reports',
  '/admin/system': 'System Health',
  '/admin/notifications': 'Notifications',
  '/admin/settings': 'Admin Settings',
  
  '/seller/dashboard': 'Seller Dashboard',
  '/seller/products': 'My Products',
  '/seller/products/create': 'Add New Product',
  '/seller/orders': 'My Orders',
  '/seller/profile': 'Seller Profile',
  '/seller/kyc': 'KYC Verification',
  '/seller/bank-accounts': 'Bank Accounts',
  '/seller/payouts': 'Payouts',
  '/seller/analytics': 'Sales Analytics',
  '/seller/settings': 'Seller Settings',
} as const;