'use client';

import { useState, useEffect } from 'react';
import { adminAuthApi, AdminSessionInfo, AdminSecurityEvent } from '@/services/adminAuthApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { 
  Monitor, 
  Smartphone, 
  MapPin, 
  Clock, 
  Shield, 
  AlertTriangle, 
  Trash2,
  RefreshCw,
  Eye,
  LogOut
} from 'lucide-react';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';

interface AdminSessionManagementProps {
  className?: string;
}

export function AdminSessionManagement({ className = '' }: AdminSessionManagementProps) {
  const [sessions, setSessions] = useState<AdminSessionInfo[]>([]);
  const [securityEvents, setSecurityEvents] = useState<AdminSecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [terminatingSession, setTerminatingSession] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'sessions' | 'security'>('sessions');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sessionsResponse, eventsResponse] = await Promise.all([
        adminAuthApi.getSessions(),
        adminAuthApi.getSecurityEvents(20)
      ]);

      if (sessionsResponse.success && sessionsResponse.data) {
        setSessions(sessionsResponse.data);
      }

      if (eventsResponse.success && eventsResponse.data) {
        setSecurityEvents(eventsResponse.data);
      }
    } catch (error) {
      toast.error('Failed to load session data');
    } finally {
      setLoading(false);
    }
  };

  const handleTerminateSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to terminate this session?')) {
      return;
    }

    setTerminatingSession(sessionId);
    try {
      const response = await adminAuthApi.terminateSession(sessionId);
      if (response.success) {
        toast.success('Session terminated successfully');
        setSessions(prev => prev.filter(session => session.id !== sessionId));
      } else {
        toast.error('Failed to terminate session');
      }
    } catch (error) {
      toast.error('Failed to terminate session');
    } finally {
      setTerminatingSession(null);
    }
  };

  const handleLogoutAll = async () => {
    if (!confirm('Are you sure you want to logout from all other sessions? This will terminate all your active sessions except the current one.')) {
      return;
    }

    try {
      const response = await adminAuthApi.logoutAll();
      if (response.success) {
        toast.success(`Logged out from ${response.data?.clearedSessions || 0} sessions`);
        await loadData();
      } else {
        toast.error('Failed to logout from all sessions');
      }
    } catch (error) {
      toast.error('Failed to logout from all sessions');
    }
  };

  const getDeviceIcon = (deviceType: string) => {
    return deviceType.toLowerCase().includes('mobile') ? 
      <Smartphone className="h-5 w-5" /> : 
      <Monitor className="h-5 w-5" />;
  };

  const getSecurityLevelBadge = (level: string) => {
    const colors = {
      standard: 'bg-blue-100 text-blue-800',
      elevated: 'bg-red-100 text-red-800',
    };
    
    return (
      <Badge className={colors[level as keyof typeof colors] || colors.standard}>
        {level.charAt(0).toUpperCase() + level.slice(1)}
      </Badge>
    );
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    };
    
    return (
      <Badge className={colors[severity as keyof typeof colors] || colors.low}>
        {severity.charAt(0).toUpperCase() + severity.slice(1)}
      </Badge>
    );
  };

  const getEventIcon = (eventType: string) => {
    const icons = {
      login: <Shield className="h-4 w-4 text-green-600" />,
      logout: <LogOut className="h-4 w-4 text-blue-600" />,
      failed_login: <AlertTriangle className="h-4 w-4 text-red-600" />,
      session_timeout: <Clock className="h-4 w-4 text-yellow-600" />,
      suspicious_activity: <AlertTriangle className="h-4 w-4 text-red-600" />,
    };
    
    return icons[eventType as keyof typeof icons] || <Eye className="h-4 w-4 text-gray-600" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Admin Session Management</h2>
          <p className="text-gray-600">Monitor and manage your administrative sessions</p>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={loadData}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </Button>
          <Button
            onClick={handleLogoutAll}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2 text-red-600 border-red-300 hover:bg-red-50"
          >
            <LogOut className="h-4 w-4" />
            <span>Logout All Others</span>
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('sessions')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'sessions'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Active Sessions ({sessions.length})
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'security'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Security Events ({securityEvents.length})
          </button>
        </nav>
      </div>

      {/* Sessions Tab */}
      {activeTab === 'sessions' && (
        <div className="space-y-4">
          {sessions.length === 0 ? (
            <Card className="p-8 text-center">
              <Monitor className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Sessions</h3>
              <p className="text-gray-600">You don't have any active admin sessions.</p>
            </Card>
          ) : (
            sessions.map((session) => (
              <Card key={session.id} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      {getDeviceIcon(session.deviceInfo.device)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-medium text-gray-900">
                          {session.deviceInfo.browser} on {session.deviceInfo.os}
                        </h3>
                        {session.isCurrent && (
                          <Badge className="bg-green-100 text-green-800">Current Session</Badge>
                        )}
                        {getSecurityLevelBadge(session.securityLevel)}
                      </div>
                      
                      <div className="space-y-2 text-sm text-gray-600">
                        <div className="flex items-center space-x-2">
                          <MapPin className="h-4 w-4" />
                          <span>
                            {session.location ? 
                              `${session.location.city || 'Unknown'}, ${session.location.country || 'Unknown'}` : 
                              'Unknown location'
                            } ({session.ipAddress})
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Clock className="h-4 w-4" />
                          <span>
                            Started {formatDistanceToNow(new Date(session.createdAt), { addSuffix: true })}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Shield className="h-4 w-4" />
                          <span>
                            Last activity: {formatDistanceToNow(new Date(session.lastActivity), { addSuffix: true })}
                          </span>
                        </div>
                        
                        <div className="text-xs text-gray-500">
                          Session expires: {new Date(session.expiresAt).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {!session.isCurrent && (
                    <Button
                      onClick={() => handleTerminateSession(session.id)}
                      variant="outline"
                      size="sm"
                      loading={terminatingSession === session.id}
                      className="flex items-center space-x-2 text-red-600 border-red-300 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Terminate</span>
                    </Button>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Security Events Tab */}
      {activeTab === 'security' && (
        <div className="space-y-4">
          {securityEvents.length === 0 ? (
            <Card className="p-8 text-center">
              <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Security Events</h3>
              <p className="text-gray-600">No recent security events to display.</p>
            </Card>
          ) : (
            securityEvents.map((event) => (
              <Card key={event.id} className="p-4">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 mt-1">
                    {getEventIcon(event.eventType)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-900">
                        {event.eventType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </h4>
                      <div className="flex items-center space-x-2">
                        {getSeverityBadge(event.severity)}
                        <span className="text-xs text-gray-500">
                          {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-600 space-y-1">
                      <div>IP Address: {event.ipAddress}</div>
                      {event.details && Object.keys(event.details).length > 0 && (
                        <div className="text-xs text-gray-500">
                          Details: {JSON.stringify(event.details, null, 2)}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}