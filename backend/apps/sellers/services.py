"""
Services for seller management and verification.
"""
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
import os
import uuid
import logging

from .models import SellerProfile, SellerKYC, SellerBankAccount, SellerPayoutHistory

logger = logging.getLogger(__name__)


class SellerVerificationService:
    """
    Service for handling seller verification processes.
    """
    
    @staticmethod
    def verify_seller_profile(seller_profile, admin_user, verification_notes=""):
        """
        Verify a seller profile.
        
        Args:
            seller_profile: The SellerProfile instance to verify
            admin_user: The admin user performing the verification
            verification_notes: Optional notes about the verification
            
        Returns:
            The updated SellerProfile instance
        """
        if not admin_user.is_staff:
            raise ValidationError("Only staff members can verify sellers")
            
        with transaction.atomic():
            seller_profile.verification_status = 'VERIFIED'
            seller_profile.verified_at = timezone.now()
            seller_profile.verified_by = admin_user
            seller_profile.verification_notes = verification_notes
            seller_profile.save()
            
            # Log the verification action
            logger.info(
                f"Seller {seller_profile.business_name} (ID: {seller_profile.id}) "
                f"verified by {admin_user.username} (ID: {admin_user.id})"
            )
            
        return seller_profile
    
    @staticmethod
    def reject_seller_profile(seller_profile, admin_user, rejection_reason):
        """
        Reject a seller profile.
        
        Args:
            seller_profile: The SellerProfile instance to reject
            admin_user: The admin user performing the rejection
            rejection_reason: The reason for rejection
            
        Returns:
            The updated SellerProfile instance
        """
        if not admin_user.is_staff:
            raise ValidationError("Only staff members can reject sellers")
            
        if not rejection_reason:
            raise ValidationError("Rejection reason is required")
            
        with transaction.atomic():
            seller_profile.verification_status = 'REJECTED'
            seller_profile.verified_at = timezone.now()
            seller_profile.verified_by = admin_user
            seller_profile.verification_notes = rejection_reason
            seller_profile.save()
            
            # Log the rejection action
            logger.info(
                f"Seller {seller_profile.business_name} (ID: {seller_profile.id}) "
                f"rejected by {admin_user.username} (ID: {admin_user.id}). "
                f"Reason: {rejection_reason}"
            )
            
        return seller_profile
    
    @staticmethod
    def suspend_seller_profile(seller_profile, admin_user, suspension_reason):
        """
        Suspend a seller profile.
        
        Args:
            seller_profile: The SellerProfile instance to suspend
            admin_user: The admin user performing the suspension
            suspension_reason: The reason for suspension
            
        Returns:
            The updated SellerProfile instance
        """
        if not admin_user.is_staff:
            raise ValidationError("Only staff members can suspend sellers")
            
        if not suspension_reason:
            raise ValidationError("Suspension reason is required")
            
        with transaction.atomic():
            seller_profile.verification_status = 'SUSPENDED'
            seller_profile.verified_at = timezone.now()
            seller_profile.verified_by = admin_user
            seller_profile.verification_notes = suspension_reason
            seller_profile.is_active = False
            seller_profile.save()
            
            # Log the suspension action
            logger.info(
                f"Seller {seller_profile.business_name} (ID: {seller_profile.id}) "
                f"suspended by {admin_user.username} (ID: {admin_user.id}). "
                f"Reason: {suspension_reason}"
            )
            
        return seller_profile
    
    @staticmethod
    def verify_kyc_document(kyc_document, admin_user, verification_notes=""):
        """
        Verify a KYC document.
        
        Args:
            kyc_document: The SellerKYC instance to verify
            admin_user: The admin user performing the verification
            verification_notes: Optional notes about the verification
            
        Returns:
            The updated SellerKYC instance
        """
        if not admin_user.is_staff:
            raise ValidationError("Only staff members can verify KYC documents")
            
        with transaction.atomic():
            kyc_document.verification_status = 'VERIFIED'
            kyc_document.verified_at = timezone.now()
            kyc_document.verified_by = admin_user
            kyc_document.verification_notes = verification_notes
            kyc_document.save()
            
            # Check if all required KYC documents are verified
            seller = kyc_document.seller
            required_document_types = ['ID_PROOF', 'ADDRESS_PROOF', 'BUSINESS_PROOF']
            verified_documents = seller.kyc_documents.filter(
                verification_status='VERIFIED',
                document_type__in=required_document_types
            ).values_list('document_type', flat=True)
            
            # If all required documents are verified, update seller verification status
            if set(required_document_types).issubset(set(verified_documents)):
                if seller.verification_status == 'PENDING':
                    seller.verification_status = 'VERIFIED'
                    seller.verified_at = timezone.now()
                    seller.verified_by = admin_user
                    seller.verification_notes = "All required KYC documents verified"
                    seller.save()
            
            # Log the verification action
            logger.info(
                f"KYC document {kyc_document.document_name} (ID: {kyc_document.id}) "
                f"for seller {kyc_document.seller.business_name} verified by "
                f"{admin_user.username} (ID: {admin_user.id})"
            )
            
        return kyc_document
    
    @staticmethod
    def reject_kyc_document(kyc_document, admin_user, rejection_reason):
        """
        Reject a KYC document.
        
        Args:
            kyc_document: The SellerKYC instance to reject
            admin_user: The admin user performing the rejection
            rejection_reason: The reason for rejection
            
        Returns:
            The updated SellerKYC instance
        """
        if not admin_user.is_staff:
            raise ValidationError("Only staff members can reject KYC documents")
            
        if not rejection_reason:
            raise ValidationError("Rejection reason is required")
            
        with transaction.atomic():
            kyc_document.verification_status = 'REJECTED'
            kyc_document.verified_at = timezone.now()
            kyc_document.verified_by = admin_user
            kyc_document.verification_notes = rejection_reason
            kyc_document.save()
            
            # Log the rejection action
            logger.info(
                f"KYC document {kyc_document.document_name} (ID: {kyc_document.id}) "
                f"for seller {kyc_document.seller.business_name} rejected by "
                f"{admin_user.username} (ID: {admin_user.id}). "
                f"Reason: {rejection_reason}"
            )
            
        return kyc_document
    
    @staticmethod
    def verify_bank_account(bank_account, admin_user, verification_notes=""):
        """
        Verify a seller bank account.
        
        Args:
            bank_account: The SellerBankAccount instance to verify
            admin_user: The admin user performing the verification
            verification_notes: Optional notes about the verification
            
        Returns:
            The updated SellerBankAccount instance
        """
        if not admin_user.is_staff:
            raise ValidationError("Only staff members can verify bank accounts")
            
        with transaction.atomic():
            bank_account.verification_status = 'VERIFIED'
            bank_account.verified_at = timezone.now()
            bank_account.verified_by = admin_user
            bank_account.verification_notes = verification_notes
            bank_account.save()
            
            # Log the verification action
            logger.info(
                f"Bank account {bank_account.bank_name} (ID: {bank_account.id}) "
                f"for seller {bank_account.seller.business_name} verified by "
                f"{admin_user.username} (ID: {admin_user.id})"
            )
            
        return bank_account
    
    @staticmethod
    def reject_bank_account(bank_account, admin_user, rejection_reason):
        """
        Reject a seller bank account.
        
        Args:
            bank_account: The SellerBankAccount instance to reject
            admin_user: The admin user performing the rejection
            rejection_reason: The reason for rejection
            
        Returns:
            The updated SellerBankAccount instance
        """
        if not admin_user.is_staff:
            raise ValidationError("Only staff members can reject bank accounts")
            
        if not rejection_reason:
            raise ValidationError("Rejection reason is required")
            
        with transaction.atomic():
            bank_account.verification_status = 'REJECTED'
            bank_account.verified_at = timezone.now()
            bank_account.verified_by = admin_user
            bank_account.verification_notes = rejection_reason
            bank_account.save()
            
            # Log the rejection action
            logger.info(
                f"Bank account {bank_account.bank_name} (ID: {bank_account.id}) "
                f"for seller {bank_account.seller.business_name} rejected by "
                f"{admin_user.username} (ID: {admin_user.id}). "
                f"Reason: {rejection_reason}"
            )
            
        return bank_account


