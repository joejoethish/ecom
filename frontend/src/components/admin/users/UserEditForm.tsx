'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Switch } from '@/components/ui/Switch';
import { Card } from '@/components/ui/card';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { ProfileImageUpload } from '@/components/user/ProfileImageUpload';
import { User } from '@/types';
import { VALIDATION } from '@/constants';
import { formatDate } from '@/utils/format';
import toast from 'react-hot-toast';

// Validation schema (password is optional for editing)
const editUserSchema = yup.object({
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
    .nullable()
    .when('password', {
      is: (value: string) => value && value.length > 0,
      then: (schema) => schema
        .min(VALIDATION.PASSWORD_MIN_LENGTH, `Password must be at least ${VALIDATION.PASSWORD_MIN_LENGTH} characters`)
        .matches(
          /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
          'Password must contain uppercase, lowercase, number, and special character'
        ),
    }),
  password_confirm: yup
    .string()
    .nullable()
    .when('password', {
      is: (value: string) => value && value.length > 0,
      then: (schema) => schema
        .required('Please confirm your password')
        .oneOf([yup.ref('password')], 'Passwords must match'),
    }),
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

interface UserEditFormData {
  username: string;
  email: string;
  password?: string;
  password_confirm?: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  user_type: 'customer' | 'seller' | 'admin';
  is_verified: boolean;
  is_email_verified: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  profile_image?: File;
}

interface UserEditFormProps {
  user: User;
  onSubmit: (data: UserEditFormData) => Promise<void>;
  onCancel?: () => void;
  onDelete?: () => void;
  loading?: boolean;
}

export function UserEditForm({
  user,
  onSubmit,
  onCancel,
  onDelete,
  loading = false,
}: UserEditFormProps) {
  const [profileImage, setProfileImage] = useState<File | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [changePassword, setChangePassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    watch,
    setValue,
  } = useForm<UserEditFormData>({
    resolver: yupResolver(editUserSchema),
    defaultValues: {
      username: user.username,
      email: user.email,
      first_name: '',
      last_name: '',
      phone_number: user.phone_number || '',
      user_type: user.user_type,
      is_verified: user.is_verified,
      is_email_verified: user.is_email_verified || false,
      is_staff: user.is_staff || false,
      is_superuser: user.is_superuser || false,
    },
  });

  const userType = watch('user_type');

  // Reset form when user changes
  useEffect(() => {
    reset({
      username: user.username,
      email: user.email,
      first_name: '',
      last_name: '',
      phone_number: user.phone_number || '',
      user_type: user.user_type,
      is_verified: user.is_verified,
      is_email_verified: user.is_email_verified || false,
      is_staff: user.is_staff || false,
      is_superuser: user.is_superuser || false,
    });
  }, [user, reset]);

  const handleFormSubmit = async (data: UserEditFormData) => {
    try {
      const submitData = {
        ...data,
        profile_image: profileImage || undefined,
        // Only include password if it's being changed
        password: changePassword ? data.password : undefined,
        password_confirm: changePassword ? data.password_confirm : undefined,
      };
      
      await onSubmit(submitData);
      
      // Reset password fields
      if (changePassword) {
        setChangePassword(false);
        setValue('password', '');
        setValue('password_confirm', '');
      }
      
      toast.success('User updated successfully!');
    } catch (error) {
      // Error handling is done in parent component
    }
  };

  const handleCancel = () => {
    reset({
      username: user.username,
      email: user.email,
      first_name: '',
      last_name: '',
      phone_number: user.phone_number || '',
      user_type: user.user_type,
      is_verified: user.is_verified,
      is_email_verified: user.is_email_verified || false,
      is_staff: user.is_staff || false,
      is_superuser: user.is_superuser || false,
    });
    setProfileImage(null);
    setChangePassword(false);
    onCancel?.();
  };

  // Auto-set staff status based on user type
  const handleUserTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newUserType = e.target.value as 'customer' | 'seller' | 'admin';
    setValue('user_type', newUserType);
    
    if (newUserType === 'admin') {
      setValue('is_staff', true);
    } else if (newUserType !== 'admin' && user.user_type !== 'admin') {
      setValue('is_staff', false);
      setValue('is_superuser', false);
    }
  };

  return (
    <Card className="max-w-4xl mx-auto">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Edit User</h2>
            <p className="text-sm text-gray-600 mt-1">
              Update user information and permissions
            </p>
          </div>
          {onDelete && (
            <Button
              variant="outline"
              onClick={onDelete}
              className="text-red-600 border-red-300 hover:bg-red-50"
              disabled={loading}
            >
              Delete User
            </Button>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit(handleFormSubmit)} className="p-6 space-y-6">
        {/* User Info Header */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-900">User ID: {user.id}</h3>
              <p className="text-sm text-gray-500">Created: {formatDate(user.created_at)}</p>
            </div>
            <div className="flex space-x-2">
              <Badge className={user.is_verified ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                {user.is_verified ? 'Active' : 'Inactive'}
              </Badge>
              {user.is_email_verified && (
                <Badge className="bg-blue-100 text-blue-800">
                  Email Verified
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Profile Image */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Profile Image
          </label>
          <ProfileImageUpload
            currentImage={`/api/users/${user.id}/avatar`}
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
            />

            <Input
              label="Email"
              type="email"
              {...register('email')}
              error={errors.email?.message}
              disabled={loading}
            />

            <Input
              label="First Name"
              {...register('first_name')}
              error={errors.first_name?.message}
              disabled={loading}
            />

            <Input
              label="Last Name"
              {...register('last_name')}
              error={errors.last_name?.message}
              disabled={loading}
            />

            <Input
              label="Phone Number"
              type="tel"
              {...register('phone_number')}
              error={errors.phone_number?.message}
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

        {/* Password Change */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Password</h3>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setChangePassword(!changePassword)}
            >
              {changePassword ? 'Cancel Password Change' : 'Change Password'}
            </Button>
          </div>

          {changePassword && (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <Input
                label="New Password"
                type="password"
                {...register('password')}
                error={errors.password?.message}
                disabled={loading}
                placeholder="Enter new password"
              />

              <Input
                label="Confirm New Password"
                type="password"
                {...register('password_confirm')}
                error={errors.password_confirm?.message}
                disabled={loading}
                placeholder="Confirm new password"
              />
            </div>
          )}

          {!changePassword && (
            <Alert variant="info">
              <p className="text-sm">
                Password is not being changed. Click "Change Password" to update the user's password.
              </p>
            </Alert>
          )}
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

            {showAdvanced && (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Email Verified
                    </label>
                    <p className="text-sm text-gray-500">
                      Mark email as verified or unverified
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
            disabled={!isDirty && !profileImage && !changePassword}
          >
            Update User
          </Button>
        </div>
      </form>
    </Card>
  );
}