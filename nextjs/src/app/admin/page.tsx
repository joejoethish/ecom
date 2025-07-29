'use client';

import { ProtectedRoute } from '@/components/auth';
import AdminDashboard from '@/components/admin/AdminDashboard';

export default function AdminPage() {
  return (
    <ProtectedRoute allowedUserTypes={['admin']}>
      <AdminDashboard />
    </ProtectedRoute>
  );
}