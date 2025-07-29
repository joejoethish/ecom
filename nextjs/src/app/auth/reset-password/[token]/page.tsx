'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ResetPasswordForm } from '@/components/auth/ResetPasswordForm';
import { ROUTES } from '@/constants';

export default function ResetPasswordPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const handleSuccess = () => {
    // Redirect to login after successful password reset
    // Give user time to read the success message
    setTimeout(() => {
      router.push(ROUTES.LOGIN + '?message=password-reset-success');
    }, 3000);
  };

  const handleBackToLogin = () => {
    router.push(ROUTES.LOGIN);
  };

  if (!token) {
    return (
      <div style={{ 
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
        padding: '20px'
      }}>
        <div style={{ 
          maxWidth: '400px', 
          margin: '0 auto', 
          padding: '32px', 
          backgroundColor: 'white', 
          borderRadius: '8px', 
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <div style={{ 
            width: '80px', 
            height: '80px', 
            backgroundColor: '#f44336', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            margin: '0 auto 24px auto',
            boxShadow: '0 4px 16px rgba(244, 67, 54, 0.3)'
          }}>
            <svg style={{ width: '40px', height: '40px', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: '#212121', marginBottom: '12px' }}>
            Invalid Reset Link
          </h1>
          <p style={{ color: '#757575', fontSize: '16px', lineHeight: '1.6', marginBottom: '24px' }}>
            This password reset link is missing or invalid. Please request a new password reset.
          </p>
          <button
            onClick={handleBackToLogin}
            style={{
              width: '100%',
              padding: '14px',
              backgroundColor: '#2196f3',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'background-color 0.2s ease'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#1976d2'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#2196f3'}
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f5f5f5',
      padding: '20px'
    }}>
      <ResetPasswordForm
        token={token}
        onSuccess={handleSuccess}
        onBackToLogin={handleBackToLogin}
      />
    </div>
  );
}