"""
<<<<<<< HEAD
Customer management services for the ecommerce platform.
"""
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
=======
Customer service layer for business logic.
"""
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any, List
import logging
>>>>>>> Task-10.3

from .models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from apps.products.models import Product

User = get_user_model()
<<<<<<< HEAD
=======
logger = logging.getLogger(__name__)
>>>>>>> Task-10.3


class CustomerService:
    """
<<<<<<< HEAD
    Service class for customer management operations.
    """
    
    @staticmethod
    def create_customer_profile(user, profile_data: Dict) -> CustomerProfile:
        """
        Create a customer profile for a user.
        
        Args:
            user: User instance
            profile_data: Dictionary containing profile information
            
        Returns:
            CustomerProfile instance
=======
    Service class for customer-related business logic.
    """
    
    @staticmethod
    def create_customer_profile(user, **profile_data) -> CustomerProfile:
        """
        Create a customer profile for a user.
>>>>>>> Task-10.3
        """
        try:
            with transaction.atomic():
                # Check if profile already exists
                if hasattr(user, 'customer_profile'):
<<<<<<< HEAD
                    raise ValidationError("Customer profile already exists for this user.")
=======
                    return user.customer_profile
>>>>>>> Task-10.3
                
                # Create customer profile
                profile = CustomerProfile.objects.create(
                    user=user,
                    **profile_data
                )
                
                # Create default wishlist
                Wishlist.objects.create(
                    customer=profile,
<<<<<<< HEAD
                    name="My Wishlist"
                )
                
                # Log activity
                CustomerService.log_activity(
                    profile, 
                    'LOGIN', 
                    'Customer profile created'
                )
                
                return profile
                
        except Exception as e:
            raise ValidationError(f"Failed to create customer profile: {str(e)}")
    
    @staticmethod
    def update_customer_profile(customer_profile: CustomerProfile, profile_data: Dict) -> CustomerProfile:
        """
        Update customer profile information.
        
        Args:
            customer_profile: CustomerProfile instance
            profile_data: Dictionary containing updated profile information
            
        Returns:
            Updated CustomerProfile instance
        """
        try:
            with transaction.atomic():
                for field, value in profile_data.items():
                    if hasattr(customer_profile, field):
                        setattr(customer_profile, field, value)
                
                customer_profile.save()
                
                # Log activity
                CustomerService.log_activity(
                    customer_profile, 
                    'LOGIN', 
                    'Profile updated'
                )
                
                return customer_profile
                
        except Exception as e:
            raise ValidationError(f"Failed to update customer profile: {str(e)}")
    
    @staticmethod
    def get_customer_analytics(customer_profile: CustomerProfile) -> Dict:
        """
        Get comprehensive analytics for a customer.
        
        Args:
            customer_profile: CustomerProfile instance
            
        Returns:
            Dictionary containing customer analytics
        """
        try:
            # Basic metrics
            analytics = {
                'total_orders': customer_profile.total_orders,
                'total_spent': float(customer_profile.total_spent),
                'loyalty_points': customer_profile.loyalty_points,
                'customer_tier': customer_profile.customer_tier,
                'account_age_days': (timezone.now() - customer_profile.created_at).days,
            }
            
            # Address analytics
            addresses = customer_profile.addresses.all()
            analytics['total_addresses'] = addresses.count()
            analytics['most_used_address'] = None
            if addresses.exists():
                most_used = addresses.order_by('-usage_count').first()
                analytics['most_used_address'] = {
                    'id': str(most_used.id),
                    'city': most_used.city,
                    'usage_count': most_used.usage_count
                }
            
            # Wishlist analytics
            wishlist = getattr(customer_profile, 'wishlist', None)
            analytics['wishlist_items'] = wishlist.item_count if wishlist else 0
            
            # Activity analytics
            activities = customer_profile.activities.all()
            analytics['total_activities'] = activities.count()
            analytics['last_activity'] = None
            if activities.exists():
                last_activity = activities.first()
                analytics['last_activity'] = {
                    'type': last_activity.activity_type,
                    'date': last_activity.created_at.isoformat()
                }
            
            # Activity breakdown
            activity_breakdown = activities.values('activity_type').annotate(
                count=Count('id')
            ).order_by('-count')
            analytics['activity_breakdown'] = list(activity_breakdown)
            
            return analytics
            
        except Exception as e:
            raise ValidationError(f"Failed to get customer analytics: {str(e)}")
    
    @staticmethod
    def log_activity(customer_profile: CustomerProfile, activity_type: str, 
                    description: str = "", **kwargs) -> CustomerActivity:
        """
        Log customer activity.
        
        Args:
            customer_profile: CustomerProfile instance
            activity_type: Type of activity
            description: Activity description
            **kwargs: Additional activity data
            
        Returns:
            CustomerActivity instance
        """
        try:
            activity_data = {
                'customer': customer_profile,
                'activity_type': activity_type,
                'description': description,
            }
            
            # Add optional fields
            for field in ['product', 'order', 'ip_address', 'user_agent', 'session_key', 'metadata']:
                if field in kwargs:
                    activity_data[field] = kwargs[field]
            
            activity = CustomerActivity.objects.create(**activity_data)
            return activity
            
        except Exception as e:
            raise ValidationError(f"Failed to log customer activity: {str(e)}")
=======
                    name='My Wishlist'
                )
                
                logger.info(f"Customer profile created for user {user.email}")
                return profile
                
        except Exception as e:
            logger.error(f"Error creating customer profile for user {user.email}: {str(e)}")
            raise
    
    @staticmethod
    def update_customer_profile(customer_profile: CustomerProfile, **update_data) -> CustomerProfile:
        """
        Update customer profile information.
        """
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(customer_profile, field):
                        setattr(customer_profile, field, value)
                
                customer_profile.full_clean()
                customer_profile.save()
                
                logger.info(f"Customer profile updated for {customer_profile.get_full_name()}")
                return customer_profile
                
        except ValidationError as e:
            logger.error(f"Validation error updating customer profile: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating customer profile: {str(e)}")
            raise
    
    @staticmethod
    def get_or_create_customer_profile(user) -> CustomerProfile:
        """
        Get existing customer profile or create a new one.
        """
        try:
            return user.customer_profile
        except CustomerProfile.DoesNotExist:
            return CustomerService.create_customer_profile(user)
    
    @staticmethod
    def update_customer_login(customer_profile: CustomerProfile, ip_address: str = None, user_agent: str = None):
        """
        Update customer login information and log activity.
        """
        try:
            with transaction.atomic():
                customer_profile.last_login_date = timezone.now()
                customer_profile.save(update_fields=['last_login_date'])
                
                # Log login activity
                CustomerActivity.objects.create(
                    customer=customer_profile,
                    activity_type='LOGIN',
                    description='User logged in',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
        except Exception as e:
            logger.error(f"Error updating customer login: {str(e)}")
    
    @staticmethod
    def deactivate_customer(customer_profile: CustomerProfile, reason: str = None) -> CustomerProfile:
        """
        Deactivate a customer account.
        """
        try:
            with transaction.atomic():
                customer_profile.account_status = 'SUSPENDED'
                customer_profile.save(update_fields=['account_status'])
                
                # Log activity
                CustomerActivity.objects.create(
                    customer=customer_profile,
                    activity_type='SUPPORT_TICKET',
                    description=f'Account suspended. Reason: {reason or "Not specified"}',
                    metadata={'reason': reason, 'action': 'suspend'}
                )
                
                logger.info(f"Customer account suspended: {customer_profile.get_full_name()}")
                return customer_profile
                
        except Exception as e:
            logger.error(f"Error deactivating customer: {str(e)}")
            raise
    
    @staticmethod
    def reactivate_customer(customer_profile: CustomerProfile) -> CustomerProfile:
        """
        Reactivate a customer account.
        """
        try:
            with transaction.atomic():
                customer_profile.account_status = 'ACTIVE'
                customer_profile.save(update_fields=['account_status'])
                
                # Log activity
                CustomerActivity.objects.create(
                    customer=customer_profile,
                    activity_type='SUPPORT_TICKET',
                    description='Account reactivated',
                    metadata={'action': 'reactivate'}
                )
                
                logger.info(f"Customer account reactivated: {customer_profile.get_full_name()}")
                return customer_profile
                
        except Exception as e:
            logger.error(f"Error reactivating customer: {str(e)}")
            raise
>>>>>>> Task-10.3


class AddressService:
    """
