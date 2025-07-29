"""
Customer views for the ecommerce platform.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import logging

from .models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from .serializers import (
    CustomerProfileSerializer, CustomerProfileCreateSerializer,
    AddressSerializer, AddressCreateSerializer,
    WishlistSerializer, WishlistItemSerializer,
    CustomerActivitySerializer, CustomerAnalyticsSerializer,
    CustomerListSerializer, CustomerDetailSerializer, CustomerSearchSerializer
)
from .services import CustomerService, AddressService, WishlistService, CustomerAnalyticsService
from apps.products.models import Product
from core.permissions import IsOwnerOrAdmin
from core.pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)


class CustomerProfileView(APIView):
    """
    View for customer profile management.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get customer profile."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            serializer = CustomerProfileSerializer(customer_profile)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error getting customer profile: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving customer profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        """Update customer profile."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            serializer = CustomerProfileSerializer(customer_profile, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_profile = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'data': CustomerProfileSerializer(updated_profile).data
                })
            
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error updating customer profile: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating customer profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Create customer profile."""
        try:
            # Check if profile already exists
            if hasattr(request.user, 'customer_profile'):
                return Response({
                    'success': False,
                    'message': 'Customer profile already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = CustomerProfileCreateSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                customer_profile = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Customer profile created successfully',
                    'data': CustomerProfileSerializer(customer_profile).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating customer profile: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating customer profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddressListView(APIView):
    """
    View for customer addresses.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get customer addresses."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            addresses = customer_profile.addresses.all().order_by('-is_default', '-created_at')
            serializer = AddressSerializer(addresses, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting customer addresses: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving addresses'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Create new address."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            serializer = AddressCreateSerializer(
                data=request.data, 
                context={'customer_profile': customer_profile}
            )
            
            if serializer.is_valid():
                address = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Address created successfully',
                    'data': AddressSerializer(address).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating address: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating address'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddressDetailView(APIView):
    """
    View for individual address management.
    """
    permission_classes = [IsAuthenticated]

    def get_address(self, request, address_id):
        """Get address ensuring it belongs to the customer."""
        customer_profile = CustomerService.get_or_create_customer_profile(request.user)
        return get_object_or_404(Address, id=address_id, customer=customer_profile)

    def get(self, request, address_id):
        """Get specific address."""
        try:
            address = self.get_address(request, address_id)
            serializer = AddressSerializer(address)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting address: {str(e)}")
            return Response({
                'success': False,
                'message': 'Address not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, address_id):
        """Update address."""
        try:
            address = self.get_address(request, address_id)
            serializer = AddressSerializer(address, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_address = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Address updated successfully',
                    'data': AddressSerializer(updated_address).data
                })
            
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error updating address: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating address'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, address_id):
        """Delete address."""
        try:
            address = self.get_address(request, address_id)
            AddressService.delete_address(address)
            
            return Response({
                'success': True,
                'message': 'Address deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting address: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error deleting address'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SetDefaultAddressView(APIView):
    """
    View for setting default addresses.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, address_id):
        """Set address as default."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            address = get_object_or_404(Address, id=address_id, customer=customer_profile)
            
            address_type = request.data.get('type', 'all')  # 'all', 'billing', 'shipping', 'general'
            
            updated_address = AddressService.set_default_address(address, address_type)
            
            return Response({
                'success': True,
                'message': f'Default {address_type} address set successfully',
                'data': AddressSerializer(updated_address).data
            })
            
        except Exception as e:
            logger.error(f"Error setting default address: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error setting default address'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WishlistView(APIView):
    """
    View for customer wishlist management.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get customer wishlist."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            wishlist = WishlistService.get_or_create_wishlist(customer_profile)
            serializer = WishlistSerializer(wishlist)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting wishlist: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving wishlist'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Add item to wishlist."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            serializer = WishlistItemSerializer(
                data=request.data,
                context={'customer_profile': customer_profile}
            )
            
            if serializer.is_valid():
                wishlist_item = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Item added to wishlist successfully',
                    'data': WishlistItemSerializer(wishlist_item).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error adding to wishlist: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error adding item to wishlist'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """Clear wishlist."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            WishlistService.clear_wishlist(customer_profile)
            
            return Response({
                'success': True,
                'message': 'Wishlist cleared successfully'
            })
            
        except Exception as e:
            logger.error(f"Error clearing wishlist: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error clearing wishlist'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WishlistItemView(APIView):
    """
    View for individual wishlist item management.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        """Remove item from wishlist."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            product = get_object_or_404(Product, id=product_id)
            
            success = WishlistService.remove_from_wishlist(customer_profile, product)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Item removed from wishlist successfully'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Item not found in wishlist'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error removing from wishlist: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error removing item from wishlist'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckWishlistView(APIView):
    """
    View to check if product is in wishlist.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        """Check if product is in wishlist."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            product = get_object_or_404(Product, id=product_id)
            
            is_in_wishlist = WishlistService.is_in_wishlist(customer_profile, product)
            
            return Response({
                'success': True,
                'data': {
                    'is_in_wishlist': is_in_wishlist,
                    'product_id': product_id
                }
            })
            
        except Exception as e:
            logger.error(f"Error checking wishlist: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error checking wishlist'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerActivityView(APIView):
    """
    View for customer activity tracking.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get customer activities."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            activity_type = request.query_params.get('type')
            limit = int(request.query_params.get('limit', 50))
            
            activities = CustomerActivityService.get_customer_activities(
                customer_profile, activity_type, limit
            )
            
            serializer = CustomerActivitySerializer(activities, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting customer activities: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving activities'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerAnalyticsView(APIView):
    """
    View for customer analytics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get customer analytics."""
        try:
            customer_profile = CustomerService.get_or_create_customer_profile(request.user)
            analytics = CustomerActivityService.get_customer_analytics(customer_profile)
            
            serializer = CustomerAnalyticsSerializer(analytics)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting customer analytics: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving analytics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin Views

class AdminCustomerListView(generics.ListAPIView):
    """
    Admin view for listing customers with search and filtering.
    """
    queryset = CustomerProfile.objects.all()
    serializer_class = CustomerListSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'phone_number']
    filterset_fields = ['account_status', 'is_verified', 'gender']
    ordering_fields = ['created_at', 'last_login_date', 'total_orders', 'total_spent']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on search parameters."""
        queryset = super().get_queryset()
        
        # Custom filtering
        search_params = self.request.query_params
        
        # Customer tier filtering
        customer_tier = search_params.get('customer_tier')
        if customer_tier:
            if customer_tier == 'PLATINUM':
                queryset = queryset.filter(total_spent__gte=100000)
            elif customer_tier == 'GOLD':
                queryset = queryset.filter(total_spent__gte=50000, total_spent__lt=100000)
            elif customer_tier == 'SILVER':
                queryset = queryset.filter(total_spent__gte=10000, total_spent__lt=50000)
            elif customer_tier == 'BRONZE':
                queryset = queryset.filter(total_spent__lt=10000)
        
        # Order count filtering
        min_orders = search_params.get('min_orders')
        if min_orders:
            queryset = queryset.filter(total_orders__gte=int(min_orders))
        
        max_orders = search_params.get('max_orders')
        if max_orders:
            queryset = queryset.filter(total_orders__lte=int(max_orders))
        
        # Spent amount filtering
        min_spent = search_params.get('min_spent')
        if min_spent:
            queryset = queryset.filter(total_spent__gte=float(min_spent))
        
        max_spent = search_params.get('max_spent')
        if max_spent:
            queryset = queryset.filter(total_spent__lte=float(max_spent))
        
        # Date filtering
        date_joined_from = search_params.get('date_joined_from')
        if date_joined_from:
            queryset = queryset.filter(created_at__date__gte=date_joined_from)
        
        date_joined_to = search_params.get('date_joined_to')
        if date_joined_to:
            queryset = queryset.filter(created_at__date__lte=date_joined_to)
        
        last_login_from = search_params.get('last_login_from')
        if last_login_from:
            queryset = queryset.filter(last_login_date__date__gte=last_login_from)
        
        last_login_to = search_params.get('last_login_to')
        if last_login_to:
            queryset = queryset.filter(last_login_date__date__lte=last_login_to)
        
        return queryset.select_related('user').prefetch_related('addresses', 'wishlist')


class AdminCustomerDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin view for customer details and management.
    """
    queryset = CustomerProfile.objects.all()
    serializer_class = CustomerDetailSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        """Get customer profile with related data."""
        return get_object_or_404(
            CustomerProfile.objects.select_related('user')
            .prefetch_related('addresses', 'wishlist__items__product', 'activities'),
            pk=self.kwargs['pk']
        )


class AdminCustomerStatusView(APIView):
    """
    Admin view for managing customer account status.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, customer_id):
        """Update customer account status."""
        try:
            customer_profile = get_object_or_404(CustomerProfile, id=customer_id)
            action = request.data.get('action')  # 'suspend', 'activate', 'block'
            reason = request.data.get('reason', '')
            
            if action == 'suspend':
                CustomerService.deactivate_customer(customer_profile, reason)
                message = 'Customer account suspended successfully'
            elif action == 'activate':
                CustomerService.reactivate_customer(customer_profile)
                message = 'Customer account activated successfully'
            elif action == 'block':
                customer_profile.account_status = 'BLOCKED'
                customer_profile.save()
                message = 'Customer account blocked successfully'
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid action'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': message,
                'data': CustomerDetailSerializer(customer_profile).data
            })
            
        except Exception as e:
            logger.error(f"Error updating customer status: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating customer status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_customer_activity(request):
    """
    Endpoint for logging customer activities.
    """
    try:
        customer_profile = CustomerService.get_or_create_customer_profile(request.user)
        
        activity_type = request.data.get('activity_type')
        description = request.data.get('description', '')
        product_id = request.data.get('product_id')
        order_id = request.data.get('order_id')
        metadata = request.data.get('metadata', {})
        
        # Get related objects
        product = None
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                pass
        
        order = None
        if order_id:
            try:
                from apps.orders.models import Order
                order = Order.objects.get(id=order_id)
            except:
                pass
        
        # Get request metadata
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        session_key = request.session.session_key
        
        activity = CustomerActivityService.log_activity(
            customer_profile=customer_profile,
            activity_type=activity_type,
            description=description,
            product=product,
            order=order,
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key,
            metadata=metadata
        )
        
        if activity:
            return Response({
                'success': True,
                'message': 'Activity logged successfully',
                'data': CustomerActivitySerializer(activity).data
            })
        else:
            return Response({
                'success': False,
                'message': 'Failed to log activity'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error logging customer activity: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error logging activity'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)