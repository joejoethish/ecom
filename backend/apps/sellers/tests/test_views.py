"""
Tests for seller views.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
import uuid

from ..models import SellerProfile, SellerKYC, SellerBankAccount, SellerPayoutHistory

User = get_user_model()


class SellerRegistrationViewTest(TestCase):
    """Test cases for the seller registration view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.register_url = reverse('seller-register')
    
    def test_seller_registration(self):
        """Test that a user can register as a seller."""
        data = {
            'business_name': 'Test Business',
            'business_type': 'INDIVIDUAL',
            'tax_id': 'TAX123456',
            'gstin': 'GSTIN123456789',
            'pan_number': 'ABCDE1234F',
            'description': 'Test business description',
            'address': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'Test Country',
            'postal_code': '12345',
            'phone_number': '1234567890',
            'email': 'business@example.com'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the seller profile was created
        self.assertTrue(SellerProfile.objects.filter(user=self.user).exists())
        
        # Check that the user type was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, 'seller')
    
    def test_seller_registration_already_has_profile(self):
        """Test that a user cannot register as a seller if they already have a profile."""
        # Create a seller profile for the user
        SellerProfile.objects.create(
            user=self.user,
            business_name='Existing Business',
            business_type='INDIVIDUAL',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            country='Test Country',
            postal_code='12345',
            phone_number='1234567890',
            email='business@example.com'
        )
        
        data = {
            'business_name': 'Test Business',
            'business_type': 'INDIVIDUAL',
            'address': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'Test Country',
            'postal_code': '12345',
            'phone_number': '1234567890',
            'email': 'business@example.com'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SellerProfileViewTest(TestCase):
    """Test cases for the seller profile view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='seller'
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            business_type='INDIVIDUAL',
            tax_id='TAX123456',
            gstin='GSTIN123456789',
            pan_number='ABCDE1234F',
            description='Test business description',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            country='Test Country',
            postal_code='12345',
            phone_number='1234567890',
            email='business@example.com'
        )
        self.client.force_authenticate(user=self.user)
        self.profile_url = reverse('seller-profile')
    
    def test_get_seller_profile(self):
        """Test that a seller can get their profile."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['business_name'], 'Test Business')
        self.assertEqual(response.data['data']['business_type'], 'INDIVIDUAL')
    
    def test_update_seller_profile(self):
        """Test that a seller can update their profile."""
        data = {
            'business_name': 'Updated Business',
            'description': 'Updated description'
        }
        
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the profile was updated
        self.seller_profile.refresh_from_db()
        self.assertEqual(self.seller_profile.business_name, 'Updated Business')
        self.assertEqual(self.seller_profile.description, 'Updated description')
    
    def test_get_profile_no_seller_profile(self):
        """Test that a user without a seller profile gets a 404."""
        # Create a new user without a seller profile
        user = User.objects.create_user(
            username='noselleruser',
            email='noseller@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SellerKYCViewSetTest(TestCase):
    """Test cases for the seller KYC viewset."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='seller'
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            business_type='INDIVIDUAL',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            country='Test Country',
            postal_code='12345',
            phone_number='1234567890',
            email='business@example.com'
        )
        
        # Create a test file
        self.test_file = SimpleUploadedFile(
            name='test_document.pdf',
            content=b'Test file content',
            content_type='application/pdf'
        )
        
        self.kyc_document = SellerKYC.objects.create(
            seller=self.seller_profile,
            document_type='ID_PROOF',
            document_number='ID12345',
            document_file=self.test_file,
            document_name='Test ID Document',
            issue_date=timezone.now().date(),
            expiry_date=(timezone.now() + timedelta(days=365)).date()
        )
        
        self.client.force_authenticate(user=self.user)
        self.kyc_list_url = reverse('seller-kyc-list')
        self.kyc_detail_url = reverse('seller-kyc-detail', args=[self.kyc_document.id])
    
    def test_list_kyc_documents(self):
        """Test that a seller can list their KYC documents."""
        response = self.client.get(self.kyc_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['document_name'], 'Test ID Document')
    
    def test_create_kyc_document(self):
        """Test that a seller can create a KYC document."""
        # Create a new test file
        test_file = SimpleUploadedFile(
            name='new_document.pdf',
            content=b'New test file content',
            content_type='application/pdf'
        )
        
        data = {
            'document_type': 'ADDRESS_PROOF',
            'document_number': 'ADDR12345',
            'document_file': test_file,
            'document_name': 'Test Address Document',
            'issue_date': timezone.now().date().isoformat(),
            'expiry_date': (timezone.now() + timedelta(days=365)).date().isoformat()
        }
        
        response = self.client.post(self.kyc_list_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the document was created
        self.assertEqual(SellerKYC.objects.count(), 2)
        self.assertTrue(SellerKYC.objects.filter(document_name='Test Address Document').exists())
    
    def test_retrieve_kyc_document(self):
        """Test that a seller can retrieve a KYC document."""
        response = self.client.get(self.kyc_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_name'], 'Test ID Document')
    
    def test_update_kyc_document(self):
        """Test that a seller can update a KYC document."""
        data = {
            'document_name': 'Updated Document Name'
        }
        
        response = self.client.patch(self.kyc_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the document was updated
        self.kyc_document.refresh_from_db()
        self.assertEqual(self.kyc_document.document_name, 'Updated Document Name')


class SellerBankAccountViewSetTest(TestCase):
    """Test cases for the seller bank account viewset."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='seller'
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            business_type='INDIVIDUAL',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            country='Test Country',
            postal_code='12345',
            phone_number='1234567890',
            email='business@example.com'
        )
        
        self.bank_account = SellerBankAccount.objects.create(
            seller=self.seller_profile,
            account_holder_name='Test User',
            bank_name='Test Bank',
            account_number='1234567890',
            ifsc_code='TESTB0001234',
            branch_name='Test Branch',
            account_type='SAVINGS',
            is_primary=True
        )
        
        self.client.force_authenticate(user=self.user)
        self.bank_list_url = reverse('seller-bank-accounts-list')
        self.bank_detail_url = reverse('seller-bank-accounts-detail', args=[self.bank_account.id])
        self.set_primary_url = reverse('seller-bank-accounts-set-primary', args=[self.bank_account.id])
    
    def test_list_bank_accounts(self):
        """Test that a seller can list their bank accounts."""
        response = self.client.get(self.bank_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['bank_name'], 'Test Bank')
    
    def test_create_bank_account(self):
        """Test that a seller can create a bank account."""
        data = {
            'account_holder_name': 'New User',
            'bank_name': 'New Bank',
            'account_number': '0987654321',
            'ifsc_code': 'NEWB0001234',
            'branch_name': 'New Branch',
            'account_type': 'CURRENT',
            'is_primary': False
        }
        
        response = self.client.post(self.bank_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the bank account was created
        self.assertEqual(SellerBankAccount.objects.count(), 2)
        self.assertTrue(SellerBankAccount.objects.filter(bank_name='New Bank').exists())
    
    def test_retrieve_bank_account(self):
        """Test that a seller can retrieve a bank account."""
        response = self.client.get(self.bank_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bank_name'], 'Test Bank')
    
    def test_update_bank_account(self):
        """Test that a seller can update a bank account."""
        data = {
            'bank_name': 'Updated Bank'
        }
        
        response = self.client.patch(self.bank_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the bank account was updated
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.bank_name, 'Updated Bank')
    
    def test_set_primary_bank_account(self):
        """Test that a seller can set a bank account as primary."""
        # Create a second bank account
        second_account = SellerBankAccount.objects.create(
            seller=self.seller_profile,
            account_holder_name='Test User',
            bank_name='Another Bank',
            account_number='0987654321',
            ifsc_code='TESTB0005678',
            branch_name='Another Branch',
            account_type='CURRENT',
            is_primary=False
        )
        
        # Set the second account as primary
        set_primary_url = reverse('seller-bank-accounts-set-primary', args=[second_account.id])
        response = self.client.post(set_primary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the second account is now primary
        second_account.refresh_from_db()
        self.bank_account.refresh_from_db()
        self.assertTrue(second_account.is_primary)
        self.assertFalse(self.bank_account.is_primary)


class SellerPayoutHistoryViewSetTest(TestCase):
    """Test cases for the seller payout history viewset."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='seller'
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            business_type='INDIVIDUAL',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            country='Test Country',
            postal_code='12345',
            phone_number='1234567890',
            email='business@example.com'
        )
        
        self.bank_account = SellerBankAccount.objects.create(
            seller=self.seller_profile,
            account_holder_name='Test User',
            bank_name='Test Bank',
            account_number='1234567890',
            ifsc_code='TESTB0001234',
            branch_name='Test Branch',
            account_type='SAVINGS',
            is_primary=True,
            verification_status='VERIFIED'
        )
        
        self.payout = SellerPayoutHistory.objects.create(
            seller=self.seller_profile,
            bank_account=self.bank_account,
            amount=1000.00,
            transaction_id=f"PO-{uuid.uuid4().hex[:8].upper()}",
            transaction_fee=20.00,
            payout_date=timezone.now(),
            status='COMPLETED',
            notes='Test payout'
        )
        
        self.client.force_authenticate(user=self.user)
        self.payout_list_url = reverse('seller-payouts-list')
        self.payout_detail_url = reverse('seller-payouts-detail', args=[self.payout.id])
    
    def test_list_payouts(self):
        """Test that a seller can list their payouts."""
        response = self.client.get(self.payout_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], '1000.00')
    
    def test_retrieve_payout(self):
        """Test that a seller can retrieve a payout."""
        response = self.client.get(self.payout_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '1000.00')
        self.assertEqual(response.data['status'], 'COMPLETED')


class AdminSellerViewSetTest(TestCase):
    """Test cases for the admin seller viewset."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create an admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            user_type='admin'
        )
        
        # Create a seller user
        self.seller_user = User.objects.create_user(
            username='selleruser',
            email='seller@example.com',
            password='sellerpass123',
            user_type='seller'
        )
        
        # Create a seller profile
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            business_name='Test Business',
            business_type='INDIVIDUAL',
            address='123 Test Street',
            city='Test City',
            state='Test State',
            country='Test Country',
            postal_code='12345',
            phone_number='1234567890',
            email='business@example.com'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        self.admin_seller_list_url = reverse('admin-sellers-list')
        self.admin_seller_detail_url = reverse('admin-sellers-detail', args=[self.seller_profile.id])
        self.verify_url = reverse('admin-sellers-verify', args=[self.seller_profile.id])
        self.reject_url = reverse('admin-sellers-reject', args=[self.seller_profile.id])
        self.suspend_url = reverse('admin-sellers-suspend', args=[self.seller_profile.id])
    
    def test_list_sellers(self):
        """Test that an admin can list all sellers."""
        response = self.client.get(self.admin_seller_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['business_name'], 'Test Business')
    
    def test_retrieve_seller(self):
        """Test that an admin can retrieve a seller."""
        response = self.client.get(self.admin_seller_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['business_name'], 'Test Business')
    
    def test_verify_seller(self):
        """Test that an admin can verify a seller."""
        data = {
            'verification_notes': 'Verified by admin'
        }
        
        response = self.client.post(self.verify_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the seller was verified
        self.seller_profile.refresh_from_db()
        self.assertEqual(self.seller_profile.verification_status, 'VERIFIED')
        self.assertEqual(self.seller_profile.verification_notes, 'Verified by admin')
        self.assertIsNotNone(self.seller_profile.verified_at)
        self.assertEqual(self.seller_profile.verified_by, self.admin_user)
    
    def test_reject_seller(self):
        """Test that an admin can reject a seller."""
        data = {
            'rejection_reason': 'Incomplete information'
        }
        
        response = self.client.post(self.reject_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the seller was rejected
        self.seller_profile.refresh_from_db()
        self.assertEqual(self.seller_profile.verification_status, 'REJECTED')
        self.assertEqual(self.seller_profile.verification_notes, 'Incomplete information')
        self.assertIsNotNone(self.seller_profile.verified_at)
        self.assertEqual(self.seller_profile.verified_by, self.admin_user)
    
    def test_suspend_seller(self):
        """Test that an admin can suspend a seller."""
        data = {
            'suspension_reason': 'Policy violation'
        }
        
        response = self.client.post(self.suspend_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the seller was suspended
        self.seller_profile.refresh_from_db()
        self.assertEqual(self.seller_profile.verification_status, 'SUSPENDED')
        self.assertEqual(self.seller_profile.verification_notes, 'Policy violation')
        self.assertIsNotNone(self.seller_profile.verified_at)
        self.assertEqual(self.seller_profile.verified_by, self.admin_user)
        self.assertFalse(self.seller_profile.is_active)