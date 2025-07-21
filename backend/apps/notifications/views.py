from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import logging

from .models import (
    NotificationTemplate, NotificationPreference, Notification,
    NotificationBatch, NotificationAnalytics
)
from .serializers import (
    NotificationTemplateSerializer, NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer, NotificationSerializer,
    NotificationCreateSerializer, NotificationBatchSerializer,
    NotificationBatchCreateSerializer, NotificationAnalyticsSerializer,
    NotificationAnalyticsSummarySerializer, NotificationMarkAsReadSerializer,
    NotificationStatsSerializer, NotificationSettingsSerializer
)
from .services import NotificationService, NotificationAnalyticsService
from core.permissions import IsAdminUser, IsOwnerOrAdmin

User = get_user_model()
logger = logging.getLogger(__name__)


# Notification Template Views (Admin only)
class NotificationTemplateListCreateView(generics.ListCreateAPIView):
    """
    List and create notification templates (Admin only)
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by template type
        template_type = self.request.query_params.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        # Filter by channel
        channel = self.request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('template_type', 'channel')


class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a notification template (Admin only)
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


# Notification Preference Views
class NotificationPreferenceListView(generics.ListAPIView):
    """
    List user's notification preferences
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)


class NotificationPreferenceUpdateView(APIView):
    """
    Bulk update user's notification preferences
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request):
        serializer = NotificationPreferenceUpdateSerializer(data=request.data)
        if serializer.is_valid():
            preferences_data = serializer.validated_data['preferences']
            
            updated_count = 0
            created_count = 0
            
            for pref_data in preferences_data:
                preference, created = NotificationPreference.objects.update_or_create(
                    user=request.user,
                    notification_type=pref_data['notification_type'],
                    channel=pref_data['channel'],
                    defaults={'is_enabled': pref_data['is_enabled']}
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            return Response({
                'message': f'Updated {updated_count} preferences, created {created_count} new preferences',
                'updated_count': updated_count,
                'created_count': created_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationPreferenceDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a specific notification preference
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)


# Notification Views
class NotificationListView(generics.ListAPIView):
    """
    List user's notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by channel
        channel = self.request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        # Filter unread notifications
        unread_only = self.request.query_params.get('unread_only')
        if unread_only and unread_only.lower() == 'true':
            queryset = queryset.exclude(status='READ')
        
        return queryset.select_related('template').order_by('-created_at')


class NotificationDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific notification
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related('template')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Mark as read if it's an in-app notification and not already read
        if instance.channel == 'IN_APP' and instance.status != 'READ':
            instance.mark_as_read()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NotificationCreateView(generics.CreateAPIView):
    """
    Create and send a notification (Admin only)
    """
    serializer_class = NotificationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Get target user
            user_id = request.data.get('user_id')
            if not user_id:
                return Response(
                    {'error': 'user_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Send notification
            service = NotificationService()
            notifications = service.send_notification(
                user=user,
                template_type=serializer.validated_data['template_type'],
                context_data=serializer.validated_data.get('context_data', {}),
                channels=serializer.validated_data.get('channels'),
                priority=serializer.validated_data.get('priority', 'NORMAL'),
                scheduled_at=serializer.validated_data.get('scheduled_at'),
                expires_at=serializer.validated_data.get('expires_at')
            )
            
            # Serialize and return created notifications
            response_serializer = NotificationSerializer(notifications, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationMarkAsReadView(APIView):
    """
    Mark notifications as read
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = NotificationMarkAsReadSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            notification_ids = serializer.validated_data['notification_ids']
            
            # Update notifications
            updated_count = Notification.objects.filter(
                id__in=notification_ids,
                user=request.user
            ).exclude(status='READ').update(
                status='READ',
                read_at=timezone.now()
            )
            
            return Response({
                'message': f'Marked {updated_count} notifications as read',
                'updated_count': updated_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationMarkAllAsReadView(APIView):
    """
    Mark all user's notifications as read
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        updated_count = Notification.objects.filter(
            user=request.user
        ).exclude(status='READ').update(
            status='READ',
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        })


class NotificationStatsView(APIView):
    """
    Get user's notification statistics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        now = timezone.now()
        
        # Base queryset
        notifications = Notification.objects.filter(user=user)
        
        # Basic counts
        total_notifications = notifications.count()
        unread_count = notifications.exclude(status='READ').count()
        read_count = notifications.filter(status='READ').count()
        failed_count = notifications.filter(status='FAILED').count()
        
        # Channel breakdown
        email_count = notifications.filter(channel='EMAIL').count()
        sms_count = notifications.filter(channel='SMS').count()
        push_count = notifications.filter(channel='PUSH').count()
        in_app_count = notifications.filter(channel='IN_APP').count()
        
        # Time-based counts
        today_count = notifications.filter(created_at__date=now.date()).count()
        week_start = now - timedelta(days=7)
        this_week_count = notifications.filter(created_at__gte=week_start).count()
        month_start = now - timedelta(days=30)
        this_month_count = notifications.filter(created_at__gte=month_start).count()
        
        stats_data = {
            'total_notifications': total_notifications,
            'unread_count': unread_count,
            'read_count': read_count,
            'failed_count': failed_count,
            'email_count': email_count,
            'sms_count': sms_count,
            'push_count': push_count,
            'in_app_count': in_app_count,
            'today_count': today_count,
            'this_week_count': this_week_count,
            'this_month_count': this_month_count,
        }
        
        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data)


class NotificationSettingsView(APIView):
    """
    Get user's notification settings overview
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get user preferences
        preferences = NotificationPreference.objects.filter(user=user)
        
        # Available notification types
        available_types = [
            {'value': choice[0], 'label': choice[1]}
            for choice in NotificationPreference.NOTIFICATION_TYPES
        ]
        
        # Available channels
        available_channels = [
            {'value': choice[0], 'label': choice[1]}
            for choice in NotificationPreference.CHANNELS
        ]
        
        settings_data = {
            'user_preferences': preferences,
            'available_types': available_types,
            'available_channels': available_channels,
        }
        
        serializer = NotificationSettingsSerializer(settings_data)
        return Response(serializer.data)


# Notification Batch Views (Admin only)
class NotificationBatchListCreateView(generics.ListCreateAPIView):
    """
    List and create notification batches (Admin only)
    """
    queryset = NotificationBatch.objects.all()
    serializer_class = NotificationBatchSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NotificationBatchCreateSerializer
        return NotificationBatchSerializer
    
    def perform_create(self, serializer):
        # Create batch
        batch_data = serializer.validated_data
        service = NotificationService()
        
        batch = service.send_bulk_notification(
            template_type=batch_data['template_type'],
            context_data=batch_data.get('context_data', {}),
            user_criteria=batch_data.get('user_criteria', {}),
            channels=batch_data['channels'],
            scheduled_at=batch_data.get('scheduled_at'),
            created_by=self.request.user,
            batch_name=batch_data['name']
        )
        
        return batch
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            batch = self.perform_create(serializer)
            response_serializer = NotificationBatchSerializer(batch)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationBatchDetailView(generics.RetrieveAPIView):
    """
    Retrieve notification batch details (Admin only)
    """
    queryset = NotificationBatch.objects.all()
    serializer_class = NotificationBatchSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


# Analytics Views (Admin only)
class NotificationAnalyticsListView(generics.ListAPIView):
    """
    List notification analytics (Admin only)
    """
    queryset = NotificationAnalytics.objects.all()
    serializer_class = NotificationAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=date_to)
            except ValueError:
                pass
        
        # Filter by template type
        template_type = self.request.query_params.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        # Filter by channel
        channel = self.request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)
        
        return queryset.order_by('-date', 'template_type', 'channel')


