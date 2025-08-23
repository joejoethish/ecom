import { Metadata } from 'next';
import { AdminLoginForm } from '@/components/admin/auth/AdminLoginForm';

export const metadata: Metadata = {
  title: 'Admin Login - Secure Portal',
  description: 'Secure administrative access portal',
  robots: 'noindex, nofollow', // Prevent search engine indexing
};

export default function AdminLoginPage() {
  return <AdminLoginForm />;
}