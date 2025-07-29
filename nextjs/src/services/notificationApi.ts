import { apiClient } from '../utils/api';
import type {
  Notification,
  NotificationPreference,
  NotificationStats,
  NotificationSettings,
  NotificationFilters,
  NotificationCreateData,
  PreferenceUpdateData,
  NotificationBatch,
  NotificationAnalytics
} from '@/components/notifications/types';

const NOTIFICATIONS_BASE_URL = '/api/v1/notifications';

export const notificationApi = {
  // Notification CRUD operations
  async getNotifications(filters?: NotificationFilters): Promise<Notification[]> {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
    }
    
    const url = `${NOTIFICATIONS_BASE_URL}${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get<Notification[]>(url);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch notifications');
    }
    return response.data;
  },

  async getNotification(id: string): Promise<Notification> {
    const response = await apiClient.get<Notification>(`${NOTIFICATIONS_BASE_URL}/${id}/`);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || `Failed to fetch notification with ID ${id}`);
    }
    return response.data;
  },

  async createNotification(data: NotificationCreateData): Promise<Notification[]> {
    const response = await apiClient.post<Notification[]>(`${NOTIFICATIONS_BASE_URL}/create/`, data);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to create notification');
    }
    return response.data;
  },

  async markAsRead(notificationIds: string[]): Promise<{ message: string; updated_count: number }> {
    const response = await apiClient.post<{ message: string; updated_count: number }>(
      `${NOTIFICATIONS_BASE_URL}/mark-as-read/`,
      { notification_ids: notificationIds }
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to mark notifications as read');
    }
    return response.data;
  },

  async markAllAsRead(): Promise<{ message: string; updated_count: number }> {
    const response = await apiClient.post<{ message: string; updated_count: number }>(
      `${NOTIFICATIONS_BASE_URL}/mark-all-as-read/`
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to mark all notifications as read');
    }
    return response.data;
  },

  // Notification preferences
  async getPreferences(): Promise<NotificationPreference[]> {
    const response = await apiClient.get<NotificationPreference[]>(`${NOTIFICATIONS_BASE_URL}/preferences/`);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch notification preferences');
    }
    return response.data;
  },

  async updatePreferences(data: PreferenceUpdateData): Promise<{ message: string; updated_count: number; created_count: number }> {
    const response = await apiClient.put<{ message: string; updated_count: number; created_count: number }>(
      `${NOTIFICATIONS_BASE_URL}/preferences/update/`,
      data
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to update notification preferences');
    }
    return response.data;
  },

  async updatePreference(id: number, data: Partial<NotificationPreference>): Promise<NotificationPreference> {
    const response = await apiClient.patch<NotificationPreference>(`${NOTIFICATIONS_BASE_URL}/preferences/${id}/`, data);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || `Failed to update notification preference with ID ${id}`);
    }
    return response.data;
  },

  // Notification statistics and settings
  async getStats(): Promise<NotificationStats> {
    const response = await apiClient.get<NotificationStats>(`${NOTIFICATIONS_BASE_URL}/stats/`);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch notification stats');
    }
    return response.data;
  },

  async getSettings(): Promise<NotificationSettings> {
    const response = await apiClient.get<NotificationSettings>(`${NOTIFICATIONS_BASE_URL}/settings/`);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch notification settings');
    }
    return response.data;
  },

  // Notification types and options
  async getNotificationTypes(): Promise<{
    notification_types: Array<{ value: string; label: string }>;
    channels: Array<{ value: string; label: string }>;
    template_types: Array<{ value: string; label: string }>;
    priorities: Array<{ value: string; label: string }>;
    statuses: Array<{ value: string; label: string }>;
  }> {
    const response = await apiClient.get<{
      notification_types: Array<{ value: string; label: string }>;
      channels: Array<{ value: string; label: string }>;
      template_types: Array<{ value: string; label: string }>;
      priorities: Array<{ value: string; label: string }>;
      statuses: Array<{ value: string; label: string }>;
    }>(`${NOTIFICATIONS_BASE_URL}/types/`);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch notification types');
    }
    return response.data;
  },

  // Admin-only endpoints
  async getBatches(): Promise<NotificationBatch[]> {
    const response = await apiClient.get<NotificationBatch[]>(`${NOTIFICATIONS_BASE_URL}/batches/`);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch notification batches');
    }
    return response.data;
  },

  async getBatch(id: string): Promise<NotificationBatch> {
    const response = await apiClient.get<NotificationBatch>(`${NOTIFICATIONS_BASE_URL}/batches/${id}/`);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || `Failed to fetch notification batch with ID ${id}`);
    }
    return response.data;
  },

  async getAnalytics(filters?: { date_from?: string; date_to?: string; template_type?: string; channel?: string }): Promise<NotificationAnalytics[]> {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value);
        }
      });
    }
    
    const url = `${NOTIFICATIONS_BASE_URL}/analytics${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get<NotificationAnalytics[]>(url);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch notification analytics');
    }
    return response.data;
  },

  async getAnalyticsSummary(dateFrom?: string, dateTo?: string): Promise<any> {
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    
    const url = `${NOTIFICATIONS_BASE_URL}/analytics/summary/${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get<any>(url);
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to fetch notification analytics summary');
    }
    return response.data;
  },

  async retryFailedNotifications(maxAgeHours?: number): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `${NOTIFICATIONS_BASE_URL}/retry-failed/`,
      { max_age_hours: maxAgeHours || 24 }
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to retry failed notifications');
    }
    return response.data;
  },

  async updateAnalytics(date?: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>(
      `${NOTIFICATIONS_BASE_URL}/update-analytics/`,
      { date }
    );
    if (!response.success || !response.data) {
      throw new Error(response.error?.message || 'Failed to update analytics');
    }
    return response.data;
  }
};