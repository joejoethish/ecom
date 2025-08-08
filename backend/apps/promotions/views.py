"""
Comprehensive Promotion and Coupon Management Views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Avg, Count, F
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
import json
from decimal import Decimal

from .models import (
    Promotion, Coupon, PromotionUsage, PromotionAnalytics,
    PromotionApproval, PromotionAuditLog, PromotionTemplate,
    PromotionSchedule, PromotionProduct, PromotionCategory,
    PromotionType, PromotionStatus, TargetType, PromotionChannel
)
from .serializers import (
    PromotionListSerializer, PromotionDetailSerializer, PromotionCreateSerializer,
    CouponSerializer, PromotionUsageSerializer, PromotionAnalyticsSerializer,
    PromotionApprovalSerializer, PromotionAuditLogSerializer,
    PromotionTemplateSerializer, PromotionScheduleSerializer,
    PromotionBulkActionSerializer, PromotionReportSerializer
)
from core.permissions import IsAdminUser
from core.pagination import CustomPageNumberPagination


class PromotionViewSet(viewsets.ModelViewSet):
    """
    Comprehensive promotion management viewset with advanced features
    """
    queryset = Promotion.objects.all()
    permission_classes = [IsAdminUser]
    pagination_class = CustomPageNumberPagination
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PromotionListSerializer
        elif self.action == 'create':
            return PromotionCreateSerializer
        elif self.action in ['bulk_action', 'bulk_actions']:
            return PromotionBulkActionSerializer
        elif self.action == 'generate_report':
            return PromotionReportSerializer
        return PromotionDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = Promotion.objects.select_related(
            'created_by', 'approved_by'
        ).prefetch_related(
            'promotion_products__product',
            'promotion_categories__category',
            'coupons',
            'analytics'
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by promotion type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(promotion_type=type_filter)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            now = timezone.now()
            if is_active.lower() == 'true':
                queryset = queryset.filter(
                    status=PromotionStatus.ACTIVE,
                    start_date__lte=now,
                    end_date__gte=now
                )
            else:
                queryset = queryset.exclude(
                    status=PromotionStatus.ACTIVE,
                    start_date__lte=now,
                    end_date__gte=now
                )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        # Filter by creator
        created_by = self.request.query_params.get('created_by')
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        
        # Search by name or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Filter by target type
        target_type = self.request.query_params.get('target_type')
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        
        # Filter by channel
        channel = self.request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(allowed_channels__contains=[channel])
        
        # Filter by priority
        min_priority = self.request.query_params.get('min_priority')
        max_priority = self.request.query_params.get('max_priority')
        if min_priority:
            queryset = queryset.filter(priority__gte=min_priority)
        if max_priority:
            queryset = queryset.filter(priority__lte=max_priority)
        
        # Filter by budget usage
        budget_usage = self.request.query_params.get('budget_usage')
        if budget_usage:
            if budget_usage == 'low':
                queryset = queryset.filter(
                    budget_limit__isnull=False,
                    budget_spent__lt=F('budget_limit') * 0.5
                )
            elif budget_usage == 'medium':
                queryset = queryset.filter(
                    budget_limit__isnull=False,
                    budget_spent__gte=F('budget_limit') * 0.5,
                    budget_spent__lt=F('budget_limit') * 0.8
                )
            elif budget_usage == 'high':
                queryset = queryset.filter(
                    budget_limit__isnull=False,
                    budget_spent__gte=F('budget_limit') * 0.8
                )
        
        # Order by
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create promotion with audit logging"""
        promotion = serializer.save()
        
        # Create audit log
        PromotionAuditLog.objects.create(
            promotion=promotion,
            user=self.request.user,
            action='created',
            changes={'promotion_created': True},
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def perform_update(self, serializer):
        """Update promotion with audit logging"""
        old_instance = self.get_object()
        old_values = {
            field.name: getattr(old_instance, field.name)
            for field in old_instance._meta.fields
        }
        
        promotion = serializer.save()
        
        # Create audit log
        new_values = {
            field.name: getattr(promotion, field.name)
            for field in promotion._meta.fields
        }
        
        changes = {}
        for field_name, old_value in old_values.items():
            new_value = new_values.get(field_name)
            if old_value != new_value:
                changes[field_name] = {
                    'old': str(old_value) if old_value is not None else None,
                    'new': str(new_value) if new_value is not None else None
                }
        
        if changes:
            PromotionAuditLog.objects.create(
                promotion=promotion,
                user=self.request.user,
                action='updated',
                changes=changes,
                old_values=old_values,
                new_values=new_values,
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a promotion"""
        promotion = self.get_object()
        
        if promotion.status == PromotionStatus.ACTIVE:
            return Response(
                {'error': 'Promotion is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if promotion requires approval
        if promotion.requires_approval and not promotion.approved_by:
            return Response(
                {'error': 'Promotion requires approval before activation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        promotion.status = PromotionStatus.ACTIVE
        promotion.save()
        
        # Create audit log
        PromotionAuditLog.objects.create(
            promotion=promotion,
            user=request.user,
            action='activated',
            changes={'status': {'old': 'inactive', 'new': 'active'}},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Promotion activated successfully'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a promotion"""
        promotion = self.get_object()
        
        if promotion.status != PromotionStatus.ACTIVE:
            return Response(
                {'error': 'Promotion is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        promotion.status = PromotionStatus.PAUSED
        promotion.save()
        
        # Create audit log
        PromotionAuditLog.objects.create(
            promotion=promotion,
            user=request.user,
            action='deactivated',
            changes={'status': {'old': 'active', 'new': 'paused'}},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Promotion deactivated successfully'})
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a promotion"""
        promotion = self.get_object()
        
        if promotion.status not in [PromotionStatus.PENDING_APPROVAL, PromotionStatus.DRAFT]:
            return Response(
                {'error': 'Promotion is not pending approval'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comments = request.data.get('comments', '')
        
        # Create or update approval record
        approval, created = PromotionApproval.objects.get_or_create(
            promotion=promotion,
            approver=request.user,
            defaults={
                'status': 'approved',
                'comments': comments
            }
        )
        
        if not created:
            approval.status = 'approved'
            approval.comments = comments
            approval.save()
        
        # Update promotion
        promotion.approved_by = request.user
        promotion.approved_at = timezone.now()
        promotion.status = PromotionStatus.APPROVED
        promotion.save()
        
        # Create audit log
        PromotionAuditLog.objects.create(
            promotion=promotion,
            user=request.user,
            action='approved',
            changes={'approved': True, 'comments': comments},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Promotion approved successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a promotion"""
        promotion = self.get_object()
        
        if promotion.status != PromotionStatus.PENDING_APPROVAL:
            return Response(
                {'error': 'Promotion is not pending approval'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comments = request.data.get('comments', '')
        
        # Create or update approval record
        approval, created = PromotionApproval.objects.get_or_create(
            promotion=promotion,
            approver=request.user,
            defaults={
                'status': 'rejected',
                'comments': comments
            }
        )
        
        if not created:
            approval.status = 'rejected'
            approval.comments = comments
            approval.save()
        
        # Update promotion
        promotion.status = PromotionStatus.DRAFT
        promotion.save()
        
        # Create audit log
        PromotionAuditLog.objects.create(
            promotion=promotion,
            user=request.user,
            action='rejected',
            changes={'rejected': True, 'comments': comments},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Promotion rejected successfully'})
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a promotion"""
        original_promotion = self.get_object()
        
        # Create duplicate
        duplicate_data = {}
        for field in original_promotion._meta.fields:
            if field.name not in ['id', 'created_at', 'updated_at', 'usage_count', 'budget_spent']:
                duplicate_data[field.name] = getattr(original_promotion, field.name)
        
        # Modify name to indicate it's a duplicate
        duplicate_data['name'] = f"{original_promotion.name} (Copy)"
        duplicate_data['status'] = PromotionStatus.DRAFT
        duplicate_data['created_by'] = request.user
        duplicate_data['approved_by'] = None
        duplicate_data['approved_at'] = None
        
        duplicate_promotion = Promotion.objects.create(**duplicate_data)
        
        # Duplicate related objects
        for product_relation in original_promotion.promotion_products.all():
            PromotionProduct.objects.create(
                promotion=duplicate_promotion,
                product=product_relation.product,
                is_included=product_relation.is_included
            )
        
        for category_relation in original_promotion.promotion_categories.all():
            PromotionCategory.objects.create(
                promotion=duplicate_promotion,
                category=category_relation.category,
                is_included=category_relation.is_included
            )
        
        # Create audit log
        PromotionAuditLog.objects.create(
            promotion=duplicate_promotion,
            user=request.user,
            action='created',
            changes={'duplicated_from': str(original_promotion.id)},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = PromotionDetailSerializer(duplicate_promotion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get promotion analytics"""
        promotion = self.get_object()
        
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        analytics = PromotionAnalytics.objects.filter(
            promotion=promotion,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        serializer = PromotionAnalyticsSerializer(analytics, many=True)
        
        # Calculate summary metrics
        summary = analytics.aggregate(
            total_uses=Sum('total_uses'),
            total_customers=Sum('unique_customers'),
            total_discount=Sum('total_discount_given'),
            total_revenue=Sum('total_revenue_generated'),
            avg_conversion_rate=Avg('conversion_rate'),
            avg_ctr=Avg('click_through_rate')
        )
        
        return Response({
            'analytics': serializer.data,
            'summary': summary,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days
            }
        })
    
    @action(detail=True, methods=['get'])
    def usage_history(self, request, pk=None):
        """Get promotion usage history"""
        promotion = self.get_object()
        
        usages = PromotionUsage.objects.filter(
            promotion=promotion
        ).select_related(
            'customer', 'order', 'coupon'
        ).order_by('-used_at')
        
        # Apply pagination
        page = self.paginate_queryset(usages)
        if page is not None:
            serializer = PromotionUsageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PromotionUsageSerializer(usages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def audit_log(self, request, pk=None):
        """Get promotion audit log"""
        promotion = self.get_object()
        
        logs = PromotionAuditLog.objects.filter(
            promotion=promotion
        ).select_related('user').order_by('-timestamp')
        
        # Apply pagination
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = PromotionAuditLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PromotionAuditLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on promotions"""
        serializer = PromotionBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        promotion_ids = serializer.validated_data['promotion_ids']
        action_type = serializer.validated_data['action']
        
        promotions = Promotion.objects.filter(id__in=promotion_ids)
        results = []
        
        with transaction.atomic():
            for promotion in promotions:
                try:
                    if action_type == 'activate':
                        if promotion.status != PromotionStatus.ACTIVE:
                            promotion.status = PromotionStatus.ACTIVE
                            promotion.save()
                            results.append({'id': promotion.id, 'status': 'activated'})
                        else:
                            results.append({'id': promotion.id, 'status': 'already_active'})
                    
                    elif action_type == 'deactivate':
                        if promotion.status == PromotionStatus.ACTIVE:
                            promotion.status = PromotionStatus.PAUSED
                            promotion.save()
                            results.append({'id': promotion.id, 'status': 'deactivated'})
                        else:
                            results.append({'id': promotion.id, 'status': 'not_active'})
                    
                    elif action_type == 'pause':
                        if promotion.status == PromotionStatus.ACTIVE:
                            promotion.status = PromotionStatus.PAUSED
                            promotion.save()
                            results.append({'id': promotion.id, 'status': 'paused'})
                        else:
                            results.append({'id': promotion.id, 'status': 'not_active'})
                    
                    elif action_type == 'delete':
                        promotion.delete()
                        results.append({'id': promotion.id, 'status': 'deleted'})
                    
                    elif action_type == 'duplicate':
                        # Create duplicate (simplified version)
                        duplicate_data = {}
                        for field in promotion._meta.fields:
                            if field.name not in ['id', 'created_at', 'updated_at', 'usage_count', 'budget_spent']:
                                duplicate_data[field.name] = getattr(promotion, field.name)
                        
                        duplicate_data['name'] = f"{promotion.name} (Copy)"
                        duplicate_data['status'] = PromotionStatus.DRAFT
                        duplicate_data['created_by'] = request.user
                        duplicate_data['approved_by'] = None
                        duplicate_data['approved_at'] = None
                        
                        duplicate = Promotion.objects.create(**duplicate_data)
                        results.append({'id': promotion.id, 'status': 'duplicated', 'duplicate_id': duplicate.id})
                    
                    # Create audit log for each action
                    PromotionAuditLog.objects.create(
                        promotion=promotion,
                        user=request.user,
                        action=action_type,
                        changes={'bulk_action': True},
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                except Exception as e:
                    results.append({'id': promotion.id, 'status': 'error', 'error': str(e)})
        
        return Response({
            'message': f'Bulk {action_type} completed',
            'results': results
        })
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate promotion report"""
        serializer = PromotionReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date_from = serializer.validated_data['date_from']
        date_to = serializer.validated_data['date_to']
        promotion_ids = serializer.validated_data.get('promotion_ids', [])
        promotion_types = serializer.validated_data.get('promotion_types', [])
        channels = serializer.validated_data.get('channels', [])
        include_analytics = serializer.validated_data.get('include_analytics', True)
        include_usage_details = serializer.validated_data.get('include_usage_details', False)
        
        # Build queryset
        queryset = Promotion.objects.all()
        
        if promotion_ids:
            queryset = queryset.filter(id__in=promotion_ids)
        
        if promotion_types:
            queryset = queryset.filter(promotion_type__in=promotion_types)
        
        # Filter by date range
        queryset = queryset.filter(
            Q(start_date__range=[date_from, date_to]) |
            Q(end_date__range=[date_from, date_to]) |
            Q(start_date__lte=date_from, end_date__gte=date_to)
        )
        
        promotions = queryset.select_related('created_by', 'approved_by')
        
        report_data = {
            'report_info': {
                'generated_at': timezone.now(),
                'date_range': {'from': date_from, 'to': date_to},
                'total_promotions': promotions.count(),
                'filters': {
                    'promotion_ids': promotion_ids,
                    'promotion_types': promotion_types,
                    'channels': channels
                }
            },
            'promotions': []
        }
        
        for promotion in promotions:
            promotion_data = PromotionListSerializer(promotion).data
            
            if include_analytics:
                # Get analytics for the date range
                analytics = PromotionAnalytics.objects.filter(
                    promotion=promotion,
                    date__range=[date_from, date_to]
                ).aggregate(
                    total_uses=Sum('total_uses'),
                    total_customers=Sum('unique_customers'),
                    total_discount=Sum('total_discount_given'),
                    total_revenue=Sum('total_revenue_generated'),
                    avg_conversion_rate=Avg('conversion_rate')
                )
                promotion_data['analytics'] = analytics
            
            if include_usage_details:
                # Get usage details for the date range
                usages = PromotionUsage.objects.filter(
                    promotion=promotion,
                    used_at__date__range=[date_from, date_to]
                ).select_related('customer', 'order')
                
                promotion_data['usage_details'] = PromotionUsageSerializer(usages, many=True).data
            
            report_data['promotions'].append(promotion_data)
        
        return Response(report_data)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export promotions to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="promotions.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'Type', 'Status', 'Discount Value', 'Start Date',
            'End Date', 'Usage Count', 'Usage Limit', 'Budget Spent',
            'Budget Limit', 'Conversion Rate', 'ROI', 'Created By', 'Created At'
        ])
        
        for promotion in queryset:
            writer.writerow([
                str(promotion.id),
                promotion.name,
                promotion.get_promotion_type_display(),
                promotion.get_status_display(),
                promotion.discount_value,
                promotion.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                promotion.end_date.strftime('%Y-%m-%d %H:%M:%S'),
                promotion.usage_count,
                promotion.usage_limit_total or '',
                promotion.budget_spent,
                promotion.budget_limit or '',
                promotion.conversion_rate,
                promotion.roi,
                promotion.created_by.get_full_name(),
                promotion.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for promotions"""
        now = timezone.now()
        
        # Basic counts
        total_promotions = Promotion.objects.count()
        active_promotions = Promotion.objects.filter(
            status=PromotionStatus.ACTIVE,
            start_date__lte=now,
            end_date__gte=now
        ).count()
        
        pending_approval = Promotion.objects.filter(
            status=PromotionStatus.PENDING_APPROVAL
        ).count()
        
        expiring_soon = Promotion.objects.filter(
            status=PromotionStatus.ACTIVE,
            end_date__range=[now, now + timedelta(days=7)]
        ).count()
        
        # Performance metrics
        this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        
        this_month_analytics = PromotionAnalytics.objects.filter(
            date__gte=this_month.date()
        ).aggregate(
            total_uses=Sum('total_uses'),
            total_discount=Sum('total_discount_given'),
            total_revenue=Sum('total_revenue_generated'),
            avg_conversion_rate=Avg('conversion_rate')
        )
        
        last_month_analytics = PromotionAnalytics.objects.filter(
            date__gte=last_month.date(),
            date__lt=this_month.date()
        ).aggregate(
            total_uses=Sum('total_uses'),
            total_discount=Sum('total_discount_given'),
            total_revenue=Sum('total_revenue_generated'),
            avg_conversion_rate=Avg('conversion_rate')
        )
        
        # Top performing promotions
        top_promotions = Promotion.objects.filter(
            status=PromotionStatus.ACTIVE
        ).order_by('-conversion_rate', '-roi')[:5]
        
        return Response({
            'counts': {
                'total_promotions': total_promotions,
                'active_promotions': active_promotions,
                'pending_approval': pending_approval,
                'expiring_soon': expiring_soon
            },
            'performance': {
                'this_month': this_month_analytics,
                'last_month': last_month_analytics
            },
            'top_promotions': PromotionListSerializer(top_promotions, many=True).data
        })


class CouponViewSet(viewsets.ModelViewSet):
    """Coupon management viewset"""
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPageNumberPagination
    
    def get_queryset(self):
        """Filter coupons based on query parameters"""
        queryset = Coupon.objects.select_related('promotion')
        
        # Filter by promotion
        promotion_id = self.request.query_params.get('promotion')
        if promotion_id:
            queryset = queryset.filter(promotion_id=promotion_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search by code
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(code__icontains=search)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def validate_coupon(self, request, pk=None):
        """Validate if a coupon can be used"""
        coupon = self.get_object()
        customer_id = request.data.get('customer_id')
        order_amount = Decimal(str(request.data.get('order_amount', 0)))
        
        # Basic validation
        if not coupon.can_be_used():
            return Response({
                'valid': False,
                'error': 'Coupon is not valid or has expired'
            })
        
        # Check promotion validity
        if not coupon.promotion.is_active:
            return Response({
                'valid': False,
                'error': 'Associated promotion is not active'
            })
        
        # Check minimum order amount
        if coupon.promotion.minimum_order_amount and order_amount < coupon.promotion.minimum_order_amount:
            return Response({
                'valid': False,
                'error': f'Minimum order amount is {coupon.promotion.minimum_order_amount}'
            })
        
        # Check customer eligibility if customer_id provided
        if customer_id:
            from apps.customers.models import Customer
            try:
                customer = Customer.objects.get(id=customer_id)
                if not coupon.promotion.can_be_used_by_customer(customer):
                    return Response({
                        'valid': False,
                        'error': 'Customer is not eligible for this promotion'
                    })
            except Customer.DoesNotExist:
                return Response({
                    'valid': False,
                    'error': 'Invalid customer'
                })
        
        return Response({
            'valid': True,
            'promotion': PromotionListSerializer(coupon.promotion).data
        })


class PromotionTemplateViewSet(viewsets.ModelViewSet):
    """Promotion template management viewset"""
    queryset = PromotionTemplate.objects.all()
    serializer_class = PromotionTemplateSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter templates based on query parameters"""
        queryset = PromotionTemplate.objects.filter(is_active=True)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('-usage_count', 'name')
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Create a promotion from a template"""
        template = self.get_object()
        
        # Increment usage count
        template.usage_count += 1
        template.save()
        
        # Create promotion from template
        template_data = template.template_data.copy()
        template_data['name'] = request.data.get('name', f"Promotion from {template.name}")
        template_data['created_by'] = request.user
        
        serializer = PromotionCreateSerializer(data=template_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        promotion = serializer.save()
        
        return Response(
            PromotionDetailSerializer(promotion).data,
            status=status.HTTP_201_CREATED
        )