"""
Rewards views for the ecommerce platform.
"""
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from django.utils import timezone

from .models import CustomerRewards, RewardTransaction, RewardProgram
from .serializers import (
    CustomerRewardsSerializer,
    RewardTransactionSerializer,
    RewardProgramSerializer,
    RedeemPointsSerializer
)


class CustomerRewardsViewSet(ModelViewSet):
    """
    ViewSet for managing customer rewards.
    """
    serializer_class = CustomerRewardsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerRewards.objects.filter(user=self.request.user)

    def get_or_create_rewards(self):
        """Get or create rewards account for the current user."""
        rewards, created = CustomerRewards.objects.get_or_create(
            user=self.request.user
        )
        return rewards

    def list(self, request):
        """Get user's rewards account."""
        rewards = self.get_or_create_rewards()
        serializer = self.get_serializer(rewards)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get current points balance."""
        rewards = self.get_or_create_rewards()
        return Response({
            'current_points': rewards.current_points,
            'tier': rewards.tier,
            'total_earned': rewards.total_points_earned,
            'total_redeemed': rewards.total_points_redeemed
        })

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get reward transactions with pagination."""
        rewards = self.get_or_create_rewards()
        transactions = rewards.transactions.all()
        
        # Filter by transaction type if provided
        transaction_type = request.query_params.get('type')
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_transactions = transactions[start:end]
        serializer = RewardTransactionSerializer(paginated_transactions, many=True)
        
        return Response({
            'results': serializer.data,
            'count': transactions.count(),
            'page': page,
            'page_size': page_size,
            'has_next': end < transactions.count(),
            'has_previous': page > 1
        })

    @action(detail=False, methods=['post'])
    def redeem(self, request):
        """Redeem points."""
        rewards = self.get_or_create_rewards()
        serializer = RedeemPointsSerializer(
            data=request.data,
            context={'customer_rewards': rewards}
        )
        
        if serializer.is_valid():
            points = serializer.validated_data['points']
            description = serializer.validated_data['description']
            reference_id = serializer.validated_data.get('reference_id')
            
            # Check minimum redemption requirement
            active_program = RewardProgram.objects.filter(
                is_active=True,
                start_date__lte=timezone.now()
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
            ).first()
            
            if active_program and points < active_program.minimum_redemption_points:
                return Response(
                    {
                        'error': f'Minimum redemption is {active_program.minimum_redemption_points} points'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success = rewards.redeem_points(points, description, reference_id)
            
            if success:
                return Response(
                    {
                        'message': 'Points redeemed successfully',
                        'points_redeemed': points,
                        'remaining_points': rewards.current_points
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Insufficient points'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def program(self, request):
        """Get active reward program details."""
        active_program = RewardProgram.objects.filter(
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
        ).first()
        
        if active_program:
            serializer = RewardProgramSerializer(active_program)
            return Response(serializer.data)
        else:
            return Response(
                {'message': 'No active reward program'},
                status=status.HTTP_404_NOT_FOUND
            )