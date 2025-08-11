'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { Breadcrumb } from '../common/Breadcrumb';
import { generateBreadcrumbs } from '@/utils/navigation';
import { SELLER_ROUTES } from '@/constants/routes';
import { 
  Home, 
  Package, 
  ShoppingCart, 
  User, 
  FileCheck, 
  CreditCard, 
  DollarSign 
} from 'lucide-react';

interface SellerLayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { name: 'Dashboard', path: SELLER_ROUTES.DASHBOARD, icon: Home },
  { name: 'Products', path: SELLER_ROUTES.PRODUCTS, icon: Package },
  { name: 'Orders', path: SELLER_ROUTES.ORDERS, icon: ShoppingCart },
  { name: 'Profile', path: SELLER_ROUTES.PROFILE, icon: User },
  { name: 'KYC Verification', path: SELLER_ROUTES.KYC, icon: FileCheck },
  { name: 'Bank Accounts', path: SELLER_ROUTES.BANK_ACCOUNTS, icon: CreditCard },
  { name: 'Payouts', path: SELLER_ROUTES.PAYOUTS, icon: DollarSign },
];

export function SellerLayout({ children }: SellerLayoutProps) {
  const pathname = usePathname();
  const breadcrumbs = generateBreadcrumbs(pathname);

  const isActive = (path: string) => {
    return pathname === path;
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-md">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Seller Panel</h2>
          {profile && (
            <p className="text-sm text-gray-600 mt-1">{profile.business_name}</p>
          )}
        </div>
        <nav className="mt-4">
          <ul>
            {navItems.map((item) => (
              <li key={item.path}>
                <Link 
                  href={item.path || '/seller'}
                  className={`flex items-center px-4 py-2 ${
                    isActive(item.path)
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className={`mr-2 h-5 w-5 ${
                    isActive(item.path) ? 'text-white' : 'text-gray-500'
                  }`} />
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <h1 className="text-lg font-semibold text-gray-900">
              {navItems.find((item) => isActive(item.path))?.name || &apos;Seller Panel&apos;}
            </h1>
            <div className="flex items-center space-x-4">
              {profile && (
                <div className="flex items-center">
                  <span className={`inline-block h-3 w-3 rounded-full mr-2 ${
                    profile.verification_status === 'VERIFIED' 
                      ? 'bg-green-500' 
                      : profile.verification_status === 'PENDING' 
                        ? 'bg-yellow-500' 
                        : 'bg-red-500'
                  }`}></span>
                  <span className="text-sm text-gray-600">{profile.verification_status_display}</span>
                </div>
              )}
              <Link href="/" className="text-sm text-blue-600 hover:text-blue-800">
                Back to Store
              </Link>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-4">
            <Breadcrumb items={breadcrumbs} />
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}