// Application constants and configuration

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login/',
    REGISTER: '/auth/register/',
    LOGOUT: '/auth/logout/',
    REFRESH: '/auth/refresh/',
    PROFILE: '/auth/profile/',
    ADMIN_LOGIN: '/admin-auth/login/',
    FORGOT_PASSWORD: '/auth/forgot-password/',
    RESET_PASSWORD: '/auth/reset-password/',
    VALIDATE_RESET_TOKEN: (token: string) => `/auth/validate-reset-token/${token}/`,
    VERIFY_EMAIL: (token: string) => `/auth/verify-email/${token}/`,
    RESEND_VERIFICATION: '/auth/resend-verification/',
  },
  // Products
  PRODUCTS: {
    LIST: '/products/',
    DETAIL: (id: string) => `/products/${id}/`,
    CATEGORIES: '/products/categories/',
  },
  // Cart
  CART: {
    LIST: '/cart/',
    ADD: '/cart/add/',
    UPDATE: (id: string) => `/cart/${id}/`,
    REMOVE: (id: string) => `/cart/${id}/`,
  },
  // Orders
  ORDERS: {
    LIST: '/orders/',
    DETAIL: (id: string) => `/orders/${id}/`,
    CREATE: '/orders/',
    CANCEL: (id: string) => `/orders/${id}/cancel/`,
    TIMELINE: (id: string) => `/orders/${id}/timeline/`,
    INVOICE: (id: string) => `/orders/${id}/invoice/`,
    DOWNLOAD_INVOICE: (id: string) => `/orders/${id}/download_invoice/`,
  },
  // Return Requests
  RETURNS: {
    LIST: '/return-requests/',
    DETAIL: (id: string) => `/return-requests/${id}/`,
    CREATE: '/return-requests/',
  },
  // Replacements
  REPLACEMENTS: {
    LIST: '/replacements/',
    DETAIL: (id: string) => `/replacements/${id}/`,
    CREATE: '/replacements/',
    UPDATE_STATUS: (id: string) => `/replacements/${id}/update_status/`,
  },
  // Search
  SEARCH: {
    PRODUCTS: '/search/products/',
    SUGGESTIONS: '/search/suggestions/',
    FILTERS: '/search/filters/',
    POPULAR: '/search/popular/',
    RELATED: '/search/related/',
  },
  // Customer Profile
  CUSTOMER: {
    PROFILE: '/customer/profile/',
    ADDRESSES: '/customer/addresses/',
    ADDRESS_DETAIL: (id: string) => `/customer/addresses/${id}/`,
    PREFERENCES: '/customer/preferences/',
  },
  // Wishlist
  WISHLIST: {
    LIST: '/wishlist/',
    ADD: '/wishlist/add/',
    REMOVE: (id: string) => `/wishlist/${id}/`,
    CLEAR: '/wishlist/clear/',
  },
  // Rewards
  REWARDS: {
    LIST: '/rewards/',
    BALANCE: '/rewards/balance/',
    TRANSACTIONS: '/rewards/transactions/',
    REDEEM: '/rewards/redeem/',
    PROGRAM: '/rewards/program/',
  },
  // Payments
  PAYMENTS: {
    METHODS: '/payments/methods/',
    CURRENCIES: '/payments/currencies/',
    CREATE: '/payments/create/',
    VERIFY: '/payments/verify/',
    STATUS: (id: string) => `/payments/${id}/status/`,
    WALLET: '/payments/wallet/',
    GIFT_CARD: {
      VALIDATE: '/payments/gift-card/validate/',
      BALANCE: (code: string) => `/payments/gift-card/${code}/balance/`,
    },
    CONVERT_CURRENCY: '/payments/convert-currency/',
  },
  // Admin
  ADMIN: {
    DASHBOARD: '/admin/dashboard/',
    ANALYTICS: '/admin/analytics/',
    PRODUCTS: '/admin/products/',
    ORDERS: '/admin/orders/',
    CUSTOMERS: '/admin/customers/',
    SETTINGS: '/admin/settings/',
  },
  // Admin Authentication
  ADMIN_AUTH: {
    LOGIN: '/admin-auth/login/',
    LOGOUT: '/admin-auth/logout/',
    LOGOUT_ALL: '/admin-auth/logout-all/',
    REFRESH: '/admin-auth/refresh/',
    SESSIONS: '/admin-auth/sessions/',
    TERMINATE_SESSION: (sessionId: string) => `/admin-auth/sessions/${sessionId}/terminate/`,
    SECURITY_EVENTS: '/admin-auth/security-events/',
    VALIDATE_SESSION: '/admin-auth/validate-session/',
  },
  // Seller
  SELLER: {
    DASHBOARD: '/seller/dashboard/',
    PRODUCTS: '/seller/products/',
    ORDERS: '/seller/orders/',
    PROFILE: '/seller/profile/',
    KYC: '/seller/kyc/',
    PAYOUTS: '/seller/payouts/',
  },
} as const;

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  CART: 'cart',
} as const;

export const USER_TYPES = {
  CUSTOMER: 'customer',
  SELLER: 'seller',
  ADMIN: 'admin',
} as const;

export const ORDER_STATUS = {
  PENDING: 'PENDING',
  CONFIRMED: 'CONFIRMED',
  PROCESSING: 'PROCESSING',
  SHIPPED: 'SHIPPED',
  DELIVERED: 'DELIVERED',
  CANCELLED: 'CANCELLED',
  RETURNED: 'RETURNED',
} as const;

export const PAYMENT_STATUS = {
  PENDING: 'PENDING',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  CANCELLED: 'CANCELLED',
  REFUNDED: 'REFUNDED',
} as const;

export const ADDRESS_TYPES = {
  HOME: 'HOME',
  WORK: 'WORK',
  OTHER: 'OTHER',
} as const;

// Import centralized routes
import {
  MAIN_ROUTES,
  AUTH_ROUTES,
  PROFILE_ROUTES,
  ADMIN_ROUTES,
  SELLER_ROUTES
} from './routes';

// Export routes for external use
export {
  MAIN_ROUTES,
  AUTH_ROUTES,
  PROFILE_ROUTES,
  ADMIN_ROUTES,
  SELLER_ROUTES
};

// Legacy routes object for backward compatibility
export const ROUTES = {
  ...MAIN_ROUTES,
  ...AUTH_ROUTES,
  PROFILE: PROFILE_ROUTES.DASHBOARD,
  ORDERS: PROFILE_ROUTES.ORDERS,
  PROFILE_ADDRESSES: PROFILE_ROUTES.ADDRESSES,
  PROFILE_WISHLIST: PROFILE_ROUTES.WISHLIST,
  PROFILE_PREFERENCES: PROFILE_ROUTES.SETTINGS,
  ADMIN: ADMIN_ROUTES.DASHBOARD,
  SELLER: SELLER_ROUTES.DASHBOARD,
} as const;

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;

export const VALIDATION = {
  PASSWORD_MIN_LENGTH: 8,
  USERNAME_MIN_LENGTH: 3,
  PHONE_REGEX: /^[\+]?[1-9][\d]{0,15}$/,
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
} as const;