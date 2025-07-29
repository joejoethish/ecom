'use client';

import { ProtectedRoute } from '@/components/auth';
import { CustomerProfileLayout, Wishlist } from '@/components/customer';

export default function WishlistPage() {
  return (
    <ProtectedRoute>
      <CustomerProfileLayout>
        <Wishlist />
      </CustomerProfileLayout>
    </ProtectedRoute>
  );
}