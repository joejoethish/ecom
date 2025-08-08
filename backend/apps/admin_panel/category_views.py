"""
Comprehensive Category Management Views for Admin Panel.
"""
import uuid
import json
import csv
import io
from datetime import datetime, timedelta
from django.db import transaction, models
from django.db.models import Q, Count, Sum, Avg, F, Case, When
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .category_models import (
    CategoryTemplate, EnhancedCategory, CategoryAttribute, 
    CategoryPerformanceMetric, CategoryMerchandising, CategoryAuditLog,
    CategoryRelationship, CategoryImportExport, CategoryRecommendation
)
from .category_serializers import (
    CategoryTemplateSerializer, EnhancedCategorySerializer, EnhancedCategoryListSerializer,
    CategoryTreeSerializer, CategoryAttributeSerializer, CategoryPerformanceMetricSerializer,
    CategoryMerchandisingSerializer, CategoryAuditLogSerializer, CategoryRelationshipSerializer,
    CategoryImportExportSerializer, CategoryRecommendationSerializer, CategoryBulkOperationSerializer,
    CategoryAnalyticsSerializer, CategorySearchSerializer
)
from .permissions import AdminPanelPermission
from .models import AdminUser


class CategoryTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category templates.
    """
    queryset = CategoryTemplate.objects.all()
    serializer_class = CategoryTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_active', 'is_system_template', 'created_by']
    ordering_fields = ['name', 'usage_count', 'created_at']
    ordering = ['-usage_count', 'name']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Use template to create a new category."""
        template = self.get_object()
        
        # Increment usage count
        template.usage_count = F('usage_count') + 1
        template.save(update_fields=['usage_count'])
        
        # Create category from template
        category_data = {
            'name': request.data.get('name', ''),
            'description': request.data.get('description', template.description),
            'template': template.id,
            'custom_attributes': template.default_attributes,
            'meta_title': template.seo_template.get('meta_title', ''),
            'meta_description': template.seo_template.get('meta_description', ''),
            'meta_keywords': template.seo_template.get('meta_keywords', ''),
        }
        
        serializer = EnhancedCategorySerializer(data=category_data, context={'request': request})
        if serializer.is_valid():
            category = serializer.save()
            return Response(EnhancedCategorySerializer(category, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnhancedCategoryViewSet(viewsets.ModelViewSet):
    """
    Comprehensive ViewSet for enhanced category management.
    """
    queryset = EnhancedCategory.objects.select_related(
        'parent', 'template', 'created_by', 'last_modified_by', 'approved_by'
    ).prefetch_related(
        'children', 'attributes', 'performance_metrics', 'merchandising'
    )
    permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'meta_title', 'meta_keywords']
    filterset_fields = [
        'status', 'visibility', 'is_featured', 'parent', 'level', 
        'language', 'created_by', 'template'
    ]
    ordering_fields = [
        'name', 'created_at', 'updated_at', 'sort_order', 'level', 
        'product_count', 'conversion_rate', 'view_count'
    ]
    ordering = ['tree_id', 'lft']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return EnhancedCategoryListSerializer
        elif self.action == 'tree':
            return CategoryTreeSerializer
        return EnhancedCategorySerializer

    def get_queryset(self):
        """Filter queryset based on user permissions and request parameters."""
        queryset = super().get_queryset()
        
        # Apply user-specific filters if needed
        user = self.request.user
        if not user.is_superuser:
            # Filter based on user access roles
            queryset = queryset.filter(
                Q(access_roles__in=user.roles.all()) | 
                Q(access_roles__isnull=True)
            ).exclude(restricted_users=user)
        
        return queryset

    def perform_create(self, serializer):
        """Create category with audit logging."""
        with transaction.atomic():
            category = serializer.save()
            
            # Log creation
            CategoryAuditLog.objects.create(
                category=category,
                action='create',
                user=self.request.user,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                additional_data={'initial_data': serializer.validated_data}
            )

    def perform_update(self, serializer):
        """Update category with change tracking."""
        with transaction.atomic():
            # Store previous state
            previous_state = {}
            if serializer.instance:
                previous_state = {
                    field.name: getattr(serializer.instance, field.name)
                    for field in serializer.instance._meta.fields
                }
            
            category = serializer.save()
            
            # Track changes
            field_changes = {}
            for field_name, new_value in serializer.validated_data.items():
                old_value = previous_state.get(field_name)
                if old_value != new_value:
                    field_changes[field_name] = {
                        'old': str(old_value) if old_value is not None else None,
                        'new': str(new_value) if new_value is not None else None
                    }
            
            # Log update
            if field_changes:
                CategoryAuditLog.objects.create(
                    category=category,
                    action='update',
                    field_changes=field_changes,
                    previous_state=previous_state,
                    user=self.request.user,
                    ip_address=self.get_client_ip(),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', '')
                )

    def perform_destroy(self, instance):
        """Delete category with audit logging."""
        with transaction.atomic():
            # Log deletion
            CategoryAuditLog.objects.create(
                category=instance,
                action='delete',
                previous_state={
                    field.name: getattr(instance, field.name)
                    for field in instance._meta.fields
                },
                user=self.request.user,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Soft delete or hard delete based on configuration
            if hasattr(instance, 'is_deleted'):
                instance.is_deleted = True
                instance.save()
            else:
                instance.delete()

    def get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure for drag-and-drop interface."""
        # Get root categories
        root_categories = self.get_queryset().filter(parent__isnull=True)
        serializer = CategoryTreeSerializer(root_categories, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move category to new position in tree."""
        category = self.get_object()
        target_id = request.data.get('target_id')
        position = request.data.get('position', 'last-child')
        
        try:
            with transaction.atomic():
                if target_id:
                    target = EnhancedCategory.objects.get(id=target_id)
                    
                    # Prevent circular references
                    if category.is_ancestor_of(target):
                        return Response(
                            {'error': 'Cannot move category to its descendant'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Store previous parent for logging
                    previous_parent = category.parent
                    
                    # Move category
                    category.move_to(target, position)
                    
                    # Log move operation
                    CategoryAuditLog.objects.create(
                        category=category,
                        action='move',
                        field_changes={
                            'parent': {
                                'old': str(previous_parent.id) if previous_parent else None,
                                'new': str(target.id)
                            },
                            'position': {'new': position}
                        },
                        user=request.user,
                        ip_address=self.get_client_ip(),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    return Response({'message': 'Category moved successfully'})
                else:
                    return Response(
                        {'error': 'Target ID is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        except EnhancedCategory.DoesNotExist:
            return Response(
                {'error': 'Target category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Perform bulk operations on categories."""
        serializer = CategoryBulkOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        category_ids = serializer.validated_data['category_ids']
        operation = serializer.validated_data['operation']
        parameters = serializer.validated_data.get('parameters', {})
        reason = serializer.validated_data.get('reason', '')
        
        # Generate batch ID for tracking
        batch_id = uuid.uuid4()
        
        try:
            with transaction.atomic():
                categories = EnhancedCategory.objects.filter(id__in=category_ids)
                results = {'success': 0, 'failed': 0, 'errors': []}
                
                for category in categories:
                    try:
                        if operation == 'activate':
                            category.status = 'active'
                            category.save()
                        elif operation == 'deactivate':
                            category.status = 'inactive'
                            category.save()
                        elif operation == 'delete':
                            category.delete()
                        elif operation == 'move':
                            target_parent_id = parameters.get('target_parent')
                            if target_parent_id:
                                target_parent = EnhancedCategory.objects.get(id=target_parent_id)
                                category.move_to(target_parent)
                        elif operation == 'update_status':
                            category.status = parameters['status']
                            category.save()
                        elif operation == 'update_visibility':
                            category.visibility = parameters['visibility']
                            category.save()
                        elif operation == 'assign_template':
                            template = CategoryTemplate.objects.get(id=parameters['template_id'])
                            category.template = template
                            category.save()
                        
                        # Log operation
                        CategoryAuditLog.objects.create(
                            category=category,
                            action='bulk_update',
                            additional_data={
                                'operation': operation,
                                'parameters': parameters,
                                'reason': reason
                            },
                            user=request.user,
                            ip_address=self.get_client_ip(),
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            batch_id=batch_id
                        )
                        
                        results['success'] += 1
                        
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append({
                            'category_id': str(category.id),
                            'error': str(e)
                        })
                
                return Response({
                    'message': f'Bulk operation completed',
                    'batch_id': str(batch_id),
                    'results': results
                })
                
        except Exception as e:
            return Response(
                {'error': f'Bulk operation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced category search with multiple filters."""
        serializer = CategorySearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = self.get_queryset()
        
        # Apply filters
        if data.get('query'):
            queryset = queryset.filter(
                Q(name__icontains=data['query']) |
                Q(description__icontains=data['query']) |
                Q(meta_title__icontains=data['query']) |
                Q(meta_keywords__icontains=data['query'])
            )
        
        if data.get('status'):
            queryset = queryset.filter(status__in=data['status'])
        
        if data.get('visibility'):
            queryset = queryset.filter(visibility__in=data['visibility'])
        
        if 'parent' in data:
            queryset = queryset.filter(parent=data['parent'])
        
        if data.get('level') is not None:
            queryset = queryset.filter(level=data['level'])
        
        if data.get('is_featured') is not None:
            queryset = queryset.filter(is_featured=data['is_featured'])
        
        if data.get('language'):
            queryset = queryset.filter(language=data['language'])
        
        if data.get('created_by'):
            queryset = queryset.filter(created_by=data['created_by'])
        
        if data.get('created_after'):
            queryset = queryset.filter(created_at__gte=data['created_after'])
        
        if data.get('created_before'):
            queryset = queryset.filter(created_at__lte=data['created_before'])
        
        if data.get('has_products') is not None:
            if data['has_products']:
                queryset = queryset.filter(product_count__gt=0)
            else:
                queryset = queryset.filter(product_count=0)
        
        if data.get('min_product_count') is not None:
            queryset = queryset.filter(product_count__gte=data['min_product_count'])
        
        if data.get('max_product_count') is not None:
            queryset = queryset.filter(product_count__lte=data['max_product_count'])
        
        if data.get('min_conversion_rate') is not None:
            queryset = queryset.filter(conversion_rate__gte=data['min_conversion_rate'])
        
        if data.get('max_conversion_rate') is not None:
            queryset = queryset.filter(conversion_rate__lte=data['max_conversion_rate'])
        
        # Apply ordering
        if data.get('ordering'):
            queryset = queryset.order_by(data['ordering'])
        
        # Paginate results
        paginator = Paginator(queryset, data.get('page_size', 20))
        page = paginator.get_page(data.get('page', 1))
        
        serializer = EnhancedCategoryListSerializer(page.object_list, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'pagination': {
                'page': page.number,
                'pages': paginator.num_pages,
                'per_page': data.get('page_size', 20),
                'total': paginator.count,
                'has_next': page.has_next(),
                'has_previous': page.has_previous()
            }
        })

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get comprehensive analytics for a category."""
        category = self.get_object()
        
        # Get date range from request
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get performance metrics
        metrics = CategoryPerformanceMetric.objects.filter(
            category=category,
            date__range=[start_date, end_date]
        ).aggregate(
            total_views=Sum('page_views'),
            unique_visitors=Sum('unique_visitors'),
            total_orders=Sum('total_orders'),
            total_revenue=Sum('total_revenue'),
            avg_bounce_rate=Avg('bounce_rate'),
            avg_conversion_rate=Avg('conversion_rate'),
            avg_order_value=Avg('avg_order_value')
        )
        
        # Get trend data
        trend_data = list(CategoryPerformanceMetric.objects.filter(
            category=category,
            date__range=[start_date, end_date]
        ).values('date', 'page_views', 'total_orders', 'total_revenue', 'conversion_rate'))
        
        # Get comparison data (previous period)
        comparison_start = start_date - timedelta(days=days)
        comparison_end = start_date - timedelta(days=1)
        
        comparison_metrics = CategoryPerformanceMetric.objects.filter(
            category=category,
            date__range=[comparison_start, comparison_end]
        ).aggregate(
            total_views=Sum('page_views'),
            unique_visitors=Sum('unique_visitors'),
            total_orders=Sum('total_orders'),
            total_revenue=Sum('total_revenue'),
            avg_conversion_rate=Avg('conversion_rate')
        )
        
        analytics_data = {
            'category_id': category.id,
            'category_name': category.name,
            'total_views': metrics['total_views'] or 0,
            'unique_visitors': metrics['unique_visitors'] or 0,
            'bounce_rate': metrics['avg_bounce_rate'] or 0,
            'conversion_rate': metrics['avg_conversion_rate'] or 0,
            'total_orders': metrics['total_orders'] or 0,
            'total_revenue': metrics['total_revenue'] or 0,
            'avg_order_value': metrics['avg_order_value'] or 0,
            'product_count': category.product_count,
            'avg_rating': 0,  # Would be calculated from product ratings
            'trend_data': trend_data,
            'comparison_data': comparison_metrics
        }
        
        serializer = CategoryAnalyticsSerializer(data=analytics_data)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export categories to CSV/Excel format."""
        format_type = request.query_params.get('format', 'csv')
        categories = self.get_queryset()
        
        # Apply filters if provided
        if request.query_params.get('status'):
            categories = categories.filter(status__in=request.query_params.getlist('status'))
        
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="categories.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Name', 'Slug', 'Description', 'Parent', 'Level', 'Status',
                'Visibility', 'Is Featured', 'Product Count', 'Conversion Rate',
                'Created At', 'Updated At'
            ])
            
            for category in categories:
                writer.writerow([
                    str(category.id),
                    category.name,
                    category.slug,
                    category.description,
                    category.parent.name if category.parent else '',
                    category.level,
                    category.status,
                    category.visibility,
                    category.is_featured,
                    category.product_count,
                    category.conversion_rate,
                    category.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    category.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            return response
        
        else:
            return Response(
                {'error': 'Unsupported format. Use csv.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_categories(self, request):
        """Import categories from CSV/Excel file."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        format_type = request.data.get('format', 'csv')
        
        # Create import record
        import_record = CategoryImportExport.objects.create(
            operation_type='import',
            format=format_type,
            source_file=file,
            created_by=request.user,
            started_at=timezone.now()
        )
        
        try:
            with transaction.atomic():
                if format_type == 'csv':
                    # Process CSV file
                    file_content = file.read().decode('utf-8')
                    csv_reader = csv.DictReader(io.StringIO(file_content))
                    
                    total_records = 0
                    successful_records = 0
                    failed_records = 0
                    errors = []
                    
                    for row in csv_reader:
                        total_records += 1
                        try:
                            # Create category from CSV row
                            category_data = {
                                'name': row.get('name', ''),
                                'description': row.get('description', ''),
                                'status': row.get('status', 'draft'),
                                'visibility': row.get('visibility', 'public'),
                                'is_featured': row.get('is_featured', '').lower() == 'true',
                                'meta_title': row.get('meta_title', ''),
                                'meta_description': row.get('meta_description', ''),
                                'meta_keywords': row.get('meta_keywords', ''),
                            }
                            
                            # Handle parent category
                            parent_name = row.get('parent', '')
                            if parent_name:
                                try:
                                    parent = EnhancedCategory.objects.get(name=parent_name)
                                    category_data['parent'] = parent.id
                                except EnhancedCategory.DoesNotExist:
                                    errors.append(f"Row {total_records}: Parent category '{parent_name}' not found")
                                    failed_records += 1
                                    continue
                            
                            serializer = EnhancedCategorySerializer(
                                data=category_data,
                                context={'request': request}
                            )
                            
                            if serializer.is_valid():
                                serializer.save()
                                successful_records += 1
                            else:
                                errors.append(f"Row {total_records}: {serializer.errors}")
                                failed_records += 1
                                
                        except Exception as e:
                            errors.append(f"Row {total_records}: {str(e)}")
                            failed_records += 1
                    
                    # Update import record
                    import_record.total_records = total_records
                    import_record.successful_records = successful_records
                    import_record.failed_records = failed_records
                    import_record.errors = errors
                    import_record.status = 'completed' if failed_records == 0 else 'failed'
                    import_record.completed_at = timezone.now()
                    import_record.save()
                    
                    return Response({
                        'message': 'Import completed',
                        'import_id': import_record.id,
                        'total_records': total_records,
                        'successful_records': successful_records,
                        'failed_records': failed_records,
                        'errors': errors[:10]  # Return first 10 errors
                    })
                
                else:
                    import_record.status = 'failed'
                    import_record.errors = ['Unsupported format']
                    import_record.completed_at = timezone.now()
                    import_record.save()
                    
                    return Response(
                        {'error': 'Unsupported format. Use csv.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
        except Exception as e:
            import_record.status = 'failed'
            import_record.errors = [str(e)]
            import_record.completed_at = timezone.now()
            import_record.save()
            
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish category with scheduling support."""
        category = self.get_object()
        scheduled_at = request.data.get('scheduled_at')
        
        if scheduled_at:
            # Schedule publication
            category.scheduled_publish_at = timezone.datetime.fromisoformat(scheduled_at)
            category.status = 'scheduled'
        else:
            # Publish immediately
            category.status = 'active'
            category.published_at = timezone.now()
        
        category.save()
        
        # Log publication
        CategoryAuditLog.objects.create(
            category=category,
            action='publish',
            additional_data={
                'scheduled_at': scheduled_at,
                'immediate': not bool(scheduled_at)
            },
            user=request.user,
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'message': 'Category published successfully' if not scheduled_at else 'Category scheduled for publication',
            'status': category.status,
            'published_at': category.published_at,
            'scheduled_publish_at': category.scheduled_publish_at
        })

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish category."""
        category = self.get_object()
        category.status = 'inactive'
        category.save()
        
        # Log unpublication
        CategoryAuditLog.objects.create(
            category=category,
            action='unpublish',
            user=request.user,
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Category unpublished successfully'})

    @action(detail=True, methods=['get'])
    def audit_log(self, request, pk=None):
        """Get audit log for a category."""
        category = self.get_object()
        logs = CategoryAuditLog.objects.filter(category=category).order_by('-created_at')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        paginator = Paginator(logs, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = CategoryAuditLogSerializer(page_obj.object_list, many=True)
        
        return Response({
            'results': serializer.data,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'per_page': page_size,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })


class CategoryAttributeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category attributes.
    """
    queryset = CategoryAttribute.objects.select_related('category')
    serializer_class = CategoryAttributeSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['category', 'attribute_type', 'is_required', 'is_filterable', 'is_active']
    ordering_fields = ['name', 'display_order', 'created_at']
    ordering = ['category', 'display_order', 'name']

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get attributes for a specific category."""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {'error': 'category_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attributes = self.get_queryset().filter(category_id=category_id, is_active=True)
        serializer = self.get_serializer(attributes, many=True)
        return Response(serializer.data)


class CategoryPerformanceMetricViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category performance metrics.
    """
    queryset = CategoryPerformanceMetric.objects.select_related('category')
    serializer_class = CategoryPerformanceMetricSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category', 'date']
    ordering_fields = ['date', 'total_revenue', 'conversion_rate', 'total_orders']
    ordering = ['-date']

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard metrics for all categories."""
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        metrics = self.get_queryset().filter(
            date__range=[start_date, end_date]
        ).values('category__name').annotate(
            total_views=Sum('page_views'),
            total_orders=Sum('total_orders'),
            total_revenue=Sum('total_revenue'),
            avg_conversion_rate=Avg('conversion_rate')
        ).order_by('-total_revenue')[:10]
        
        return Response(list(metrics))


class CategoryMerchandisingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category merchandising.
    """
    queryset = CategoryMerchandising.objects.select_related('category', 'created_by')
    serializer_class = CategoryMerchandisingSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['category', 'merchandising_type', 'is_active']
    ordering_fields = ['priority', 'start_date', 'created_at']
    ordering = ['-priority', '-created_at']

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active merchandising items."""
        now = timezone.now()
        active_items = self.get_queryset().filter(
            is_active=True,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )
        
        serializer = self.get_serializer(active_items, many=True)
        return Response(serializer.data)


class CategoryRelationshipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category relationships.
    """
    queryset = CategoryRelationship.objects.select_related('from_category', 'to_category', 'created_by')
    serializer_class = CategoryRelationshipSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['from_category', 'to_category', 'relationship_type', 'is_active']
    ordering_fields = ['weight', 'strength', 'created_at']
    ordering = ['-weight', '-created_at']

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get relationships for a specific category."""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {'error': 'category_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        relationships = self.get_queryset().filter(
            Q(from_category_id=category_id) | Q(to_category_id=category_id),
            is_active=True
        )
        
        serializer = self.get_serializer(relationships, many=True)
        return Response(serializer.data)


class CategoryImportExportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category import/export operations.
    """
    queryset = CategoryImportExport.objects.select_related('created_by')
    serializer_class = CategoryImportExportSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['operation_type', 'format', 'status', 'created_by']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'])
    def download_result(self, request, pk=None):
        """Download result file from import/export operation."""
        operation = self.get_object()
        
        if operation.result_file:
            response = HttpResponse(
                operation.result_file.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{operation.result_file.name}"'
            return response
        
        return Response(
            {'error': 'No result file available'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=['get'])
    def download_errors(self, request, pk=None):
        """Download error file from import operation."""
        operation = self.get_object()
        
        if operation.error_file:
            response = HttpResponse(
                operation.error_file.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{operation.error_file.name}"'
            return response
        
        return Response(
            {'error': 'No error file available'},
            status=status.HTTP_404_NOT_FOUND
        )


class CategoryRecommendationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category recommendations.
    """
    queryset = CategoryRecommendation.objects.select_related(
        'category', 'reviewed_by', 'implemented_by'
    )
    serializer_class = CategoryRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated, AdminPanelPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['category', 'recommendation_type', 'priority', 'status']
    ordering_fields = ['priority', 'confidence_score', 'created_at']
    ordering = ['-priority', '-confidence_score', '-created_at']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a recommendation."""
        recommendation = self.get_object()
        recommendation.status = 'approved'
        recommendation.reviewed_by = request.user
        recommendation.reviewed_at = timezone.now()
        recommendation.review_notes = request.data.get('notes', '')
        recommendation.save()
        
        return Response({'message': 'Recommendation approved successfully'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a recommendation."""
        recommendation = self.get_object()
        recommendation.status = 'rejected'
        recommendation.reviewed_by = request.user
        recommendation.reviewed_at = timezone.now()
        recommendation.review_notes = request.data.get('notes', '')
        recommendation.save()
        
        return Response({'message': 'Recommendation rejected successfully'})

    @action(detail=True, methods=['post'])
    def implement(self, request, pk=None):
        """Mark recommendation as implemented."""
        recommendation = self.get_object()
        recommendation.status = 'implemented'
        recommendation.implemented_by = request.user
        recommendation.implemented_at = timezone.now()
        recommendation.implementation_notes = request.data.get('notes', '')
        recommendation.save()
        
        return Response({'message': 'Recommendation marked as implemented'})

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending recommendations."""
        pending = self.get_queryset().filter(status='pending').order_by('-priority', '-confidence_score')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)