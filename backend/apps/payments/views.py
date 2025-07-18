"""
Views for the payments app.
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import (
    Currency, PaymentMethod, Payment, Refund,
    Wallet, WalletTransaction, GiftCard, GiftCardTransaction
)
from .serializers import (
    CurrencySerializer, PaymentMethodSerializer, PaymentSerializer,
    PaymentCreateSerializer, PaymentVerifySerializer, RefundSerializer,
    RefundCreateSerializer, WalletSerializer, WalletTransactionSerializer,
    WalletAddFundsSerializer, GiftCardSerializer, GiftCardTransactionSerializer,
    GiftCardPurchaseSerializer, GiftCardCheckSerializer, PaymentLinkSerializer
)
from .services import (
    PaymentService, CurrencyService, WalletService, GiftCardService
)
from core.exceptions import (
    PaymentGatewayError, InsufficientFundsError, NotFoundError
)

logger = logging.getLogger(__name__)


class CurrencyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for currencies.
    """
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Override permissions:
        - List and retrieve are available to authenticated users
        - Create, update, and delete are restricted to admin users
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    API endpoint for payment methods.
    """
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Override permissions:
        - List and retrieve are available to authenticated users
        - Create, update, and delete are restricted to admin users
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class PaymentViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin):
    """
    API endpoint for payments.
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter payments by the current user.
        Admin users can see all payments.
        """
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all().order_by('-created_at')
        return Payment.objects.filter(user=user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def create_payment(self, request):
        """
        Create a new payment.
        """
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = PaymentService.create_payment(
                order_id=serializer.validated_data['order_id'],
                user_id=request.user.id,
                amount=serializer.validated_data['amount'],
                currency_code=serializer.validated_data['currency_code'],
                payment_method_id=serializer.validated_data['payment_method_id'],
                metadata=serializer.validated_data.get('metadata')
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except (PaymentGatewayError, InsufficientFundsError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """
        Verify a payment.
        """
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = PaymentService.verify_payment(
                payment_id=serializer.validated_data['payment_id'],
                gateway_payment_id=serializer.validated_data['gateway_payment_id'],
                gateway_signature=serializer.validated_data['gateway_signature'],
                metadata=serializer.validated_data.get('metadata')
            )
            return Response(result)
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Get the current status of a payment.
        """
        payment = self.get_object()
        
        try:
            result = PaymentService.get_payment_status(payment.id)
            return Response(result)
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generate_payment_link(self, request):
        """
        Generate a payment link.
        """
        serializer = PaymentLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get the payment method
            payment_method = PaymentMethod.objects.get(
                id=serializer.validated_data['payment_method_id']
            )
            
            # Get the gateway
            from core.integrations.payment_gateways.factory import PaymentGatewayFactory
            gateway = PaymentGatewayFactory.get_gateway(payment_method.gateway)
            
            # Generate payment link
            metadata = serializer.validated_data.get('metadata', {})
            metadata.update({
                'success_url': serializer.validated_data['success_url'],
                'cancel_url': serializer.validated_data['cancel_url']
            })
            
            payment_link = gateway.generate_payment_link(
                float(serializer.validated_data['amount']),
                serializer.validated_data['currency_code'],
                str(serializer.validated_data['order_id']),
                metadata
            )
            
            return Response({'payment_link': payment_link})
        except PaymentMethod.DoesNotExist:
            return Response(
                {'error': 'Invalid payment method'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RefundViewSet(viewsets.GenericViewSet,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin):
    """
    API endpoint for refunds.
    """
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter refunds by the current user.
        Admin users can see all refunds.
        """
        user = self.request.user
        if user.is_staff:
            return Refund.objects.all().order_by('-created_at')
        return Refund.objects.filter(payment__user=user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def create_refund(self, request):
        """
        Create a new refund.
        """
        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Check if the payment belongs to the user
            payment = Payment.objects.get(id=serializer.validated_data['payment_id'])
            if not request.user.is_staff and payment.user != request.user:
                return Response(
                    {'error': 'You do not have permission to refund this payment'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            result = PaymentService.process_refund(
                payment_id=serializer.validated_data['payment_id'],
                amount=serializer.validated_data['amount'],
                reason=serializer.validated_data['reason'],
                metadata=serializer.validated_data.get('metadata')
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WalletViewSet(viewsets.GenericViewSet,
                    mixins.RetrieveModelMixin):
    """
    API endpoint for wallets.
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter wallets by the current user.
        Admin users can see all wallets.
        """
        user = self.request.user
        if user.is_staff:
            return Wallet.objects.all()
        return Wallet.objects.filter(user=user)
    
    def get_object(self):
        """
        Get the wallet for the current user.
        """
        try:
            wallet = Wallet.objects.get(user=self.request.user)
            self.check_object_permissions(self.request, wallet)
            return wallet
        except Wallet.DoesNotExist:
            # Create a wallet if it doesn't exist
            default_currency = Currency.objects.get(code='USD')
            wallet = Wallet.objects.create(
                user=self.request.user,
                balance=Decimal('0.0'),
                currency=default_currency,
                is_active=True
            )
            return wallet
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """
        Get the wallet for the current user.
        """
        wallet = self.get_object()
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        Get the transactions for the current user's wallet.
        """
        wallet = self.get_object()
        transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
        
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = WalletTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_funds(self, request):
        """
        Add funds to the wallet.
        """
        serializer = WalletAddFundsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = WalletService.add_funds(
                user_id=request.user.id,
                amount=serializer.validated_data['amount'],
                currency_code=serializer.validated_data['currency_code'],
                payment_method_id=serializer.validated_data['payment_method_id'],
                metadata=serializer.validated_data.get('metadata')
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def complete_add_funds(self, request):
        """
        Complete the process of adding funds to the wallet.
        """
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = WalletService.complete_add_funds(
                payment_id=serializer.validated_data['payment_id'],
                gateway_payment_id=serializer.validated_data['gateway_payment_id'],
                gateway_signature=serializer.validated_data['gateway_signature'],
                metadata=serializer.validated_data.get('metadata')
            )
            return Response(result)
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GiftCardViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin):
    """
    API endpoint for gift cards.
    """
    serializer_class = GiftCardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter gift cards by the current user.
        Admin users can see all gift cards.
        """
        user = self.request.user
        if user.is_staff:
            return GiftCard.objects.all().order_by('-created_at')
        return GiftCard.objects.filter(issued_to=user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def check(self, request):
        """
        Check a gift card's details.
        """
        serializer = GiftCardCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = GiftCardService.get_gift_card_details(
                serializer.validated_data['code']
            )
            return Response(result)
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def purchase(self, request):
        """
        Purchase a gift card.
        """
        serializer = GiftCardPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = GiftCardService.purchase_gift_card(
                user_id=request.user.id,
                amount=serializer.validated_data['amount'],
                currency_code=serializer.validated_data['currency_code'],
                payment_method_id=serializer.validated_data['payment_method_id'],
                recipient_email=serializer.validated_data['recipient_email'],
                expiry_days=serializer.validated_data['expiry_days'],
                metadata=serializer.validated_data.get('metadata')
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def complete_purchase(self, request):
        """
        Complete the process of purchasing a gift card.
        """
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = GiftCardService.complete_gift_card_purchase(
                payment_id=serializer.validated_data['payment_id'],
                gateway_payment_id=serializer.validated_data['gateway_payment_id'],
                gateway_signature=serializer.validated_data['gateway_signature'],
                metadata=serializer.validated_data.get('metadata')
            )
            return Response(result)
        except PaymentGatewayError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """
        Get the transactions for a gift card.
        """
        gift_card = self.get_object()
        transactions = GiftCardTransaction.objects.filter(gift_card=gift_card).order_by('-created_at')
        
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = GiftCardTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = GiftCardTransactionSerializer(transactions, many=True)
        return Response(serializer.data)