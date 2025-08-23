'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/card';
import { Alert } from '@/components/ui/Alert';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { UserSession } from '@/types';
import { formatDate, formatRelativeTime } from '@/utils/format';
import toast from 'react-hot-toast';

interface SessionListViewProps {
    sessions: UserSession[];
    loading?: boolean;
    error?: string | null;
    onTerminateSession?: (sessionId: string) => Promise<void>;
    onTerminateAllOthers?: () => Promise<void>;
    onRefresh?: () => void;
}

export function SessionListView({
    sessions,
    loading = false,
    error = null,
    onTerminateSession,
    onTerminateAllOthers,
    onRefresh,
}: SessionListViewProps) {
    const [terminatingSession, setTerminatingSession] = useState<string | null>(null);
    const [terminatingAll, setTerminatingAll] = useState(false);

    const handleTerminateSession = async (sessionId: string) => {
        if (!onTerminateSession) return;

        try {
            setTerminatingSession(sessionId);
            await onTerminateSession(sessionId);
            toast.success('Session terminated successfully');
        } catch (error) {
            toast.error('Failed to terminate session');
        } finally {
            setTerminatingSession(null);
        }
    };

    const handleTerminateAllOthers = async () => {
        if (!onTerminateAllOthers) return;

        try {
            setTerminatingAll(true);
            await onTerminateAllOthers();
            toast.success('All other sessions terminated successfully');
        } catch (error) {
            toast.error('Failed to terminate sessions');
        } finally {
            setTerminatingAll(false);
        }
    };

    const getDeviceIcon = (deviceInfo: UserSession['device_info']) => {
        const device = deviceInfo.device?.toLowerCase() || '';
        const browser = deviceInfo.browser?.toLowerCase() || '';

        if (device.includes('mobile') || device.includes('phone')) {
            return (
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a1 1 0 001-1V4a1 1 0 00-1-1H8a1 1 0 00-1 1v16a1 1 0 001 1z" />
                </svg>
            );
        }

        if (device.includes('tablet') || device.includes('ipad')) {
            return (
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
            );
        }

        return (
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
        );
    };

    const getLocationString = (location?: UserSession['location']) => {
        if (!location) return 'Unknown location';

        const parts = [];
        if (location.city) parts.push(location.city);
        if (location.region) parts.push(location.region);
        if (location.country) parts.push(location.country);

        return parts.length > 0 ? parts.join(', ') : 'Unknown location';
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

    const activeSessions = sessions.filter(session => session.is_active);
    const currentSession = sessions.find(session => session.is_current);
    const otherSessions = activeSessions.filter(session => !session.is_current);

    if (error) {
        return (
            <Alert variant="destructive" className="m-6">
                <div className="flex items-center justify-between">
                    <span>{error}</span>
                    {onRefresh && (
                        <Button variant="outline" size="sm" onClick={onRefresh}>
                            Retry
                        </Button>
                    )}
                </div>
            </Alert>
        );
    }

    return (
        <Card className="w-full max-w-4xl mx-auto">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-semibold text-gray-900">Active Sessions</h2>
                        <p className="text-sm text-gray-600 mt-1">
                            Manage your active login sessions across different devices
                        </p>
                    </div>
                    <div className="flex space-x-3">
                        {onRefresh && (
                            <Button
                                variant="outline"
                                onClick={onRefresh}
                                loading={loading}
                            >
                                Refresh
                            </Button>
                        )}
                        {otherSessions.length > 0 && onTerminateAllOthers && (
                            <Button
                                variant="outline"
                                onClick={handleTerminateAllOthers}
                                loading={terminatingAll}
                                className="text-red-600 border-red-300 hover:bg-red-50"
                            >
                                Terminate All Others
                            </Button>
                        )}
                    </div>
                </div>
            </div>

            {/* Session Statistics */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">{activeSessions.length}</div>
                        <div className="text-sm text-gray-500">Active Sessions</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">1</div>
                        <div className="text-sm text-gray-500">Current Session</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{otherSessions.length}</div>
                        <div className="text-sm text-gray-500">Other Devices</div>
                    </div>
                </div>
            </div>

            {/* Sessions List */}
            <div className="divide-y divide-gray-200">
                {loading && sessions.length === 0 ? (
                    <div className="flex items-center justify-center py-12">
                        <LoadingSpinner size="lg" />
                    </div>
                ) : (
                    <>
                        {/* Current Session */}
                        {currentSession && (
                            <div className="px-6 py-4 bg-green-50">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-4">
                                        {getDeviceIcon(currentSession.device_info)}
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-2">
                                                <h3 className="text-sm font-medium text-gray-900">
                                                    {getBrowserName(currentSession.device_info.user_agent)} on {getOSName(currentSession.device_info.user_agent)}
                                                </h3>
                                                <Badge className="bg-green-100 text-green-800">
                                                    Current Session
                                                </Badge>
                                            </div>
                                            <div className="mt-1 text-sm text-gray-500">
                                                <div>IP: {currentSession.ip_address}</div>
                                                <div>Location: {getLocationString(currentSession.location)}</div>
                                                <div>Last activity: {formatRelativeTime(currentSession.last_activity)}</div>
                                                <div>Started: {formatDate(currentSession.created_at)}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-sm text-green-600 font-medium">
                                        This device
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Other Sessions */}
                        {otherSessions.map((session) => (
                            <div key={session.id} className="px-6 py-4 hover:bg-gray-50">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-4">
                                        {getDeviceIcon(session.device_info)}
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-2">
                                                <h3 className="text-sm font-medium text-gray-900">
                                                    {getBrowserName(session.device_info.user_agent)} on {getOSName(session.device_info.user_agent)}
                                                </h3>
                                                <Badge className="bg-blue-100 text-blue-800">
                                                    Active
                                                </Badge>
                                            </div>
                                            <div className="mt-1 text-sm text-gray-500">
                                                <div>IP: {session.ip_address}</div>
                                                <div>Location: {getLocationString(session.location)}</div>
                                                <div>Last activity: {formatRelativeTime(session.last_activity)}</div>
                                                <div>Started: {formatDate(session.created_at)}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        {onTerminateSession && (
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleTerminateSession(session.id)}
                                                loading={terminatingSession === session.id}
                                                className="text-red-600 border-red-300 hover:bg-red-50"
                                            >
                                                Terminate
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </>
                )}
            </div>

            {/* Empty State */}
            {!loading && sessions.length === 0 && (
                <div className="text-center py-12">
                    <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                        />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No active sessions</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        You don't have any active sessions at the moment.
                    </p>
                </div>
            )}

            {/* Security Notice */}
            <div className="px-6 py-4 bg-blue-50 border-t border-gray-200">
                <Alert variant="default">
                    <div className="text-sm">
                        <p className="font-medium">Security Notice</p>
                        <p className="mt-1">
                            If you see any sessions you don't recognize, terminate them immediately and change your password.
                            Sessions are automatically terminated after 30 days of inactivity.
                        </p>
                    </div>
                </Alert>
            </div>
        </Card>
    );
}