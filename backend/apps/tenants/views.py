from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.core.cache import cache
from datetime import datetime, timedelta
from .models import (
    Tenant, TenantUser, TenantSubscription, TenantUsage,
    TenantInvitation, TenantAuditLog, TenantBackup
)
from .serializers import (
    TenantSerializer, TenantCreateSerializer, TenantUserSerializer,
    TenantUserCreateSerializer, TenantSubscriptionSerializer,
    TenantUsageSerializer, TenantInvitationSerializer,
    TenantInvitationCreateSerializer, TenantAuditLogSerializer,
    TenantBackupSerializer, TenantDashboardSerializer,
    TenantSettingsSerializer, TenantAnalyticsSerializer
)
from .services import (
    TenantProvisioningService, TenantUserManagementService,
    TenantBillingService, TenantAnalyticsService, TenantBackupService
)
from .middleware import get_current_tenant, TenantPermissionMixin


class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant management"""
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant'):
            # Regular tenant users can only see their own tenant
            return Tenant.objects.filter(id=user.tenant.id)
        else:
            # Super admin can see all tenants
            return Tenant.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TenantCreateSerializer
        return TenantSerializer
    
    def create(self, request):
        """Create new tenant"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            tenant = TenantProvisioningService.create_tenant(serializer.validated_data)
            response_serializer = TenantSerializer(tenant)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get tenant dashboard data"""
        tenant = self.get_object()
        
        # Get dashboard stats
        stats = TenantAnalyticsService.get_tenant_dashboard_stats(tenant)
        
        # Get recent activity
        recent_activity = TenantAuditLog.objects.filter(
            tenant=tenant
        ).order_by('-timestamp')[:10]
        
        # Get usage chart data
        usage_data = TenantUsage.objects.filter(
            tenant=tenant,
            period_start__gte=timezone.now() - timedelta(days=30)
        ).order_by('period_start')
        
        usage_chart_data = [
            {
                'date': usage.period_start.date().isoformat(),
                'users': usage.users_count,
                'storage': float(usage.storage_used_gb),
                'api_calls': usage.api_calls_count,
            }
            for usage in usage_data
        ]
        
        # Get alerts
        alerts = []
        if stats['storage_used'] > tenant.max_storage_gb * 0.8:
            alerts.append({
                'type': 'warning',
                'message': 'Storage usage is approaching limit'
            })
        
        if stats['users_count'] > tenant.max_users * 0.9:
            alerts.append({
                'type': 'warning',
                'message': 'User count is approaching limit'
            })
        
        dashboard_data = {
            'tenant': tenant,
            'stats': stats,
            'recent_activity': recent_activity,
            'usage_chart_data': usage_chart_data,
            'alerts': alerts,
        }
        
        serializer = TenantDashboardSerializer(dashboard_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'put'])
    def settings(self, request, pk=None):
        """Get or update tenant settings"""
        tenant = self.get_object()
        
        if request.method == 'GET':
            settings_data = {
                'branding': {
                    'primary_color': tenant.primary_color,
                    'secondary_color': tenant.secondary_color,
                    'logo': tenant.logo.url if tenant.logo else None,
                    'favicon': tenant.favicon.url if tenant.favicon else None,
                },
                'features': tenant.features,
                'limits': {
                    'max_users': tenant.max_users,
                    'max_products': tenant.max_products,
                    'max_orders': tenant.max_orders,
                    'max_storage_gb': tenant.max_storage_gb,
                },
                'notifications': tenant.custom_settings.get('notifications', {}),
                'security': tenant.custom_settings.get('security', {}),
                'integrations': tenant.custom_settings.get('integrations', {}),
            }
            
            serializer = TenantSettingsSerializer(settings_data)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = TenantSettingsSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            data = serializer.validated_data
            
            # Update branding
            if 'branding' in data:
                branding = data['branding']
                tenant.primary_color = branding.get('primary_color', tenant.primary_color)
                tenant.secondary_color = branding.get('secondary_color', tenant.secondary_color)
            
            # Update features
            if 'features' in data:
                tenant.features.update(data['features'])
            
            # Update custom settings
            if 'notifications' in data:
                tenant.custom_settings['notifications'] = data['notifications']
            
            if 'security' in data:
                tenant.custom_settings['security'] = data['security']
            
            if 'integrations' in data:
                tenant.custom_settings['integrations'] = data['integrations']
            
            tenant.save()
            
            return Response({'message': 'Settings updated successfully'})
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get tenant analytics"""
        tenant = self.get_object()
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = timezone.now() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = timezone.now()
        
        # Generate analytics report
        report = TenantAnalyticsService.generate_usage_report(
            tenant, start_date, end_date
        )
        
        serializer = TenantAnalyticsSerializer(report)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def backup(self, request, pk=None):
        """Create tenant backup"""
        tenant = self.get_object()
        backup_type = request.data.get('backup_type', 'full')
        
        backup = TenantBackupService.create_backup(tenant, backup_type)
        serializer = TenantBackupSerializer(backup)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore tenant from backup"""
        tenant = self.get_object()
        backup_id = request.data.get('backup_id')
        
        if not backup_id:
            return Response(
                {'error': 'backup_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            TenantBackupService.restore_backup(tenant, backup_id)
            return Response({'message': 'Restore process started'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TenantUserViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant user management"""
    serializer_class = TenantUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return TenantUser.objects.filter(tenant=tenant)
        return TenantUser.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TenantUserCreateSerializer
        return TenantUserSerializer
    
    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)
    
    @action(detail=False, methods=['post'])
    def invite(self, request):
        """Invite user to tenant"""
        serializer = TenantInvitationCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        tenant = get_current_tenant()
        invitation = TenantUserManagementService.invite_user(
            tenant=tenant,
            inviter=request.user,
            email=serializer.validated_data['email'],
            role=serializer.validated_data['role']
        )
        
        response_serializer = TenantInvitationSerializer(invitation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user"""
        user = self.get_object()
        user.is_active = False
        user.save()
        
        return Response({'message': 'User deactivated successfully'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user"""
        user = self.get_object()
        user.is_active = True
        user.save()
        
        return Response({'message': 'User activated successfully'})


class TenantSubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tenant subscription management"""
    serializer_class = TenantSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return TenantSubscription.objects.filter(tenant=tenant)
        return TenantSubscription.objects.none()
    
    @action(detail=False, methods=['post'])
    def upgrade(self, request):
        """Upgrade subscription plan"""
        tenant = get_current_tenant()
        plan_data = request.data
        
        try:
            subscription = TenantBillingService.create_subscription(tenant, plan_data)
            serializer = TenantSubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel subscription"""
        subscription = self.get_object()
        
        # Update subscription status
        subscription.payment_status = 'cancelled'
        subscription.save()
        
        # Update tenant status
        subscription.tenant.status = 'cancelled'
        subscription.tenant.save()
        
        return Response({'message': 'Subscription cancelled successfully'})


class TenantUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tenant usage tracking"""
    serializer_class = TenantUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return TenantUsage.objects.filter(tenant=tenant).order_by('-period_start')
        return TenantUsage.objects.none()
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current usage statistics"""
        tenant = get_current_tenant()
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create today's usage record
        today = timezone.now().date()
        usage, created = TenantUsage.objects.get_or_create(
            tenant=tenant,
            period_start=datetime.combine(today, datetime.min.time()),
            period_end=datetime.combine(today, datetime.max.time()),
            defaults={
                'users_count': tenant.users.count(),
                'storage_used_gb': TenantAnalyticsService.calculate_storage_usage(tenant),
                'api_calls_count': TenantAnalyticsService.get_api_calls_count(tenant, 'today'),
            }
        )
        
        serializer = TenantUsageSerializer(usage)
        return Response(serializer.data)


class TenantInvitationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tenant invitations"""
    serializer_class = TenantInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return TenantInvitation.objects.filter(tenant=tenant).order_by('-created_at')
        return TenantInvitation.objects.none()
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend invitation"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Can only resend pending invitations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extend expiration and resend
        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.save()
        
        TenantUserManagementService.send_invitation_email(invitation)
        
        return Response({'message': 'Invitation resent successfully'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel invitation"""
        invitation = self.get_object()
        invitation.status = 'cancelled'
        invitation.save()
        
        return Response({'message': 'Invitation cancelled successfully'})


class TenantAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tenant audit logs"""
    serializer_class = TenantAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            queryset = TenantAuditLog.objects.filter(tenant=tenant).order_by('-timestamp')
            
            # Filter by action
            action = self.request.query_params.get('action')
            if action:
                queryset = queryset.filter(action=action)
            
            # Filter by user
            user_id = self.request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            # Filter by date range
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')
            
            if start_date:
                queryset = queryset.filter(timestamp__gte=start_date)
            if end_date:
                queryset = queryset.filter(timestamp__lte=end_date)
            
            return queryset
        return TenantAuditLog.objects.none()


class TenantBackupViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tenant backups"""
    serializer_class = TenantBackupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return TenantBackup.objects.filter(tenant=tenant).order_by('-created_at')
        return TenantBackup.objects.none()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download backup file"""
        backup = self.get_object()
        
        if backup.status != 'completed':
            return Response(
                {'error': 'Backup is not completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return download URL or file response
        return Response({
            'download_url': f'/api/tenants/backups/{backup.id}/file/',
            'file_size': backup.file_size,
            'created_at': backup.created_at,
        })


class AcceptInvitationView(APIView):
    """View for accepting tenant invitations"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, token):
        """Accept invitation and create user account"""
        try:
            user = TenantUserManagementService.accept_invitation(
                token=token,
                user_data=request.data
            )
            
            serializer = TenantUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TenantStatsView(APIView):
    """View for tenant statistics (for super admin)"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get overall tenant statistics"""
        stats = {
            'total_tenants': Tenant.objects.count(),
            'active_tenants': Tenant.objects.filter(status='active').count(),
            'trial_tenants': Tenant.objects.filter(status='trial').count(),
            'suspended_tenants': Tenant.objects.filter(status='suspended').count(),
            'total_users': TenantUser.objects.count(),
            'total_revenue': TenantSubscription.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'plans_distribution': Tenant.objects.values('plan').annotate(
                count=Count('id')
            ),
            'monthly_signups': Tenant.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }
        
        return Response(stats)