import React from 'react';
import { Metadata } from 'next';
import EmailVerificationPage from '@/components/auth/EmailVerificationPage';

export const metadata: Metadata = {
  title: 'Email Verification | E-Commerce Platform',
  description: 'Verify your email address to complete your account setup',
};

interface PageProps {
  params: Promise<{
    token: string;
  }>;
}

export default async function VerifyEmailPage({ params }: PageProps) {
  const { token } = await params;
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-indigo-600">
            E-Commerce Platform
          </h1>
        </div>
      </div>
      
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <EmailVerificationPage token={token} />
        </div>
      </div>
    </div>
  );
}

export async function generateStaticParams() {
  // Return empty array since tokens are dynamic
  return [];
}