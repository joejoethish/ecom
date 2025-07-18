"""
Seller models for the ecommerce platform.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import BaseModel


class SellerProfile(BaseModel):
    """
    Seller profile model for storing business information.
    """
    BUSINESS_TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('PARTNERSHIP', 'Partnership'),
        ('LLC', 'Limited Liability Company'),
        ('CORPORATION', 'Corporation'),
        ('OTHER', 'Other'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=100, choices=BUSINESS_TYPE_CHOICES)
    tax_id = models.CharField(max_length=50, blank=True)
    gstin = models.CharField(max_length=15, blank=True, verbose_name="GSTIN")
    pan_number = models.CharField(max_length=10, blank=True, verbose_name="PAN Number")
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='sellers/logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='sellers/banners/', blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Verification fields
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES, 
        default='PENDING'
    )
    verification_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_sellers'
    )
    
    # Business metrics
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Commission percentage charged on sales"
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    def __str__(self):
        return self.business_name


class SellerKYC(BaseModel):
    """
    Seller KYC (Know Your Customer) model for document verification.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('ID_PROOF', 'ID Proof'),
        ('ADDRESS_PROOF', 'Address Proof'),
        ('BUSINESS_PROOF', 'Business Proof'),
        ('TAX_DOCUMENT', 'Tax Document'),
        ('BANK_STATEMENT', 'Bank Statement'),
        ('OTHER', 'Other'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=50)
    document_file = models.FileField(upload_to='sellers/kyc/')
    document_name = models.CharField(max_length=100)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES, 
        default='PENDING'
    )
    verification_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_kyc_documents'
    )
    
    def __str__(self):
        return f"{self.seller.business_name} - {self.get_document_type_display()}"
    
    class Meta:
        verbose_name = "Seller KYC Document"
        verbose_name_plural = "Seller KYC Documents"


class SellerBankAccount(BaseModel):
    """
    Seller bank account model for payout management.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('SAVINGS', 'Savings'),
        ('CURRENT', 'Current/Checking'),
        ('BUSINESS', 'Business'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]
    
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name='bank_accounts')
    account_holder_name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20, verbose_name="IFSC Code")
    branch_name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    is_primary = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES, 
        default='PENDING'
    )
    verification_document = models.FileField(
        upload_to='sellers/bank_verification/', 
        null=True, 
        blank=True,
        help_text="Upload a cancelled cheque or bank statement"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_bank_accounts'
    )
    
    def __str__(self):
        return f"{self.seller.business_name} - {self.bank_name} ({self.account_number[-4:]})"
    
    def save(self, *args, **kwargs):
        # If this account is set as primary, unset any other primary accounts
        if self.is_primary:
            SellerBankAccount.objects.filter(
                seller=self.seller, 
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Seller Bank Account"
        verbose_name_plural = "Seller Bank Accounts"


class SellerPayoutHistory(BaseModel):
    """
    Seller payout history model for tracking payments to sellers.
    """
    PAYOUT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name='payouts')
    bank_account = models.ForeignKey(SellerBankAccount, on_delete=models.SET_NULL, null=True, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True)
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payout_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.seller.business_name} - {self.amount} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = "Seller Payout"
        verbose_name_plural = "Seller Payouts"
        ordering = ['-payout_date']