'use client';

import React from 'react';
import { ProtectedRoute } from '@/components/auth';
import AdminLayout from '@/components/layout/AdminLayout';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayoutWrapper({ children }: AdminLayoutProps) {
  return (
    <ProtectedRoute allowedUserTypes={['admin']}>
      <AdminLayout>
        {children}
      </AdminLayout>
    </ProtectedRoute>
  );
}