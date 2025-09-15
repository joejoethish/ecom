'use client';

import React from 'react';
import Link from 'next/link';
import { Category } from '@/services/categoriesApi';

interface CategoryBreadcrumbProps {
  category: Category;
}

export function CategoryBreadcrumb({ category }: CategoryBreadcrumbProps) {
  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center space-x-2 py-3 text-sm">
          <Link
            href="/"
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            Home
          </Link>
          
          <svg
            className="h-4 w-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
          
          <Link
            href="/products"
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            Products
          </Link>
          
          <svg
            className="h-4 w-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
          
          <span className="text-gray-900 font-medium">
            {category.name}
          </span>
        </div>
      </div>
    </nav>
  );
}