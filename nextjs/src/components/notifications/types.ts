export interface NotificationTemplate {
  id: number;
  name: string;
  template_type: string;
  template_type_display: string;
  channel: string;
  channel_display: string;
  subject_template: string;
  body_template: string;
  html_template?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreference {
  id: number;
  notification_type: string;
  notification_type_display: string;
  channel: string;
  channel_display: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  user: string;
  template?: NotificationTemplate;
  channel: string;
  channel_display: string;
  priority: string;
  priority_display: string;
  status: string;
  status_display: string;
  subject: string;
  message: string;
  html_content?: string;
  recipient_email?: string;
  recipient_phone?: string;
  sent_at?: string;
  delivered_at?: string;
  read_at?: string;
  scheduled_at?: string;
  expires_at?: string;
  metadata?: Record<string, any>;
  external_id?: string;
  error_message?: string;
  retry_count: number;
  max_retries: number;
  is_expired: boolean;
  can_retry: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationStats {
  total_notifications: number;
  unread_count: number;
  read_count: number;
  failed_count: number;
  email_count: number;
  sms_count: number;
  push_count: number;
  in_app_count: number;
  today_count: number;
  this_week_count: number;
  this_month_count: number;
}

export interface NotificationSettings {
  user_preferences: NotificationPreference[];
  available_types: Array<{
    value: string;
    label: string;
  }>;
  available_channels: Array<{
    value: string;
    label: string;
  }>;
}

export interface NotificationBatch {
  id: string;
  name: string;
  template: NotificationTemplate;
  status: string;
  status_display: string;
  total_recipients: number;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  success_rate: number;
  target_criteria: Record<string, any>;
  scheduled_at?: string;
  started_at?: string;
  completed_at?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationAnalytics {
  id: number;
  date: string;
  template_type: string;
  template_type_display: string;
  channel: string;
  channel_display: string;
  sent_count: number;
  delivered_count: number;
  read_count: number;
  failed_count: number;
  delivery_rate: number;
  read_rate: number;
  failure_rate: number;
  created_at: string;
  updated_at: string;
}

export interface NotificationFilters {
  status?: string;
  channel?: string;
  priority?: string;
  date_from?: string;
  date_to?: string;
  unread_only?: boolean;
}

export interface NotificationCreateData {
  user_id: number;
  template_type: string;
  channels: string[];
  context_data?: Record<string, any>;
  priority?: string;
  scheduled_at?: string;
  expires_at?: string;
}

export interface PreferenceUpdateData {
  preferences: Array<{
    notification_type: string;
    channel: string;
    is_enabled: boolean;
  }>;
}