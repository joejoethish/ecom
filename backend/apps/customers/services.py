"""
Customer service layer for business logic.
"""
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any, List
import logging

from .models import CustomerProfile, Address, Wishlist, WishlistItem, CustomerActivity
from apps.products.models import Product

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomerService:
    """
    Service class for customer-related business logic.
    """
    
    @staticmethod
    def create_customer_profile(user, **profile_data) -> CustomerProfile:
        """
        Create a customer profile for a user.
        """
        try:
            with transaction.atomic():
                # Check if profile already exists
                if hasattr(user, 'customer_profile'):
                    return user.customer_profile
                
                # Create customer profile
                profile = CustomerProfile.objects.create(
                    user=user,
                    **profile_data
                )
                
                # Create default wishlist
                Wishlist.objects.create(
                    customer=profile,
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


class AddressService:
    """
    Service class for address-related business logic.
    """
    
    @staticmethod
    def create_address(customer_profile: CustomerProfile, address_data: Dict[str, Any]) -> Address:
        """
        Create a new address for a customer.
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
    
    @staticmethod
    def delete_address(address: Address) -> bool:
        """
        Delete an address and handle default address reassignment.
        """
        try:
            with transaction.atomic():
                customer = address.customer
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
    
    @staticmethod
    def set_default_address(address: Address, address_type: str = 'all') -> Address:
        """
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


class WishlistService:
    """
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
    
    @staticmethod
    def remove_from_wishlist(customer_profile: CustomerProfile, product: Product) -> bool:
        """
        Remove a product from customer's wishlist.
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
    
    @staticmethod
    def clear_wishlist(customer_profile: CustomerProfile) -> bool:
        """
        Clear all items from customer's wishlist.
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