'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Button } from '@/components/ui/Button';
import { useAppDispatch } from '@/store';
import { addToCart } from '@/store/slices/cartSlice';
import toast from 'react-hot-toast';

// Mock product data
const mockProduct = {
  id: '1',
  name: 'iPhone 15 Pro Max (Natural Titanium, 256GB)',
  brand: 'Apple',
  price: 134900,
  originalPrice: 159900,
  rating: 4.5,
  reviewCount: 12543,
  images: [
    '/api/placeholder/600/600',
    '/api/placeholder/600/600',
    '/api/placeholder/600/600',
    '/api/placeholder/600/600'
  ],
  features: [
    'A17 Pro Chip with 6-core GPU',
    '48MP Main Camera with 2x Telephoto',
    '5x Telephoto Camera',
    'Action Button',
    'USB-C Connector',
    'All-Day Battery Life',
    'Titanium Design',
    'Ceramic Shield Front'
  ],
  specifications: {
    'Display': '6.7-inch Super Retina XDR display',
    'Chip': 'A17 Pro chip',
    'Camera': '48MP Main, 12MP Ultra Wide, 12MP 2x Telephoto, 12MP 5x Telephoto',
    'Storage': '256GB',
    'Battery': 'Up to 29 hours video playback',
    'Operating System': 'iOS 17',
    'Connectivity': '5G, Wi-Fi 6E, Bluetooth 5.3',
    'Water Resistance': 'IP68'
  },
  highlights: [
    'FORGED IN TITANIUM — iPhone 15 Pro Max has a strong and light titanium design with a textured matte-glass back. It also features a Customizable Action Button and a USB-C connector.',
    'ADVANCED CAMERA SYSTEM — Get incredible framing flexibility with 7 pro lenses. Capture super high-resolution photos with more color and detail using the 48MP Main camera.',
    'POWERFUL PRO CAMERA FEATURES — Take your videos to a whole new level with 4K ProRes and new Action mode. And with improved Night mode, you can capture stunning low-light photos.',
    'A17 PRO CHIP — The most powerful chip in a smartphone delivers incredible performance for demanding workflows and next-level gaming.'
  ],
  inStock: true,
  freeDelivery: true,
  exchangeOffer: true,
  warranty: '1 Year Limited Warranty'
};

