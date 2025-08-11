'use client';

import { useRouter } from 'next/navigation';
import { useAppDispatch, useAppSelector } from '@/store';
import { logoutUser } from '@/store/slices/authSlice';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/constants';
import toast from 'react-hot-toast';

interface LogoutButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  children?: React.ReactNode;
  redirectTo?: string;
}

export function LogoutButton({ 
  variant = 'ghost', 
  size = 'sm', 
  className = '',
  children = 'Logout',
  redirectTo = ROUTES.HOME
}: LogoutButtonProps) {
  const dispatch = useAppDispatch();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await dispatch(logoutUser()).unwrap();
      toast.success(&apos;Logged out successfully&apos;);
      router.push(redirectTo);
    } catch (error: unknown) {
      toast.error(&apos;Logout failed&apos;);
      // Even if logout API fails, we still redirect since tokens are cleared
      router.push(redirectTo);
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      className={className}
      onClick={handleLogout}
      loading={loading}
    >
      {children}
    </Button>
  );
}