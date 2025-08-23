'use client';

import { GuestRoute, RegisterForm } from '@/components/auth';

export default function RegisterPage() {
  return (
    <GuestRoute>
      <div className="space-y-6">
        <div>
          <h2 className="text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Join our platform and start your journey today.
          </p>
        </div>
        <RegisterForm />
      </div>
    </GuestRoute>
  );
}