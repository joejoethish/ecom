"""
Serializers for the payments app.
"""
from rest_framework import serializers
from .models import (
    Currency, PaymentMethod, Payment, Refund,
    Wallet, WalletTransaction, GiftCard, GiftCardTransaction
)


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency model."""
    
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol', 'exchange_rate', 'is_active']
        read_only_fields = ['id']


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for PaymentMethod model."""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'method_type', 'gateway', 'icon',
            'is_active', 'processing_fee_percentage', 'processing_fee_fixed', 'description'
        ]
        read_only_fields = ['id']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    payment_method_details = PaymentMethodSerializer(source='payment_method', read_only=True)
    currency_details = CurrencySerializer(source='currency', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'user', 'payment_method', 'payment_method_details',
            'amount', 'currency', 'currency_details', 'status', 'transaction_id',
            'gateway_payment_id', 'gateway_order_id', 'gateway_signature',
            'processing_fee', 'failure_reason', 'payment_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'gateway_payment_id', 'gateway_order_id',
            'gateway_signature', 'processing_fee', 'failure_reason', 'payment_date',
            'created_at', 'updated_at'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating a new payment."""
    
    order_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency_code = serializers.CharField(max_length=3)
    payment_method_id = serializers.UUIDField()
    metadata = serializers.JSONField(required=False)


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for verifying a payment."""
    
    payment_id = serializers.UUIDField()
    gateway_payment_id = serializers.CharField()
    gateway_signature = serializers.CharField()
    metadata = serializers.JSONField(required=False)


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for Refund model."""
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'reason', 'status',
            'transaction_id', 'gateway_response', 'refund_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'gateway_response', 'refund_date',
            'created_at', 'updated_at'
        ]


class RefundCreateSerializer(serializers.Serializer):
    """Serializer for creating a refund."""
    
    payment_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField()
    metadata = serializers.JSONField(required=False)


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model."""
    
    currency_details = CurrencySerializer(source='currency', read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'balance', 'currency', 'currency_details',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'balance', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for WalletTransaction model."""
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'amount', 'transaction_type', 'description',
            'balance_after_transaction', 'reference_id', 'payment',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'amount', 'transaction_type', 'balance_after_transaction',
            'reference_id', 'created_at', 'updated_at'
        ]


class WalletAddFundsSerializer(serializers.Serializer):
    """Serializer for adding funds to a wallet."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency_code = serializers.CharField(max_length=3)
    payment_method_id = serializers.UUIDField()
    metadata = serializers.JSONField(required=False)


class GiftCardSerializer(serializers.ModelSerializer):
    """Serializer for GiftCard model."""
    
    currency_details = CurrencySerializer(source='currency', read_only=True)
    
    class Meta:
        model = GiftCard
        fields = [
            'id', 'code', 'initial_balance', 'current_balance',
            'currency', 'currency_details', 'issued_to', 'purchased_by',
            'status', 'expiry_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'code', 'initial_balance', 'current_balance',
            'created_at', 'updated_at'
        ]


class GiftCardTransactionSerializer(serializers.ModelSerializer):
    """Serializer for GiftCardTransaction model."""
    
    class Meta:
        model = GiftCardTransaction
        fields = [
            'id', 'gift_card', 'amount', 'payment',
            'balance_after_transaction', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'amount', 'balance_after_transaction',
            'created_at', 'updated_at'
        ]


class GiftCardPurchaseSerializer(serializers.Serializer):
    """Serializer for purchasing a gift card."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency_code = serializers.CharField(max_length=3)
    payment_method_id = serializers.UUIDField()
    recipient_email = serializers.EmailField()
    expiry_days = serializers.IntegerField(min_value=30, max_value=730)
    metadata = serializers.JSONField(required=False)


class GiftCardCheckSerializer(serializers.Serializer):
    """Serializer for checking a gift card."""
    
    code = serializers.CharField()


class PaymentLinkSerializer(serializers.Serializer):
    """Serializer for generating a payment link."""
    
    order_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency_code = serializers.CharField(max_length=3)
    payment_method_id = serializers.UUIDField()
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()
    metadata = serializers.JSONField(required=False)