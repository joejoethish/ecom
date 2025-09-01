"""
Cart views for the ecommerce platform.
"""
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
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
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            
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
            
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
            
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


class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for cart operations with add_item, remove_item, and update_quantity actions.
    """
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """
        Get cart queryset based on user or session.
        """
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if session_key:
                return Cart.objects.filter(session_key=session_key)
            return Cart.objects.none()
    
    def get_cart(self):
        """
        Get or create cart for current user/session.
        """
        session_key = self.request.session.session_key
        return CartService.get_or_create_cart(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=session_key
        )
    
    def list(self, request):
        """
        Get cart contents.
        """
        cart = self.get_cart()
        
        if not cart:
            return Response({
                'message': 'No cart found',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.get_serializer(cart)
        return Response({
            'cart': serializer.data,
            'success': True
        })
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """
        Add item to cart.
        """
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        is_gift = request.data.get('is_gift', False)
        gift_message = request.data.get('gift_message')
        
        if not product_id:
            return Response({
                'message': 'Product ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart = self.get_cart()
        
        # Add item to cart
        cart_item, message = CartService.add_to_cart(
            cart=cart,
            product_id=product_id,
            quantity=quantity,
            is_gift=is_gift,
            gift_message=gift_message
        )
        
        if cart_item:
            cart_serializer = self.get_serializer(cart)
            return Response({
                'message': message,
                'cart': cart_serializer.data,
                'success': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """
        Remove item from cart.
        """
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({
                'message': 'Product ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart = self.get_cart()
        
        # Remove item from cart
        success, message = CartService.remove_from_cart(
            cart=cart,
            product_id=product_id
        )
        
        if success:
            cart_serializer = self.get_serializer(cart)
            return Response({
                'message': message,
                'cart': cart_serializer.data,
                'success': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def update_quantity(self, request):
        """
        Update item quantity in cart.
        """
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        
        if not product_id:
            return Response({
                'message': 'Product ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity is None:
            return Response({
                'message': 'Quantity is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({
                'message': 'Quantity must be a valid integer',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart = self.get_cart()
        
        # Update item quantity
        cart_item, message = CartService.update_quantity(
            cart=cart,
            product_id=product_id,
            quantity=quantity
        )
        
        if cart_item or quantity == 0:  # quantity 0 means item was removed
            cart_serializer = self.get_serializer(cart)
            return Response({
                'message': message,
                'cart': cart_serializer.data,
                'success': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Clear all items from cart.
        """
        cart = self.get_cart()
        
        # Clear cart
        success, message = CartService.clear_cart(cart)
        
        if success:
            cart_serializer = self.get_serializer(cart)
            return Response({
                'message': message,
                'cart': cart_serializer.data,
                'success': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': message,
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)