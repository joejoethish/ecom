'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import { Layout } from '@/components/layout/Layout';
import { ProductGrid } from '@/components/products/ProductGrid';
import { Button } from '@/components/ui/Button';

// Mock data for demonstration
const mockProducts = [
  {
    id: '1',
    name: 'iPhone 15 Pro Max (Natural Titanium, 256GB)',
    price: 134900,
    originalPrice: 159900,
    rating: 4.5,
    reviewCount: 12543,
    image: '/api/placeholder/300/300',
    brand: 'Apple',
    features: ['A17 Pro Chip', '48MP Camera System', '5G Ready'],
    freeDelivery: true,
    exchangeOffer: true
  },
  {
    id: '2',
    name: 'Samsung Galaxy S24 Ultra (Titanium Black, 512GB)',
    price: 129999,
    originalPrice: 149999,
    rating: 4.3,
    reviewCount: 8765,
    image: '/api/placeholder/300/300',
    brand: 'Samsung',
    features: ['200MP Camera', 'S Pen Included', 'AI Features'],
    freeDelivery: true,
    exchangeOffer: true
  },
  {
    id: '3',
    name: 'MacBook Air M3 (13-inch, Midnight, 8GB RAM, 256GB SSD)',
    price: 114900,
    originalPrice: 134900,
    rating: 4.7,
    reviewCount: 5432,
    image: '/api/placeholder/300/300',
    brand: 'Apple',
    features: ['M3 Chip', '18-hour Battery', 'Liquid Retina Display'],
    freeDelivery: true,
    exchangeOffer: false
  },
  {
    id: '4',
    name: 'Sony WH-1000XM5 Wireless Noise Canceling Headphones',
    price: 29990,
    originalPrice: 34990,
    rating: 4.6,
    reviewCount: 3210,
    image: '/api/placeholder/300/300',
    brand: 'Sony',
    features: ['30-hour Battery', 'Industry Leading ANC', 'Quick Charge'],
    freeDelivery: true,
    exchangeOffer: false
  },
  {
    id: '5',
    name: 'Dell XPS 13 Plus (Intel i7, 16GB RAM, 512GB SSD)',
    price: 149999,
    originalPrice: 179999,
    rating: 4.4,
    reviewCount: 2876,
    image: '/api/placeholder/300/300',
    brand: 'Dell',
    features: ['12th Gen Intel i7', '13.4" OLED Display', 'Premium Build'],
    freeDelivery: true,
    exchangeOffer: true
  },
  {
    id: '6',
    name: 'iPad Pro 12.9-inch (M2, Wi-Fi, 128GB) - Space Gray',
    price: 112900,
    originalPrice: 129900,
    rating: 4.8,
    reviewCount: 4567,
    image: '/api/placeholder/300/300',
    brand: 'Apple',
    features: ['M2 Chip', 'Liquid Retina XDR Display', 'Apple Pencil Support'],
    freeDelivery: true,
    exchangeOffer: true
  }
];

const categories = [
  'Electronics',
  'Fashion',
  'Home & Kitchen',
  'Books',
  'Sports',
  'Beauty',
  'Grocery',
  'Toys'
];

const sortOptions = [
  { label: 'Popularity', value: 'popularity' },
  { label: 'Price -- Low to High', value: 'price_asc' },
  { label: 'Price -- High to Low', value: 'price_desc' },
  { label: 'Newest First', value: 'newest' },
  { label: 'Customer Rating', value: 'rating' }
];

function ProductsPageContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get('search') || '';
  const categorySlug = searchParams.get('category') || '';
  const [products, setProducts] = useState(mockProducts);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState('popularity');
  const [showFilters, setShowFilters] = useState(false);
  
  useEffect(() => {
    // Simulate API call
    setLoading(true);
    setTimeout(() => {
      setProducts(mockProducts);
      setLoading(false);
    }, 1000);
  }, [query, categorySlug]);

  const handleSortChange = (value: string) => {
    setSortBy(value);
    // Implement sorting logic here
    const sortedProducts = [...products];
    switch (value) {
      case 'price_asc':
        sortedProducts.sort((a, b) => a.price - b.price);
        break;
      case 'price_desc':
        sortedProducts.sort((a, b) => b.price - a.price);
        break;
      case 'rating':
        sortedProducts.sort((a, b) => b.rating - a.rating);
        break;
      default:
        // Keep original order for popularity
        break;
    }
    setProducts(sortedProducts);
  };
  
  return (
    <Layout>
      <div className="bg-gray-50 min-h-screen">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Breadcrumb */}
          <nav className="flex mb-4" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2 text-sm">
              <li>
                <a href="/" className="text-blue-600 hover:text-blue-700">Home</a>
              </li>
              <li>
                <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </li>
              <li className="text-gray-500">Products</li>
              {categorySlug && (
                <>
                  <li>
                    <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </li>
                  <li className="text-gray-900 font-medium capitalize">{categorySlug.replace('-', ' ')}</li>
                </>
              )}
            </ol>
          </nav>

          <div className="flex flex-col lg:flex-row gap-6">
            {/* Sidebar Filters */}
            <div className={`lg:w-64 ${showFilters ? 'block' : 'hidden lg:block'}`}>
              <div className="bg-white rounded-lg shadow-sm p-4 sticky top-4">
                <h3 className="font-semibold text-gray-900 mb-4">Filters</h3>
                
                {/* Categories */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Categories</h4>
                  <div className="space-y-2">
                    {categories.map((category) => (
                      <label key={category} className="flex items-center">
                        <input
                          type="checkbox"
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{category}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Price Range */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Price Range</h4>
                  <div className="space-y-2">
                    {[
                      'Under ₹1,000',
                      '₹1,000 - ₹5,000',
                      '₹5,000 - ₹10,000',
                      '₹10,000 - ₹25,000',
                      'Over ₹25,000'
                    ].map((range) => (
                      <label key={range} className="flex items-center">
                        <input
                          type="checkbox"
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{range}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Brand */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Brand</h4>
                  <div className="space-y-2">
                    {['Apple', 'Samsung', 'Sony', 'Dell', 'HP', 'Lenovo'].map((brand) => (
                      <label key={brand} className="flex items-center">
                        <input
                          type="checkbox"
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{brand}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Rating */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Customer Rating</h4>
                  <div className="space-y-2">
                    {[4, 3, 2, 1].map((rating) => (
                      <label key={rating} className="flex items-center">
                        <input
                          type="checkbox"
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 flex items-center">
                          {rating}★ & above
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="flex-1">
              {/* Header */}
              <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                  <div className="mb-4 sm:mb-0">
                    <h1 className="text-xl font-semibold text-gray-900">
                      {query ? `Search results for "${query}"` : 'All Products'}
                    </h1>
                    <p className="text-sm text-gray-600 mt-1">
                      Showing {products.length} results
                    </p>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {/* Mobile Filter Toggle */}
                    <Button
                      variant="outline"
                      size="sm"
                      className="lg:hidden"
                      onClick={() => setShowFilters(!showFilters)}
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                      </svg>
                      Filters
                    </Button>

                    {/* Sort Dropdown */}
                    <div className="relative">
                      <select
                        value={sortBy}
                        onChange={(e) => handleSortChange(e.target.value)}
                        className="appearance-none bg-white border border-gray-300 rounded-md px-4 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {sortOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            Sort by: {option.label}
                          </option>
                        ))}
                      </select>
                      <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Products Grid */}
              <ProductGrid products={products} loading={loading} />

              {/* Load More Button */}
              {!loading && products.length > 0 && (
                <div className="text-center mt-8">
                  <Button variant="outline" size="lg">
                    Load More Products
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ProductsPageContent />
    </Suspense>
  );
}