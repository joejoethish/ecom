"""
Advanced Customer Management System views for the admin panel.
"""
import csv
import json
import io
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, F, Case, When, Value
from django.db.models.functions import TruncMonth, TruncWeek
from django.http import HttpResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from apps.customers.models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from apps.orders.models import Order
from .customer_models import (
    CustomerSegment, CustomerSegmentMembership, CustomerLifecycleStage, CustomerLifecycleHistory,
    CustomerCommunicationHistory, CustomerSupportTicket, CustomerSupportTicketResponse,
    CustomerAnalytics, CustomerPaymentMethod, CustomerLoyaltyProgram, CustomerLoyaltyTransaction,
    CustomerRiskAssessment, CustomerGDPRCompliance, CustomerJourneyMapping,
    CustomerSatisfactionSurvey, CustomerReferralProgram, CustomerSocialMediaIntegration,
    CustomerWinBackCampaign, CustomerAccountHealthScore, CustomerPreferenceCenter,
    CustomerComplaintManagement, CustomerServiceLevelAgreement, CustomerChurnPrediction
)
from .customer_serializers import (
    CustomerProfileDetailSerializer, CustomerSegmentSerializer, CustomerSegmentMembershipSerializer,
    CustomerLifecycleStageSerializer, CustomerLifecycleHistorySerializer,
    CustomerCommunicationHistorySerializer, CustomerSupportTicketSerializer,
    CustomerSupportTicketResponseSerializer, CustomerAnalyticsSerializer,
    CustomerPaymentMethodSerializer, CustomerLoyaltyProgramSerializer,
    CustomerLoyaltyTransactionSerializer, CustomerRiskAssessmentSerializer,
    CustomerGDPRComplianceSerializer, CustomerJourneyMappingSerializer,
    CustomerSatisfactionSurveySerializer, CustomerReferralProgramSerializer,
    CustomerSocialMediaIntegrationSerializer, CustomerWinBackCampaignSerializer,
    CustomerAccountHealthScoreSerializer, CustomerPreferenceCenterSerializer,
    CustomerComplaintManagementSerializer, CustomerServiceLevelAgreementSerializer,
    CustomerChurnPredictionSerializer, AddressSerializer, WishlistSerializer, 
    CustomerActivitySerializer, CustomerImportSerializer, CustomerExportSerializer, 
    CustomerMergeSerializer, CustomerSplitSerializer, CustomerBulkActionSerializer, 
    CustomerSearchSerializer, CustomerAnalyticsReportSerializer
)
from .permissions import AdminPermissionRequired

User = get_user_model()


