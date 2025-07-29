'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppDispatch, useAppSelector } from '@/store';
import { registerUser } from '@/store/slices/authSlice';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ROUTES, USER_TYPES } from '@/constants';
import { validateEmail, validatePassword, validateUsername, validatePasswordMatch } from '@/utils/validation';
import Link from 'next/link';
import toast from 'react-hot-toast';

export function RegisterForm() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    user_type: USER_TYPES.CUSTOMER as 'customer' | 'seller',
    phone_number: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const dispatch = useAppDispatch();
  const router = useRouter();
  const { loading, error } = useAppSelector((state) => state.auth);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    // Username validation
    const usernameErrors = validateUsername(formData.username);
    if (usernameErrors.length > 0) {
      newErrors.username = usernameErrors[0];
    }

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    const passwordErrors = validatePassword(formData.password);
    if (passwordErrors.length > 0) {
      newErrors.password = passwordErrors[0];
    }

    // Password confirmation validation
    const passwordMatchError = validatePasswordMatch(formData.password, formData.password_confirm);
    if (passwordMatchError) {
      newErrors.password_confirm = passwordMatchError;
    }

    // Phone number validation (optional)
    if (formData.phone_number && !/^[\+]?[1-9][\d]{0,15}$/.test(formData.phone_number)) {
      newErrors.phone_number = 'Please enter a valid phone number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await dispatch(registerUser(formData)).unwrap();
      toast.success('Registration successful! Welcome to our platform!');
      router.push(ROUTES.HOME);
    } catch (error: any) {
      toast.error(error || 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{' '}
            <Link
              href={ROUTES.LOGIN}
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              sign in to your existing account
            </Link>
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={formData.username}
              onChange={handleChange}
              error={errors.username}
              placeholder="Choose a username"
              helperText="Username must be at least 3 characters and contain only letters, numbers, and underscores"
            />
            
            <Input
              label="Email address"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              placeholder="Enter your email"
            />
            
            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              value={formData.password}
              onChange={handleChange}
              error={errors.password}
              placeholder="Create a password"
              helperText="Password must be at least 8 characters with uppercase, lowercase, and number"
            />
            
            <Input
              label="Confirm Password"
              name="password_confirm"
              type="password"
              autoComplete="new-password"
              required
              value={formData.password_confirm}
              onChange={handleChange}
              error={errors.password_confirm}
              placeholder="Confirm your password"
            />
            
            <Input
              label="Phone Number (Optional)"
              name="phone_number"
              type="tel"
              autoComplete="tel"
              value={formData.phone_number}
              onChange={handleChange}
              error={errors.phone_number}
              placeholder="+1234567890"
            />

            <div className="space-y-1">
              <label htmlFor="user_type" className="block text-sm font-medium text-gray-700">
                Account Type
              </label>
              <select
                id="user_type"
                name="user_type"
                value={formData.user_type}
                onChange={handleChange}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value={USER_TYPES.CUSTOMER}>Customer</option>
                <option value={USER_TYPES.SELLER}>Seller</option>
              </select>
            </div>
          </div>

          <div className="flex items-center">
            <input
              id="terms"
              name="terms"
              type="checkbox"
              required
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="terms" className="ml-2 block text-sm text-gray-900">
              I agree to the{' '}
              <a href="#" className="text-blue-600 hover:text-blue-500">
                Terms and Conditions
              </a>{' '}
              and{' '}
              <a href="#" className="text-blue-600 hover:text-blue-500">
                Privacy Policy
              </a>
            </label>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">
              {error}
            </div>
          )}

          <div>
            <Button
              type="submit"
              loading={loading}
              className="w-full"
              size="lg"
            >
              Create Account
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}