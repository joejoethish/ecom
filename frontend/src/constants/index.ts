// Application constants and configuration

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

  // Authentication
  AUTH: {
    LOGIN: '/auth/login/',
    REGISTER: '/auth/register/',
    LOGOUT: '/auth/logout/',
    REFRESH: '/auth/refresh/',
    PROFILE: '/auth/profile/',
    FORGOT_PASSWORD: '/auth/forgot-password/',
    RESET_PASSWORD: '/auth/reset-password/',
    VALIDATE_RESET_TOKEN: (token: string) => `/auth/validate-reset-token/${token}/`,
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

  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  CART: 'cart',
} as const;

  CUSTOMER: 'customer',
  SELLER: 'seller',
  ADMIN: 'admin',
} as const;

  PENDING: 'PENDING',
  CONFIRMED: 'CONFIRMED',
  PROCESSING: 'PROCESSING',
  SHIPPED: 'SHIPPED',
  DELIVERED: 'DELIVERED',
  CANCELLED: 'CANCELLED',
  RETURNED: 'RETURNED',
} as const;

  PENDING: 'PENDING',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  CANCELLED: 'CANCELLED',
  REFUNDED: 'REFUNDED',
} as const;

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

  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;

  PASSWORD_MIN_LENGTH: 8,
  USERNAME_MIN_LENGTH: 3,
  PHONE_REGEX: /^[\+]?[1-9][\d]{0,15}$/,
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
} as const;