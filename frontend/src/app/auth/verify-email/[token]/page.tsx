import React from 'react';
import { Metadata } from 'next';
import EmailVerificationPage from '@/components/auth/EmailVerificationPage';

export const metadata: Metadata = {
  title: 'Email Verification | E-Commerce Platform',
  description: 'Verify your email address to complete your account setup',
};

interface PageProps {
  params: {
    token: string;
  };
}

export default function VerifyEmailPage({ params }: PageProps) {
  return <EmailVerificationPage token={params.token} />;
}

export async function generateStaticParams() {
  // Return empty array since tokens are dynamic
  return [];
}