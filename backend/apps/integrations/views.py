from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import (
    IntegrationCategory, IntegrationProvider, Integration,
    IntegrationLog, IntegrationMapping, IntegrationWebhook,
    IntegrationSync, IntegrationTemplate
)
from .serializers import (
    IntegrationCategorySerializer, IntegrationProviderSerializer,
    IntegrationSerializer, IntegrationLogSerializer,
    IntegrationMappingSerializer, IntegrationWebhookSerializer,
    IntegrationSyncSerializer, IntegrationTemplateSerializer,
    IntegrationStatsSerializer, IntegrationTestSerializer,
    IntegrationConfigSerializer, BulkIntegrationActionSerializer
)
from .services import IntegrationFactory, sync_integration_data, test_integration_connection


class IntegrationCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for integration categories"""
    queryset = IntegrationCategory.objects.filter(is_active=True)
    serializer_class = IntegrationCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset


class IntegrationProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for integration providers"""
    queryset = IntegrationProvider.objects.filter(status='active')
    serializer_class = IntegrationProviderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        popular = self.request.query_params.get('popular')
        
        if category:
            queryset = queryset.filter(category__category=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if popular == 'true':
            queryset = queryset.filter(is_popular=True)
            
        return queryset.order_by('-is_popular', 'name')
    
    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """Get templates for a provider"""
        provider = self.get_object()
        templates = IntegrationTemplate.objects.filter(provider=provider)
        serializer = IntegrationTemplateSerializer(templates, many=True)
        return Response(serializer.data)


class IntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet for integrations"""
    queryset = Integration.objects.all()
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        category = self.request.query_params.get('category')
        provider = self.request.query_params.get('provider')
        search = self.request.query_params.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if category:
            queryset = queryset.filter(provider__category__category=category)
        if provider:
            queryset = queryset.filter(provider_id=provider)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(provider__name__icontains=search)
            )
            
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test integration connection"""
        integration = self.get_object()
        
        # Start background test
        task = test_integration_connection.delay(str(integration.id))
        
        return Response({
            'message': 'Connection test started',
            'task_id': task.id
        })
    
    @action(detail=True, methods=['post'])
    def sync_data(self, request, pk=None):
        """Trigger data sync"""
        integration = self.get_object()
        sync_type = request.data.get('sync_type', 'incremental')
        
        # Start background sync
        task = sync_integration_data.delay(str(integration.id), sync_type)
        
        return Response({
            'message': 'Data sync started',
            'task_id': task.id,
            'sync_type': sync_type
        })
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get integration logs"""
        integration = self.get_object()
        logs = IntegrationLog.objects.filter(integration=integration)
        
        # Filter by level
        level = request.query_params.get('level')
        if level:
            logs = logs.filter(level=level)
        
        # Filter by action type
        action_type = request.query_params.get('action_type')
        if action_type:
            logs = logs.filter(action_type=action_type)
        
        # Date range filter
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            logs = logs.filter(created_at__gte=start_date)
        if end_date:
            logs = logs.filter(created_at__lte=end_date)
        
        logs = logs.order_by('-created_at')[:100]  # Limit to 100 recent logs
        serializer = IntegrationLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def syncs(self, request, pk=None):
        """Get integration sync history"""
        integration = self.get_object()
        syncs = IntegrationSync.objects.filter(integration=integration)
        syncs = syncs.order_by('-created_at')[:50]  # Limit to 50 recent syncs
        serializer = IntegrationSyncSerializer(syncs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'])
    def mappings(self, request, pk=None):
        """Get or update integration mappings"""
        integration = self.get_object()
        
        if request.method == 'GET':
            mappings = IntegrationMapping.objects.filter(integration=integration)
            serializer = IntegrationMappingSerializer(mappings, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Bulk update mappings
            mappings_data = request.data.get('mappings', [])
            
            # Delete existing mappings
            IntegrationMapping.objects.filter(integration=integration).delete()
            
            # Create new mappings
            for mapping_data in mappings_data:
                mapping_data['integration'] = integration.id
                serializer = IntegrationMappingSerializer(data=mapping_data)
                if serializer.is_valid():
                    serializer.save()
            
            return Response({'message': 'Mappings updated successfully'})
    
    @action(detail=True, methods=['get', 'post'])
    def webhooks(self, request, pk=None):
        """Get or update integration webhooks"""
        integration = self.get_object()
        
        if request.method == 'GET':
            webhooks = IntegrationWebhook.objects.filter(integration=integration)
            serializer = IntegrationWebhookSerializer(webhooks, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Create or update webhook
            webhook_data = request.data
            webhook_data['integration'] = integration.id
            
            # Check if webhook exists
            existing_webhook = IntegrationWebhook.objects.filter(
                integration=integration,
                event_type=webhook_data.get('event_type')
            ).first()
            
            if existing_webhook:
                serializer = IntegrationWebhookSerializer(
                    existing_webhook, data=webhook_data, partial=True
                )
            else:
                serializer = IntegrationWebhookSerializer(data=webhook_data)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get integration statistics"""
        today = timezone.now().date()
        
        # Basic counts
        total_integrations = Integration.objects.count()
        active_integrations = Integration.objects.filter(status='active').count()
        failed_integrations = Integration.objects.filter(status='error').count()
        
        # Sync stats for today
        today_syncs = IntegrationSync.objects.filter(created_at__date=today)
        total_syncs_today = today_syncs.count()
        successful_syncs_today = today_syncs.filter(status='completed').count()
        failed_syncs_today = today_syncs.filter(status='failed').count()
        
        # API call stats for today
        today_logs = IntegrationLog.objects.filter(
            created_at__date=today,
            action_type='api_call'
        )
        total_api_calls_today = today_logs.count()
        average_response_time = today_logs.aggregate(
            avg_time=Avg('execution_time')
        )['avg_time'] or 0
        
        # Top providers
        top_providers = Integration.objects.values(
            'provider__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Recent errors
        recent_errors = IntegrationLog.objects.filter(
            level='error',
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-created_at')[:10]
        
        recent_errors_data = [{
            'integration': log.integration.name,
            'message': log.message,
            'created_at': log.created_at
        } for log in recent_errors]
        
        stats_data = {
            'total_integrations': total_integrations,
            'active_integrations': active_integrations,
            'failed_integrations': failed_integrations,
            'total_syncs_today': total_syncs_today,
            'successful_syncs_today': successful_syncs_today,
            'failed_syncs_today': failed_syncs_today,
            'total_api_calls_today': total_api_calls_today,
            'average_response_time': round(average_response_time, 2),
            'top_providers': list(top_providers),
            'recent_errors': recent_errors_data
        }
        
        serializer = IntegrationStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on integrations"""
        serializer = BulkIntegrationActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        integration_ids = serializer.validated_data['integration_ids']
        action = serializer.validated_data['action']
        parameters = serializer.validated_data.get('parameters', {})
        
        integrations = Integration.objects.filter(id__in=integration_ids)
        results = []
        
        for integration in integrations:
            try:
                if action == 'activate':
                    integration.status = 'active'
                    integration.save()
                    results.append({'id': integration.id, 'success': True})
                
                elif action == 'deactivate':
                    integration.status = 'inactive'
                    integration.save()
                    results.append({'id': integration.id, 'success': True})
                
                elif action == 'sync':
                    sync_type = parameters.get('sync_type', 'incremental')
                    task = sync_integration_data.delay(str(integration.id), sync_type)
                    results.append({
                        'id': integration.id, 
                        'success': True, 
                        'task_id': task.id
                    })
                
                elif action == 'test':
                    task = test_integration_connection.delay(str(integration.id))
                    results.append({
                        'id': integration.id, 
                        'success': True, 
                        'task_id': task.id
                    })
                
                elif action == 'delete':
                    integration.delete()
                    results.append({'id': integration.id, 'success': True})
                
            except Exception as e:
                results.append({
                    'id': integration.id, 
                    'success': False, 
                    'error': str(e)
                })
        
        return Response({
            'message': f'Bulk {action} completed',
            'results': results
        })


class IntegrationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for integration templates"""
    queryset = IntegrationTemplate.objects.all()
    serializer_class = IntegrationTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        provider = self.request.query_params.get('provider')
        category = self.request.query_params.get('category')
        official = self.request.query_params.get('official')
        
        if provider:
            queryset = queryset.filter(provider_id=provider)
        if category:
            queryset = queryset.filter(provider__category__category=category)
        if official == 'true':
            queryset = queryset.filter(is_official=True)
            
        return queryset.order_by('-is_official', '-rating', '-usage_count')
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Create integration from template"""
        template = self.get_object()
        serializer = IntegrationConfigSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        config_data = serializer.validated_data
        
        # Create integration from template
        integration = Integration.objects.create(
            name=config_data['name'],
            provider=template.provider,
            environment=config_data['environment'],
            configuration={**template.configuration_template, **config_data['configuration']},
            created_by=request.user
        )
        
        # Create mappings from template
        for mapping_data in template.mapping_template.get('mappings', []):
            IntegrationMapping.objects.create(
                integration=integration,
                **mapping_data
            )
        
        # Create webhooks from template
        for webhook_data in template.webhook_template.get('webhooks', []):
            IntegrationWebhook.objects.create(
                integration=integration,
                **webhook_data
            )
        
        # Update template usage count
        template.usage_count += 1
        template.save(update_fields=['usage_count'])
        
        serializer = IntegrationSerializer(integration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IntegrationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for integration logs"""
    queryset = IntegrationLog.objects.all()
    serializer_class = IntegrationLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        integration = self.request.query_params.get('integration')
        level = self.request.query_params.get('level')
        action_type = self.request.query_params.get('action_type')
        
        if integration:
            queryset = queryset.filter(integration_id=integration)
        if level:
            queryset = queryset.filter(level=level)
        if action_type:
            queryset = queryset.filter(action_type=action_type)
            
        return queryset.order_by('-created_at')


class IntegrationSyncViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for integration syncs"""
    queryset = IntegrationSync.objects.all()
    serializer_class = IntegrationSyncSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        integration = self.request.query_params.get('integration')
        status_filter = self.request.query_params.get('status')
        sync_type = self.request.query_params.get('sync_type')
        
        if integration:
            queryset = queryset.filter(integration_id=integration)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if sync_type:
            queryset = queryset.filter(sync_type=sync_type)
            
        return queryset.order_by('-created_at')