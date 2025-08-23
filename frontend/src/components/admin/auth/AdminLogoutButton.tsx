'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppDispatch } from '@/store';
import { logoutUser } from '@/store/slices/authSlice';
import { useAdminAuth } from '@/contexts/AdminAuthContext';
import { Button } from '@/components/ui/Button';
import { LogOut, Shield } from 'lucide-react';
import toast from 'react-hot-toast';

interface AdminLogoutButtonProps {
  variant?: 'button' | 'menu-item';
  className?: string;
}

export function AdminLogoutButton({ 
  variant = 'button', 
  className = '' 
}: AdminLogoutButtonProps) {
  const [loading, setLoading] = useState(false);
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { logoutAll } = useAdminAuth();

  const handleLogout = async () => {
    if (!confirm('Are you sure you want to logout from all admin sessions?')) {
      return;
    }

    setLoading(true);
    try {
      // Logout from all admin sessions first
      await logoutAll();
      
      // Then logout from the main auth system
      await dispatch(logoutUser()).unwrap();
      
      toast.success('Logged out successfully');
      router.push('/admin/login');
    } catch (error) {
      console.error('Logout failed:', error);
      toast.error('Logout failed');
    } finally {
      setLoading(false);
    }
  };

  if (variant === 'menu-item') {
    return (
      <button
        onClick={handleLogout}
        disabled={loading}
        className={`flex items-center space-x-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 ${className}`}
      >
        <LogOut className="h-4 w-4" />
        <span>{loading ? 'Logging out...' : 'Secure Logout'}</span>
      </button>
    );
  }

  return (
    <Button
      onClick={handleLogout}
      loading={loading}
      variant="outline"
      size="sm"
      className={`flex items-center space-x-2 text-red-600 border-red-300 hover:bg-red-50 ${className}`}
    >
      <Shield className="h-4 w-4" />
      <span>Secure Logout</span>
    </Button>
  );
}