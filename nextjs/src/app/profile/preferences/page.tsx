'use client';

import { ProtectedRoute } from '@/components/auth';
import { CustomerProfileLayout, CustomerPreferences } from '@/components/customer';

export default function PreferencesPage() {
  return (
    <ProtectedRoute>
      <CustomerProfileLayout>
        <CustomerPreferences />
      </CustomerProfileLayout>
    </ProtectedRoute>
  );
}