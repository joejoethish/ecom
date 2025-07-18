"""
Tests for payment models.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.orders.models import Order
from apps.payments.models import (
    Currency, PaymentMethod, Payment, Refund,
    Wallet, WalletTransaction, GiftCard, GiftCardTransaction
)

User = get_user_model()


class CurrencyModelTest(TestCase):
    """Test cases for the Currency model."""
    
    def setUp(self):
        self.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
    
    def test_currency_creation(self):
        """Test that a currency can be created."""
        self.assertEqual(self.currency.code, 'USD')
        self.assertEqual(self.currency.name, 'US Dollar')
        self.assertEqual(self.currency.symbol, '$')
        self.assertEqual(self.currency.exchange_rate, Decimal('1.0'))
        self.assertTrue(self.currency.is_active)
    
    def test_currency_str_representation(self):
        """Test the string representation of a currency."""
        self.assertEqual(str(self.currency), 'USD - US Dollar')


class PaymentMethodModelTest(TestCase):
    """Test cases for the PaymentMethod model."""
    
    def setUp(self):
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            method_type='CARD',
            gateway='STRIPE',
            is_active=True,
            processing_fee_percentage=Decimal('2.5'),
            processing_fee_fixed=Decimal('0.30'),
            description='Pay with credit card'
        )
    
    def test_payment_method_creation(self):
        """Test that a payment method can be created."""
        self.assertEqual(self.payment_method.name, 'Credit Card')
        self.assertEqual(self.payment_method.method_type, 'CARD')
        self.assertEqual(self.payment_method.gateway, 'STRIPE')
        self.assertTrue(self.payment_method.is_active)
        self.assertEqual(self.payment_method.processing_fee_percentage, Decimal('2.5'))
        self.assertEqual(self.payment_method.processing_fee_fixed, Decimal('0.30'))
        self.assertEqual(self.payment_method.description, 'Pay with credit card')
    
    def test_payment_method_str_representation(self):
        """Test the string representation of a payment method."""
        self.assertEqual(str(self.payment_method), 'Credit Card (Stripe)')


class PaymentModelTest(TestCase):
    """Test cases for the Payment model."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test order
        self.order = Order.objects.create(
            user=self.user,
            order_number='ORD-12345',
            total_amount=Decimal('100.00')
        )
        
        # Create test currency
        self.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            method_type='CARD',
            gateway='STRIPE',
            is_active=True
        )
        
        # Create test payment
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency=self.currency,
            status='PENDING',
            transaction_id='txn_12345',
            gateway_payment_id='pi_12345',
            gateway_order_id='or_12345',
            processing_fee=Decimal('2.80')
        )
    
    def test_payment_creation(self):
        """Test that a payment can be created."""
        self.assertEqual(self.payment.order, self.order)
        self.assertEqual(self.payment.user, self.user)
        self.assertEqual(self.payment.payment_method, self.payment_method)
        self.assertEqual(self.payment.amount, Decimal('100.00'))
        self.assertEqual(self.payment.currency, self.currency)
        self.assertEqual(self.payment.status, 'PENDING')
        self.assertEqual(self.payment.transaction_id, 'txn_12345')
        self.assertEqual(self.payment.gateway_payment_id, 'pi_12345')
        self.assertEqual(self.payment.gateway_order_id, 'or_12345')
        self.assertEqual(self.payment.processing_fee, Decimal('2.80'))
    
    def test_payment_str_representation(self):
        """Test the string representation of a payment."""
        self.assertEqual(str(self.payment), f"Payment {self.payment.id} - {self.order.order_number}")


class RefundModelTest(TestCase):
    """Test cases for the Refund model."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test order
        self.order = Order.objects.create(
            user=self.user,
            order_number='ORD-12345',
            total_amount=Decimal('100.00')
        )
        
        # Create test currency
        self.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            method_type='CARD',
            gateway='STRIPE',
            is_active=True
        )
        
        # Create test payment
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency=self.currency,
            status='COMPLETED',
            transaction_id='txn_12345'
        )
        
        # Create test refund
        self.refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('50.00'),
            reason='Item out of stock',
            status='PENDING',
            transaction_id='ref_12345'
        )
    
    def test_refund_creation(self):
        """Test that a refund can be created."""
        self.assertEqual(self.refund.payment, self.payment)
        self.assertEqual(self.refund.amount, Decimal('50.00'))
        self.assertEqual(self.refund.reason, 'Item out of stock')
        self.assertEqual(self.refund.status, 'PENDING')
        self.assertEqual(self.refund.transaction_id, 'ref_12345')
    
    def test_refund_str_representation(self):
        """Test the string representation of a refund."""
        self.assertEqual(str(self.refund), f"Refund {self.refund.id} for Payment {self.payment.id}")


class WalletModelTest(TestCase):
    """Test cases for the Wallet model."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test currency
        self.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test wallet
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('500.00'),
            currency=self.currency,
            is_active=True
        )
    
    def test_wallet_creation(self):
        """Test that a wallet can be created."""
        self.assertEqual(self.wallet.user, self.user)
        self.assertEqual(self.wallet.balance, Decimal('500.00'))
        self.assertEqual(self.wallet.currency, self.currency)
        self.assertTrue(self.wallet.is_active)
    
    def test_wallet_str_representation(self):
        """Test the string representation of a wallet."""
        self.assertEqual(str(self.wallet), f"Wallet of {self.user.email}")


