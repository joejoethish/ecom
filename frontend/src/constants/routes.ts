/**
 * Centralized route definitions for the application
 */

// Main routes
  HOME: '/',
  PRODUCTS: '/products',
  PRODUCT_DETAIL: (slug: string) => `/products/${slug}`,
  CART: &apos;/cart&apos;,
  CHECKOUT: &apos;/checkout&apos;,
  SEARCH: &apos;/search&apos;,
  ABOUT: &apos;/about&apos;,
  CONTACT: &apos;/contact&apos;,
  TERMS: &apos;/terms&apos;,
  PRIVACY: &apos;/privacy&apos;,
  FAQ: &apos;/faq&apos;,
} as const;

// Authentication routes
  LOGIN: &apos;/auth/login&apos;,
  REGISTER: &apos;/auth/register&apos;,
  FORGOT_PASSWORD: &apos;/auth/forgot-password&apos;,
  RESET_PASSWORD: &apos;/auth/reset-password&apos;,
  VERIFY_EMAIL: &apos;/auth/verify-email&apos;,
} as const;

// User profile routes
  DASHBOARD: &apos;/profile&apos;,
  ORDERS: &apos;/profile/orders&apos;,
  ORDER_DETAIL: (id: string) => `/profile/orders/${id}`,
  ADDRESSES: &apos;/profile/addresses&apos;,
  WISHLIST: &apos;/profile/wishlist&apos;,
  SETTINGS: &apos;/profile/settings&apos;,
  NOTIFICATIONS: &apos;/profile/notifications&apos;,
} as const;

// Admin routes
  DASHBOARD: &apos;/admin&apos;,
  ANALYTICS: &apos;/admin/analytics&apos;,
  ORDERS: &apos;/admin/orders&apos;,
  ORDER_DETAIL: (id: string) => `/admin/orders/${id}`,
  PRODUCTS: &apos;/admin/products&apos;,
  PRODUCT_EDIT: (id: string) => `/admin/products/${id}/edit`,
  PRODUCT_CREATE: &apos;/admin/products/create&apos;,
  CUSTOMERS: &apos;/admin/customers&apos;,
  CUSTOMER_DETAIL: (id: string) => `/admin/customers/${id}`,
  CONTENT: &apos;/admin/content&apos;,
  REPORTS: &apos;/admin/reports&apos;,
  SYSTEM: &apos;/admin/system&apos;,
  NOTIFICATIONS: &apos;/admin/notifications&apos;,
  SETTINGS: &apos;/admin/settings&apos;,
} as const;

// Seller routes
  DASHBOARD: &apos;/seller/dashboard&apos;,
  PRODUCTS: &apos;/seller/products&apos;,
  PRODUCT_EDIT: (id: string) => `/seller/products/${id}/edit`,
  PRODUCT_CREATE: &apos;/seller/products/create&apos;,
  ORDERS: &apos;/seller/orders&apos;,
  ORDER_DETAIL: (id: string) => `/seller/orders/${id}`,
  PROFILE: &apos;/seller/profile&apos;,
  KYC: &apos;/seller/kyc&apos;,
  BANK_ACCOUNTS: &apos;/seller/bank-accounts&apos;,
  PAYOUTS: &apos;/seller/payouts&apos;,
  ANALYTICS: &apos;/seller/analytics&apos;,
  SETTINGS: &apos;/seller/settings&apos;,
} as const;

// Human-readable labels for routes
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