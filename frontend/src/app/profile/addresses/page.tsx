'use client';

import { ProtectedRoute } from '@/components/auth';
import { CustomerProfileLayout, AddressManagement } from '@/components/customer';

export default function AddressesPage() {
  return (
    <ProtectedRoute>
      <CustomerProfileLayout>
        <AddressManagement />
      </CustomerProfileLayout>
    </ProtectedRoute>
  );
}