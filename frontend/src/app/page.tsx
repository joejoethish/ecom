'use client';

import { Layout } from '@/components/layout/Layout';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useCategories } from '@/hooks/useCategories';

export default function Home() {
  const [currentSlide, setCurrentSlide] = useState(0);
  
  // Use dynamic categories
  const { featuredCategories, loading: categoriesLoading, error: categoriesError } = useCategories({
    featured: true,
    autoFetch: true
  });
  
  const bannerSlides = [
    {
      id: 1,
      title: "Big Billion Days",
      subtitle: "The Biggest Sale of the Year",
      description: "Up to 80% off on Electronics, Fashion & More",
      image: "/api/placeholder/800/300",
      bgColor: "bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500"
    },
    {
      id: 2,
      title: "Fashion Fest",
      subtitle: "Trendy Styles for Everyone",
      description: "50-70% off on Top Fashion Brands",
      image: "/api/placeholder/800/300",
      bgColor: "bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500"
    },
    {
      id: 3,
      title: "Electronics Sale",
      subtitle: "Latest Gadgets & Tech",
      description: "Best Deals on Smartphones, Laptops & More",
      image: "/api/placeholder/800/300",
      bgColor: "bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500"
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % bannerSlides.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [bannerSlides.length]);

  // Use dynamic categories or fallback to static ones
  const categories = featuredCategories.length > 0 ? featuredCategories : [
    { name: "Mobiles", icon: "📱", href: "/category/mobiles" },
    { name: "Fashion", icon: "👗", href: "/category/fashion" },
    { name: "Electronics", icon: "💻", href: "/category/electronics" },
    { name: "Home & Furniture", icon: "🏠", href: "/category/home-furniture" },
    { name: "Appliances", icon: "🔌", href: "/category/appliances" },
    { name: "Travel", icon: "✈️", href: "/category/travel" },
    { name: "Beauty, Toys & More", icon: "💄", href: "/category/beauty-toys" },
    { name: "Two Wheelers", icon: "🏍️", href: "/category/two-wheelers" },
    { name: "Grocery", icon: "🛒", href: "/category/grocery" }
  ];

  const topOffers = [
    { 
      title: "Top Offers", 
      subtitle: "On Everything", 
      image: "/api/placeholder/200/200",
      bgColor: "bg-gradient-to-br from-orange-400 to-red-500"
    },
    { 
      title: "Mobiles", 
      subtitle: "Top Rated", 
      image: "/api/placeholder/200/200",
      bgColor: "bg-gradient-to-br from-blue-400 to-purple-500"
    },
    { 
      title: "Fashion", 
      subtitle: "Best Sellers", 
      image: "/api/placeholder/200/200",
      bgColor: "bg-gradient-to-br from-pink-400 to-red-400"
    },
    { 
      title: "Electronics", 
      subtitle: "Great Deals", 
      image: "/api/placeholder/200/200",
      bgColor: "bg-gradient-to-br from-green-400 to-blue-500"
    },
    { 
      title: "Home & Kitchen", 
      subtitle: "Essentials", 
      image: "/api/placeholder/200/200",
      bgColor: "bg-gradient-to-br from-yellow-400 to-orange-500"
    },
    { 
      title: "Appliances", 
      subtitle: "Big Discounts", 
      image: "/api/placeholder/200/200",
      bgColor: "bg-gradient-to-br from-purple-400 to-pink-500"
    }
  ];

  const dealProducts = [
    { 
      id: 1,
      name: "iPhone 15 Pro", 
      originalPrice: "₹1,34,900", 
      discountPrice: "₹1,19,900",
      discount: "11% off",
      image: "/api/placeholder/200/200",
      rating: 4.5,
      reviews: 1234
    },
    { 
      id: 2,
      name: "Samsung Galaxy S24", 
      originalPrice: "₹89,999", 
      discountPrice: "₹74,999",
      discount: "17% off",
      image: "/api/placeholder/200/200",
      rating: 4.3,
      reviews: 856
    },
    { 
      id: 3,
      name: "MacBook Air M2", 
      originalPrice: "₹1,14,900", 
      discountPrice: "₹99,900",
      discount: "13% off",
      image: "/api/placeholder/200/200",
      rating: 4.7,
      reviews: 2341
    },
    { 
      id: 4,
      name: "Sony WH-1000XM5", 
      originalPrice: "₹29,990", 
      discountPrice: "₹24,990",
      discount: "17% off",
      image: "/api/placeholder/200/200",
      rating: 4.6,
      reviews: 567
    },
    { 
      id: 5,
      name: "Dell XPS 13", 
      originalPrice: "₹1,05,000", 
      discountPrice: "₹89,999",
      discount: "14% off",
      image: "/api/placeholder/200/200",
      rating: 4.4,
      reviews: 432
    },
    { 
      id: 6,
      name: "iPad Pro 11", 
      originalPrice: "₹81,900", 
      discountPrice: "₹71,900",
      discount: "12% off",
      image: "/api/placeholder/200/200",
      rating: 4.5,
      reviews: 789
    }
  ];

  return (
    <Layout>
      <div style={{ backgroundColor: '#f1f3f6', minHeight: '100vh' }}>
        {/* Main Container */}
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          
          {/* Categories Bar - Flipkart Style */}
          <div style={{ backgroundColor: 'white', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              padding: '8px 16px', 
              overflowX: 'auto' 
            }}>
              {categories.map((category) => (
                <Link
                  key={category.name}
                  href={category.href || '/products'}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    minWidth: '80px',
                    padding: '8px',
                    textDecoration: 'none',
                    borderRadius: '8px',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#e3f2fd';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <div style={{ fontSize: '24px', marginBottom: '4px' }}>
                    {category.icon}
                  </div>
                  <span style={{ 
                    fontSize: '12px', 
                    fontWeight: '500', 
                    color: '#424242', 
                    textAlign: 'center',
                    lineHeight: '1.2'
                  }}>
                    {category.name}
                  </span>
                </Link>
              ))}
            </div>
          </div>

          {/* Main Content Area */}
          <div style={{ display: 'flex', gap: '16px', padding: '16px' }}>
            
            {/* Left Sidebar - Categories */}
            <div style={{ 
              display: 'none', 
              width: '256px', 
              backgroundColor: 'white', 
              borderRadius: '8px', 
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)', 
              height: 'fit-content' 
            }} className="lg:block">
              <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
                <h3 style={{ fontWeight: '600', color: '#212121', margin: 0 }}>Top Categories</h3>
              </div>
              <div style={{ padding: '8px' }}>
                {categories.slice(0, 6).map((category) => (
                  <Link
                    key={category.name}
                    href={category.href || '/products'}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '12px',
                      textDecoration: 'none',
                      borderRadius: '8px',
                      transition: 'background-color 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f5f5f5';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <span style={{ fontSize: '18px', marginRight: '12px' }}>{category.icon}</span>
                    <span style={{ fontSize: '14px', fontWeight: '500', color: '#424242' }}>{category.name}</span>
                  </Link>
                ))}
              </div>
            </div>

            {/* Main Content */}
            <div style={{ flex: 1 }}>
              
              {/* Hero Banner Carousel */}
              <div style={{ 
                position: 'relative', 
                height: '320px', 
                borderRadius: '8px', 
                overflow: 'hidden', 
                marginBottom: '16px', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
              }}>
                {bannerSlides.map((slide, index) => (
                  <div
                    key={slide.id}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      transform: `translateX(${index === currentSlide ? '0%' : index < currentSlide ? '-100%' : '100%'})`,
                      transition: 'transform 0.5s ease-in-out'
                    }}
                  >
                    <div style={{
                      background: slide.bgColor.includes('gradient') 
                        ? 'linear-gradient(135deg, #ff9800 0%, #f44336 100%)'
                        : slide.bgColor,
                      height: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0 32px',
                      color: 'white'
                    }}>
                      <div style={{ flex: 1 }}>
                        <h1 style={{ 
                          fontSize: '32px', 
                          fontWeight: 'bold', 
                          marginBottom: '8px',
                          margin: 0
                        }}>{slide.title}</h1>
                        <p style={{ 
                          fontSize: '20px', 
                          marginBottom: '8px', 
                          opacity: 0.9,
                          margin: '8px 0'
                        }}>{slide.subtitle}</p>
                        <p style={{ 
                          fontSize: '16px', 
                          marginBottom: '24px', 
                          opacity: 0.8,
                          margin: '8px 0 24px 0'
                        }}>{slide.description}</p>
                        <button style={{
                          backgroundColor: 'white',
                          color: '#212121',
                          padding: '12px 24px',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '16px',
                          fontWeight: '600',
                          cursor: 'pointer',
                          transition: 'background-color 0.2s'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f5f5f5';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'white';
                        }}>
                          Shop Now
                        </button>
                      </div>
                      <div style={{ 
                        display: 'none', 
                        flex: 1, 
                        textAlign: 'right' 
                      }} className="md:block">
                        <div style={{
                          width: '192px',
                          height: '192px',
                          backgroundColor: 'rgba(255,255,255,0.1)',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '64px',
                          marginLeft: 'auto'
                        }}>
                          🛍️
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Carousel Indicators */}
                <div style={{
                  position: 'absolute',
                  bottom: '16px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  display: 'flex',
                  gap: '8px'
                }}>
                  {bannerSlides.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentSlide(index)}
                      style={{
                        width: index === currentSlide ? '24px' : '8px',
                        height: '8px',
                        borderRadius: '4px',
                        border: 'none',
                        backgroundColor: index === currentSlide ? 'white' : 'rgba(255,255,255,0.5)',
                        cursor: 'pointer',
                        transition: 'all 0.3s'
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Top Offers Section */}
              <div style={{ 
                backgroundColor: 'white', 
                borderRadius: '8px', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)', 
                marginBottom: '16px' 
              }}>
                <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
                  <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#212121', margin: 0 }}>Top Offers</h2>
                </div>
                <div style={{ padding: '16px' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', 
                    gap: '16px' 
                  }}>
                    {topOffers.map((offer, index) => (
                      <div key={index} style={{ textAlign: 'center', cursor: 'pointer' }}>
                        <div style={{
                          background: 'linear-gradient(135deg, #ff9800 0%, #f44336 100%)',
                          borderRadius: '8px',
                          padding: '16px',
                          marginBottom: '8px',
                          transition: 'transform 0.2s'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'scale(1.05)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'scale(1)';
                        }}>
                          <div style={{
                            width: '64px',
                            height: '64px',
                            backgroundColor: 'rgba(255,255,255,0.2)',
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            margin: '0 auto',
                            fontSize: '24px'
                          }}>
                            🎯
                          </div>
                        </div>
                        <h3 style={{ 
                          fontWeight: '600', 
                          fontSize: '14px', 
                          color: '#212121',
                          margin: '0 0 4px 0'
                        }}>{offer.title}</h3>
                        <p style={{ 
                          fontSize: '12px', 
                          color: '#757575',
                          margin: 0
                        }}>{offer.subtitle}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Deals of the Day */}
              <div style={{ 
                backgroundColor: 'white', 
                borderRadius: '8px', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)', 
                marginBottom: '16px' 
              }}>
                <div style={{ 
                  padding: '16px', 
                  borderBottom: '1px solid #e0e0e0', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between' 
                }}>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#212121', margin: '0 0 4px 0' }}>Deals of the Day</h2>
                    <p style={{ fontSize: '14px', color: '#757575', margin: 0 }}>Limited time offers</p>
                  </div>
                  <Link href="/deals" style={{ 
                    color: '#2196f3', 
                    fontWeight: '500', 
                    fontSize: '14px',
                    textDecoration: 'none'
                  }}>
                    View All
                  </Link>
                </div>
                <div style={{ padding: '16px' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
                    gap: '16px' 
                  }}>
                    {dealProducts.map((product) => (
                      <div key={product.id} style={{
                        border: '1px solid #e0e0e0',
                        borderRadius: '8px',
                        padding: '12px',
                        cursor: 'pointer',
                        transition: 'box-shadow 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.boxShadow = 'none';
                      }}>
                        <div style={{
                          aspectRatio: '1',
                          backgroundColor: '#f5f5f5',
                          borderRadius: '8px',
                          marginBottom: '12px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          transition: 'background-color 0.2s'
                        }}>
                          <span style={{ fontSize: '32px' }}>📱</span>
                        </div>
                        <h3 style={{ 
                          fontWeight: '500', 
                          fontSize: '14px', 
                          color: '#212121', 
                          marginBottom: '4px',
                          lineHeight: '1.3',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                        }}>{product.name}</h3>
                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{
                            fontSize: '12px',
                            backgroundColor: '#4caf50',
                            color: 'white',
                            padding: '2px 4px',
                            borderRadius: '3px',
                            marginRight: '4px'
                          }}>★ {product.rating}</span>
                          <span style={{ fontSize: '12px', color: '#757575' }}>({product.reviews})</span>
                        </div>
                        <div style={{ marginBottom: '4px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '14px', color: '#212121' }}>{product.discountPrice}</span>
                            <span style={{ fontSize: '12px', color: '#757575', textDecoration: 'line-through' }}>{product.originalPrice}</span>
                          </div>
                          <span style={{ fontSize: '12px', color: '#4caf50', fontWeight: '500' }}>{product.discount}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Features Section - Flipkart Style */}
              <div style={{ 
                backgroundColor: 'white', 
                borderRadius: '8px', 
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
              }}>
                <div style={{ padding: '24px' }}>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                    gap: '24px' 
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{
                        width: '48px',
                        height: '48px',
                        backgroundColor: '#e3f2fd',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 12px auto'
                      }}>
                        <svg style={{ width: '24px', height: '24px', color: '#2196f3' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                      </div>
                      <h3 style={{ fontWeight: '600', fontSize: '14px', color: '#212121', marginBottom: '4px' }}>Free Delivery</h3>
                      <p style={{ fontSize: '12px', color: '#757575', margin: 0 }}>On orders above ₹499</p>
                    </div>

                    <div style={{ textAlign: 'center' }}>
                      <div style={{
                        width: '48px',
                        height: '48px',
                        backgroundColor: '#e8f5e8',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 12px auto'
                      }}>
                        <svg style={{ width: '24px', height: '24px', color: '#4caf50' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <h3 style={{ fontWeight: '600', fontSize: '14px', color: '#212121', marginBottom: '4px' }}>Quality Assured</h3>
                      <p style={{ fontSize: '12px', color: '#757575', margin: 0 }}>100% authentic products</p>
                    </div>

                    <div style={{ textAlign: 'center' }}>
                      <div style={{
                        width: '48px',
                        height: '48px',
                        backgroundColor: '#fff3e0',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 12px auto'
                      }}>
                        <svg style={{ width: '24px', height: '24px', color: '#ff9800' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </div>
                      <h3 style={{ fontWeight: '600', fontSize: '14px', color: '#212121', marginBottom: '4px' }}>Easy Returns</h3>
                      <p style={{ fontSize: '12px', color: '#757575', margin: 0 }}>7 days return policy</p>
                    </div>

                    <div style={{ textAlign: 'center' }}>
                      <div style={{
                        width: '48px',
                        height: '48px',
                        backgroundColor: '#f3e5f5',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 12px auto'
                      }}>
                        <svg style={{ width: '24px', height: '24px', color: '#9c27b0' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                      </div>
                      <h3 style={{ fontWeight: '600', fontSize: '14px', color: '#212121', marginBottom: '4px' }}>Secure Payments</h3>
                      <p style={{ fontSize: '12px', color: '#757575', margin: 0 }}>Safe & secure transactions</p>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}