class SellerPayoutService:
    """
    Service for handling seller payouts.
    """
    
    @staticmethod
    def create_payout(seller, amount, bank_account=None, notes=""):
        """
        Create a new payout for a seller.
        
        Args:
            seller: The SellerProfile instance
            amount: The payout amount
            bank_account: Optional specific bank account to use (defaults to primary)
            notes: Optional notes about the payout
            
        Returns:
            The created SellerPayoutHistory instance
        """
        if amount <= 0:
            raise ValidationError("Payout amount must be greater than zero")
            
        # If no bank account specified, use the primary one
        if not bank_account:
            bank_account = seller.bank_accounts.filter(
                is_primary=True, 
                verification_status='VERIFIED'
            ).first()
            
            if not bank_account:
                raise ValidationError(
                    "No verified primary bank account found for this seller"
                )
        
        # Ensure the bank account belongs to the seller and is verified
        if bank_account.seller != seller:
            raise ValidationError("Bank account does not belong to this seller")
            
        if bank_account.verification_status != 'VERIFIED':
            raise ValidationError("Cannot process payout to unverified bank account")
        
        # Calculate transaction fee (example: 2% of the amount)
        transaction_fee = round(amount * 0.02, 2)
        
        # Create the payout record
        payout = SellerPayoutHistory.objects.create(
            seller=seller,
            bank_account=bank_account,
            amount=amount,
            transaction_fee=transaction_fee,
            payout_date=timezone.now(),
            status='PENDING',
            notes=notes,
            transaction_id=f"PO-{uuid.uuid4().hex[:8].upper()}"
        )
        
        # Log the payout creation
        logger.info(
            f"Payout of {amount} created for seller {seller.business_name} "
            f"(ID: {seller.id}). Transaction ID: {payout.transaction_id}"
        )
        
        return payout
    
    @staticmethod
    def process_payout(payout):
        """
        Process a pending payout.
        
        Args:
            payout: The SellerPayoutHistory instance to process
            
        Returns:
            The updated SellerPayoutHistory instance
        """
        if payout.status != 'PENDING':
            raise ValidationError(f"Cannot process payout with status {payout.status}")
        
        # In a real implementation, this would integrate with a payment gateway
        # For now, we'll just simulate the processing
        
        # Update payout status
        payout.status = 'PROCESSING'
        payout.save()
        
        # Log the processing
        logger.info(
            f"Processing payout {payout.transaction_id} for "
            f"seller {payout.seller.business_name}"
        )
        
        # Here you would integrate with your payment gateway
        # For demonstration, we'll just mark it as completed
        payout.status = 'COMPLETED'
        payout.save()
        
        # Log the completion
        logger.info(
            f"Completed payout {payout.transaction_id} for "
            f"seller {payout.seller.business_name}"
        )
        
        return payout