'use client';

import { GuestRoute, RegisterForm } from '@/components/auth';

export default function RegisterPage() {
  return (
    <GuestRoute>
      <RegisterForm />
    </GuestRoute>
  );
}