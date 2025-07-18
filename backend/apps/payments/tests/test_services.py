"""
Tests for payment services.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.orders.models import Order
from apps.payments.models import (
    Currency, PaymentMethod, Payment, Refund,
    Wallet, WalletTransaction, GiftCard, GiftCardTransaction
)
from apps.payments.services import (
    CurrencyService, PaymentService, WalletService, GiftCardService
)
from core.exceptions import PaymentGatewayError, InsufficientFundsError

User = get_user_model()


class CurrencyServiceTest(TestCase):
    """Test cases for the CurrencyService."""
    
    def setUp(self):
        # Create test currencies
        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        self.eur = Currency.objects.create(
            code='EUR',
            name='Euro',
            symbol='€',
            exchange_rate=Decimal('0.85'),
            is_active=True
        )
        
        self.inr = Currency.objects.create(
            code='INR',
            name='Indian Rupee',
            symbol='₹',
            exchange_rate=Decimal('75.0'),
            is_active=True
        )
    
    def test_get_exchange_rate(self):
        """Test getting exchange rates between currencies."""
        # Same currency should return 1.0
        self.assertEqual(
            CurrencyService.get_exchange_rate('USD', 'USD'),
            Decimal('1.0')
        )
        
        # USD to EUR
        self.assertEqual(
            CurrencyService.get_exchange_rate('USD', 'EUR'),
            Decimal('0.85')
        )
        
        # EUR to USD
        self.assertAlmostEqual(
            float(CurrencyService.get_exchange_rate('EUR', 'USD')),
            float(Decimal('1.0') / Decimal('0.85')),
            places=4
        )
        
        # USD to INR
        self.assertEqual(
            CurrencyService.get_exchange_rate('USD', 'INR'),
            Decimal('75.0')
        )
        
        # EUR to INR
        expected_rate = Decimal('75.0') / Decimal('0.85')
        actual_rate = CurrencyService.get_exchange_rate('EUR', 'INR')
        self.assertAlmostEqual(float(expected_rate), float(actual_rate), places=4)
    
    def test_convert_amount(self):
        """Test converting amounts between currencies."""
        # Same currency
        self.assertEqual(
            CurrencyService.convert_amount(Decimal('100.0'), 'USD', 'USD'),
            Decimal('100.0')
        )
        
        # USD to EUR
        self.assertEqual(
            CurrencyService.convert_amount(Decimal('100.0'), 'USD', 'EUR'),
            Decimal('85.0')
        )
        
        # EUR to USD
        expected_amount = Decimal('100.0') * (Decimal('1.0') / Decimal('0.85'))
        actual_amount = CurrencyService.convert_amount(Decimal('100.0'), 'EUR', 'USD')
        self.assertAlmostEqual(float(expected_amount), float(actual_amount), places=4)
        
        # USD to INR
        self.assertEqual(
            CurrencyService.convert_amount(Decimal('100.0'), 'USD', 'INR'),
            Decimal('7500.0')
        )


class PaymentServiceTest(TestCase):
    """Test cases for the PaymentService."""
    
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
        
        # Create test currencies
        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test payment methods
        self.card_payment = PaymentMethod.objects.create(
            name='Credit Card',
            method_type='CARD',
            gateway='STRIPE',
            is_active=True,
            processing_fee_percentage=Decimal('2.5'),
            processing_fee_fixed=Decimal('0.30')
        )
        
        self.wallet_payment = PaymentMethod.objects.create(
            name='Wallet',
            method_type='WALLET',
            gateway='INTERNAL',
            is_active=True
        )
        
        self.gift_card_payment = PaymentMethod.objects.create(
            name='Gift Card',
            method_type='GIFT_CARD',
            gateway='INTERNAL',
            is_active=True
        )
        
        # Create test wallet
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('500.00'),
            currency=self.usd,
            is_active=True
        )
        
        # Create test gift card
        self.gift_card = GiftCard.objects.create(
            code='GIFT-1234-5678-9012',
            initial_balance=Decimal('200.00'),
            current_balance=Decimal('200.00'),
            currency=self.usd,
            issued_to=self.user,
            purchased_by=self.user,
            status='ACTIVE',
            expiry_date=timezone.now().date() + timezone.timedelta(days=365)
        )
    
    @patch('apps.payments.services.PaymentGatewayFactory.get_gateway')
    def test_create_payment_with_stripe(self, mock_get_gateway):
        """Test creating a payment with Stripe gateway."""
        # Mock the gateway
        mock_gateway = MagicMock()
        mock_gateway.create_payment.return_value = {
            'gateway_payment_id': 'pi_12345',
            'client_secret': 'cs_12345',
            'amount': 100.0,
            'currency': 'USD',
            'gateway_data': {
                'id': 'pi_12345',
                'status': 'requires_payment_method'
            }
        }
        mock_get_gateway.return_value = mock_gateway
        
        # Create payment
        result = PaymentService.create_payment(
            order_id=self.order.id,
            user_id=self.user.id,
            amount=Decimal('100.00'),
            currency_code='USD',
            payment_method_id=self.card_payment.id,
            metadata={'customer_name': 'Test User'}
        )
        
        # Check that gateway was called correctly
        mock_get_gateway.assert_called_once_with('STRIPE')
        mock_gateway.create_payment.assert_called_once()
        
        # Check result
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(result['amount'], 100.0)
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['payment_method'], 'CARD')
        self.assertEqual(result['gateway_data']['gateway_payment_id'], 'pi_12345')
        
        # Check that payment was created in database
        payment = Payment.objects.get(order_id=self.order.id)
        self.assertEqual(payment.status, 'PENDING')
        self.assertEqual(payment.amount, Decimal('100.00'))
        self.assertEqual(payment.gateway_payment_id, 'pi_12345')
    
    def test_create_payment_with_wallet(self):
        """Test creating a payment with wallet."""
        # Create payment
        result = PaymentService.create_payment(
            order_id=self.order.id,
            user_id=self.user.id,
            amount=Decimal('50.00'),
            currency_code='USD',
            payment_method_id=self.wallet_payment.id
        )
        
        # Check result
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['amount'], 50.0)
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['payment_method'], 'WALLET')
        self.assertEqual(result['wallet_balance'], 450.0)
        
        # Check that payment was created in database
        payment = Payment.objects.get(order_id=self.order.id)
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.amount, Decimal('50.00'))
        
        # Check that wallet was updated
        wallet = Wallet.objects.get(id=self.wallet.id)
        self.assertEqual(wallet.balance, Decimal('450.00'))
        
        # Check that wallet transaction was created
        transaction = WalletTransaction.objects.get(wallet=wallet, payment=payment)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.transaction_type, 'DEBIT')
        self.assertEqual(transaction.balance_after_transaction, Decimal('450.00'))
    
    def test_create_payment_with_insufficient_wallet_balance(self):
        """Test creating a payment with insufficient wallet balance."""
        # Try to create payment with amount greater than wallet balance
        with self.assertRaises(InsufficientFundsError):
            PaymentService.create_payment(
                order_id=self.order.id,
                user_id=self.user.id,
                amount=Decimal('600.00'),  # Wallet only has 500.00
                currency_code='USD',
                payment_method_id=self.wallet_payment.id
            )
        
        # Check that wallet was not updated
        wallet = Wallet.objects.get(id=self.wallet.id)
        self.assertEqual(wallet.balance, Decimal('500.00'))
    
    def test_create_payment_with_gift_card(self):
        """Test creating a payment with gift card."""
        # Create payment
        result = PaymentService.create_payment(
            order_id=self.order.id,
            user_id=self.user.id,
            amount=Decimal('50.00'),
            currency_code='USD',
            payment_method_id=self.gift_card_payment.id,
            metadata={'gift_card_code': 'GIFT-1234-5678-9012'}
        )
        
        # Check result
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['amount'], 50.0)
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['payment_method'], 'GIFT_CARD')
        self.assertEqual(result['gift_card_balance'], 150.0)
        
        # Check that payment was created in database
        payment = Payment.objects.get(order_id=self.order.id)
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.amount, Decimal('50.00'))
        
        # Check that gift card was updated
        gift_card = GiftCard.objects.get(id=self.gift_card.id)
        self.assertEqual(gift_card.current_balance, Decimal('150.00'))
        
        # Check that gift card transaction was created
        transaction = GiftCardTransaction.objects.get(gift_card=gift_card, payment=payment)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.balance_after_transaction, Decimal('150.00'))
    
    def test_create_payment_with_insufficient_gift_card_balance(self):
        """Test creating a payment with insufficient gift card balance."""
        # Try to create payment with amount greater than gift card balance
        with self.assertRaises(InsufficientFundsError):
            PaymentService.create_payment(
                order_id=self.order.id,
                user_id=self.user.id,
                amount=Decimal('300.00'),  # Gift card only has 200.00
                currency_code='USD',
                payment_method_id=self.gift_card_payment.id,
                metadata={'gift_card_code': 'GIFT-1234-5678-9012'}
            )
        
        # Check that gift card was not updated
        gift_card = GiftCard.objects.get(id=self.gift_card.id)
        self.assertEqual(gift_card.current_balance, Decimal('200.00'))
    
    @patch('apps.payments.services.PaymentGatewayFactory.get_gateway')
    def test_verify_payment(self, mock_get_gateway):
        """Test verifying a payment."""
        # Create a payment
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.card_payment,
            amount=Decimal('100.00'),
            currency=self.usd,
            status='PENDING',
            gateway_order_id='or_12345'
        )
        
        # Mock the gateway
        mock_gateway = MagicMock()
        mock_gateway.verify_payment.return_value = True
        mock_get_gateway.return_value = mock_gateway
        
        # Verify payment
        result = PaymentService.verify_payment(
            payment_id=payment.id,
            gateway_payment_id='pi_12345',
            gateway_signature='sig_12345',
            metadata={'razorpay_order_id': 'or_12345'}
        )
        
        # Check that gateway was called correctly
        mock_get_gateway.assert_called_once_with('STRIPE')
        mock_gateway.verify_payment.assert_called_once_with(
            'pi_12345',
            'sig_12345',
            {'razorpay_order_id': 'or_12345'}
        )
        
        # Check result
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertTrue(result['verified'])
        
        # Check that payment was updated in database
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.gateway_payment_id, 'pi_12345')
        self.assertEqual(payment.gateway_signature, 'sig_12345')
    
    @patch('apps.payments.services.PaymentGatewayFactory.get_gateway')
    def test_verify_payment_failure(self, mock_get_gateway):
        """Test verifying a payment that fails verification."""
        # Create a payment
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.card_payment,
            amount=Decimal('100.00'),
            currency=self.usd,
            status='PENDING',
            gateway_order_id='or_12345'
        )
        
        # Mock the gateway
        mock_gateway = MagicMock()
        mock_gateway.verify_payment.return_value = False
        mock_get_gateway.return_value = mock_gateway
        
        # Verify payment
        result = PaymentService.verify_payment(
            payment_id=payment.id,
            gateway_payment_id='pi_12345',
            gateway_signature='sig_12345',
            metadata={'razorpay_order_id': 'or_12345'}
        )
        
        # Check result
        self.assertEqual(result['status'], 'FAILED')
        self.assertFalse(result['verified'])
        
        # Check that payment was updated in database
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'FAILED')
    
    @patch('apps.payments.services.PaymentGatewayFactory.get_gateway')
    def test_process_refund(self, mock_get_gateway):
        """Test processing a refund."""
        # Create a completed payment
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.card_payment,
            amount=Decimal('100.00'),
            currency=self.usd,
            status='COMPLETED',
            gateway_payment_id='pi_12345'
        )
        
        # Mock the gateway
        mock_gateway = MagicMock()
        mock_gateway.process_refund.return_value = {
            'refund_id': 're_12345',
            'amount': 50.0,
            'status': 'succeeded',
            'gateway_data': {
                'id': 're_12345',
                'status': 'succeeded'
            }
        }
        mock_get_gateway.return_value = mock_gateway
        
        # Process refund
        result = PaymentService.process_refund(
            payment_id=payment.id,
            amount=Decimal('50.00'),
            reason='Customer request',
            metadata={'customer_name': 'Test User'}
        )
        
        # Check that gateway was called correctly
        mock_get_gateway.assert_called_once_with('STRIPE')
        mock_gateway.process_refund.assert_called_once()
        
        # Check result
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['amount'], 50.0)
        self.assertEqual(result['gateway_data']['refund_id'], 're_12345')
        
        # Check that refund was created in database
        refund = Refund.objects.get(payment=payment)
        self.assertEqual(refund.status, 'COMPLETED')
        self.assertEqual(refund.amount, Decimal('50.00'))
        self.assertEqual(refund.reason, 'Customer request')
        self.assertEqual(refund.transaction_id, 're_12345')
        
        # Check that payment status was updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'PARTIALLY_REFUNDED')
    
    def test_process_refund_with_wallet_payment(self):
        """Test processing a refund for a wallet payment."""
        # Create a completed wallet payment
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.wallet_payment,
            amount=Decimal('50.00'),
            currency=self.usd,
            status='COMPLETED'
        )
        
        # Update wallet balance to simulate the payment
        self.wallet.balance = Decimal('450.00')
        self.wallet.save()
        
        # Process refund
        result = PaymentService.process_refund(
            payment_id=payment.id,
            amount=Decimal('50.00'),
            reason='Customer request'
        )
        
        # Check result
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['amount'], 50.0)
        self.assertEqual(result['wallet_balance'], 500.0)
        
        # Check that refund was created in database
        refund = Refund.objects.get(payment=payment)
        self.assertEqual(refund.status, 'COMPLETED')
        self.assertEqual(refund.amount, Decimal('50.00'))
        self.assertEqual(refund.reason, 'Customer request')
        
        # Check that payment status was updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'REFUNDED')
        
        # Check that wallet was updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('500.00'))
        
        # Check that wallet transaction was created
        transaction = WalletTransaction.objects.filter(
            wallet=self.wallet,
            transaction_type='REFUND',
            amount=Decimal('50.00')
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.balance_after_transaction, Decimal('500.00'))


class WalletServiceTest(TestCase):
    """Test cases for the WalletService."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test currencies
        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test payment methods
        self.card_payment = PaymentMethod.objects.create(
            name='Credit Card',
            method_type='CARD',
            gateway='STRIPE',
            is_active=True
        )
        
        # Create test wallet
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('100.00'),
            currency=self.usd,
            is_active=True
        )
    
    @patch('apps.payments.services.PaymentService.create_payment')
    def test_add_funds(self, mock_create_payment):
        """Test adding funds to a wallet."""
        # Mock the payment service
        mock_create_payment.return_value = {
            'payment_id': 'pay_12345',
            'status': 'PENDING',
            'amount': 50.0,
            'currency': 'USD',
            'payment_method': 'CARD',
            'gateway_data': {
                'gateway_payment_id': 'pi_12345',
                'client_secret': 'cs_12345'
            }
        }
        
        # Add funds
        result = WalletService.add_funds(
            user_id=self.user.id,
            amount=Decimal('50.00'),
            currency_code='USD',
            payment_method_id=self.card_payment.id,
            metadata={'customer_name': 'Test User'}
        )
        
        # Check that payment service was called correctly
        mock_create_payment.assert_called_once()
        
        # Check result
        self.assertEqual(result['wallet_id'], str(self.wallet.id))
        self.assertEqual(result['current_balance'], 100.0)
        self.assertEqual(result['payment']['payment_id'], 'pay_12345')
        self.assertEqual(result['payment']['amount'], 50.0)
    
    @patch('apps.payments.services.PaymentService.verify_payment')
    def test_complete_add_funds(self, mock_verify_payment):
        """Test completing the process of adding funds to a wallet."""
        # Create a pending payment
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.card_payment,
            amount=Decimal('50.00'),
            currency=self.usd,
            status='PENDING',
            gateway_payment_id='pi_12345'
        )
        
        # Mock the payment service
        mock_verify_payment.return_value = {
            'payment_id': str(payment.id),
            'status': 'COMPLETED',
            'verified': True
        }
        
        # Complete add funds
        result = WalletService.complete_add_funds(
            payment_id=payment.id,
            gateway_payment_id='pi_12345',
            gateway_signature='sig_12345'
        )
        
        # Check that payment service was called correctly
        mock_verify_payment.assert_called_once_with(
            payment.id,
            'pi_12345',
            'sig_12345',
            None
        )
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['wallet_id'], str(self.wallet.id))
        self.assertEqual(result['new_balance'], 150.0)
        self.assertEqual(result['added_amount'], 50.0)
        
        # Check that wallet was updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('150.00'))
        
        # Check that wallet transaction was created
        transaction = WalletTransaction.objects.get(wallet=self.wallet, payment=payment)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.transaction_type, 'CREDIT')
        self.assertEqual(transaction.balance_after_transaction, Decimal('150.00'))


