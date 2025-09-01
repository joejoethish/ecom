"""
Rewards models for the ecommerce platform.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import BaseModel
from decimal import Decimal


class RewardProgram(BaseModel):
    """
    Reward program configuration.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_per_dollar = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    dollar_per_point = models.DecimalField(max_digits=5, decimal_places=4, default=0.01)
    minimum_redemption_points = models.PositiveIntegerField(default=100)
    maximum_redemption_points = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Reward Program'
        verbose_name_plural = 'Reward Programs'

    def __str__(self):
        return self.name


class CustomerRewards(BaseModel):
    """
    Customer rewards account.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rewards'
    )
    total_points_earned = models.PositiveIntegerField(default=0)
    total_points_redeemed = models.PositiveIntegerField(default=0)
    current_points = models.PositiveIntegerField(default=0)
    tier = models.CharField(
        max_length=20,
        choices=[
            ('bronze', 'Bronze'),
            ('silver', 'Silver'),
            ('gold', 'Gold'),
            ('platinum', 'Platinum'),
        ],
        default='bronze'
    )

    class Meta:
        verbose_name = 'Customer Rewards'
        verbose_name_plural = 'Customer Rewards'

    def __str__(self):
        return f"{self.user.username} - {self.current_points} points"

    def add_points(self, points, transaction_type, description, reference_id=None):
        """Add points to the customer's account."""
        self.total_points_earned += points
        self.current_points += points
        self.save()

        # Create transaction record
        RewardTransaction.objects.create(
            customer_rewards=self,
            transaction_type=transaction_type,
            points=points,
            description=description,
            reference_id=reference_id
        )

        # Update tier if necessary
        self.update_tier()

    def redeem_points(self, points, description, reference_id=None):
        """Redeem points from the customer's account."""
        if self.current_points >= points:
            self.total_points_redeemed += points
            self.current_points -= points
            self.save()

            # Create transaction record
            RewardTransaction.objects.create(
                customer_rewards=self,
                transaction_type='redemption',
                points=-points,
                description=description,
                reference_id=reference_id
            )
            return True
        return False

    def update_tier(self):
        """Update customer tier based on total points earned."""
        if self.total_points_earned >= 10000:
            self.tier = 'platinum'
        elif self.total_points_earned >= 5000:
            self.tier = 'gold'
        elif self.total_points_earned >= 1000:
            self.tier = 'silver'
        else:
            self.tier = 'bronze'
        self.save()

    def get_tier_benefits(self):
        """Get benefits for the current tier."""
        benefits = {
            'bronze': ['Basic rewards', 'Birthday bonus'],
            'silver': ['Basic rewards', 'Birthday bonus', '5% bonus points'],
            'gold': ['Basic rewards', 'Birthday bonus', '10% bonus points', 'Free shipping'],
            'platinum': ['Basic rewards', 'Birthday bonus', '15% bonus points', 'Free shipping', 'Priority support']
        }
        return benefits.get(self.tier, [])


class RewardTransaction(BaseModel):
    """
    Individual reward transaction.
    """
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('bonus', 'Bonus'),
        ('referral', 'Referral'),
        ('birthday', 'Birthday'),
        ('redemption', 'Redemption'),
        ('adjustment', 'Adjustment'),
        ('expiration', 'Expiration'),
    ]

    customer_rewards = models.ForeignKey(
        CustomerRewards,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()  # Can be negative for redemptions
    description = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=100, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Reward Transaction'
        verbose_name_plural = 'Reward Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_rewards.user.username} - {self.points} points ({self.transaction_type})"