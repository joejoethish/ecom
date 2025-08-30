import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable experimental features for debugging dashboard
  experimental: {
    // Enable server components for better performance
    serverComponentsExternalPackages: ['@mui/material'],
  },
  
  // Environment variables for debugging system
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    NEXT_PUBLIC_DEBUGGING_ENABLED: process.env.NEXT_PUBLIC_DEBUGGING_ENABLED || 'true',
    NEXT_PUBLIC_WEBSOCKET_URL: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws',
    NEXT_PUBLIC_DEBUGGING_DASHBOARD_PATH: process.env.NEXT_PUBLIC_DEBUGGING_DASHBOARD_PATH || '/debug',
  },
  
  // Webpack configuration for debugging tools
  webpack: (config, { dev, isServer }) => {
    // Add debugging-specific webpack configurations
    if (dev) {
      // Enable source maps for better debugging
      config.devtool = 'eval-source-map';
      
      // Add debugging dashboard specific optimizations
      config.resolve.alias = {
        ...config.resolve.alias,
        '@/debugging': './src/debugging',
      };
    }
    
    return config;
  },
  
  // Headers for debugging dashboard
  async headers() {
    return [
      {
        source: '/debug/:path*',
        headers: [
          {
            key: 'X-Debugging-Dashboard',
            value: 'true',
          },
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
        ],
      },
    ];
  },
  
  // Rewrites for debugging API calls
  async rewrites() {
    return [
      {
        source: '/api/debug/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/v1/debugging/:path*`,
      },
    ];
  },
  
  // Redirects for debugging dashboard
  async redirects() {
    return [
      {
        source: '/debugging',
        destination: '/debug',
        permanent: false,
      },
    ];
  },
  
  // Image optimization configuration
  images: {
    domains: ['localhost', '127.0.0.1'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  
  // TypeScript configuration
  typescript: {
    // Enable strict mode for better type checking
    ignoreBuildErrors: false,
  },
  
  // ESLint configuration
  eslint: {
    // Enable ESLint during builds
    ignoreDuringBuilds: false,
  },
  
  // Output configuration
  output: 'standalone',
  
  // Compression
  compress: true,
  
  // Power by header
  poweredByHeader: false,
  
  // React strict mode
  reactStrictMode: true,
  
  // SWC minification
  swcMinify: true,
};

export default nextConfig;
