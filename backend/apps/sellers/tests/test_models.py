"""
Tests for seller models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta

from ..models import SellerProfile, SellerKYC, SellerBankAccount, SellerPayoutHistory

User = get_user_model()


class SellerProfileModelTest(TestCase):
    """Test cases for the SellerProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
    
    def test_seller_profile_creation(self):
        """Test that a seller profile can be created."""
        self.assertEqual(self.seller_profile.business_name, 'Test Business')
        self.assertEqual(self.seller_profile.business_type, 'INDIVIDUAL')
        self.assertEqual(self.seller_profile.verification_status, 'PENDING')
        self.assertEqual(self.seller_profile.user, self.user)
        self.assertTrue(self.seller_profile.is_active)
        self.assertFalse(self.seller_profile.is_featured)
    
    def test_seller_profile_str_method(self):
        """Test the string representation of a seller profile."""
        self.assertEqual(str(self.seller_profile), 'Test Business')


class SellerKYCModelTest(TestCase):
    """Test cases for the SellerKYC model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
        
        # Create a simple test file
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
    
    def test_kyc_document_creation(self):
        """Test that a KYC document can be created."""
        self.assertEqual(self.kyc_document.document_type, 'ID_PROOF')
        self.assertEqual(self.kyc_document.document_number, 'ID12345')
        self.assertEqual(self.kyc_document.document_name, 'Test ID Document')
        self.assertEqual(self.kyc_document.verification_status, 'PENDING')
        self.assertEqual(self.kyc_document.seller, self.seller_profile)
    
    def test_kyc_document_str_method(self):
        """Test the string representation of a KYC document."""
        expected_str = f"{self.seller_profile.business_name} - ID Proof"
        self.assertEqual(str(self.kyc_document), expected_str)


class SellerBankAccountModelTest(TestCase):
    """Test cases for the SellerBankAccount model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
    
    def test_bank_account_creation(self):
        """Test that a bank account can be created."""
        self.assertEqual(self.bank_account.account_holder_name, 'Test User')
        self.assertEqual(self.bank_account.bank_name, 'Test Bank')
        self.assertEqual(self.bank_account.account_number, '1234567890')
        self.assertEqual(self.bank_account.ifsc_code, 'TESTB0001234')
        self.assertEqual(self.bank_account.account_type, 'SAVINGS')
        self.assertTrue(self.bank_account.is_primary)
        self.assertEqual(self.bank_account.verification_status, 'PENDING')
        self.assertEqual(self.bank_account.seller, self.seller_profile)
    
    def test_bank_account_str_method(self):
        """Test the string representation of a bank account."""
        expected_str = f"{self.seller_profile.business_name} - Test Bank (7890)"
        self.assertEqual(str(self.bank_account), expected_str)
    
    def test_primary_account_logic(self):
        """Test that only one account can be primary."""
        # Create a second bank account and set it as primary
        second_account = SellerBankAccount.objects.create(
            seller=self.seller_profile,
            account_holder_name='Test User',
            bank_name='Another Bank',
            account_number='0987654321',
            ifsc_code='TESTB0005678',
            branch_name='Another Branch',
            account_type='CURRENT',
            is_primary=True
        )
        
        # Refresh the first account from the database
        self.bank_account.refresh_from_db()
        
        # Check that the first account is no longer primary
        self.assertFalse(self.bank_account.is_primary)
        self.assertTrue(second_account.is_primary)


class SellerPayoutHistoryModelTest(TestCase):
    """Test cases for the SellerPayoutHistory model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
        
        self.payout = SellerPayoutHistory.objects.create(
            seller=self.seller_profile,
            bank_account=self.bank_account,
            amount=1000.00,
            transaction_id='TEST123456',
            transaction_fee=20.00,
            payout_date=timezone.now(),
            status='PENDING',
            notes='Test payout'
        )
    
    def test_payout_creation(self):
        """Test that a payout can be created."""
        self.assertEqual(self.payout.amount, 1000.00)
        self.assertEqual(self.payout.transaction_id, 'TEST123456')
        self.assertEqual(self.payout.transaction_fee, 20.00)
        self.assertEqual(self.payout.status, 'PENDING')
        self.assertEqual(self.payout.notes, 'Test payout')
        self.assertEqual(self.payout.seller, self.seller_profile)
        self.assertEqual(self.payout.bank_account, self.bank_account)
    
    def test_payout_str_method(self):
        """Test the string representation of a payout."""
        expected_str = f"{self.seller_profile.business_name} - 1000.00 (Pending)"
        self.assertEqual(str(self.payout), expected_str)