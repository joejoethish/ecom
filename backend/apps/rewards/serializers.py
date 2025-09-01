"""
Rewards serializers for the ecommerce platform.
"""
from rest_framework import serializers
from .models import CustomerRewards, RewardTransaction, RewardProgram


class RewardTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for reward transactions.
    """
    class Meta:
        model = RewardTransaction
        fields = [
            'id', 'transaction_type', 'points', 'description',
            'reference_id', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CustomerRewardsSerializer(serializers.ModelSerializer):
    """
    Serializer for customer rewards.
    """
    recent_transactions = RewardTransactionSerializer(
        source='transactions',
        many=True,
        read_only=True
    )
    tier_benefits = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRewards
        fields = [
            'id', 'total_points_earned', 'total_points_redeemed',
            'current_points', 'tier', 'tier_benefits',
            'recent_transactions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tier_benefits(self, obj):
        return obj.get_tier_benefits()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Limit recent transactions to last 10
        if 'recent_transactions' in data:
            data['recent_transactions'] = data['recent_transactions'][:10]
        return data


class RewardProgramSerializer(serializers.ModelSerializer):
    """
    Serializer for reward programs.
    """
    class Meta:
        model = RewardProgram
        fields = [
            'id', 'name', 'description', 'points_per_dollar',
            'dollar_per_point', 'minimum_redemption_points',
            'maximum_redemption_points', 'is_active',
            'start_date', 'end_date'
        ]
        read_only_fields = ['id']


class RedeemPointsSerializer(serializers.Serializer):
    """
    Serializer for redeeming points.
    """
    points = serializers.IntegerField(min_value=1)
    description = serializers.CharField(max_length=255)
    reference_id = serializers.CharField(max_length=100, required=False)

    def validate_points(self, value):
        # Get the customer rewards from context
        customer_rewards = self.context.get('customer_rewards')
        if customer_rewards and value > customer_rewards.current_points:
            raise serializers.ValidationError(
                f"Insufficient points. You have {customer_rewards.current_points} points available."
            )
        return value