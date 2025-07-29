'use client';

import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { Breadcrumb } from '../common/Breadcrumb';
import { SkipToContent } from '../common/SkipToContent';
import { usePathname } from 'next/navigation';
import { generateBreadcrumbs } from '@/utils/navigation';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { measureRenderTime } from '@/utils/performance';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const pathname = usePathname();
  const breadcrumbs = generateBreadcrumbs(pathname);
  const isLargeScreen = useMediaQuery('(min-width: 1024px)');
  
  return measureRenderTime('MainLayout', () => (
    <div className="min-h-screen flex flex-col">
      <SkipToContent />
      <Header />
      <div className="container mx-auto px-4 py-2">
        <Breadcrumb items={breadcrumbs} />
      </div>
      <main id="main-content" className={`flex-1 container mx-auto px-4 py-6 ${isLargeScreen ? 'max-w-6xl' : ''}`}>
        {children}
      </main>
      <Footer />
    </div>
  ));
}