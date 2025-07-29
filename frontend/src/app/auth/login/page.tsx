'use client';

import { Suspense } from 'react';
import { GuestRoute, LoginForm } from '@/components/auth';

export default function LoginPage() {
  return (
    <GuestRoute>
      <Suspense fallback={<div>Loading...</div>}>
        <LoginForm />
      </Suspense>
    </GuestRoute>
  );
}