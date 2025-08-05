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
    def create_customer_profile(user: User, **kwargs) -> CustomerProfile:
        """
        Create a customer profile for a user.
        
        Args:
            user: User instance
            **kwargs: Additional profile data
            
        Returns:
            CustomerProfile instance
        """
        try:
            with transaction.atomic():
                # Check if profile already exists
                if hasattr(user, 'customer_profile'):
                    return user.customer_profile
                
                # Create new profile
                profile = CustomerProfile.objects.create(
                    user=user,
                    **kwargs
                )
                
                logger.info(f"Customer profile created for user {user.username}")
                return profile
                
        except Exception as e:
            logger.error(f"Failed to create customer profile: {str(e)}")
            raise ValidationError(f"Failed to create customer profile: {str(e)}")
    
    @staticmethod
    def update_customer_profile(customer_profile: CustomerProfile, **kwargs) -> CustomerProfile:
        """
        Update customer profile information.
        
        Args:
            customer_profile: CustomerProfile instance
            **kwargs: Fields to update
            
        Returns:
            Updated CustomerProfile instance
        """
        try:
            with transaction.atomic():
                for field, value in kwargs.items():
                    if hasattr(customer_profile, field):
                        setattr(customer_profile, field, value)
                
                customer_profile.save()
                logger.info(f"Customer profile updated for {customer_profile.get_full_name()}")
                return customer_profile
                
        except Exception as e:
            logger.error(f"Failed to update customer profile: {str(e)}")
            raise ValidationError(f"Failed to update customer profile: {str(e)}")


class AddressService:
    """
    Service class for address-related business logic.
    """
    
    @staticmethod
    def create_address(customer_profile: CustomerProfile, **address_data) -> Address:
        """
        Create a new address for a customer.
        
        Args:
            customer_profile: CustomerProfile instance
            **address_data: Address fields
            
        Returns:
            Address instance
        """
        try:
            with transaction.atomic():
                address = Address.objects.create(
                    customer=customer_profile,
                    **address_data
                )
                
                logger.info(f"Address created for customer {customer_profile.get_full_name()}")
                return address
                
        except Exception as e:
            logger.error(f"Failed to create address: {str(e)}")
            raise ValidationError(f"Failed to create address: {str(e)}")
    
    @staticmethod
    def update_address(address: Address, **address_data) -> Address:
        """
        Update an existing address.
        
        Args:
            address: Address instance
            **address_data: Fields to update
            
        Returns:
            Updated Address instance
        """
        try:
            with transaction.atomic():
                for field, value in address_data.items():
                    if hasattr(address, field):
                        setattr(address, field, value)
                
                address.save()
                return address
                
        except Exception as e:
            logger.error(f"Failed to update address: {str(e)}")
            raise ValidationError(f"Failed to update address: {str(e)}")
    
    @staticmethod
    def delete_address(address: Address) -> bool:
        """
        Delete an address and handle default address reassignment.
        
        Args:
            address: Address instance to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            with transaction.atomic():
                customer = address.customer
                was_default = address.is_default
                was_billing_default = address.is_billing_default
                
                address.delete()
                
                # If deleted address was default, set another as default
                if was_default:
                    other_address = Address.objects.filter(customer=customer).first()
                    if other_address:
                        other_address.is_default = True
                        other_address.save()
                
                if was_billing_default:
                    other_address = Address.objects.filter(customer=customer).first()
                    if other_address:
                        other_address.is_billing_default = True
                        other_address.save()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete address: {str(e)}")
            raise ValidationError(f"Failed to delete address: {str(e)}")


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
        
        Args:
            customer_profile: CustomerProfile instance
            product: Product instance
            notes: Optional notes about the item
            
        Returns:
            WishlistItem instance
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
                
                return wishlist_item
                
        except Exception as e:
            logger.error(f"Failed to add to wishlist: {str(e)}")
            raise ValidationError(f"Failed to add to wishlist: {str(e)}")
    
    @staticmethod
    def remove_from_wishlist(customer_profile: CustomerProfile, product: Product) -> bool:
        """
        Remove a product from customer's wishlist.
        
        Args:
            customer_profile: CustomerProfile instance
            product: Product instance
            
        Returns:
            Boolean indicating success
        """
        try:
            wishlist = WishlistService.get_or_create_wishlist(customer_profile)
            wishlist_item = WishlistItem.objects.get(
                wishlist=wishlist,
                product=product
            )
            wishlist_item.delete()
            return True
            
        except WishlistItem.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to remove from wishlist: {str(e)}")
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
            wishlist = WishlistService.get_or_create_wishlist(customer_profile)
            return list(wishlist.items.select_related('product').all())
            
        except Exception as e:
            logger.error(f"Failed to get wishlist items: {str(e)}")
            raise ValidationError(f"Failed to get wishlist items: {str(e)}")


class CustomerAnalyticsService:
    """
    Service class for customer analytics and reporting.
    """
    
    @staticmethod
    def get_customer_stats(customer_profile: CustomerProfile) -> Dict[str, Any]:
        """
        Get customer statistics and analytics.
        
        Args:
            customer_profile: CustomerProfile instance
            
        Returns:
            Dictionary with customer stats
        """
        try:
            # Basic stats - would need to import Order model for real implementation
            stats = {
                'total_orders': 0,
                'total_spent': 0,
                'average_order_value': 0,
                'wishlist_items': WishlistService.get_wishlist_items(customer_profile).__len__(),
                'addresses_count': customer_profile.addresses.count(),
                'registration_date': customer_profile.user.date_joined,
                'last_login': customer_profile.user.last_login,
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get customer stats: {str(e)}")
            raise ValidationError(f"Failed to get customer stats: {str(e)}")
    
    @staticmethod
    def get_top_customers(limit: int = 10) -> List[CustomerProfile]:
        """
        Get top customers by various metrics.
        
        Args:
            limit: Number of customers to return
            
        Returns:
            List of CustomerProfile instances
        """
        try:
            # For now, just return recent customers
            # In real implementation, would order by total spent or orders
            return list(CustomerProfile.objects.select_related('user').order_by('-user__date_joined')[:limit])
            
        except Exception as e:
            logger.error(f"Failed to get top customers: {str(e)}")
            raise ValidationError(f"Failed to get top customers: {str(e)}")