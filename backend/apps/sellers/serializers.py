"""
Serializers for seller models.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.serializers import BaseSerializer, UserSerializer
from .models import SellerProfile, SellerKYC, SellerBankAccount, SellerPayoutHistory

User = get_user_model()


class SellerProfileSerializer(BaseSerializer):
    """
    Serializer for the SellerProfile model.
    """
    user = UserSerializer(read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)
    
    class Meta:
        model = SellerProfile
        fields = [
            'id', 'user', 'business_name', 'business_type', 'business_type_display',
            'tax_id', 'gstin', 'pan_number', 'description', 'logo', 'banner',
            'address', 'city', 'state', 'country', 'postal_code',
            'phone_number', 'email', 'website', 'verification_status',
            'verification_status_display', 'verification_notes', 'verified_at',
            'commission_rate', 'rating', 'total_sales', 'is_active', 'is_featured',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'verification_status', 'verification_notes', 'verified_at',
            'verified_by', 'commission_rate', 'rating', 'total_sales', 'is_featured',
            'created_at', 'updated_at'
        ]


class SellerProfileCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a seller profile.
    """
    class Meta:
        model = SellerProfile
        fields = [
            'business_name', 'business_type', 'tax_id', 'gstin', 'pan_number',
            'description', 'logo', 'banner', 'address', 'city', 'state',
            'country', 'postal_code', 'phone_number', 'email', 'website'
        ]
    
    def create(self, validated_data):
        """
        Create a new seller profile for the authenticated user.
        """
        user = self.context['request'].user
        
        # Check if user already has a seller profile
        if hasattr(user, 'seller_profile'):
            raise serializers.ValidationError("User already has a seller profile")
        
        # Update user type to seller
        user.user_type = 'seller'
        user.save()
        
        # Create seller profile
        seller_profile = SellerProfile.objects.create(user=user, **validated_data)
        return seller_profile


class SellerKYCSerializer(BaseSerializer):
    """
    Serializer for the SellerKYC model.
    """
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    class Meta:
        model = SellerKYC
        fields = [
            'id', 'seller', 'document_type', 'document_type_display', 'document_number',
            'document_file', 'document_name', 'issue_date', 'expiry_date',
            'verification_status', 'verification_status_display', 'verification_notes',
            'verified_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'seller', 'verification_status', 'verification_status_display',
            'verification_notes', 'verified_at', 'verified_by', 'created_at', 'updated_at'
        ]


class SellerKYCCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a seller KYC document.
    """
    class Meta:
        model = SellerKYC
        fields = [
            'document_type', 'document_number', 'document_file',
            'document_name', 'issue_date', 'expiry_date'
        ]
    
    def create(self, validated_data):
        """
        Create a new KYC document for the seller.
        """
        user = self.context['request'].user
        
        # Check if user has a seller profile
        if not hasattr(user, 'seller_profile'):
            raise serializers.ValidationError("User does not have a seller profile")
        
        seller = user.seller_profile
        kyc_document = SellerKYC.objects.create(seller=seller, **validated_data)
        return kyc_document


class SellerBankAccountSerializer(BaseSerializer):
    """
    Serializer for the SellerBankAccount model.
    """
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    class Meta:
        model = SellerBankAccount
        fields = [
            'id', 'seller', 'account_holder_name', 'bank_name', 'account_number',
            'ifsc_code', 'branch_name', 'account_type', 'account_type_display',
            'is_primary', 'verification_status', 'verification_status_display',
            'verification_document', 'verified_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'seller', 'verification_status', 'verification_status_display',
            'verified_at', 'verified_by', 'created_at', 'updated_at'
        ]


class SellerBankAccountCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a seller bank account.
    """
    class Meta:
        model = SellerBankAccount
        fields = [
            'account_holder_name', 'bank_name', 'account_number', 'ifsc_code',
            'branch_name', 'account_type', 'is_primary', 'verification_document'
        ]
    
    def create(self, validated_data):
        """
        Create a new bank account for the seller.
        """
        user = self.context['request'].user
        
        # Check if user has a seller profile
        if not hasattr(user, 'seller_profile'):
            raise serializers.ValidationError("User does not have a seller profile")
        
        seller = user.seller_profile
        bank_account = SellerBankAccount.objects.create(seller=seller, **validated_data)
        return bank_account


class SellerPayoutHistorySerializer(BaseSerializer):
    """
    Serializer for the SellerPayoutHistory model.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SellerPayoutHistory
        fields = [
            'id', 'seller', 'bank_account', 'amount', 'transaction_id',
            'transaction_fee', 'payout_date', 'status', 'status_display',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'seller', 'bank_account', 'amount', 'transaction_id',
            'transaction_fee', 'payout_date', 'status', 'status_display',
            'notes', 'created_at', 'updated_at'
        ]