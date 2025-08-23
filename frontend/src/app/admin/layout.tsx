'use client';

import React from 'react';
import { AdminAuthProvider } from '@/contexts/AdminAuthContext';
import { AdminRouteGuard } from '@/components/admin/auth';
import AdminLayout from '@/components/layout/AdminLayout';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayoutWrapper({ children }: AdminLayoutProps) {
  return (
    <AdminAuthProvider>
      <AdminRouteGuard>
        <AdminLayout>
          {children}
        </AdminLayout>
      </AdminRouteGuard>
    </AdminAuthProvider>
  );
}