'use client';

import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { UserSession } from '@/types';
import { formatDate, formatRelativeTime } from '@/utils/format';

interface SessionTerminateConfirmDialogProps {
  session?: UserSession;
  isOpen: boolean;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  isTerminatingAll?: boolean;
}

export function SessionTerminateConfirmDialog({
  session,
  isOpen,
  onConfirm,
  onCancel,
  loading = false,
  isTerminatingAll = false,
}: SessionTerminateConfirmDialogProps) {
  if (!isOpen) return null;

  const getDeviceIcon = (deviceInfo: UserSession['device_info']) => {
    const device = deviceInfo.device?.toLowerCase() || '';
    
    if (device.includes('mobile') || device.includes('phone')) {
      return (
        <svg className="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a1 1 0 001-1V4a1 1 0 00-1-1H8a1 1 0 00-1 1v16a1 1 0 001 1z" />
        </svg>
      );
    }
    
    if (device.includes('tablet') || device.includes('ipad')) {
      return (
        <svg className="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      );
    }
    
    return (
      <svg className="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    );
  };

  const getBrowserName = (userAgent?: string) => {
    if (!userAgent) return 'Unknown browser';
    
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    if (userAgent.includes('Opera')) return 'Opera';
    
    return 'Unknown browser';
  };

  const getOSName = (userAgent?: string) => {
    if (!userAgent) return 'Unknown OS';
    
    if (userAgent.includes('Windows')) return 'Windows';
    if (userAgent.includes('Mac')) return 'macOS';
    if (userAgent.includes('Linux')) return 'Linux';
    if (userAgent.includes('Android')) return 'Android';
    if (userAgent.includes('iOS')) return 'iOS';
    
    return 'Unknown OS';
  };

  const getLocationString = (location?: UserSession['location']) => {
    if (!location) return 'Unknown location';
    
    const parts = [];
    if (location.city) parts.push(location.city);
    if (location.region) parts.push(location.region);
    if (location.country) parts.push(location.country);
    
    return parts.length > 0 ? parts.join(', ') : 'Unknown location';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onCancel}
        />

        {/* Modal */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
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
                {isTerminatingAll ? 'Terminate All Other Sessions' : 'Terminate Session'}
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  {isTerminatingAll
                    ? 'This will sign you out of all other devices and browsers. You will remain signed in on this device.'
                    : 'This will sign you out of the selected device. This action cannot be undone.'}
                </p>
              </div>
            </div>
          </div>

          {/* Session Information */}
          {session && !isTerminatingAll && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {getDeviceIcon(session.device_info)}
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-medium text-gray-900">
                      {getBrowserName(session.device_info.user_agent)} on {getOSName(session.device_info.user_agent)}
                    </h4>
                    {session.is_current && (
                      <Badge className="bg-green-100 text-green-800">
                        Current
                      </Badge>
                    )}
                  </div>
                  <div className="mt-1 text-xs text-gray-500 space-y-1">
                    <div>IP: {session.ip_address}</div>
                    <div>Location: {getLocationString(session.location)}</div>
                    <div>Last activity: {formatRelativeTime(session.last_activity)}</div>
                    <div>Started: {formatDate(session.created_at)}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Warning for terminating all sessions */}
          {isTerminatingAll && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-yellow-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">
                    Security Action
                  </h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    <p>
                      This will immediately sign you out of all other devices. Use this if you suspect
                      unauthorized access to your account.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <Button
              variant="primary"
              onClick={onConfirm}
              loading={loading}
              className="w-full sm:w-auto sm:ml-3 bg-red-600 hover:bg-red-700"
            >
              {isTerminatingAll ? 'Terminate All Others' : 'Terminate Session'}
            </Button>
            <Button
              variant="outline"
              onClick={onCancel}
              disabled={loading}
              className="mt-3 w-full sm:mt-0 sm:w-auto"
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}