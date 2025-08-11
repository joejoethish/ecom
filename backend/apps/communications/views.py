"""
Communications API views for admin panel.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
import json

from core.permissions import IsAdminUser
from .models import (
    EmailTemplate, EmailCampaign, EmailRecipient, EmailAutomation,
    EmailAutomationInstance, EmailList, EmailSubscriber, EmailAnalytics,
    EmailDeliverabilitySettings, EmailSuppressionList
)
from .serializers import (
    EmailTemplateSerializer, EmailTemplateCreateUpdateSerializer,
    EmailCampaignSerializer, EmailCampaignCreateUpdateSerializer,
    EmailRecipientSerializer, EmailAutomationSerializer,
    EmailAutomationInstanceSerializer, EmailListSerializer,
    EmailSubscriberSerializer, EmailAnalyticsSerializer,
    EmailDeliverabilitySettingsSerializer, EmailSuppressionListSerializer,
    EmailDashboardSerializer, EmailPerformanceSerializer,
    EmailTemplatePreviewSerializer, EmailCampaignTestSerializer,
    EmailBulkActionSerializer, EmailSegmentationSerializer,
    EmailA11yTestSerializer
)
from .services import (
    EmailTemplateService, EmailCampaignService, EmailAutomationService,
    EmailListService, EmailAnalyticsService, EmailDeliverabilityService
)


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for email template management.
    """
    queryset = EmailTemplate.objects.filter(is_deleted=False).order_by('-usage_count', 'name')
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return EmailTemplateCreateUpdateSerializer
        return EmailTemplateSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        template_type = self.request.query_params.get('template_type')
        is_active = self.request.query_params.get('is_active')
        is_system = self.request.query_params.get('is_system')
        
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_system is not None:
            queryset = queryset.filter(is_system_template=is_system.lower() == 'true')
            
        return queryset

    def perform_create(self, serializer):
        """Set created_by when creating template."""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete template."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate an email template."""
        template = self.get_object()
        
        template.pk = None
        template.name = f"{template.name} (Copy)"
        template.is_system_template = False
        template.created_by = request.user
        template.usage_count = 0
        template.save()
        
        serializer = EmailTemplateSerializer(template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Preview email template with sample data."""
        template = self.get_object()
        
        serializer = EmailTemplatePreviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        preview_data = serializer.validated_data
        
        try:
            result = EmailTemplateService.preview_template(
                template, preview_data.get('preview_data', {}),
                preview_data.get('render_html', True),
                preview_data.get('render_text', False)
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to preview template: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def test_accessibility(self, request, pk=None):
        """Test email template accessibility."""
        template = self.get_object()
        
        serializer = EmailA11yTestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_data = serializer.validated_data
        
        try:
            result = EmailTemplateService.test_accessibility(
                template, test_data['test_types']
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to test accessibility: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailCampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet for email campaign management.
    """
    queryset = EmailCampaign.objects.filter(is_deleted=False).order_by('-created_at')
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return EmailCampaignCreateUpdateSerializer
        return EmailCampaignSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        campaign_type = self.request.query_params.get('campaign_type')
        status_filter = self.request.query_params.get('status')
        created_by = self.request.query_params.get('created_by')
        
        if campaign_type:
            queryset = queryset.filter(campaign_type=campaign_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
            
        return queryset

    def perform_create(self, serializer):
        """Set created_by when creating campaign."""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete campaign."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        """Send test email for campaign."""
        campaign = self.get_object()
        
        serializer = EmailCampaignTestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_data = serializer.validated_data
        
        try:
            result = EmailCampaignService.send_test_email(
                campaign, test_data['test_emails'],
                test_data.get('personalization_data', {})
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to send test email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule campaign for sending."""
        campaign = self.get_object()
        scheduled_at = request.data.get('scheduled_at')
        
        if not scheduled_at:
            return Response(
                {'error': 'scheduled_at is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            EmailCampaignService.schedule_campaign(campaign, scheduled_at)
            return Response({'message': 'Campaign scheduled successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to schedule campaign: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def send_now(self, request, pk=None):
        """Send campaign immediately."""
        campaign = self.get_object()
        
        try:
            result = EmailCampaignService.send_campaign(campaign, request.user)
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to send campaign: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause campaign sending."""
        campaign = self.get_object()
        
        try:
            EmailCampaignService.pause_campaign(campaign)
            return Response({'message': 'Campaign paused successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to pause campaign: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume paused campaign."""
        campaign = self.get_object()
        
        try:
            EmailCampaignService.resume_campaign(campaign)
            return Response({'message': 'Campaign resumed successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to resume campaign: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def recipients(self, request, pk=None):
        """Get campaign recipients."""
        campaign = self.get_object()
        recipients = campaign.recipients.all().order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            recipients = recipients.filter(status=status_filter)
        
        serializer = EmailRecipientSerializer(recipients, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get campaign analytics."""
        campaign = self.get_object()
        
        try:
            analytics = EmailAnalyticsService.get_campaign_analytics(campaign.id)
            return Response(analytics)
        except Exception as e:
            return Response(
                {'error': f'Failed to get analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on campaigns."""
        serializer = EmailBulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action_data = serializer.validated_data
        
        try:
            result = EmailCampaignService.bulk_action(
                action_data['action'], action_data['campaign_ids'], request.user
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to perform bulk action: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailAutomationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for email automation management.
    """
    queryset = EmailAutomation.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = EmailAutomationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        trigger_type = self.request.query_params.get('trigger_type')
        is_active = self.request.query_params.get('is_active')
        
        if trigger_type:
            queryset = queryset.filter(trigger_type=trigger_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_create(self, serializer):
        """Set created_by when creating automation."""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete automation."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate email automation."""
        automation = self.get_object()
        automation.is_active = True
        automation.save()
        
        return Response({'message': 'Automation activated successfully'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate email automation."""
        automation = self.get_object()
        automation.is_active = False
        automation.save()
        
        return Response({'message': 'Automation deactivated successfully'})

    @action(detail=True, methods=['get'])
    def instances(self, request, pk=None):
        """Get automation instances."""
        automation = self.get_object()
        instances = automation.instances.all().order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            instances = instances.filter(status=status_filter)
        
        serializer = EmailAutomationInstanceSerializer(instances, many=True)
        return Response(serializer.data)


class EmailListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for email list management.
    """
    queryset = EmailList.objects.filter(is_deleted=False).order_by('name')
    serializer_class = EmailListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_create(self, serializer):
        """Set created_by when creating list."""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete list."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['get'])
    def subscribers(self, request, pk=None):
        """Get list subscribers."""
        email_list = self.get_object()
        subscribers = email_list.subscribers.all().order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            subscribers = subscribers.filter(status=status_filter)
        
        serializer = EmailSubscriberSerializer(subscribers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def import_subscribers(self, request, pk=None):
        """Import subscribers from CSV file."""
        email_list = self.get_object()
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            return Response(
                {'error': 'CSV file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = EmailListService.import_subscribers(email_list, csv_file)
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to import subscribers: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def export_subscribers(self, request, pk=None):
        """Export subscribers to CSV file."""
        email_list = self.get_object()
        
        try:
            csv_content = EmailListService.export_subscribers(email_list)
            
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{email_list.name}_subscribers.csv"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Failed to export subscribers: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for email analytics and reporting.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get email dashboard data."""
        try:
            dashboard_data = EmailAnalyticsService.get_dashboard_data()
            serializer = EmailDashboardSerializer(dashboard_data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get dashboard data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get email performance analytics."""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        campaign_type = request.query_params.get('campaign_type')
        
        try:
            performance_data = EmailAnalyticsService.get_performance_analytics(
                date_from, date_to, campaign_type
            )
            serializer = EmailPerformanceSerializer(performance_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get performance data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def deliverability(self, request):
        """Get email deliverability metrics."""
        try:
            deliverability_data = EmailDeliverabilityService.get_deliverability_metrics()
            return Response(deliverability_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get deliverability data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailDeliverabilitySettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for email deliverability settings management.
    """
    queryset = EmailDeliverabilitySettings.objects.filter(is_deleted=False).order_by('name')
    serializer_class = EmailDeliverabilitySettingsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        provider = self.request.query_params.get('provider')
        is_active = self.request.query_params.get('is_active')
        
        if provider:
            queryset = queryset.filter(provider=provider)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_destroy(self, instance):
        """Soft delete settings."""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set as default email provider."""
        settings = self.get_object()
        
        # Remove default from other settings
        EmailDeliverabilitySettings.objects.filter(is_default=True).update(is_default=False)
        
        # Set this as default
        settings.is_default = True
        settings.save()
        
        return Response({'message': 'Provider set as default'})

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test email provider connection."""
        settings = self.get_object()
        
        try:
            result = EmailDeliverabilityService.test_provider_connection(settings)
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to test connection: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailSuppressionListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for email suppression list management.
    """
    queryset = EmailSuppressionList.objects.filter(is_deleted=False).order_by('-suppressed_at')
    serializer_class = EmailSuppressionListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        suppression_type = self.request.query_params.get('suppression_type')
        email = self.request.query_params.get('email')
        
        if suppression_type:
            queryset = queryset.filter(suppression_type=suppression_type)
        if email:
            queryset = queryset.filter(email__icontains=email)
            
        return queryset

    def perform_create(self, serializer):
        """Set added_by when creating suppression."""
        serializer.save(added_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete suppression."""
        instance.is_deleted = True
        instance.save()

    @action(detail=False, methods=['post'])
    def bulk_add(self, request):
        """Bulk add emails to suppression list."""
        emails = request.data.get('emails', [])
        suppression_type = request.data.get('suppression_type', 'manual')
        reason = request.data.get('reason', '')
        
        if not emails:
            return Response(
                {'error': 'emails list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            added_count = 0
            for email in emails:
                suppression, created = EmailSuppressionList.objects.get_or_create(
                    email=email,
                    defaults={
                        'suppression_type': suppression_type,
                        'reason': reason,
                        'added_by': request.user
                    }
                )
                if created:
                    added_count += 1
            
            return Response({
                'message': f'Added {added_count} emails to suppression list',
                'added_count': added_count
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to add emails: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )