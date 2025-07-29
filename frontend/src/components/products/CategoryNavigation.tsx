'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Category } from '@/types';
import { ROUTES } from '@/constants';

interface CategoryNavigationProps {
  categories: Category[];
  selectedCategorySlug?: string;
  onSelectCategory?: (categorySlug: string) => void;
}

export function CategoryNavigation({ 
  categories, 
  selectedCategorySlug,
  onSelectCategory 
}: CategoryNavigationProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Group categories by parent
  const rootCategories = categories.filter(cat => !cat.parent);
  const categoryMap = categories.reduce((acc, cat) => {
    if (cat.parent?.id) {
      if (!acc[cat.parent.id]) {
        acc[cat.parent.id] = [];
      }
      acc[cat.parent.id].push(cat);
    }
    return acc;
  }, {} as Record<string, Category[]>);

  const toggleExpand = (categoryId: string) => {
    setExpanded(prev => ({
      ...prev,
      [categoryId]: !prev[categoryId]
    }));
  };

  const handleCategoryClick = (slug: string) => {
    if (onSelectCategory) {
      onSelectCategory(slug);
    }
  };

  const renderCategory = (category: Category, level = 0) => {
    const hasChildren = categoryMap[category.id]?.length > 0;
    const isExpanded = expanded[category.id];
    const isSelected = category.slug === selectedCategorySlug;
    
    return (
      <div key={category.id} className="mb-1">
        <div className={`flex items-center ${level > 0 ? 'ml-' + (level * 4) : ''}`}>
          {hasChildren && (
            <button 
              onClick={() => toggleExpand(category.id)}
              className="mr-2 p-1 text-gray-500 hover:text-gray-700 focus:outline-none"
            >
              <svg 
                className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}
          
          <Link 
            href={category.slug ? ROUTES.PRODUCTS + `?category=${category.slug}` : ROUTES.PRODUCTS}
            onClick={() => handleCategoryClick(category.slug || '')}
            className={`py-1 px-2 text-sm rounded-md flex-grow ${
              isSelected 
                ? 'bg-blue-100 text-blue-700 font-medium' 
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            {category.name}
          </Link>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {categoryMap[category.id].map(child => renderCategory(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (!categories || categories.length === 0) {
    return (
      <div className="p-4 border rounded-lg bg-gray-50">
        <p className="text-gray-500 text-sm">No categories available</p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded-lg bg-white">
      <h3 className="font-medium text-gray-900 mb-3">Categories</h3>
      <div>
        <div className="mb-2">
          <Link 
            href={ROUTES.PRODUCTS}
            onClick={() => handleCategoryClick('')}
            className={`py-1 px-2 text-sm rounded-md block ${
              !selectedCategorySlug 
                ? 'bg-blue-100 text-blue-700 font-medium' 
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            All Products
          </Link>
        </div>
        {rootCategories.map(category => renderCategory(category))}
      </div>
    </div>
  );
}