<<<<<<< HEAD
    Service class for address management operations.
    """
    
    @staticmethod
    def create_address(customer_profile: CustomerProfile, address_data: Dict) -> Address:
        """
        Create a new address for a customer.
        
        Args:
            customer_profile: CustomerProfile instance
            address_data: Dictionary containing address information
            
        Returns:
            Address instance
=======
    Service class for address-related business logic.
    """
    
    @staticmethod
    def create_address(customer_profile: CustomerProfile, address_data: Dict[str, Any]) -> Address:
        """
        Create a new address for a customer.
>>>>>>> Task-10.3
        """
        try:
            with transaction.atomic():
                address = Address.objects.create(
                    customer=customer_profile,
                    **address_data
                )
                
                # If this is the first address, make it default
                if customer_profile.addresses.count() == 1:
                    address.is_default = True
                    address.is_billing_default = True
                    address.is_shipping_default = True
                    address.save()
                
<<<<<<< HEAD
                # Log activity
                CustomerService.log_activity(
                    customer_profile, 
                    'LOGIN', 
                    f'New address added: {address.city}'
                )
                
                return address
                
        except Exception as e:
            raise ValidationError(f"Failed to create address: {str(e)}")
    
    @staticmethod
    def update_address(address: Address, address_data: Dict) -> Address:
        """
        Update an existing address.
        
        Args:
            address: Address instance
            address_data: Dictionary containing updated address information
            
        Returns:
            Updated Address instance
        """
        try:
            with transaction.atomic():
                for field, value in address_data.items():
                    if hasattr(address, field):
                        setattr(address, field, value)
                
                address.save()
                
                # Log activity
                CustomerService.log_activity(
                    address.customer, 
                    'LOGIN', 
                    f'Address updated: {address.city}'
                )
                
                return address
                
        except Exception as e:
            raise ValidationError(f"Failed to update address: {str(e)}")
=======
                logger.info(f"Address created for customer {customer_profile.get_full_name()}")
                return address
                
        except ValidationError as e:
            logger.error(f"Validation error creating address: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating address: {str(e)}")
            raise
    
    @staticmethod
    def update_address(address: Address, update_data: Dict[str, Any]) -> Address:
        """
        Update an existing address.
        """
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(address, field):
                        setattr(address, field, value)
                
                address.full_clean()
                address.save()
                
                logger.info(f"Address updated for customer {address.customer.get_full_name()}")
                return address
                
        except ValidationError as e:
            logger.error(f"Validation error updating address: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating address: {str(e)}")
            raise
>>>>>>> Task-10.3
    
    @staticmethod
    def delete_address(address: Address) -> bool:
        """
