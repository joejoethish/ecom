'use client';

import { ProtectedRoute } from '@/components/auth';
import { CustomerProfileLayout, CustomerProfile } from '@/components/customer';

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <CustomerProfileLayout>
        <CustomerProfile />
      </CustomerProfileLayout>
    </ProtectedRoute>
  );
}