'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Switch } from '@/components/ui/Switch';
import { Card } from '@/components/ui/card';
import { Alert } from '@/components/ui/Alert';
import { ProfileImageUpload } from '@/components/user/ProfileImageUpload';
import { VALIDATION } from '@/constants';
import toast from 'react-hot-toast';

// Validation schema
const createUserSchema = yup.object({
  username: yup
    .string()
    .required('Username is required')
    .min(VALIDATION.USERNAME_MIN_LENGTH, `Username must be at least ${VALIDATION.USERNAME_MIN_LENGTH} characters`)
    .matches(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores'),
  email: yup
    .string()
    .required('Email is required')
    .matches(VALIDATION.EMAIL_REGEX, 'Please enter a valid email address'),
  password: yup
    .string()
    .required('Password is required')
    .min(VALIDATION.PASSWORD_MIN_LENGTH, `Password must be at least ${VALIDATION.PASSWORD_MIN_LENGTH} characters`)
    .matches(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
      'Password must contain uppercase, lowercase, number, and special character'
    ),
  password_confirm: yup
    .string()
    .required('Please confirm your password')
    .oneOf([yup.ref('password')], 'Passwords must match'),
  first_name: yup.string().required('First name is required'),
  last_name: yup.string().required('Last name is required'),
  phone_number: yup
    .string()
    .nullable()
    .matches(VALIDATION.PHONE_REGEX, 'Please enter a valid phone number'),
  user_type: yup
    .string()
    .oneOf(['customer', 'seller', 'admin'], 'Please select a valid user type')
    .required('User type is required'),
});

interface UserCreateFormData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  user_type: 'customer' | 'seller' | 'admin';
  is_verified: boolean;
  is_email_verified: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  send_welcome_email: boolean;
  profile_image?: File;
}

interface UserCreateFormProps {
  onSubmit: (data: UserCreateFormData) => Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
}

export function UserCreateForm({
  onSubmit,
  onCancel,
  loading = false,
}: UserCreateFormProps) {
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    watch,
    setValue,
  } = useForm<UserCreateFormData>({
    resolver: yupResolver(createUserSchema),
    defaultValues: {
      user_type: 'customer',
      is_verified: true,
      is_email_verified: false,
      is_staff: false,
      is_superuser: false,
      send_welcome_email: true,
    },
  });

  const userType = watch('user_type');

  const handleFormSubmit = async (data: UserCreateFormData) => {
    try {
      const submitData = {
        ...data,
        profile_image: profileImage || undefined,
      };
      
      await onSubmit(submitData);
      
      // Reset form on success
      reset();
      setProfileImage(null);
      toast.success('User created successfully!');
    } catch (error) {
      // Error handling is done in parent component
    }
  };

  const handleCancel = () => {
    reset();
    setProfileImage(null);
    onCancel?.();
  };

  // Auto-set staff status based on user type
  const handleUserTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newUserType = e.target.value as 'customer' | 'seller' | 'admin';
    setValue('user_type', newUserType);
    
    if (newUserType === 'admin') {
      setValue('is_staff', true);
      setValue('is_verified', true);
    } else {
      setValue('is_staff', false);
      setValue('is_superuser', false);
    }
  };

  return (
    <Card className="max-w-4xl mx-auto">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Create New User</h2>
        <p className="text-sm text-gray-600 mt-1">
          Add a new user to the system with the specified permissions
        </p>
      </div>

      <form onSubmit={handleSubmit(handleFormSubmit)} className="p-6 space-y-6">
        {/* Profile Image */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Profile Image
          </label>
          <ProfileImageUpload
            onImageChange={setProfileImage}
            loading={loading}
          />
        </div>

        {/* Basic Information */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Input
              label="Username"
              {...register('username')}
              error={errors.username?.message}
              disabled={loading}
              placeholder="johndoe"
            />

            <Input
              label="Email"
              type="email"
              {...register('email')}
              error={errors.email?.message}
              disabled={loading}
              placeholder="john@example.com"
            />

            <Input
              label="First Name"
              {...register('first_name')}
              error={errors.first_name?.message}
              disabled={loading}
              placeholder="John"
            />

            <Input
              label="Last Name"
              {...register('last_name')}
              error={errors.last_name?.message}
              disabled={loading}
              placeholder="Doe"
            />

            <Input
              label="Phone Number"
              type="tel"
              {...register('phone_number')}
              error={errors.phone_number?.message}
              placeholder="+1234567890"
              disabled={loading}
            />

            <Select
              label="User Type"
              {...register('user_type')}
              onChange={handleUserTypeChange}
              error={errors.user_type?.message}
              disabled={loading}
            >
              <option value="customer">Customer</option>
              <option value="seller">Seller</option>
              <option value="admin">Admin</option>
            </Select>
          </div>
        </div>

        {/* Password */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Password</h3>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Input
              label="Password"
              type="password"
              {...register('password')}
              error={errors.password?.message}
              disabled={loading}
              placeholder="Enter secure password"
            />

            <Input
              label="Confirm Password"
              type="password"
              {...register('password_confirm')}
              error={errors.password_confirm?.message}
              disabled={loading}
              placeholder="Confirm password"
            />
          </div>
          
          <Alert variant="info" className="mt-4">
            <div className="text-sm">
              <p className="font-medium">Password Requirements:</p>
              <ul className="mt-1 list-disc list-inside space-y-1">
                <li>At least {VALIDATION.PASSWORD_MIN_LENGTH} characters long</li>
                <li>Contains uppercase and lowercase letters</li>
                <li>Contains at least one number</li>
                <li>Contains at least one special character (@$!%*?&)</li>
              </ul>
            </div>
          </Alert>
        </div>

        {/* Account Settings */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Account Settings</h3>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? 'Hide' : 'Show'} Advanced Options
            </Button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Account Active
                </label>
                <p className="text-sm text-gray-500">
                  User can log in and access the system
                </p>
              </div>
              <Switch
                {...register('is_verified')}
                disabled={loading}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Send Welcome Email
                </label>
                <p className="text-sm text-gray-500">
                  Send account creation notification to user
                </p>
              </div>
              <Switch
                {...register('send_welcome_email')}
                disabled={loading}
              />
            </div>

            {showAdvanced && (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Email Verified
                    </label>
                    <p className="text-sm text-gray-500">
                      Mark email as already verified
                    </p>
                  </div>
                  <Switch
                    {...register('is_email_verified')}
                    disabled={loading}
                  />
                </div>

                {userType === 'admin' && (
                  <>
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">
                          Staff Status
                        </label>
                        <p className="text-sm text-gray-500">
                          Can access admin interface
                        </p>
                      </div>
                      <Switch
                        {...register('is_staff')}
                        disabled={loading}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">
                          Superuser Status
                        </label>
                        <p className="text-sm text-gray-500">
                          Has all permissions without explicitly assigning them
                        </p>
                      </div>
                      <Switch
                        {...register('is_superuser')}
                        disabled={loading}
                      />
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={loading}
            >
              Cancel
            </Button>
          )}
          <Button
            type="submit"
            loading={loading}
            disabled={!isDirty}
          >
            Create User
          </Button>
        </div>
      </form>
    </Card>
  );
}