"""
Cart views for the ecommerce platform.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, SavedItem
from .serializers import CartSerializer, CartItemSerializer, SavedItemSerializer
from .services import CartService


class CartView(APIView):
    """
    View for retrieving cart contents.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Get cart based on user or session
        session_key = request.session.session_key
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        if not cart:
            return Response({
                'message': 'No cart found',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = CartSerializer(cart)
        return Response({
            'cart': serializer.data,
            'success': True
        })


class AddToCartView(APIView):
    """
    View for adding items to cart.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get required parameters
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        is_gift = request.data.get('is_gift', False)
        gift_message = request.data.get('gift_message')
        
        if not product_id:
            return Response({
                'message': 'Product ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Get cart based on user or session
        session_key = request.session.session_key
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Add item to cart
        cart_item, message = CartService.add_to_cart(
            cart=cart,
            product_id=product_id,
            quantity=quantity,
            is_gift=is_gift,
            gift_message=gift_message
        )
        
        if cart_item:
            serializer = CartItemSerializer(cart_item)
            return Response({
                'message': message,
                'cart_item': serializer.data,
                'success': True
            })
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class UpdateCartItemView(APIView):
    """
    View for updating cart item quantity.
    """
    permission_classes = [AllowAny]

    def put(self, request):
        # Get required parameters
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not product_id:
            return Response({
                'message': 'Product ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Get cart based on user or session
        session_key = request.session.session_key
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Update item quantity
        cart_item, message = CartService.update_quantity(
            cart=cart,
            product_id=product_id,
            quantity=quantity
        )
        
        if cart_item:
            serializer = CartItemSerializer(cart_item)
            return Response({
                'message': message,
                'cart_item': serializer.data,
                'success': True
            })
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class RemoveFromCartView(APIView):
    """
    View for removing items from cart.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get required parameters
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({
                'message': 'Product ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Get cart based on user or session
        session_key = request.session.session_key
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Remove item from cart
        success, message = CartService.remove_from_cart(
            cart=cart,
            product_id=product_id
        )
        
        if success:
            return Response({
                'message': message,
                'success': True
            })
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class ClearCartView(APIView):
    """
    View for clearing cart.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get cart based on user or session
        session_key = request.session.session_key
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Clear cart
        success, message = CartService.clear_cart(cart)
        
        if success:
            return Response({
                'message': message,
                'success': True
            })
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class SaveForLaterView(APIView):
    """
    View for saving items for later.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get required parameters
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({
                'message': 'Product ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Get cart based on user
        cart = CartService.get_or_create_cart(user=request.user)
        
        # Save item for later
        saved_item, message = CartService.save_for_later(
            cart=cart,
            product_id=product_id
        )
        
        if saved_item:
            serializer = SavedItemSerializer(saved_item)
            return Response({
                'message': message,
                'saved_item': serializer.data,
                'success': True
            })
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class MoveToCartView(APIView):
    """
    View for moving saved items to cart.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get required parameters
        saved_item_id = request.data.get('saved_item_id')
        
        if not saved_item_id:
            return Response({
                'message': 'Saved item ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Move saved item to cart
        cart_item, message = CartService.move_to_cart(
            user=request.user,
            saved_item_id=saved_item_id
        )
        
        if cart_item:
            serializer = CartItemSerializer(cart_item)
            return Response({
                'message': message,
                'cart_item': serializer.data,
                'success': True
            })
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class SavedItemsView(APIView):
    """
    View for retrieving saved items.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved_items = SavedItem.objects.filter(user=request.user)
        serializer = SavedItemSerializer(saved_items, many=True)
        return Response({
            'saved_items': serializer.data,
            'success': True
        })


class ApplyCouponView(APIView):
    """
    View for applying coupon to cart.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get required parameters
        coupon_code = request.data.get('coupon_code')
        
        if not coupon_code:
            return Response({
                'message': 'Coupon code is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Get cart based on user or session
        session_key = request.session.session_key
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Apply coupon
        success, message = CartService.apply_coupon(
            cart=cart,
            coupon_code=coupon_code
        )
        
        if success:
            return Response({
                'message': message,
                'success': True
            })
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)


class RemoveCouponView(APIView):
    """
    View for removing coupon from cart.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get cart based on user or session
        session_key = request.session.session_key
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Remove coupon
        success, message = CartService.remove_coupon(cart)
        
        if success:
            return Response({
                'message': message,
                'success': True
            })
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)