class CustomerPagination(PageNumberPagination):
    """Custom pagination for customer lists."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomerFilter(filters.FilterSet):
    """Advanced filtering for customers."""
    email = filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    first_name = filters.CharFilter(field_name='user__first_name', lookup_expr='icontains')
    last_name = filters.CharFilter(field_name='user__last_name', lookup_expr='icontains')
    total_spent_min = filters.NumberFilter(field_name='total_spent', lookup_expr='gte')
    total_spent_max = filters.NumberFilter(field_name='total_spent', lookup_expr='lte')
    total_orders_min = filters.NumberFilter(field_name='total_orders', lookup_expr='gte')
    total_orders_max = filters.NumberFilter(field_name='total_orders', lookup_expr='lte')
    registration_date_from = filters.DateFilter(field_name='user__date_joined', lookup_expr='gte')
    registration_date_to = filters.DateFilter(field_name='user__date_joined', lookup_expr='lte')
    last_order_date_from = filters.DateFilter(field_name='last_order_date', lookup_expr='gte')
    last_order_date_to = filters.DateFilter(field_name='last_order_date', lookup_expr='lte')
    
    class Meta:
        model = CustomerProfile
        fields = [
            'account_status', 'is_verified', 'newsletter_subscription',
            'sms_notifications', 'email_notifications'
        ]


class ComprehensiveCustomerViewSet(viewsets.ModelViewSet):
    """
    Comprehensive customer management with all advanced features.
    """
    queryset = CustomerProfile.objects.select_related('user').prefetch_related(
        'addresses', 'support_tickets', 'segment_memberships__segment'
    )
    serializer_class = CustomerProfileDetailSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    pagination_class = CustomerPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomerFilter
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone_number']
    ordering_fields = ['created_at', 'total_spent', 'total_orders', 'last_order_date']
    ordering = ['-created_at']

    def get_required_permissions(self):
        """Get required permissions based on action."""
        permission_map = {
            'create': ['customers.create'],
            'update': ['customers.edit'],
            'partial_update': ['customers.edit'],
            'destroy': ['customers.delete'],
            'export': ['customers.export'],
            'import_customers': ['customers.import'],
            'merge_customers': ['customers.manage'],
            'split_customer': ['customers.manage'],
            'bulk_action': ['customers.manage'],
        }
        return permission_map.get(self.action, ['customers.view'])

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get customer dashboard statistics."""
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        stats = {
            'total_customers': CustomerProfile.objects.count(),
            'new_customers_today': CustomerProfile.objects.filter(created_at__date=today).count(),
            'new_customers_this_month': CustomerProfile.objects.filter(
                created_at__date__gte=today.replace(day=1)
            ).count(),
            'active_customers': CustomerProfile.objects.filter(
                last_order_date__gte=last_30_days
            ).count(),
            'total_lifetime_value': CustomerProfile.objects.aggregate(
                total=Sum('total_spent')
            )['total'] or 0,
            'average_order_value': CustomerProfile.objects.filter(
                total_orders__gt=0
            ).aggregate(
                avg=Avg(F('total_spent') / F('total_orders'))
            )['avg'] or 0,
            'customer_segments': CustomerSegment.objects.filter(is_active=True).count(),
            'support_tickets_open': CustomerSupportTicket.objects.filter(
                status__in=['open', 'in_progress']
            ).count(),
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'])
    def analytics_overview(self, request):
        """Get customer analytics overview."""
        # Customer growth over time
        growth_data = CustomerProfile.objects.extra(
            select={'month': "DATE_FORMAT(created_at, '%%Y-%%m')"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Customer tier distribution
        tier_data = []
        for profile in CustomerProfile.objects.all():
            tier = profile.customer_tier
            tier_data.append(tier)
        
        tier_distribution = {}
        for tier in tier_data:
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        # Top customers by value
        top_customers = CustomerProfile.objects.order_by('-total_spent')[:10].values(
            'id', 'user__first_name', 'user__last_name', 'user__email', 'total_spent', 'total_orders'
        )
        
        return Response({
            'customer_growth': list(growth_data),
            'tier_distribution': tier_distribution,
            'top_customers': list(top_customers),
        })

    @action(detail=True, methods=['get'])
    def detailed_profile(self, request, pk=None):
        """Get detailed customer profile with all related data."""
        customer = self.get_object()
        
        # Get related data
        addresses = Address.objects.filter(customer=customer)
        orders = Order.objects.filter(customer=customer.user).order_by('-created_at')[:10]
        support_tickets = CustomerSupportTicket.objects.filter(customer=customer).order_by('-created_at')[:5]
        activities = CustomerActivity.objects.filter(customer=customer).order_by('-created_at')[:20]
        
        # Get analytics if exists
        try:
            analytics = customer.admin_analytics
            analytics_data = CustomerAnalyticsSerializer(analytics).data
        except:
            analytics_data = None
        
        # Get lifecycle stage if exists
        try:
            lifecycle = customer.lifecycle_stage
            lifecycle_data = CustomerLifecycleStageSerializer(lifecycle).data
        except:
            lifecycle_data = None
        
        # Get risk assessment if exists
        try:
            risk_assessment = customer.risk_assessment
            risk_data = CustomerRiskAssessmentSerializer(risk_assessment).data
        except:
            risk_data = None
        
        return Response({
            'customer': CustomerProfileDetailSerializer(customer).data,
            'addresses': AddressSerializer(addresses, many=True).data,
            'recent_orders': [
                {
                    'id': order.id,
                    'order_number': order.order_number,
                    'status': order.status,
                    'total_amount': order.total_amount,
                    'created_at': order.created_at,
                }
                for order in orders
            ],
            'support_tickets': CustomerSupportTicketSerializer(support_tickets, many=True).data,
            'recent_activities': CustomerActivitySerializer(activities, many=True).data,
            'analytics': analytics_data,
            'lifecycle_stage': lifecycle_data,
            'risk_assessment': risk_data,
        })

    @action(detail=False, methods=['post'])
    def advanced_search(self, request):
        """Advanced customer search with multiple criteria."""
        serializer = CustomerSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = self.get_queryset()
        
        # Apply search filters
        if data.get('query'):
            query = data['query']
            queryset = queryset.filter(
                Q(user__email__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(phone_number__icontains=query)
            )
        
        if data.get('email'):
            queryset = queryset.filter(user__email__icontains=data['email'])
        
        if data.get('phone'):
            queryset = queryset.filter(phone_number__icontains=data['phone'])
        
        if data.get('account_status'):
            queryset = queryset.filter(account_status=data['account_status'])
        
        if data.get('lifecycle_stage'):
            queryset = queryset.filter(lifecycle_stage__current_stage=data['lifecycle_stage'])
        
        if data.get('segment_ids'):
            queryset = queryset.filter(segment_memberships__segment__id__in=data['segment_ids'])
        
        # Apply range filters
        if data.get('total_spent_min'):
            queryset = queryset.filter(total_spent__gte=data['total_spent_min'])
        if data.get('total_spent_max'):
            queryset = queryset.filter(total_spent__lte=data['total_spent_max'])
        
        if data.get('total_orders_min'):
            queryset = queryset.filter(total_orders__gte=data['total_orders_min'])
        if data.get('total_orders_max'):
            queryset = queryset.filter(total_orders__lte=data['total_orders_max'])
        
        # Apply date filters
        if data.get('last_order_date_from'):
            queryset = queryset.filter(last_order_date__gte=data['last_order_date_from'])
        if data.get('last_order_date_to'):
            queryset = queryset.filter(last_order_date__lte=data['last_order_date_to'])
        
        if data.get('registration_date_from'):
            queryset = queryset.filter(user__date_joined__gte=data['registration_date_from'])
        if data.get('registration_date_to'):
            queryset = queryset.filter(user__date_joined__lte=data['registration_date_to'])
        
        # Apply other filters
        if data.get('has_support_tickets') is not None:
            if data['has_support_tickets']:
                queryset = queryset.filter(support_tickets__isnull=False).distinct()
            else:
                queryset = queryset.filter(support_tickets__isnull=True)
        
        if data.get('risk_level'):
            queryset = queryset.filter(risk_assessment__overall_risk_level=data['risk_level'])
        
        # Apply ordering
        queryset = queryset.order_by(data.get('ordering', '-created_at'))
        
        # Paginate results
        page_size = data.get('page_size', 25)
        page = data.get('page', 1)
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        results = queryset[start:end]
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': CustomerProfileDetailSerializer(results, many=True).data,
        })

    @action(detail=False, methods=['post'])
    def export(self, request):
        """Export customers to various formats."""
        serializer = CustomerExportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = self.get_queryset()
        
        # Apply date filters if provided
        if data.get('date_from'):
            queryset = queryset.filter(created_at__date__gte=data['date_from'])
        if data.get('date_to'):
            queryset = queryset.filter(created_at__date__lte=data['date_to'])
        
        # Apply segment filters if provided
        if data.get('segment_ids'):
            queryset = queryset.filter(segment_memberships__segment__id__in=data['segment_ids'])
        
        export_format = data.get('format', 'csv')
        
        if export_format == 'csv':
            return self._export_csv(queryset, data)
        elif export_format == 'excel':
            return self._export_excel(queryset, data)
        elif export_format == 'json':
            return self._export_json(queryset, data)
        else:
            return Response({'error': 'Unsupported format'}, status=status.HTTP_400_BAD_REQUEST)

    def _export_csv(self, queryset, options):
        """Export customers to CSV format."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="customers_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        headers = [
            'ID', 'Email', 'First Name', 'Last Name', 'Phone', 'Account Status',
            'Total Orders', 'Total Spent', 'Loyalty Points', 'Customer Tier',
            'Registration Date', 'Last Order Date'
        ]
        
        if options.get('include_addresses'):
            headers.extend(['Primary Address', 'City', 'State', 'Country'])
        
        writer.writerow(headers)
        
        # Write data
        for customer in queryset:
            row = [
                customer.id,
                customer.user.email,
                customer.user.first_name,
                customer.user.last_name,
                customer.phone_number,
                customer.account_status,
                customer.total_orders,
                customer.total_spent,
                customer.loyalty_points,
                customer.customer_tier,
                customer.user.date_joined.strftime('%Y-%m-%d'),
                customer.last_order_date.strftime('%Y-%m-%d') if customer.last_order_date else '',
            ]
            
            if options.get('include_addresses'):
                primary_address = customer.addresses.filter(is_default=True).first()
                if primary_address:
                    row.extend([
                        primary_address.get_full_address(),
                        primary_address.city,
                        primary_address.state,
                        primary_address.country,
                    ])
                else:
                    row.extend(['', '', '', ''])
            
            writer.writerow(row)
        
        return response

    def _export_json(self, queryset, options):
        """Export customers to JSON format."""
        customers_data = []
        
        for customer in queryset:
            customer_data = CustomerProfileDetailSerializer(customer).data
            
            if options.get('include_addresses'):
                customer_data['addresses'] = AddressSerializer(
                    customer.addresses.all(), many=True
                ).data
            
            if options.get('include_orders'):
                orders = Order.objects.filter(customer=customer.user)
                customer_data['orders'] = [
                    {
                        'order_number': order.order_number,
                        'status': order.status,
                        'total_amount': str(order.total_amount),
                        'created_at': order.created_at.isoformat(),
                    }
                    for order in orders
                ]
            
            customers_data.append(customer_data)
        
        response = HttpResponse(
            json.dumps(customers_data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="customers_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response

    @action(detail=False, methods=['post'])
    def import_customers(self, request):
        """Import customers from file."""
        serializer = CustomerImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        file_obj = data['file']
        file_format = data.get('format', 'csv')
        
        try:
            if file_format == 'csv':
                result = self._import_csv(file_obj, data)
            elif file_format == 'json':
                result = self._import_json(file_obj, data)
            else:
                return Response({'error': 'Unsupported format'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _import_csv(self, file_obj, options):
        """Import customers from CSV file."""
        file_content = file_obj.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        created_count = 0
        updated_count = 0
        errors = []
        
        with transaction.atomic():
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    email = row.get('email', '').strip()
                    if not email:
                        errors.append(f"Row {row_num}: Email is required")
                        continue
                    
                    # Check if user exists
                    user, user_created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            'username': email,
                            'first_name': row.get('first_name', '').strip(),
                            'last_name': row.get('last_name', '').strip(),
                        }
                    )
                    
                    if not user_created and not options.get('update_existing'):
                        continue
                    
                    # Create or update customer profile
                    customer, customer_created = CustomerProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'phone_number': row.get('phone', '').strip(),
                            'account_status': row.get('account_status', 'ACTIVE'),
                        }
                    )
                    
                    if customer_created:
                        created_count += 1
                    else:
                        # Update existing customer
                        customer.phone_number = row.get('phone', customer.phone_number)
                        customer.account_status = row.get('account_status', customer.account_status)
                        customer.save()
                        updated_count += 1
                
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        return {
            'created': created_count,
            'updated': updated_count,
            'errors': errors,
        }

    @action(detail=False, methods=['post'])
    def merge_customers(self, request):
        """Merge multiple customer accounts."""
        serializer = CustomerMergeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            with transaction.atomic():
                primary_customer = CustomerProfile.objects.get(id=data['primary_customer_id'])
                secondary_customers = CustomerProfile.objects.filter(
                    id__in=data['secondary_customer_ids']
                )
                
                for secondary_customer in secondary_customers:
                    # Merge orders
                    if data.get('merge_orders', True):
                        Order.objects.filter(customer=secondary_customer.user).update(
                            customer=primary_customer.user
                        )
                    
                    # Merge addresses
                    if data.get('merge_addresses', True):
                        Address.objects.filter(customer=secondary_customer).update(
                            customer=primary_customer
                        )
                    
                    # Merge loyalty points
                    if data.get('merge_loyalty_points', True):
                        primary_customer.loyalty_points += secondary_customer.loyalty_points
                    
                    # Merge communication history
                    if data.get('merge_communication_history', True):
                        CustomerCommunicationHistory.objects.filter(
                            customer=secondary_customer
                        ).update(customer=primary_customer)
                    
                    # Update totals
                    primary_customer.total_orders += secondary_customer.total_orders
                    primary_customer.total_spent += secondary_customer.total_spent
                    
                    # Delete secondary customer
                    secondary_customer.user.delete()  # This will cascade delete the profile
                
                primary_customer.save()
                
                return Response({'message': 'Customers merged successfully'})
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on customers."""
        serializer = CustomerBulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        customers = CustomerProfile.objects.filter(id__in=data['customer_ids'])
        action = data['action']
        parameters = data.get('parameters', {})
        
        try:
            with transaction.atomic():
                if action == 'update_segment':
                    segment_id = parameters.get('segment_id')
                    if segment_id:
                        segment = CustomerSegment.objects.get(id=segment_id)
                        for customer in customers:
                            CustomerSegmentMembership.objects.get_or_create(
                                customer=customer,
                                segment=segment,
                                defaults={'auto_assigned': False}
                            )
                
                elif action == 'update_lifecycle_stage':
                    new_stage = parameters.get('stage')
                    if new_stage:
                        for customer in customers:
                            lifecycle, created = CustomerLifecycleStage.objects.get_or_create(
                                customer=customer,
                                defaults={'current_stage': new_stage}
                            )
                            if not created:
                                lifecycle.update_stage(new_stage, "Bulk update")
                
                elif action == 'suspend':
                    customers.update(account_status='SUSPENDED')
                
                elif action == 'activate':
                    customers.update(account_status='ACTIVE')
                
                elif action == 'delete':
                    # Soft delete by deactivating users
                    User.objects.filter(customer_profile__in=customers).update(is_active=False)
                
                return Response({
                    'message': f'Bulk action "{action}" completed successfully',
                    'affected_customers': customers.count()
                })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomerSegmentViewSet(viewsets.ModelViewSet):
    """
    Customer segment management.
    """
    queryset = CustomerSegment.objects.all()
    serializer_class = CustomerSegmentSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-priority', 'name']

    @action(detail=True, methods=['post'])
    def calculate_membership(self, request, pk=None):
        """Calculate segment membership based on criteria."""
        segment = self.get_object()
        
        # This would contain complex logic to evaluate criteria
        # For now, we'll implement a basic structure
        
        return Response({'message': 'Membership calculation completed'})

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get segment members."""
        segment = self.get_object()
        memberships = CustomerSegmentMembership.objects.filter(
            segment=segment, is_active=True
        ).select_related('customer__user')
        
        serializer = CustomerSegmentMembershipSerializer(memberships, many=True)
        return Response(serializer.data)


class CustomerSupportTicketViewSet(viewsets.ModelViewSet):
    """
    Customer support ticket management.
    """
    queryset = CustomerSupportTicket.objects.select_related(
        'customer__user', 'assigned_to'
    ).prefetch_related('responses')
    serializer_class = CustomerSupportTicketSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def add_response(self, request, pk=None):
        """Add response to support ticket."""
        ticket = self.get_object()
        
        response_data = {
            'ticket': ticket.id,
            'message': request.data.get('message'),
            'is_internal': request.data.get('is_internal', False),
            'admin_user': request.user.id if hasattr(request.user, 'id') else None,
        }
        
        serializer = CustomerSupportTicketResponseSerializer(data=response_data)
        if serializer.is_valid():
            serializer.save()
            
            # Update ticket status if needed
            if not request.data.get('is_internal', False):
                ticket.status = 'pending_customer'
                if not ticket.first_response_at:
                    ticket.first_response_at = timezone.now()
                ticket.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign ticket to admin user."""
        ticket = self.get_object()
        admin_user_id = request.data.get('admin_user_id')
        
        if admin_user_id:
            from .models import AdminUser
            try:
                admin_user = AdminUser.objects.get(id=admin_user_id)
                ticket.assigned_to = admin_user
                ticket.save()
                
                return Response({'message': 'Ticket assigned successfully'})
            except AdminUser.DoesNotExist:
                return Response({'error': 'Admin user not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'error': 'Admin user ID is required'}, status=status.HTTP_400_BAD_REQUEST)


class CustomerAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Customer analytics and insights.
    """
    queryset = CustomerAnalytics.objects.select_related('customer__user')
    serializer_class = CustomerAnalyticsSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view', 'analytics.view']

    @action(detail=False, methods=['get'])
    def overview_report(self, request):
        """Generate customer analytics overview report."""
        # Customer distribution by tier
        tier_distribution = {}
        for profile in CustomerProfile.objects.all():
            tier = profile.customer_tier
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        # Churn risk analysis
        high_risk_customers = CustomerAnalytics.objects.filter(
            churn_probability__gte=0.7
        ).count()
        
        # Engagement metrics
        avg_engagement = CustomerAnalytics.objects.aggregate(
            avg_engagement=Avg('engagement_score')
        )['avg_engagement'] or 0
        
        # Loyalty metrics
        avg_loyalty = CustomerAnalytics.objects.aggregate(
            avg_loyalty=Avg('loyalty_score')
        )['avg_loyalty'] or 0
        
        return Response({
            'tier_distribution': tier_distribution,
            'high_risk_customers': high_risk_customers,
            'average_engagement_score': round(avg_engagement, 2),
            'average_loyalty_score': round(avg_loyalty, 2),
            'total_customers_analyzed': CustomerAnalytics.objects.count(),
        })


class CustomerLoyaltyProgramViewSet(viewsets.ModelViewSet):
    """
    Customer loyalty program management.
    """
    queryset = CustomerLoyaltyProgram.objects.select_related('customer__user')
    serializer_class = CustomerLoyaltyProgramSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']

    @action(detail=True, methods=['post'])
    def add_points(self, request, pk=None):
        """Add loyalty points to customer."""
        loyalty_program = self.get_object()
        points = request.data.get('points', 0)
        reason = request.data.get('reason', 'Manual adjustment')
        
        if points > 0:
            loyalty_program.add_points(points, reason)
            return Response({'message': f'Added {points} points successfully'})
        
        return Response({'error': 'Points must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def redeem_points(self, request, pk=None):
        """Redeem loyalty points."""
        loyalty_program = self.get_object()
        points = request.data.get('points', 0)
        reason = request.data.get('reason', 'Manual redemption')
        
        if points > 0:
            if loyalty_program.redeem_points(points, reason):
                return Response({'message': f'Redeemed {points} points successfully'})
            else:
                return Response({'error': 'Insufficient points'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'Points must be positive'}, status=status.HTTP_400_BAD_REQUEST)


class CustomerRiskAssessmentViewSet(viewsets.ModelViewSet):
    """
    Customer risk assessment management.
    """
    queryset = CustomerRiskAssessment.objects.select_related('customer__user')
    serializer_class = CustomerRiskAssessmentSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view', 'security.view']

    @action(detail=False, methods=['get'])
    def high_risk_customers(self, request):
        """Get customers with high risk scores."""
        high_risk = self.queryset.filter(
            overall_risk_level__in=['high', 'very_high']
        ).order_by('-overall_risk_score')
        
        serializer = self.get_serializer(high_risk, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def manual_review(self, request, pk=None):
        """Mark customer for manual review."""
        risk_assessment = self.get_object()
        risk_assessment.manual_review_required = True
        risk_assessment.save()
        
        return Response({'message': 'Customer marked for manual review'})


class CustomerGDPRComplianceViewSet(viewsets.ModelViewSet):
    """
    Customer GDPR compliance management.
    """
    queryset = CustomerGDPRCompliance.objects.select_related('customer__user')
    serializer_class = CustomerGDPRComplianceSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view', 'gdpr.manage']

    @action(detail=True, methods=['post'])
    def export_data(self, request, pk=None):
        """Export customer data for GDPR compliance."""
        gdpr_compliance = self.get_object()
        
        # This would generate a comprehensive data export
        gdpr_compliance.request_data_export()
        
        return Response({'message': 'Data export request processed'})

    @action(detail=True, methods=['post'])
    def delete_data(self, request, pk=None):
        """Process data deletion request."""
        gdpr_compliance = self.get_object()
        
        # This would handle the right to be forgotten
        gdpr_compliance.request_deletion()
        
        return Response({'message': 'Data deletion request processed'})


class CustomerSocialMediaIntegrationViewSet(viewsets.ModelViewSet):
    """
    Customer social media integration management.
    """
    queryset = CustomerSocialMediaIntegration.objects.select_related('customer__user')
    serializer_class = CustomerSocialMediaIntegrationSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'])
    def sync_social_data(self, request):
        """Sync social media data for all customers."""
        # This would integrate with social media APIs to update data
        return Response({'message': 'Social media data sync initiated'})


class CustomerWinBackCampaignViewSet(viewsets.ModelViewSet):
    """
    Customer win-back campaign management.
    """
    queryset = CustomerWinBackCampaign.objects.select_related('customer__user')
    serializer_class = CustomerWinBackCampaignSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def activate_campaign(self, request, pk=None):
        """Activate a win-back campaign."""
        campaign = self.get_object()
        campaign.status = 'active'
        campaign.started_at = timezone.now()
        campaign.save()
        
        return Response({'message': 'Campaign activated successfully'})

    @action(detail=False, methods=['get'])
    def campaign_performance(self, request):
        """Get win-back campaign performance metrics."""
        campaigns = self.get_queryset()
        
        stats = {
            'total_campaigns': campaigns.count(),
            'active_campaigns': campaigns.filter(status='active').count(),
            'completed_campaigns': campaigns.filter(status='completed').count(),
            'total_emails_sent': campaigns.aggregate(total=Sum('emails_sent'))['total'] or 0,
            'total_revenue_generated': campaigns.aggregate(total=Sum('revenue_generated'))['total'] or 0,
            'average_success_rate': campaigns.filter(is_successful=True).count() / max(campaigns.count(), 1) * 100,
        }
        
        return Response(stats)


class CustomerAccountHealthScoreViewSet(viewsets.ModelViewSet):
    """
    Customer account health score management.
    """
    queryset = CustomerAccountHealthScore.objects.select_related('customer__user')
    serializer_class = CustomerAccountHealthScoreSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-overall_score']

    @action(detail=False, methods=['post'])
    def recalculate_all_scores(self, request):
        """Recalculate health scores for all customers."""
        health_scores = self.get_queryset()
        
        for health_score in health_scores:
            health_score.calculate_health_score()
        
        return Response({'message': f'Recalculated {health_scores.count()} health scores'})

    @action(detail=False, methods=['get'])
    def health_distribution(self, request):
        """Get health score distribution."""
        distribution = CustomerAccountHealthScore.objects.values('health_level').annotate(
            count=Count('id')
        ).order_by('health_level')
        
        return Response(list(distribution))


class CustomerPreferenceCenterViewSet(viewsets.ModelViewSet):
    """
    Customer preference center management.
    """
    queryset = CustomerPreferenceCenter.objects.select_related('customer__user')
    serializer_class = CustomerPreferenceCenterSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-last_updated']

    @action(detail=False, methods=['get'])
    def preference_analytics(self, request):
        """Get preference analytics."""
        preferences = self.get_queryset()
        
        analytics = {
            'email_marketing_opt_in_rate': preferences.filter(email_marketing=True).count() / max(preferences.count(), 1) * 100,
            'sms_marketing_opt_in_rate': preferences.filter(sms_marketing=True).count() / max(preferences.count(), 1) * 100,
            'push_notifications_opt_in_rate': preferences.filter(push_notifications=True).count() / max(preferences.count(), 1) * 100,
            'personalization_acceptance_rate': preferences.filter(personalized_recommendations=True).count() / max(preferences.count(), 1) * 100,
            'most_preferred_frequency': preferences.values('email_frequency').annotate(count=Count('id')).order_by('-count').first(),
        }
        
        return Response(analytics)


class CustomerComplaintManagementViewSet(viewsets.ModelViewSet):
    """
    Customer complaint management.
    """
    queryset = CustomerComplaintManagement.objects.select_related('customer__user', 'assigned_to')
    serializer_class = CustomerComplaintManagementSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-received_at']

    @action(detail=True, methods=['post'])
    def resolve_complaint(self, request, pk=None):
        """Resolve a customer complaint."""
        complaint = self.get_object()
        
        complaint.status = 'resolved'
        complaint.resolved_at = timezone.now()
        complaint.resolution_description = request.data.get('resolution_description', '')
        complaint.compensation_offered = request.data.get('compensation_offered', 0)
        complaint.compensation_type = request.data.get('compensation_type', '')
        complaint.save()
        
        return Response({'message': 'Complaint resolved successfully'})

    @action(detail=False, methods=['get'])
    def complaint_analytics(self, request):
        """Get complaint analytics."""
        complaints = self.get_queryset()
        
        analytics = {
            'total_complaints': complaints.count(),
            'open_complaints': complaints.filter(status__in=['received', 'investigating']).count(),
            'resolved_complaints': complaints.filter(status='resolved').count(),
            'average_resolution_time': complaints.filter(
                resolved_at__isnull=False
            ).aggregate(
                avg_time=Avg(F('resolved_at') - F('received_at'))
            )['avg_time'],
            'complaints_by_type': list(complaints.values('complaint_type').annotate(count=Count('id'))),
            'sla_breach_rate': complaints.filter(sla_breached=True).count() / max(complaints.count(), 1) * 100,
        }
        
        return Response(analytics)


class CustomerServiceLevelAgreementViewSet(viewsets.ModelViewSet):
    """
    Customer SLA tracking management.
    """
    queryset = CustomerServiceLevelAgreement.objects.select_related('customer__user')
    serializer_class = CustomerServiceLevelAgreementSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-start_time']

    @action(detail=False, methods=['get'])
    def sla_performance(self, request):
        """Get SLA performance metrics."""
        slas = self.get_queryset()
        
        performance = {
            'total_slas': slas.count(),
            'met_slas': slas.filter(is_met=True).count(),
            'breached_slas': slas.filter(is_breached=True).count(),
            'sla_compliance_rate': slas.filter(is_met=True).count() / max(slas.count(), 1) * 100,
            'performance_by_type': list(slas.values('sla_type').annotate(
                total=Count('id'),
                met=Count(Case(When(is_met=True, then=1))),
                breached=Count(Case(When(is_breached=True, then=1)))
            )),
        }
        
        return Response(performance)


class CustomerChurnPredictionViewSet(viewsets.ModelViewSet):
    """
    Customer churn prediction management.
    """
    queryset = CustomerChurnPrediction.objects.select_related('customer__user')
    serializer_class = CustomerChurnPredictionSerializer
    permission_classes = [AdminPermissionRequired]
    required_permissions = ['customers.view']
    ordering = ['-churn_probability']

    @action(detail=False, methods=['post'])
    def run_churn_prediction(self, request):
        """Run churn prediction for all customers."""
        # This would integrate with ML models to predict churn
        customers_without_prediction = CustomerProfile.objects.filter(
            churn_prediction__isnull=True
        )
        
        predictions_created = 0
        for customer in customers_without_prediction:
            # Create basic prediction (in real implementation, this would use ML models)
            CustomerChurnPrediction.objects.create(
                customer=customer,
                churn_probability=0.5,  # Placeholder
                churn_risk_level='medium',
                model_used='logistic_regression',
                model_version='1.0',
                prediction_confidence=0.8
            )
            predictions_created += 1
        
        return Response({
            'message': f'Created {predictions_created} churn predictions',
            'total_predictions': CustomerChurnPrediction.objects.count()
        })

    @action(detail=False, methods=['get'])
    def churn_analytics(self, request):
        """Get churn prediction analytics."""
        predictions = self.get_queryset()
        
        analytics = {
            'total_predictions': predictions.count(),
            'high_risk_customers': predictions.filter(churn_risk_level__in=['high', 'very_high']).count(),
            'average_churn_probability': predictions.aggregate(avg=Avg('churn_probability'))['avg'] or 0,
            'risk_distribution': list(predictions.values('churn_risk_level').annotate(count=Count('id'))),
            'model_performance': list(predictions.values('model_used').annotate(
                count=Count('id'),
                avg_confidence=Avg('prediction_confidence')
            )),
        }
        
        return Response(analytics)