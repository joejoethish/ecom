'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAppDispatch, useAppSelector } from '@/store';
import { loginUser } from '@/store/slices/authSlice';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ADMIN_ROUTES } from '@/constants';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { Shield, AlertTriangle, Eye, EyeOff } from 'lucide-react';

interface AdminLoginFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

function AdminLoginFormContent() {
  const [formData, setFormData] = useState<AdminLoginFormData>({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [isLocked, setIsLocked] = useState(false);
  const [lockoutTime, setLockoutTime] = useState<number | null>(null);

  const dispatch = useAppDispatch();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { loading, error } = useAppSelector((state) => state.auth);

  // Enhanced security: Track failed login attempts
  useEffect(() => {
    const storedAttempts = localStorage.getItem('admin_login_attempts');
    const storedLockout = localStorage.getItem('admin_lockout_time');
    
    if (storedAttempts) {
      setLoginAttempts(parseInt(storedAttempts, 10));
    }
    
    if (storedLockout) {
      const lockoutTime = parseInt(storedLockout, 10);
      if (Date.now() < lockoutTime) {
        setIsLocked(true);
        setLockoutTime(lockoutTime);
      } else {
        // Lockout expired, clear it
        localStorage.removeItem('admin_lockout_time');
        localStorage.removeItem('admin_login_attempts');
        setLoginAttempts(0);
      }
    }
  }, []);

  // Countdown timer for lockout
  useEffect(() => {
    if (isLocked && lockoutTime) {
      const interval = setInterval(() => {
        if (Date.now() >= lockoutTime) {
          setIsLocked(false);
          setLockoutTime(null);
          setLoginAttempts(0);
          localStorage.removeItem('admin_lockout_time');
          localStorage.removeItem('admin_login_attempts');
          clearInterval(interval);
        }
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [isLocked, lockoutTime]);

  // Show success message if redirected from password reset
  useEffect(() => {
    const message = searchParams.get('message');
    if (message === 'password-reset-success') {
      toast.success('Password reset successful! You can now log in with your new password.');
    }
  }, [searchParams]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleFailedLogin = () => {
    const newAttempts = loginAttempts + 1;
    setLoginAttempts(newAttempts);
    localStorage.setItem('admin_login_attempts', newAttempts.toString());

    // Lock account after 3 failed attempts for 15 minutes
    if (newAttempts >= 3) {
      const lockoutTime = Date.now() + (15 * 60 * 1000); // 15 minutes
      setIsLocked(true);
      setLockoutTime(lockoutTime);
      localStorage.setItem('admin_lockout_time', lockoutTime.toString());
      toast.error('Too many failed attempts. Account locked for 15 minutes.');
    } else {
      toast.error(`Invalid credentials. ${3 - newAttempts} attempts remaining.`);
    }
  };

  const handleSuccessfulLogin = () => {
    // Clear failed attempts on successful login
    setLoginAttempts(0);
    localStorage.removeItem('admin_login_attempts');
    localStorage.removeItem('admin_lockout_time');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isLocked) {
      toast.error('Account is temporarily locked. Please try again later.');
      return;
    }

    if (!validateForm()) {
      return;
    }

    try {
      const result = await dispatch(loginUser({
        email: formData.email,
        password: formData.password,
      })).unwrap();

      // Verify user is admin
      if (result.user.user_type !== 'admin' && result.user.user_type !== 'super_admin') {
        toast.error('Access denied. Admin privileges required.');
        await dispatch(loginUser({ email: '', password: '' })); // Force logout
        return;
      }

      handleSuccessfulLogin();
      toast.success('Admin login successful!');
      
      // Log security event
      console.log('Admin login successful:', {
        userId: result.user.id,
        email: result.user.email,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
      });

      router.push(ADMIN_ROUTES.DASHBOARD);
    } catch (error: any) {
      handleFailedLogin();
      
      // Log security event
      console.log('Admin login failed:', {
        email: formData.email,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        error: error,
      });
    }
  };

  const getRemainingLockoutTime = () => {
    if (!lockoutTime) return '';
    const remaining = Math.ceil((lockoutTime - Date.now()) / 1000);
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header with enhanced security indicators */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-red-600 rounded-full flex items-center justify-center mb-4">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-extrabold text-white">
            Admin Portal
          </h2>
          <p className="mt-2 text-sm text-gray-300">
            Secure administrative access
          </p>
          
          {/* Security warning */}
          <div className="mt-4 p-3 bg-yellow-900/50 border border-yellow-600 rounded-md">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-yellow-400 mr-2" />
              <p className="text-sm text-yellow-200">
                This is a secure area. All activities are monitored and logged.
              </p>
            </div>
          </div>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Admin Email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              placeholder="Enter your admin email"
              className="bg-gray-800 border-gray-600 text-white placeholder-gray-400"
              disabled={isLocked}
            />
            
            <div className="relative">
              <Input
                label="Password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={formData.password}
                onChange={handleChange}
                error={errors.password}
                placeholder="Enter your password"
                className="bg-gray-800 border-gray-600 text-white placeholder-gray-400 pr-10"
                disabled={isLocked}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 top-6 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLocked}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
          </div>

          {/* Enhanced security options */}
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="rememberMe"
                type="checkbox"
                checked={formData.rememberMe}
                onChange={handleChange}
                className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-600 rounded bg-gray-800"
                disabled={isLocked}
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-300">
                Keep me signed in (not recommended on shared devices)
              </label>
            </div>
          </div>

          {/* Security status indicators */}
          {loginAttempts > 0 && !isLocked && (
            <div className="text-yellow-400 text-sm text-center">
              Warning: {loginAttempts}/3 failed attempts
            </div>
          )}

          {isLocked && (
            <div className="text-red-400 text-sm text-center">
              Account locked. Try again in: {getRemainingLockoutTime()}
            </div>
          )}

          {error && (
            <div className="text-red-400 text-sm text-center">
              {error}
            </div>
          )}

          <div>
            <Button
              type="submit"
              loading={loading}
              className="w-full bg-red-600 hover:bg-red-700 focus:ring-red-500"
              size="lg"
              disabled={isLocked}
            >
              {isLocked ? 'Account Locked' : 'Secure Sign In'}
            </Button>
          </div>

          {/* Security footer */}
          <div className="text-center">
            <p className="text-xs text-gray-400">
              Having trouble? Contact your system administrator.
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Session timeout: 30 minutes of inactivity
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}

export function AdminLoginForm() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="text-white">Loading...</div>
      </div>
    }>
      <AdminLoginFormContent />
    </Suspense>
  );
}