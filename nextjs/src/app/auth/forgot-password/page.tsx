'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { ForgotPasswordForm } from '@/components/auth/ForgotPasswordForm';
import { ROUTES } from '@/constants';

export default function ForgotPasswordPage() {
  const router = useRouter();

  const handleSuccess = () => {
    // Stay on the same page to show success message
    // User can navigate back to login from the success screen
  };

  const handleBackToLogin = () => {
    router.push(ROUTES.LOGIN);
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f5f5f5',
      padding: '20px'
    }}>
      <ForgotPasswordForm
        onSuccess={handleSuccess}
        onBackToLogin={handleBackToLogin}
      />
    </div>
  );
}