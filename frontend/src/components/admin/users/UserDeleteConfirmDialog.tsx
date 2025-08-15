'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/avatar';
import { User } from '@/types';
import { formatDate } from '@/utils/format';

interface UserDeleteConfirmDialogProps {
  user: User;
  isOpen: boolean;
  onConfirm: (deleteData?: boolean) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export function UserDeleteConfirmDialog({
  user,
  isOpen,
  onConfirm,
  onCancel,
  loading = false,
}: UserDeleteConfirmDialogProps) {
  const [confirmText, setConfirmText] = useState('');
  const [deleteUserData, setDeleteUserData] = useState(false);
  const [step, setStep] = useState<'warning' | 'confirm'>('warning');

  const expectedConfirmText = `DELETE ${user.username}`;
  const isConfirmValid = confirmText === expectedConfirmText;

  const handleConfirm = async () => {
    if (step === 'warning') {
      setStep('confirm');
      return;
    }

    if (isConfirmValid) {
      try {
        await onConfirm(deleteUserData);
        handleClose();
      } catch (error) {
        // Error handling is done in parent component
      }
    }
  };

  const handleClose = () => {
    setConfirmText('');
    setDeleteUserData(false);
    setStep('warning');
    onCancel();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        />

        {/* Modal */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          {step === 'warning' ? (
            <>
              {/* Warning Step */}
              <div className="sm:flex sm:items-start">
                <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                  <svg
                    className="h-6 w-6 text-red-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z"
                    />
                  </svg>
                </div>
                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Delete User Account
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      You are about to permanently delete this user account. This action cannot be undone.
                    </p>
                  </div>
                </div>
              </div>

              {/* User Information */}
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Avatar className="h-12 w-12">
                    <div className="h-full w-full bg-gray-300 flex items-center justify-center">
                      <span className="text-gray-500 text-sm font-medium">
                        {user.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </Avatar>
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900">{user.username}</h4>
                    <p className="text-sm text-gray-500">{user.email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge className="text-xs">
                        {user.user_type.charAt(0).toUpperCase() + user.user_type.slice(1)}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        Created {formatDate(user.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Warning Messages */}
              <div className="mt-4 space-y-3">
                <Alert variant="warning">
                  <div className="text-sm">
                    <p className="font-medium">This will permanently delete:</p>
                    <ul className="mt-1 list-disc list-inside space-y-1">
                      <li>User account and profile information</li>
                      <li>Authentication credentials and sessions</li>
                      <li>User preferences and settings</li>
                      {user.user_type === 'seller' && <li>Seller profile and business information</li>}
                      {user.user_type === 'admin' && <li>Admin permissions and access logs</li>}
                    </ul>
                  </div>
                </Alert>

                {(user.user_type === 'seller' || user.user_type === 'admin') && (
                  <Alert variant="error">
                    <div className="text-sm">
                      <p className="font-medium">⚠️ Special Account Type Warning</p>
                      <p className="mt-1">
                        This is a {user.user_type} account. Deleting it may affect:
                        {user.user_type === 'seller' && ' product listings, orders, and business operations.'}
                        {user.user_type === 'admin' && ' system administration and other admin functions.'}
                      </p>
                    </div>
                  </Alert>
                )}
              </div>

              {/* Actions */}
              <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                <Button
                  variant="primary"
                  onClick={handleConfirm}
                  disabled={loading}
                  className="w-full sm:w-auto sm:ml-3 bg-red-600 hover:bg-red-700"
                >
                  Continue to Confirmation
                </Button>
                <Button
                  variant="outline"
                  onClick={handleClose}
                  disabled={loading}
                  className="mt-3 w-full sm:mt-0 sm:w-auto"
                >
                  Cancel
                </Button>
              </div>
            </>
          ) : (
            <>
              {/* Confirmation Step */}
              <div className="sm:flex sm:items-start">
                <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                  <svg
                    className="h-6 w-6 text-red-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </div>
                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Final Confirmation Required
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      To confirm deletion, type <code className="bg-gray-100 px-1 rounded font-mono">{expectedConfirmText}</code> below:
                    </p>
                  </div>
                </div>
              </div>

              {/* Confirmation Input */}
              <div className="mt-4">
                <Input
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder={expectedConfirmText}
                  disabled={loading}
                  className={`font-mono ${
                    confirmText && !isConfirmValid ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
                  }`}
                />
                {confirmText && !isConfirmValid && (
                  <p className="mt-1 text-sm text-red-600">
                    Text does not match. Please type exactly: {expectedConfirmText}
                  </p>
                )}
              </div>

              {/* Data Deletion Option */}
              <div className="mt-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={deleteUserData}
                    onChange={(e) => setDeleteUserData(e.target.checked)}
                    disabled={loading}
                    className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Also delete all associated user data (orders, reviews, etc.)
                  </span>
                </label>
                <p className="mt-1 text-xs text-gray-500">
                  If unchecked, user data will be anonymized but preserved for business records.
                </p>
              </div>

              {/* Actions */}
              <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                <Button
                  variant="primary"
                  onClick={handleConfirm}
                  disabled={!isConfirmValid || loading}
                  loading={loading}
                  className="w-full sm:w-auto sm:ml-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-300"
                >
                  Delete User Permanently
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setStep('warning')}
                  disabled={loading}
                  className="mt-3 w-full sm:mt-0 sm:w-auto"
                >
                  Back
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}