<<<<<<< HEAD
        Delete an address (soft delete).
        
        Args:
            address: Address instance
            
        Returns:
            Boolean indicating success
=======
        Delete an address and handle default address reassignment.
>>>>>>> Task-10.3
        """
        try:
            with transaction.atomic():
                customer = address.customer
<<<<<<< HEAD
                
                # If this was a default address, set another as default
                if address.is_default:
                    other_address = customer.addresses.exclude(id=address.id).first()
                    if other_address:
                        other_address.is_default = True
                        other_address.save()
                
                if address.is_billing_default:
                    other_address = customer.addresses.exclude(id=address.id).first()
                    if other_address:
                        other_address.is_billing_default = True
                        other_address.save()
                
                if address.is_shipping_default:
                    other_address = customer.addresses.exclude(id=address.id).first()
                    if other_address:
                        other_address.is_shipping_default = True
                        other_address.save()
                
                # Soft delete
                address.delete()
                
                # Log activity
                CustomerService.log_activity(
                    customer, 
                    'LOGIN', 
                    f'Address deleted: {address.city}'
                )
                
                return True
                
        except Exception as e:
            raise ValidationError(f"Failed to delete address: {str(e)}")
=======
                was_default = address.is_default
                was_billing_default = address.is_billing_default
                was_shipping_default = address.is_shipping_default
                
                address.delete()
                
                # If deleted address was default, assign new defaults
                if was_default or was_billing_default or was_shipping_default:
                    remaining_addresses = customer.addresses.all()
                    if remaining_addresses.exists():
                        new_default = remaining_addresses.first()
                        
                        if was_default and not customer.addresses.filter(is_default=True).exists():
                            new_default.is_default = True
                        
                        if was_billing_default and not customer.addresses.filter(is_billing_default=True).exists():
                            new_default.is_billing_default = True
                        
                        if was_shipping_default and not customer.addresses.filter(is_shipping_default=True).exists():
                            new_default.is_shipping_default = True
                        
                        new_default.save()
                
                logger.info(f"Address deleted for customer {customer.get_full_name()}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting address: {str(e)}")
            raise
>>>>>>> Task-10.3
    
    @staticmethod
    def set_default_address(address: Address, address_type: str = 'all') -> Address:
        """
