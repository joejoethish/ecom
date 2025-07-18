"""
Admin configuration for the payments app.
"""
from django.contrib import admin
from .models import (
    Currency, PaymentMethod, Payment, Refund,
    Wallet, WalletTransaction, GiftCard, GiftCardTransaction
)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Admin configuration for Currency model."""
    list_display = ('code', 'name', 'symbol', 'exchange_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentMethod model."""
    list_display = ('name', 'method_type', 'gateway', 'is_active')
    list_filter = ('method_type', 'gateway', 'is_active')
    search_fields = ('name',)


class RefundInline(admin.TabularInline):
    """Inline admin for Refund model."""
    model = Refund
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""
    list_display = ('id', 'order', 'user', 'amount', 'currency', 'payment_method', 'status', 'payment_date')
    list_filter = ('status', 'payment_method', 'currency', 'payment_date')
    search_fields = ('order__order_number', 'user__email', 'transaction_id', 'gateway_payment_id')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RefundInline]
    date_hierarchy = 'payment_date'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Admin configuration for Refund model."""
    list_display = ('id', 'payment', 'amount', 'status', 'refund_date')
    list_filter = ('status', 'refund_date')
    search_fields = ('payment__order__order_number', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'refund_date'


class WalletTransactionInline(admin.TabularInline):
    """Inline admin for WalletTransaction model."""
    model = WalletTransaction
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin configuration for Wallet model."""
    list_display = ('id', 'user', 'balance', 'currency', 'is_active')
    list_filter = ('currency', 'is_active')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WalletTransactionInline]


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for WalletTransaction model."""
    list_display = ('id', 'wallet', 'amount', 'transaction_type', 'balance_after_transaction', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__email', 'description', 'reference_id')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


class GiftCardTransactionInline(admin.TabularInline):
    """Inline admin for GiftCardTransaction model."""
    model = GiftCardTransaction
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    """Admin configuration for GiftCard model."""
    list_display = ('id', 'code', 'initial_balance', 'current_balance', 'currency', 'status', 'expiry_date')
    list_filter = ('status', 'currency', 'expiry_date')
    search_fields = ('code', 'issued_to__email', 'purchased_by__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [GiftCardTransactionInline]
    date_hierarchy = 'expiry_date'


@admin.register(GiftCardTransaction)
class GiftCardTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for GiftCardTransaction model."""
    list_display = ('id', 'gift_card', 'amount', 'balance_after_transaction', 'created_at')
    search_fields = ('gift_card__code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'