export default function ProductDetailPage() {
  const params = useParams();
  const dispatch = useAppDispatch();
  const [selectedImage, setSelectedImage] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [activeTab, setActiveTab] = useState('features');
  const [isWishlisted, setIsWishlisted] = useState(false);

  const discountPercentage = Math.round(((mockProduct.originalPrice - mockProduct.price) / mockProduct.originalPrice) * 100);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  const handleAddToCart = async () => {
    try {
      await dispatch(addToCart({ 
        productId: mockProduct.id, 
        quantity 
      })).unwrap();
      toast.success('Added to cart successfully!');
    } catch (error) {
      toast.error('Failed to add to cart');
    }
  };

  const renderStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <svg key={i} className="w-4 h-4 text-yellow-400 fill-current" viewBox="0 0 20 20">
          <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
        </svg>
      );
    }

    if (hasHalfStar) {
      stars.push(
        <svg key="half" className="w-4 h-4 text-yellow-400" viewBox="0 0 20 20">
          <defs>
            <linearGradient id="half-fill">
              <stop offset="50%" stopColor="currentColor" />
              <stop offset="50%" stopColor="transparent" />
            </linearGradient>
          </defs>
          <path fill="url(#half-fill)" d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
        </svg>
      );
    }

    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(
        <svg key={`empty-${i}`} className="w-4 h-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
        </svg>
      );
    }

    return stars;
  };

  return (
    <Layout>
      <div className="bg-gray-50 min-h-screen">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Breadcrumb */}
          <nav className="flex mb-4" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2 text-sm">
              <li><a href="/" className="text-blue-600 hover:text-blue-700">Home</a></li>
              <li><span className="text-gray-400">/</span></li>
              <li><a href="/products" className="text-blue-600 hover:text-blue-700">Products</a></li>
              <li><span className="text-gray-400">/</span></li>
              <li className="text-gray-500">Electronics</li>
              <li><span className="text-gray-400">/</span></li>
              <li className="text-gray-900 font-medium">{mockProduct.name}</li>
            </ol>
          </nav>

          <div className="bg-white rounded-lg shadow-sm">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-6">
              {/* Product Images */}
              <div className="space-y-4">
                {/* Main Image */}
                <div className="aspect-square bg-gray-50 rounded-lg overflow-hidden">
                  <img
                    src={mockProduct.images[selectedImage]}
                    alt={mockProduct.name}
                    className="w-full h-full object-contain"
                  />
                </div>

                {/* Thumbnail Images */}
                <div className="flex space-x-2">
                  {mockProduct.images.map((image, index) => (
                    <button
                      key={index}
                      onClick={() => setSelectedImage(index)}
                      className={`w-16 h-16 rounded-lg overflow-hidden border-2 ${
                        selectedImage === index ? 'border-blue-500' : 'border-gray-200'
                      }`}
                    >
                      <img
                        src={image}
                        alt={`${mockProduct.name} ${index + 1}`}
                        className="w-full h-full object-contain"
                      />
                    </button>
                  ))}
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-4">
                  <Button
                    variant="outline"
                    className="flex-1 flex items-center justify-center space-x-2"
                    onClick={() => setIsWishlisted(!isWishlisted)}
                  >
                    <svg
                      className={`w-5 h-5 ${isWishlisted ? 'text-red-500 fill-current' : 'text-gray-400'}`}
                      fill={isWishlisted ? 'currentColor' : 'none'}
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                      />
                    </svg>
                    <span>Wishlist</span>
                  </Button>
                  <Button variant="outline" className="flex-1">
                    Share
                  </Button>
                </div>
              </div>

              {/* Product Info */}
              <div className="space-y-6">
                {/* Brand and Name */}
                <div>
                  <p className="text-sm text-gray-500 mb-1">{mockProduct.brand}</p>
                  <h1 className="text-2xl font-semibold text-gray-900">{mockProduct.name}</h1>
                </div>

                {/* Rating */}
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <div className="flex items-center">
                      {renderStars(mockProduct.rating)}
                    </div>
                    <span className="text-sm font-medium text-gray-900">{mockProduct.rating}</span>
                  </div>
                  <span className="text-sm text-gray-500">
                    ({mockProduct.reviewCount.toLocaleString()} reviews)
                  </span>
                </div>

                {/* Price */}
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl font-bold text-gray-900">
                      {formatPrice(mockProduct.price)}
                    </span>
                    <span className="text-lg text-gray-500 line-through">
                      {formatPrice(mockProduct.originalPrice)}
                    </span>
                    <span className="text-lg text-green-600 font-medium">
                      {discountPercentage}% off
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">inclusive of all taxes</p>
                </div>

                {/* Offers */}
                <div className="space-y-3">
                  <h3 className="font-medium text-gray-900">Available offers</h3>
                  <div className="space-y-2">
                    {mockProduct.freeDelivery && (
                      <div className="flex items-center text-sm text-green-600">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Free Delivery
                      </div>
                    )}
                    {mockProduct.exchangeOffer && (
                      <div className="flex items-center text-sm text-blue-600">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                        Exchange Offer
                      </div>
                    )}
                    <div className="flex items-center text-sm text-purple-600">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                      Bank Offer: 10% off on HDFC Bank Cards
                    </div>
                  </div>
                </div>

                {/* Quantity and Actions */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <label className="text-sm font-medium text-gray-900">Quantity:</label>
                    <div className="flex items-center border border-gray-300 rounded">
                      <button
                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                        className="px-3 py-1 hover:bg-gray-100"
                      >
                        -
                      </button>
                      <span className="px-4 py-1 border-x border-gray-300">{quantity}</span>
                      <button
                        onClick={() => setQuantity(quantity + 1)}
                        className="px-3 py-1 hover:bg-gray-100"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  <div className="flex space-x-4">
                    <Button
                      size="lg"
                      className="flex-1 bg-orange-500 hover:bg-orange-600"
                      onClick={handleAddToCart}
                    >
                      Add to Cart
                    </Button>
                    <Button size="lg" className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black">
                      Buy Now
                    </Button>
                  </div>
                </div>

                {/* Delivery Info */}
                <div className="border-t pt-4">
                  <h3 className="font-medium text-gray-900 mb-2">Delivery</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center text-green-600">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Free delivery by tomorrow
                    </div>
                    <div className="flex items-center text-gray-600">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                      </svg>
                      7 days replacement policy
                    </div>
                    <div className="flex items-center text-gray-600">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      {mockProduct.warranty}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Product Details Tabs */}
            <div className="border-t">
              <div className="flex border-b">
                {['features', 'specifications', 'highlights'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-6 py-3 text-sm font-medium capitalize ${
                      activeTab === tab
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <div className="p-6">
                {activeTab === 'features' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {mockProduct.features.map((feature, index) => (
                      <div key={index} className="flex items-center">
                        <svg className="w-4 h-4 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-sm text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'specifications' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {Object.entries(mockProduct.specifications).map(([key, value]) => (
                      <div key={key} className="border-b border-gray-200 pb-2">
                        <dt className="text-sm font-medium text-gray-900">{key}</dt>
                        <dd className="text-sm text-gray-600 mt-1">{value}</dd>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'highlights' && (
                  <div className="space-y-4">
                    {mockProduct.highlights.map((highlight, index) => (
                      <div key={index} className="flex">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                        <p className="text-sm text-gray-700">{highlight}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}