'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/Separator';
import { User } from '@/types';
import { formatDate } from '@/utils/format';

interface UserProfileViewProps {
  user: User;
  onEdit?: () => void;
  onRefresh?: () => void;
  loading?: boolean;
  showActions?: boolean;
  showSensitiveInfo?: boolean;
}

export function UserProfileView({
  user,
  onEdit,
  onRefresh,
  loading = false,
  showActions = true,
  showSensitiveInfo = true,
}: UserProfileViewProps) {
  const [imageError, setImageError] = useState(false);

  const getUserTypeColor = (userType: string) => {
    switch (userType) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'seller':
        return 'bg-blue-100 text-blue-800';
      case 'customer':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getVerificationStatus = () => {
    if (user.is_email_verified) {
      return {
        label: 'Verified',
        color: 'bg-green-100 text-green-800',
      };
    }
    return {
      label: 'Unverified',
      color: 'bg-yellow-100 text-yellow-800',
    };
  };

  return (
    <Card className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Avatar className="h-16 w-16">
              {!imageError ? (
                <img
                  src={`/api/users/${user.id}/avatar`}
                  alt={`${user.username}'s avatar`}
                  className="h-full w-full object-cover"
                  onError={() => setImageError(true)}
                />
              ) : (
                <div className="h-full w-full bg-gray-300 flex items-center justify-center">
                  <span className="text-gray-500 text-lg font-medium">
                    {user.username.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
            </Avatar>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{user.username}</h2>
              <p className="text-gray-600">{user.email}</p>
            </div>
          </div>
          
          {showActions && (
            <div className="flex space-x-2">
              {onRefresh && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRefresh}
                  loading={loading}
                >
                  Refresh
                </Button>
              )}
              {onEdit && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onEdit}
                  disabled={loading}
                >
                  Edit Profile
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Profile Information */}
      <div className="px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Username</label>
                <p className="mt-1 text-sm text-gray-900">{user.username}</p>
              </div>

              {showSensitiveInfo && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <div className="mt-1 flex items-center space-x-2">
                    <p className="text-sm text-gray-900">{user.email}</p>
                    <Badge className={getVerificationStatus().color}>
                      {getVerificationStatus().label}
                    </Badge>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700">Phone Number</label>
                <p className="mt-1 text-sm text-gray-900">
                  {user.phone_number || 'Not provided'}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">User Type</label>
                <div className="mt-1">
                  <Badge className={getUserTypeColor(user.user_type)}>
                    {user.user_type.charAt(0).toUpperCase() + user.user_type.slice(1)}
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          {/* Account Status */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Account Status</h3>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Account Status</label>
                <div className="mt-1">
                  <Badge className={user.is_verified ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                    {user.is_verified ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Email Verification</label>
                <div className="mt-1">
                  <Badge className={getVerificationStatus().color}>
                    {getVerificationStatus().label}
                  </Badge>
                </div>
              </div>

              {user.is_staff && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Staff Status</label>
                  <div className="mt-1">
                    <Badge className="bg-purple-100 text-purple-800">
                      Staff Member
                    </Badge>
                  </div>
                </div>
              )}

              {user.is_superuser && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Admin Status</label>
                  <div className="mt-1">
                    <Badge className="bg-red-100 text-red-800">
                      Super Admin
                    </Badge>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700">Member Since</label>
                <p className="mt-1 text-sm text-gray-900">
                  {formatDate(user.created_at)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Information */}
        {user.seller_profile && (
          <>
            <Separator className="my-6" />
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Seller Information</h3>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-blue-800">
                  This user has an active seller profile with additional business information.
                </p>
              </div>
            </div>
          </>
        )}

        {/* Account Actions */}
        {showActions && (
          <>
            <Separator className="my-6" />
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Account Actions</h3>
              <div className="flex flex-wrap gap-3">
                {!user.is_email_verified && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      // This would trigger email verification resend
                      console.log('Resend verification email');
                    }}
                  >
                    Resend Verification Email
                  </Button>
                )}
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    // This would trigger password reset
                    console.log('Reset password');
                  }}
                >
                  Reset Password
                </Button>

                {showSensitiveInfo && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-600 border-red-300 hover:bg-red-50"
                    onClick={() => {
                      // This would trigger account deactivation
                      console.log('Deactivate account');
                    }}
                  >
                    Deactivate Account
                  </Button>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}