"""
Seller views for the ecommerce platform.
"""
from rest_framework import viewsets, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.permissions import IsSellerOrReadOnly, IsAdminOrReadOnly
from .models import SellerProfile, SellerKYC, SellerBankAccount, SellerPayoutHistory
from .serializers import (
    SellerProfileSerializer, SellerProfileCreateSerializer,
    SellerKYCSerializer, SellerKYCCreateSerializer,
    SellerBankAccountSerializer, SellerBankAccountCreateSerializer,
    SellerPayoutHistorySerializer
)
from .services import SellerVerificationService, SellerPayoutService

User = get_user_model()


class SellerRegistrationView(generics.CreateAPIView):
    """
    View for seller registration.
    """
    serializer_class = SellerProfileCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class SellerProfileView(APIView):
    """
    View for seller profile management.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the seller profile for the authenticated user.
        """
        user = request.user
        
        # Check if user has a seller profile
        if not hasattr(user, 'seller_profile'):
            return Response({
                'success': False,
                'error': {
                    'message': 'Seller profile not found',
                    'code': 'seller_profile_not_found',
                    'status_code': 404
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SellerProfileSerializer(user.seller_profile)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request):
        """
        Update the seller profile for the authenticated user.
        """
        user = request.user
        
        # Check if user has a seller profile
        if not hasattr(user, 'seller_profile'):
            return Response({
                'success': False,
                'error': {
                    'message': 'Seller profile not found',
                    'code': 'seller_profile_not_found',
                    'status_code': 404
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SellerProfileSerializer(user.seller_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Seller profile updated successfully'
            })
        
        return Response({
            'success': False,
            'error': {
                'message': 'Invalid data',
                'code': 'invalid_data',
                'status_code': 400,
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)


class SellerKYCViewSet(viewsets.ModelViewSet):
    """
    ViewSet for seller KYC documents.
    """
    serializer_class = SellerKYCSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return KYC documents for the authenticated seller.
        """
        user = self.request.user
        
        # Check if user has a seller profile
        if not hasattr(user, 'seller_profile'):
            return SellerKYC.objects.none()
        
        return SellerKYC.objects.filter(seller=user.seller_profile)
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class.
        """
        if self.action == 'create':
            return SellerKYCCreateSerializer
        return SellerKYCSerializer
    
    def perform_create(self, serializer):
        """
        Create a new KYC document for the seller.
        """
        serializer.save()


class SellerBankAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for seller bank accounts.
    """
    serializer_class = SellerBankAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return bank accounts for the authenticated seller.
        """
        user = self.request.user
        
        # Check if user has a seller profile
        if not hasattr(user, 'seller_profile'):
            return SellerBankAccount.objects.none()
        
        return SellerBankAccount.objects.filter(seller=user.seller_profile)
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class.
        """
        if self.action == 'create':
            return SellerBankAccountCreateSerializer
        return SellerBankAccountSerializer
    
    def perform_create(self, serializer):
        """
        Create a new bank account for the seller.
        """
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """
        Set a bank account as primary.
        """
        bank_account = self.get_object()
        
        # Set as primary
        bank_account.is_primary = True
        bank_account.save()
        
        serializer = self.get_serializer(bank_account)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Bank account set as primary'
        })


class SellerPayoutHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for seller payout history.
    """
    serializer_class = SellerPayoutHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return payout history for the authenticated seller.
        """
        user = self.request.user
        
        # Check if user has a seller profile
        if not hasattr(user, 'seller_profile'):
            return SellerPayoutHistory.objects.none()
        
        return SellerPayoutHistory.objects.filter(seller=user.seller_profile)


class AdminSellerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin management of sellers.
    """
    queryset = SellerProfile.objects.all()
    serializer_class = SellerProfileSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['business_name', 'email', 'user__email', 'user__username']
    ordering_fields = ['business_name', 'created_at', 'verification_status', 'rating', 'total_sales']
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify a seller profile.
        """
        seller_profile = self.get_object()
        verification_notes = request.data.get('verification_notes', '')
        
        try:
            updated_profile = SellerVerificationService.verify_seller_profile(
                seller_profile=seller_profile,
                admin_user=request.user,
                verification_notes=verification_notes
            )
            
            serializer = self.get_serializer(updated_profile)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Seller profile verified successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'verification_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a seller profile.
        """
        seller_profile = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not rejection_reason:
            return Response({
                'success': False,
                'error': {
                    'message': 'Rejection reason is required',
                    'code': 'rejection_reason_required',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_profile = SellerVerificationService.reject_seller_profile(
                seller_profile=seller_profile,
                admin_user=request.user,
                rejection_reason=rejection_reason
            )
            
            serializer = self.get_serializer(updated_profile)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Seller profile rejected successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'rejection_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """
        Suspend a seller profile.
        """
        seller_profile = self.get_object()
        suspension_reason = request.data.get('suspension_reason', '')
        
        if not suspension_reason:
            return Response({
                'success': False,
                'error': {
                    'message': 'Suspension reason is required',
                    'code': 'suspension_reason_required',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_profile = SellerVerificationService.suspend_seller_profile(
                seller_profile=seller_profile,
                admin_user=request.user,
                suspension_reason=suspension_reason
            )
            
            serializer = self.get_serializer(updated_profile)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Seller profile suspended successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'suspension_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminSellerKYCViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin management of seller KYC documents.
    """
    queryset = SellerKYC.objects.all()
    serializer_class = SellerKYCSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['seller__business_name', 'document_name', 'document_number']
    ordering_fields = ['created_at', 'verification_status']
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify a KYC document.
        """
        kyc_document = self.get_object()
        verification_notes = request.data.get('verification_notes', '')
        
        try:
            updated_document = SellerVerificationService.verify_kyc_document(
                kyc_document=kyc_document,
                admin_user=request.user,
                verification_notes=verification_notes
            )
            
            serializer = self.get_serializer(updated_document)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'KYC document verified successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'verification_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a KYC document.
        """
        kyc_document = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not rejection_reason:
            return Response({
                'success': False,
                'error': {
                    'message': 'Rejection reason is required',
                    'code': 'rejection_reason_required',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_document = SellerVerificationService.reject_kyc_document(
                kyc_document=kyc_document,
                admin_user=request.user,
                rejection_reason=rejection_reason
            )
            
            serializer = self.get_serializer(updated_document)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'KYC document rejected successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'rejection_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminSellerBankAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin management of seller bank accounts.
    """
    queryset = SellerBankAccount.objects.all()
    serializer_class = SellerBankAccountSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['seller__business_name', 'account_holder_name', 'bank_name']
    ordering_fields = ['created_at', 'verification_status']
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify a bank account.
        """
        bank_account = self.get_object()
        verification_notes = request.data.get('verification_notes', '')
        
        try:
            updated_account = SellerVerificationService.verify_bank_account(
                bank_account=bank_account,
                admin_user=request.user,
                verification_notes=verification_notes
            )
            
            serializer = self.get_serializer(updated_account)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Bank account verified successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'verification_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a bank account.
        """
        bank_account = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not rejection_reason:
            return Response({
                'success': False,
                'error': {
                    'message': 'Rejection reason is required',
                    'code': 'rejection_reason_required',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_account = SellerVerificationService.reject_bank_account(
                bank_account=bank_account,
                admin_user=request.user,
                rejection_reason=rejection_reason
            )
            
            serializer = self.get_serializer(updated_account)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Bank account rejected successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'rejection_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminSellerPayoutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin management of seller payouts.
    """
    queryset = SellerPayoutHistory.objects.all()
    serializer_class = SellerPayoutHistorySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['seller__business_name', 'transaction_id']
    ordering_fields = ['payout_date', 'status', 'amount']
    
    @action(detail=False, methods=['post'])
    def create_payout(self, request):
        """
        Create a new payout for a seller.
        """
        seller_id = request.data.get('seller_id')
        amount = request.data.get('amount')
        bank_account_id = request.data.get('bank_account_id')
        notes = request.data.get('notes', '')
        
        if not seller_id or not amount:
            return Response({
                'success': False,
                'error': {
                    'message': 'Seller ID and amount are required',
                    'code': 'missing_required_fields',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = float(amount)
        except ValueError:
            return Response({
                'success': False,
                'error': {
                    'message': 'Amount must be a valid number',
                    'code': 'invalid_amount',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            seller = SellerProfile.objects.get(id=seller_id)
            
            bank_account = None
            if bank_account_id:
                bank_account = SellerBankAccount.objects.get(id=bank_account_id, seller=seller)
            
            payout = SellerPayoutService.create_payout(
                seller=seller,
                amount=amount,
                bank_account=bank_account,
                notes=notes
            )
            
            serializer = self.get_serializer(payout)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Payout created successfully'
            })
        except SellerProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'message': 'Seller not found',
                    'code': 'seller_not_found',
                    'status_code': 404
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except SellerBankAccount.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'message': 'Bank account not found',
                    'code': 'bank_account_not_found',
                    'status_code': 404
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'payout_creation_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Process a pending payout.
        """
        payout = self.get_object()
        
        try:
            processed_payout = SellerPayoutService.process_payout(payout)
            
            serializer = self.get_serializer(processed_payout)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Payout processed successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'payout_processing_error',
                    'status_code': 400
                }
            }, status=status.HTTP_400_BAD_REQUEST)