class NotificationAnalyticsSummaryView(APIView):
    """
    Get notification analytics summary (Admin only)
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # Get date range from query params
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if not date_from or not date_to:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get analytics summary
        service = NotificationAnalyticsService()
        summary = service.get_analytics_summary(start_date, end_date)
        
        # Get additional breakdowns
        analytics = NotificationAnalytics.objects.filter(
            date__range=[start_date, end_date]
        )
        
        # Channel breakdown
        channel_breakdown = list(
            analytics.values('channel')
            .annotate(
                total_sent=Count('sent_count'),
                total_delivered=Count('delivered_count'),
                total_failed=Count('failed_count')
            )
        )
        
        # Template type breakdown
        template_breakdown = list(
            analytics.values('template_type')
            .annotate(
                total_sent=Count('sent_count'),
                total_delivered=Count('delivered_count'),
                total_failed=Count('failed_count')
            )
        )
        
        # Daily trends
        daily_trends = list(
            analytics.values('date')
            .annotate(
                total_sent=Count('sent_count'),
                total_delivered=Count('delivered_count'),
                total_failed=Count('failed_count')
            )
            .order_by('date')
        )
        
        summary.update({
            'channel_breakdown': channel_breakdown,
            'template_breakdown': template_breakdown,
            'daily_trends': daily_trends,
        })
        
        serializer = NotificationAnalyticsSummarySerializer(summary)
        return Response(serializer.data)


# Utility Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def retry_failed_notifications(request):
    """
    Retry failed notifications (Admin only)
    """
    max_age_hours = request.data.get('max_age_hours', 24)
    
    service = NotificationService()
    service.retry_failed_notifications(max_age_hours)
    
    return Response({
        'message': f'Retried failed notifications (max age: {max_age_hours} hours)'
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def update_analytics(request):
    """
    Update notification analytics (Admin only)
    """
    date_str = request.data.get('date')
    
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        date = timezone.now().date()
    
    service = NotificationAnalyticsService()
    service.update_daily_analytics(date)
    
    return Response({
        'message': f'Updated analytics for {date}'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_types(request):
    """
    Get available notification types and channels
    """
    data = {
        'notification_types': [
            {'value': choice[0], 'label': choice[1]}
            for choice in NotificationPreference.NOTIFICATION_TYPES
        ],
        'channels': [
            {'value': choice[0], 'label': choice[1]}
            for choice in NotificationPreference.CHANNELS
        ],
        'template_types': [
            {'value': choice[0], 'label': choice[1]}
            for choice in NotificationTemplate.TEMPLATE_TYPES
        ],
        'priorities': [
            {'value': choice[0], 'label': choice[1]}
            for choice in Notification.PRIORITY_CHOICES
        ],
        'statuses': [
            {'value': choice[0], 'label': choice[1]}
            for choice in Notification.STATUS_CHOICES
        ],
    }
    
    return Response(data)