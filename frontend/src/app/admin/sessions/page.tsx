import { Metadata } from 'next';
import { AdminSessionManagement } from '@/components/admin/auth';

export const metadata: Metadata = {
  title: 'Session Management - Admin Portal',
  description: 'Manage administrative sessions and security',
};

export default function AdminSessionsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <AdminSessionManagement />
    </div>
  );
}