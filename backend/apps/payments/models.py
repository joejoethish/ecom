"""
Payment models for the ecommerce platform.
"""
from django.db import models
from django.conf import settings
from core.models import BaseModel


class Currency(BaseModel):
    """
    Currency model for multi-currency support.
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('INR', 'Indian Rupee'),
        ('AED', 'United Arab Emirates Dirham'),
        ('EUR', 'Euro'),
        ('SGD', 'Singapore Dollar'),
    ]
    
    code = models.CharField(max_length=3, choices=CURRENCY_CHOICES, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    exchange_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        help_text="Exchange rate relative to base currency (USD)"
    )
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        verbose_name_plural = "Currencies"


class PaymentMethod(BaseModel):
    """
    Payment method model to store available payment methods.
    """
    METHOD_TYPES = [
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI'),
        ('WALLET', 'Digital Wallet'),
        ('NETBANKING', 'Net Banking'),
        ('COD', 'Cash on Delivery'),
        ('GIFT_CARD', 'Gift Card'),
        ('IMPS', 'IMPS'),
        ('RTGS', 'RTGS'),
        ('NEFT', 'NEFT'),
    ]
    
    GATEWAY_CHOICES = [
        ('RAZORPAY', 'Razorpay'),
        ('STRIPE', 'Stripe'),
        ('INTERNAL', 'Internal'),
    ]
    
    name = models.CharField(max_length=100)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    icon = models.ImageField(upload_to='payment_methods/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    processing_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_gateway_display()})"


class Payment(BaseModel):
    """
    Payment model for tracking payment transactions.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
        ('CANCELLED', 'Cancelled'),
    ]

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(blank=True, null=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    failure_reason = models.TextField(blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment {self.id} - {self.order.order_number}"


class Refund(BaseModel):
    """
    Refund model for tracking refund transactions.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(blank=True, null=True)
    refund_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Refund {self.id} for Payment {self.payment.id}"


class Wallet(BaseModel):
    """
    Digital wallet for users to store and use funds.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Wallet of {self.user.email}"


class WalletTransaction(BaseModel):
    """
    Transactions for user wallets.
    """
    TRANSACTION_TYPES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('REFUND', 'Refund'),
        ('CASHBACK', 'Cashback'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField()
    balance_after_transaction = models.DecimalField(max_digits=10, decimal_places=2)
    reference_id = models.CharField(max_length=100, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount} for {self.wallet.user.email}"


class GiftCard(BaseModel):
    """
    Gift card model for prepaid cards.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('USED', 'Used'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    initial_balance = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    issued_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_gift_cards', null=True, blank=True)
    purchased_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='purchased_gift_cards', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    expiry_date = models.DateField()
    
    def __str__(self):
        return f"Gift Card {self.code} - {self.current_balance}"


class GiftCardTransaction(BaseModel):
    """
    Transactions for gift cards.
    """
    gift_card = models.ForeignKey(GiftCard, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='gift_card_transactions')
    balance_after_transaction = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    
    def __str__(self):
        return f"Gift Card Transaction of {self.amount} for {self.gift_card.code}"