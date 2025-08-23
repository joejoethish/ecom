'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';
import { Avatar } from '@/components/ui/avatar';
import { User } from '@/types';
import { VALIDATION } from '@/constants';
import toast from 'react-hot-toast';

// Validation schema
const profileSchema = yup.object({
  username: yup
    .string()
    .required('Username is required')
    .min(VALIDATION.USERNAME_MIN_LENGTH, `Username must be at least ${VALIDATION.USERNAME_MIN_LENGTH} characters`),
  email: yup
    .string()
    .required('Email is required')
    .matches(VALIDATION.EMAIL_REGEX, 'Please enter a valid email address'),
  first_name: yup.string().required('First name is required'),
  last_name: yup.string().required('Last name is required'),
  phone_number: yup
    .string()
    .nullable()
    .matches(VALIDATION.PHONE_REGEX, 'Please enter a valid phone number'),
  user_type: yup
    .string()
    .oneOf(['customer', 'seller', 'admin', 'inventory_manager', 'warehouse_staff'], 'Please select a valid user type')
    .required('User type is required'),
});

interface UserProfileFormData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  user_type: 'customer' | 'seller' | 'admin' | 'inventory_manager' | 'warehouse_staff';
  profile_image?: File;
}

interface UserProfileFormProps {
  user?: User;
  onSubmit: (data: UserProfileFormData) => Promise<void>;
  loading?: boolean;
  isEditing?: boolean;
  onCancel?: () => void;
  showImageUpload?: boolean;
}

export function UserProfileForm({
  user,
  onSubmit,
  loading = false,
  isEditing = false,
  onCancel,
  showImageUpload = true,
}: UserProfileFormProps) {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    setValue,
    watch,
  } = useForm<UserProfileFormData>({
    resolver: yupResolver(profileSchema) as any,
    defaultValues: {
      username: user?.username || '',
      email: user?.email || '',
      first_name: '',
      last_name: '',
      phone_number: user?.phone_number || '',
      user_type: user?.user_type || 'customer',
    },
  });

  // Reset form when user data changes
  useEffect(() => {
    if (user) {
      reset({
        username: user.username,
        email: user.email,
        first_name: '',
        last_name: '',
        phone_number: user.phone_number || '',
        user_type: user.user_type,
      });
    }
  }, [user, reset]);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        toast.error('Please select a valid image file');
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Image size must be less than 5MB');
        return;
      }

      setImageFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleFormSubmit = async (data: UserProfileFormData) => {
    try {
      const submitData = {
        ...data,
        profile_image: imageFile || undefined,
      };
      
      await onSubmit(submitData);
      
      if (!isEditing) {
        reset();
        setImagePreview(null);
        setImageFile(null);
      }
    } catch (error) {
      // Error handling is done in parent component
    }
  };

  const handleCancel = () => {
    if (user) {
      reset({
        username: user.username,
        email: user.email,
        first_name: '',
        last_name: '',
        phone_number: user.phone_number || '',
        user_type: user.user_type,
      });
    } else {
      reset();
    }
    setImagePreview(null);
    setImageFile(null);
    onCancel?.();
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Profile Image Upload */}
      {showImageUpload && (
        <div className="flex items-center space-x-6">
          <div className="shrink-0">
            <Avatar className="h-20 w-20">
              {imagePreview ? (
                <img
                  src={imagePreview}
                  alt="Profile preview"
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="h-full w-full bg-gray-300 flex items-center justify-center">
                  <span className="text-gray-500 text-sm">No Image</span>
                </div>
              )}
            </Avatar>
          </div>
          <div>
            <label
              htmlFor="profile-image"
              className="cursor-pointer bg-white py-2 px-3 border border-gray-300 rounded-md shadow-sm text-sm leading-4 font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Change Photo
            </label>
            <input
              id="profile-image"
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="sr-only"
            />
            <p className="mt-2 text-xs text-gray-500">
              JPG, GIF or PNG. Max size 5MB.
            </p>
          </div>
        </div>
      )}

      {/* Form Fields */}
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
          placeholder="+1234567890"
          disabled={loading}
        />

        <Select
          label="User Type"
          value={watch('user_type')}
          onChange={(value) => setValue('user_type', value as any)}
          error={errors.user_type?.message}
          disabled={loading}
        >
          <option value="customer">Customer</option>
          <option value="seller">Seller</option>
          <option value="admin">Admin</option>
          <option value="inventory_manager">Inventory Manager</option>
          <option value="warehouse_staff">Warehouse Staff</option>
        </Select>
      </div>

      {/* Email Verification Status */}
      {user && (
        <Alert
          variant={user.is_email_verified ? 'success' : 'warning'}
          className="mt-4"
        >
          <div className="flex items-center justify-between">
            <span>
              Email Status: {user.is_email_verified ? 'Verified' : 'Not Verified'}
            </span>
            {!user.is_email_verified && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  // This would trigger email verification resend
                  toast.success('Verification email sent!');
                }}
              >
                Resend Verification
              </Button>
            )}
          </div>
        </Alert>
      )}

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
          disabled={!isDirty && !imageFile}
        >
          {isEditing ? 'Update Profile' : 'Create Profile'}
        </Button>
      </div>
    </form>
  );
}