<<<<<<< HEAD
        Set an address as default.
        
        Args:
            address: Address instance
            address_type: Type of default ('all', 'billing', 'shipping')
            
        Returns:
            Updated Address instance
        """
        try:
            with transaction.atomic():
                if address_type in ['all', 'billing']:
                    # Unset other billing defaults
                    Address.objects.filter(
                        customer=address.customer,
                        is_billing_default=True
                    ).exclude(id=address.id).update(is_billing_default=False)
                    address.is_billing_default = True
                
                if address_type in ['all', 'shipping']:
                    # Unset other shipping defaults
                    Address.objects.filter(
                        customer=address.customer,
                        is_shipping_default=True
                    ).exclude(id=address.id).update(is_shipping_default=False)
                    address.is_shipping_default = True
                
                if address_type == 'all':
                    # Unset other general defaults
                    Address.objects.filter(
                        customer=address.customer,
                        is_default=True
                    ).exclude(id=address.id).update(is_default=False)
                    address.is_default = True
                
                address.save()
                
                # Log activity
                CustomerService.log_activity(
                    address.customer, 
                    'LOGIN', 
                    f'Default address set: {address.city}'
                )
                
                return address
                
        except Exception as e:
            raise ValidationError(f"Failed to set default address: {str(e)}")
=======
        Set an address as default for specified type(s).
        
        Args:
            address: Address to set as default
            address_type: 'all', 'billing', 'shipping', or 'general'
        """
        try:
            with transaction.atomic():
                if address_type in ['all', 'general']:
                    address.is_default = True
                
                if address_type in ['all', 'billing']:
                    address.is_billing_default = True
                
                if address_type in ['all', 'shipping']:
                    address.is_shipping_default = True
                
                address.save()
                
                logger.info(f"Default address set for customer {address.customer.get_full_name()}")
                return address
                
        except Exception as e:
            logger.error(f"Error setting default address: {str(e)}")
            raise
>>>>>>> Task-10.3


