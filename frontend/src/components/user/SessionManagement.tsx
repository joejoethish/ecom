'use client';

import { useState, useEffect } from 'react';
import { SessionListView } from './SessionListView';
import { SessionTerminateConfirmDialog } from './SessionTerminateConfirmDialog';
import { UserSession, ApiResponse } from '@/types';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';
import toast from 'react-hot-toast';

interface SessionManagementProps {
  className?: string;
}

export function SessionManagement({ className = '' }: SessionManagementProps) {
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<UserSession | null>(null);
  const [showTerminateDialog, setShowTerminateDialog] = useState(false);
  const [isTerminatingAll, setIsTerminatingAll] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch sessions
  const fetchSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.get<UserSession[]>('/users/me/sessions/');
      
      if (response.success && response.data) {
        setSessions(response.data);
      } else {
        throw new Error(response.error?.message || 'Failed to fetch sessions');
      }
    } catch (error: any) {
      setError(error.message || 'Failed to load sessions');
      toast.error('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  // Load sessions on component mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Handle terminate single session
  const handleTerminateSession = async (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return;

    setSelectedSession(session);
    setIsTerminatingAll(false);
    setShowTerminateDialog(true);
  };

  // Handle terminate all other sessions
  const handleTerminateAllOthers = async () => {
    setSelectedSession(null);
    setIsTerminatingAll(true);
    setShowTerminateDialog(true);
  };

  // Confirm termination
  const handleConfirmTermination = async () => {
    try {
      setActionLoading(true);

      if (isTerminatingAll) {
        // Terminate all other sessions
        const response = await apiClient.delete('/users/me/sessions/all/');
        
        if (response.success) {
          // Keep only the current session
          setSessions(prev => prev.filter(session => session.is_current));
          toast.success('All other sessions terminated successfully');
        } else {
          throw new Error(response.error?.message || 'Failed to terminate sessions');
        }
      } else if (selectedSession) {
        // Terminate specific session
        const response = await apiClient.delete(`/users/me/sessions/${selectedSession.id}/`);
        
        if (response.success) {
          setSessions(prev => prev.filter(session => session.id !== selectedSession.id));
          toast.success('Session terminated successfully');
        } else {
          throw new Error(response.error?.message || 'Failed to terminate session');
        }
      }

      setShowTerminateDialog(false);
      setSelectedSession(null);
      setIsTerminatingAll(false);
    } catch (error: any) {
      toast.error(error.message || 'Failed to terminate session');
    } finally {
      setActionLoading(false);
    }
  };

  // Cancel termination
  const handleCancelTermination = () => {
    setShowTerminateDialog(false);
    setSelectedSession(null);
    setIsTerminatingAll(false);
  };

  return (
    <div className={className}>
      <SessionListView
        sessions={sessions}
        loading={loading}
        error={error}
        onTerminateSession={handleTerminateSession}
        onTerminateAllOthers={handleTerminateAllOthers}
        onRefresh={fetchSessions}
      />

      <SessionTerminateConfirmDialog
        session={selectedSession || undefined}
        isOpen={showTerminateDialog}
        onConfirm={handleConfirmTermination}
        onCancel={handleCancelTermination}
        loading={actionLoading}
        isTerminatingAll={isTerminatingAll}
      />
    </div>
  );
}