class WalletTransactionModelTest(TestCase):
    """Test cases for the WalletTransaction model."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test currency
        self.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test wallet
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('500.00'),
            currency=self.currency,
            is_active=True
        )
        
        # Create test wallet transaction
        self.transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('100.00'),
            transaction_type='CREDIT',
            description='Wallet funding',
            balance_after_transaction=Decimal('600.00'),
            reference_id='ref_12345'
        )
    
    def test_wallet_transaction_creation(self):
        """Test that a wallet transaction can be created."""
        self.assertEqual(self.transaction.wallet, self.wallet)
        self.assertEqual(self.transaction.amount, Decimal('100.00'))
        self.assertEqual(self.transaction.transaction_type, 'CREDIT')
        self.assertEqual(self.transaction.description, 'Wallet funding')
        self.assertEqual(self.transaction.balance_after_transaction, Decimal('600.00'))
        self.assertEqual(self.transaction.reference_id, 'ref_12345')
    
    def test_wallet_transaction_str_representation(self):
        """Test the string representation of a wallet transaction."""
        self.assertEqual(str(self.transaction), f"Credit of {self.transaction.amount} for {self.user.email}")


class GiftCardModelTest(TestCase):
    """Test cases for the GiftCard model."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test currency
        self.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test gift card
        self.gift_card = GiftCard.objects.create(
            code='GIFT-1234-5678-9012',
            initial_balance=Decimal('100.00'),
            current_balance=Decimal('75.00'),
            currency=self.currency,
            issued_to=self.user,
            purchased_by=self.user,
            status='ACTIVE',
            expiry_date=timezone.now().date() + timezone.timedelta(days=365)
        )
    
    def test_gift_card_creation(self):
        """Test that a gift card can be created."""
        self.assertEqual(self.gift_card.code, 'GIFT-1234-5678-9012')
        self.assertEqual(self.gift_card.initial_balance, Decimal('100.00'))
        self.assertEqual(self.gift_card.current_balance, Decimal('75.00'))
        self.assertEqual(self.gift_card.currency, self.currency)
        self.assertEqual(self.gift_card.issued_to, self.user)
        self.assertEqual(self.gift_card.purchased_by, self.user)
        self.assertEqual(self.gift_card.status, 'ACTIVE')
    
    def test_gift_card_str_representation(self):
        """Test the string representation of a gift card."""
        self.assertEqual(str(self.gift_card), f"Gift Card {self.gift_card.code} - {self.gift_card.current_balance}")


class GiftCardTransactionModelTest(TestCase):
    """Test cases for the GiftCardTransaction model."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test currency
        self.currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test gift card
        self.gift_card = GiftCard.objects.create(
            code='GIFT-1234-5678-9012',
            initial_balance=Decimal('100.00'),
            current_balance=Decimal('75.00'),
            currency=self.currency,
            issued_to=self.user,
            purchased_by=self.user,
            status='ACTIVE',
            expiry_date=timezone.now().date() + timezone.timedelta(days=365)
        )
        
        # Create test gift card transaction
        self.transaction = GiftCardTransaction.objects.create(
            gift_card=self.gift_card,
            amount=Decimal('25.00'),
            balance_after_transaction=Decimal('75.00'),
            description='Purchase payment'
        )
    
    def test_gift_card_transaction_creation(self):
        """Test that a gift card transaction can be created."""
        self.assertEqual(self.transaction.gift_card, self.gift_card)
        self.assertEqual(self.transaction.amount, Decimal('25.00'))
        self.assertEqual(self.transaction.balance_after_transaction, Decimal('75.00'))
        self.assertEqual(self.transaction.description, 'Purchase payment')
    
    def test_gift_card_transaction_str_representation(self):
        """Test the string representation of a gift card transaction."""
        self.assertEqual(str(self.transaction), f"Gift Card Transaction of {self.transaction.amount} for {self.gift_card.code}")