class WishlistService:
    """
<<<<<<< HEAD
    Service class for wishlist management operations.
    """
    
    @staticmethod
    def add_to_wishlist(customer_profile: CustomerProfile, product: Product, 
                       notes: str = "") -> WishlistItem:
        """
        Add a product to customer's wishlist.
        
        Args:
            customer_profile: CustomerProfile instance
            product: Product instance
            notes: Optional notes about the item
            
        Returns:
            WishlistItem instance
        """
        try:
            with transaction.atomic():
                # Get or create wishlist
                wishlist, created = Wishlist.objects.get_or_create(
                    customer=customer_profile,
                    defaults={'name': 'My Wishlist'}
                )
=======
    Service class for wishlist-related business logic.
    """
    
    @staticmethod
    def get_or_create_wishlist(customer_profile: CustomerProfile) -> Wishlist:
        """
        Get customer's wishlist or create if it doesn't exist.
        """
        try:
            return customer_profile.wishlist
        except Wishlist.DoesNotExist:
            return Wishlist.objects.create(
                customer=customer_profile,
                name='My Wishlist'
            )
    
    @staticmethod
    def add_to_wishlist(customer_profile: CustomerProfile, product: Product, notes: str = '') -> WishlistItem:
        """
        Add a product to customer's wishlist.
        """
        try:
            with transaction.atomic():
                wishlist = WishlistService.get_or_create_wishlist(customer_profile)
>>>>>>> Task-10.3
                
                # Check if item already exists
                wishlist_item, created = WishlistItem.objects.get_or_create(
                    wishlist=wishlist,
                    product=product,
                    defaults={'notes': notes}
                )
                
                if not created:
                    # Update notes if item already exists
                    if notes:
                        wishlist_item.notes = notes
<<<<<<< HEAD
                        wishlist_item.save()
                
                # Log activity
                CustomerService.log_activity(
                    customer_profile, 
                    'ADD_TO_WISHLIST', 
                    f'Added {product.name} to wishlist',
                    product=product
                )
                
                return wishlist_item
                
        except Exception as e:
            raise ValidationError(f"Failed to add to wishlist: {str(e)}")
=======
                        wishlist_item.save(update_fields=['notes'])
                
                # Log activity
                CustomerActivity.objects.create(
                    customer=customer_profile,
                    activity_type='ADD_TO_WISHLIST',
                    description=f'Added {product.name} to wishlist',
                    product=product
                )
                
                logger.info(f"Product {product.name} added to wishlist for {customer_profile.get_full_name()}")
                return wishlist_item
                
        except Exception as e:
            logger.error(f"Error adding to wishlist: {str(e)}")
            raise
>>>>>>> Task-10.3
    
    @staticmethod
    def remove_from_wishlist(customer_profile: CustomerProfile, product: Product) -> bool:
        """
        Remove a product from customer's wishlist.
<<<<<<< HEAD
        
        Args:
            customer_profile: CustomerProfile instance
            product: Product instance
            
        Returns:
            Boolean indicating success
        """
        try:
            with transaction.atomic():
                wishlist = getattr(customer_profile, 'wishlist', None)
                if not wishlist:
                    return False
                
                wishlist_item = WishlistItem.objects.filter(
                    wishlist=wishlist,
                    product=product
                ).first()
                
                if wishlist_item:
                    wishlist_item.delete()
                    
                    # Log activity
                    CustomerService.log_activity(
                        customer_profile, 
                        'REMOVE_FROM_WISHLIST', 
                        f'Removed {product.name} from wishlist',
                        product=product
                    )
                    
                    return True
                
                return False
                
        except Exception as e:
            raise ValidationError(f"Failed to remove from wishlist: {str(e)}")
    
    @staticmethod
    def get_wishlist_items(customer_profile: CustomerProfile) -> List[WishlistItem]:
        """
        Get all items in customer's wishlist.
        
        Args:
            customer_profile: CustomerProfile instance
            
        Returns:
            List of WishlistItem instances
        """
        try:
            wishlist = getattr(customer_profile, 'wishlist', None)
            if not wishlist:
                return []
            
            return list(wishlist.items.select_related('product').all())
            
        except Exception as e:
            raise ValidationError(f"Failed to get wishlist items: {str(e)}")
=======
        """
        try:
            with transaction.atomic():
                wishlist = WishlistService.get_or_create_wishlist(customer_profile)
                
                try:
                    wishlist_item = WishlistItem.objects.get(
                        wishlist=wishlist,
                        product=product
                    )
                    wishlist_item.delete()
                    
                    # Log activity
                    CustomerActivity.objects.create(
                        customer=customer_profile,
                        activity_type='REMOVE_FROM_WISHLIST',
                        description=f'Removed {product.name} from wishlist',
                        product=product
                    )
                    
                    logger.info(f"Product {product.name} removed from wishlist for {customer_profile.get_full_name()}")
                    return True
                    
                except WishlistItem.DoesNotExist:
                    return False
                
        except Exception as e:
            logger.error(f"Error removing from wishlist: {str(e)}")
            raise
