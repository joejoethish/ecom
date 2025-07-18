"""
Tests for payment views.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.orders.models import Order
from apps.payments.models import (
    Currency, PaymentMethod, Payment, Refund,
    Wallet, WalletTransaction, GiftCard, GiftCardTransaction
)

User = get_user_model()


class PaymentAPITest(APITestCase):
    """Test cases for the Payment API."""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
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
        
        self.eur = Currency.objects.create(
            code='EUR',
            name='Euro',
            symbol='€',
            exchange_rate=Decimal('0.85'),
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
        
        # Create test payment
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.card_payment,
            amount=Decimal('100.00'),
            currency=self.usd,
            status='PENDING',
            gateway_payment_id='pi_12345'
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
    
    def test_list_currencies(self):
        """Test listing currencies."""
        url = reverse('payments:currency-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # USD and EUR
    
    def test_list_payment_methods(self):
        """Test listing payment methods."""
        url = reverse('payments:paymentmethod-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Card and Wallet
    
    def test_list_payments(self):
        """Test listing payments."""
        url = reverse('payments:payment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_retrieve_payment(self):
        """Test retrieving a payment."""
        url = reverse('payments:payment-detail', args=[self.payment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.payment.id))
    
    @patch('apps.payments.services.PaymentService.create_payment')
    def test_create_payment(self, mock_create_payment):
        """Test creating a payment."""
        mock_create_payment.return_value = {
            'payment_id': str(self.payment.id),
            'status': 'PENDING',
            'amount': 100.0,
            'currency': 'USD',
            'payment_method': 'CARD',
            'gateway_data': {
                'gateway_payment_id': 'pi_12345',
                'client_secret': 'cs_12345'
            }
        }
        
        url = reverse('payments:payment-create-payment')
        data = {
            'order_id': str(self.order.id),
            'amount': '100.00',
            'currency_code': 'USD',
            'payment_method_id': str(self.card_payment.id)
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['payment_id'], str(self.payment.id))
        
        mock_create_payment.assert_called_once_with(
            order_id=self.order.id,
            user_id=self.user.id,
            amount=Decimal('100.00'),
            currency_code='USD',
            payment_method_id=self.card_payment.id,
            metadata=None
        )
    
    @patch('apps.payments.services.PaymentService.verify_payment')
    def test_verify_payment(self, mock_verify_payment):
        """Test verifying a payment."""
        mock_verify_payment.return_value = {
            'payment_id': str(self.payment.id),
            'status': 'COMPLETED',
            'verified': True
        }
        
        url = reverse('payments:payment-verify-payment')
        data = {
            'payment_id': str(self.payment.id),
            'gateway_payment_id': 'pi_12345',
            'gateway_signature': 'sig_12345'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'COMPLETED')
        self.assertTrue(response.data['verified'])
        
        mock_verify_payment.assert_called_once_with(
            payment_id=self.payment.id,
            gateway_payment_id='pi_12345',
            gateway_signature='sig_12345',
            metadata=None
        )
    
    @patch('apps.payments.services.PaymentService.get_payment_status')
    def test_get_payment_status(self, mock_get_payment_status):
        """Test getting payment status."""
        mock_get_payment_status.return_value = {
            'payment_id': str(self.payment.id),
            'status': 'COMPLETED',
            'amount': 100.0,
            'currency': 'USD',
            'payment_method': 'CARD'
        }
        
        url = reverse('payments:payment-status', args=[self.payment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'COMPLETED')
        
        mock_get_payment_status.assert_called_once_with(self.payment.id)
    
    @patch('apps.payments.views.PaymentGatewayFactory.get_gateway')
    def test_generate_payment_link(self, mock_get_gateway):
        """Test generating a payment link."""
        mock_gateway = MagicMock()
        mock_gateway.generate_payment_link.return_value = 'https://example.com/pay/12345'
        mock_get_gateway.return_value = mock_gateway
        
        url = reverse('payments:payment-generate-payment-link')
        data = {
            'order_id': str(self.order.id),
            'amount': '100.00',
            'currency_code': 'USD',
            'payment_method_id': str(self.card_payment.id),
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['payment_link'], 'https://example.com/pay/12345')
        
        mock_get_gateway.assert_called_once_with('STRIPE')
        mock_gateway.generate_payment_link.assert_called_once()
    
    @patch('apps.payments.services.PaymentService.process_refund')
    def test_create_refund(self, mock_process_refund):
        """Test creating a refund."""
        mock_process_refund.return_value = {
            'refund_id': 'ref_12345',
            'payment_id': str(self.payment.id),
            'amount': 50.0,
            'status': 'COMPLETED'
        }
        
        url = reverse('payments:refund-create-refund')
        data = {
            'payment_id': str(self.payment.id),
            'amount': '50.00',
            'reason': 'Customer request'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['refund_id'], 'ref_12345')
        
        mock_process_refund.assert_called_once_with(
            payment_id=self.payment.id,
            amount=Decimal('50.00'),
            reason='Customer request',
            metadata=None
        )
    
    def test_get_wallet(self):
        """Test getting the user's wallet."""
        url = reverse('payments:wallet-my-wallet')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.wallet.id))
        self.assertEqual(float(response.data['balance']), 500.0)
    
    @patch('apps.payments.services.WalletService.add_funds')
    def test_add_funds_to_wallet(self, mock_add_funds):
        """Test adding funds to the wallet."""
        mock_add_funds.return_value = {
            'wallet_id': str(self.wallet.id),
            'current_balance': 500.0,
            'payment': {
                'payment_id': 'pay_12345',
                'status': 'PENDING',
                'amount': 100.0,
                'currency': 'USD',
                'payment_method': 'CARD'
            }
        }
        
        url = reverse('payments:wallet-add-funds')
        data = {
            'amount': '100.00',
            'currency_code': 'USD',
            'payment_method_id': str(self.card_payment.id)
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['wallet_id'], str(self.wallet.id))
        
        mock_add_funds.assert_called_once_with(
            user_id=self.user.id,
            amount=Decimal('100.00'),
            currency_code='USD',
            payment_method_id=self.card_payment.id,
            metadata=None
        )
    
    def test_get_gift_cards(self):
        """Test listing gift cards."""
        url = reverse('payments:gift-card-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    @patch('apps.payments.services.GiftCardService.get_gift_card_details')
    def test_check_gift_card(self, mock_get_gift_card_details):
        """Test checking a gift card."""
        mock_get_gift_card_details.return_value = {
            'gift_card_id': str(self.gift_card.id),
            'code': 'GIFT-1234-5678-9012',
            'balance': 200.0,
            'currency': 'USD',
            'expiry_date': self.gift_card.expiry_date.isoformat()
        }
        
        url = reverse('payments:gift-card-check')
        data = {
            'code': 'GIFT-1234-5678-9012'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'GIFT-1234-5678-9012')
        self.assertEqual(response.data['balance'], 200.0)
        
        mock_get_gift_card_details.assert_called_once_with('GIFT-1234-5678-9012')
    
    @patch('apps.payments.services.GiftCardService.purchase_gift_card')
    def test_purchase_gift_card(self, mock_purchase_gift_card):
        """Test purchasing a gift card."""
        expiry_date = (timezone.now().date() + timezone.timedelta(days=180)).isoformat()
        mock_purchase_gift_card.return_value = {
            'payment': {
                'payment_id': 'pay_12345',
                'status': 'PENDING',
                'amount': 100.0,
                'currency': 'USD',
                'payment_method': 'CARD'
            },
            'expiry_date': expiry_date
        }
        
        url = reverse('payments:gift-card-purchase')
        data = {
            'amount': '100.00',
            'currency_code': 'USD',
            'payment_method_id': str(self.card_payment.id),
            'recipient_email': 'recipient@example.com',
            'expiry_days': 180
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['payment']['payment_id'], 'pay_12345')
        self.assertEqual(response.data['expiry_date'], expiry_date)
        
        mock_purchase_gift_card.assert_called_once_with(
            user_id=self.user.id,
            amount=Decimal('100.00'),
            currency_code='USD',
            payment_method_id=self.card_payment.id,
            recipient_email='recipient@example.com',
            expiry_days=180,
            metadata=None
        )