class GiftCardServiceTest(TestCase):
    """Test cases for the GiftCardService."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test currencies
        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('1.0'),
            is_active=True
        )
        
        # Create test payment methods
        self.card_payment = PaymentMethod.objects.create(
            name='Credit Card',
            method_type='CARD',
            gateway='STRIPE',
            is_active=True
        )
    
    def test_create_gift_card(self):
        """Test creating a gift card."""
        # Create gift card
        expiry_date = timezone.now().date() + timezone.timedelta(days=365)
        result = GiftCardService.create_gift_card(
            initial_balance=Decimal('100.00'),
            currency_code='USD',
            expiry_date=expiry_date,
            purchased_by_id=self.user.id,
            issued_to_id=self.user.id
        )
        
        # Check result
        self.assertIn('gift_card_id', result)
        self.assertIn('code', result)
        self.assertEqual(result['balance'], 100.0)
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['expiry_date'], expiry_date.isoformat())
        
        # Check that gift card was created in database
        gift_card = GiftCard.objects.get(id=result['gift_card_id'])
        self.assertEqual(gift_card.code, result['code'])
        self.assertEqual(gift_card.initial_balance, Decimal('100.00'))
        self.assertEqual(gift_card.current_balance, Decimal('100.00'))
        self.assertEqual(gift_card.currency, self.usd)
        self.assertEqual(gift_card.purchased_by, self.user)
        self.assertEqual(gift_card.issued_to, self.user)
        self.assertEqual(gift_card.status, 'ACTIVE')
        self.assertEqual(gift_card.expiry_date, expiry_date)
    
    def test_get_gift_card_details(self):
        """Test getting gift card details."""
        # Create a gift card
        expiry_date = timezone.now().date() + timezone.timedelta(days=365)
        gift_card = GiftCard.objects.create(
            code='GIFT-1234-5678-9012',
            initial_balance=Decimal('100.00'),
            current_balance=Decimal('75.00'),
            currency=self.usd,
            issued_to=self.user,
            purchased_by=self.user,
            status='ACTIVE',
            expiry_date=expiry_date
        )
        
        # Get gift card details
        result = GiftCardService.get_gift_card_details('GIFT-1234-5678-9012')
        
        # Check result
        self.assertEqual(result['gift_card_id'], str(gift_card.id))
        self.assertEqual(result['code'], 'GIFT-1234-5678-9012')
        self.assertEqual(result['balance'], 75.0)
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['expiry_date'], expiry_date.isoformat())
    
    def test_get_gift_card_details_invalid_code(self):
        """Test getting details of an invalid gift card."""
        with self.assertRaises(PaymentGatewayError):
            GiftCardService.get_gift_card_details('INVALID-CODE')
    
    @patch('apps.payments.services.PaymentService.create_payment')
    def test_purchase_gift_card(self, mock_create_payment):
        """Test purchasing a gift card."""
        # Mock the payment service
        mock_create_payment.return_value = {
            'payment_id': 'pay_12345',
            'status': 'PENDING',
            'amount': 100.0,
            'currency': 'USD',
            'payment_method': 'CARD',
            'gateway_data': {
                'gateway_payment_id': 'pi_12345',
                'client_secret': 'cs_12345'
            }
        }
        
        # Purchase gift card
        result = GiftCardService.purchase_gift_card(
            user_id=self.user.id,
            amount=Decimal('100.00'),
            currency_code='USD',
            payment_method_id=self.card_payment.id,
            recipient_email='recipient@example.com',
            expiry_days=180
        )
        
        # Check that payment service was called correctly
        mock_create_payment.assert_called_once()
        
        # Check result
        self.assertEqual(result['payment']['payment_id'], 'pay_12345')
        self.assertEqual(result['payment']['amount'], 100.0)
        self.assertIn('expiry_date', result)
    
    @patch('apps.payments.services.PaymentService.verify_payment')
    @patch('apps.payments.services.GiftCardService.create_gift_card')
    def test_complete_gift_card_purchase(self, mock_create_gift_card, mock_verify_payment):
        """Test completing the process of purchasing a gift card."""
        # Create a pending payment
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.card_payment,
            amount=Decimal('100.00'),
            currency=self.usd,
            status='PENDING',
            gateway_payment_id='pi_12345',
            gateway_response={
                'metadata': {
                    'recipient_email': 'recipient@example.com',
                    'expiry_days': 180
                }
            }
        )
        
        # Mock the payment service
        mock_verify_payment.return_value = {
            'payment_id': str(payment.id),
            'status': 'COMPLETED',
            'verified': True
        }
        
        # Mock the gift card service
        mock_create_gift_card.return_value = {
            'gift_card_id': 'gc_12345',
            'code': 'GIFT-1234-5678-9012',
            'balance': 100.0,
            'currency': 'USD',
            'expiry_date': (timezone.now().date() + timezone.timedelta(days=180)).isoformat()
        }
        
        # Complete gift card purchase
        result = GiftCardService.complete_gift_card_purchase(
            payment_id=payment.id,
            gateway_payment_id='pi_12345',
            gateway_signature='sig_12345'
        )
        
        # Check that payment service was called correctly
        mock_verify_payment.assert_called_once_with(
            payment.id,
            'pi_12345',
            'sig_12345',
            None
        )
        
        # Check that gift card service was called correctly
        mock_create_gift_card.assert_called_once()
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['gift_card']['gift_card_id'], 'gc_12345')
        self.assertEqual(result['gift_card']['code'], 'GIFT-1234-5678-9012')
        self.assertEqual(result['gift_card']['balance'], 100.0)