>>>>>>> Task-10.3
    
    @staticmethod
    def clear_wishlist(customer_profile: CustomerProfile) -> bool:
        """
        Clear all items from customer's wishlist.
<<<<<<< HEAD
        
        Args:
            customer_profile: CustomerProfile instance
            
        Returns:
            Boolean indicating success
        """
        try:
            with transaction.atomic():
                wishlist = getattr(customer_profile, 'wishlist', None)
                if not wishlist:
                    return False
                
                item_count = wishlist.items.count()
                wishlist.items.all().delete()
                
                # Log activity
                CustomerService.log_activity(
                    customer_profile, 
                    'REMOVE_FROM_WISHLIST', 
                    f'Cleared wishlist ({item_count} items)'
                )
                
                return True
                
        except Exception as e:
            raise ValidationError(f"Failed to clear wishlist: {str(e)}")


class CustomerAnalyticsService:
    """
    Service class for customer analytics and insights.
    """
    
    @staticmethod
    def get_customer_segments() -> Dict:
        """
        Get customer segmentation data.
        
        Returns:
            Dictionary containing customer segment analytics
        """
        try:
            total_customers = CustomerProfile.objects.count()
            
            # Segment by tier
            tier_segments = {}
            for tier in ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM']:
                if tier == 'BRONZE':
                    count = CustomerProfile.objects.filter(total_spent__lt=10000).count()
                elif tier == 'SILVER':
                    count = CustomerProfile.objects.filter(
                        total_spent__gte=10000, total_spent__lt=50000
                    ).count()
                elif tier == 'GOLD':
                    count = CustomerProfile.objects.filter(
                        total_spent__gte=50000, total_spent__lt=100000
                    ).count()
                else:  # PLATINUM
                    count = CustomerProfile.objects.filter(total_spent__gte=100000).count()
                
                tier_segments[tier] = {
                    'count': count,
                    'percentage': (count / total_customers * 100) if total_customers > 0 else 0
                }
            
            # Segment by activity
            active_customers = CustomerProfile.objects.filter(
                last_login_date__gte=timezone.now() - timezone.timedelta(days=30)
            ).count()
            
            inactive_customers = total_customers - active_customers
            
            return {
                'total_customers': total_customers,
                'tier_segments': tier_segments,
                'activity_segments': {
                    'active': {
                        'count': active_customers,
                        'percentage': (active_customers / total_customers * 100) if total_customers > 0 else 0
                    },
                    'inactive': {
                        'count': inactive_customers,
                        'percentage': (inactive_customers / total_customers * 100) if total_customers > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            raise ValidationError(f"Failed to get customer segments: {str(e)}")
    
    @staticmethod
    def get_top_customers(limit: int = 10) -> List[Dict]:
        """
        Get top customers by total spent.
        
        Args:
            limit: Number of top customers to return
            
        Returns:
            List of customer data dictionaries
        """
        try:
            top_customers = CustomerProfile.objects.select_related('user').order_by(
                '-total_spent'
            )[:limit]
            
            return [
                {
                    'id': str(customer.id),
                    'name': customer.get_full_name(),
                    'email': customer.user.email,
                    'total_spent': float(customer.total_spent),
                    'total_orders': customer.total_orders,
                    'customer_tier': customer.customer_tier,
                    'loyalty_points': customer.loyalty_points
                }
                for customer in top_customers
            ]
            
        except Exception as e:
            raise ValidationError(f"Failed to get top customers: {str(e)}")
=======
        """
        try:
            with transaction.atomic():
                wishlist = WishlistService.get_or_create_wishlist(customer_profile)
                count = wishlist.items.count()
                wishlist.items.all().delete()
                
                logger.info(f"Cleared {count} items from wishlist for {customer_profile.get_full_name()}")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing wishlist: {str(e)}")
            raise
    
    @staticmethod
    def is_in_wishlist(customer_profile: CustomerProfile, product: Product) -> bool:
        """
        Check if a product is in customer's wishlist.
        """
        try:
            wishlist = WishlistService.get_or_create_wishlist(customer_profile)
            return WishlistItem.objects.filter(
                wishlist=wishlist,
                product=product
            ).exists()
        except Exception:
            return False


class CustomerActivityService:
    """
    Service class for tracking customer activities.
    """
    
    @staticmethod
    def log_activity(
        customer_profile: CustomerProfile,
        activity_type: str,
        description: str = '',
        product: Product = None,
        order = None,
        ip_address: str = None,
        user_agent: str = None,
        session_key: str = None,
        metadata: Dict[str, Any] = None
    ) -> CustomerActivity:
        """
        Log a customer activity.
        """
        try:
            activity = CustomerActivity.objects.create(
                customer=customer_profile,
                activity_type=activity_type,
                description=description,
                product=product,
                order=order,
                ip_address=ip_address,
                user_agent=user_agent,
                session_key=session_key,
                metadata=metadata or {}
            )
            
            return activity
            
        except Exception as e:
            logger.error(f"Error logging customer activity: {str(e)}")
            # Don't raise exception for activity logging to avoid breaking main flow
            return None
    
    @staticmethod
    def get_customer_activities(
        customer_profile: CustomerProfile,
        activity_type: str = None,
        limit: int = 50
    ) -> List[CustomerActivity]:
        """
        Get customer activities with optional filtering.
        """
        try:
            queryset = customer_profile.activities.all()
            
            if activity_type:
                queryset = queryset.filter(activity_type=activity_type)
            
            return list(queryset[:limit])
            
        except Exception as e:
            logger.error(f"Error getting customer activities: {str(e)}")
            return []
    
    @staticmethod
    def get_customer_analytics(customer_profile: CustomerProfile) -> Dict[str, Any]:
        """
        Get customer analytics data.
        """
        try:
            activities = customer_profile.activities.all()
            
            analytics = {
                'total_activities': activities.count(),
                'login_count': activities.filter(activity_type='LOGIN').count(),
                'product_views': activities.filter(activity_type='PRODUCT_VIEW').count(),
                'cart_additions': activities.filter(activity_type='ADD_TO_CART').count(),
                'wishlist_additions': activities.filter(activity_type='ADD_TO_WISHLIST').count(),
                'orders_placed': activities.filter(activity_type='ORDER_PLACED').count(),
                'reviews_submitted': activities.filter(activity_type='REVIEW_SUBMITTED').count(),
                'last_activity': activities.first().created_at if activities.exists() else None,
                'customer_tier': customer_profile.customer_tier,
                'total_spent': float(customer_profile.total_spent),
                'loyalty_points': customer_profile.loyalty_points,
                'account_age_days': (timezone.now() - customer_profile.created_at).days,
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting customer analytics: {str(e)}")
            return {}
>>>>>>> Task-10.3
