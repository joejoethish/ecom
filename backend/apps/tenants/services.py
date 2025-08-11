from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from celery import shared_task
import uuid
import os
import shutil
import json
from datetime import timedelta, datetime
from decimal import Decimal
from .models import (
    Tenant, TenantUser, TenantSubscription, TenantUsage, 
    TenantInvitation, TenantAuditLog, TenantBackup
)


class TenantProvisioningService:
    """Service for tenant provisioning and setup"""
    
    @staticmethod
    def create_tenant(data):
        """Create a new tenant with initial setup"""
        with transaction.atomic():
            # Create tenant
            tenant = Tenant.objects.create(
                name=data['name'],
                slug=data['slug'],
                subdomain=data['subdomain'],
                contact_name=data['contact_name'],
                contact_email=data['contact_email'],
                plan=data.get('plan', 'starter'),
                status='trial'
            )
            
            # Set trial period
            tenant.trial_ends_at = timezone.now() + timedelta(days=14)
            tenant.save()
            
            # Create owner user
            owner = TenantUser.objects.create_user(
                tenant=tenant,
                username=data['owner_username'],
                email=data['owner_email'],
                password=data['owner_password'],
                role='owner',
                first_name=data.get('owner_first_name', ''),
                last_name=data.get('owner_last_name', '')
            )
            
            # Initialize tenant settings
            TenantProvisioningService.initialize_tenant_settings(tenant)
            
            # Create initial usage record
            TenantUsage.objects.create(
                tenant=tenant,
                users_count=1,
                period_start=timezone.now(),
                period_end=timezone.now() + timedelta(days=1)
            )
            
            # Send welcome email
            TenantProvisioningService.send_welcome_email(tenant, owner)
            
            return tenant
    
    @staticmethod
    def initialize_tenant_settings(tenant):
        """Initialize default settings for tenant"""
        default_features = {
            'analytics': True,
            'reports': True,
            'api_access': True,
            'custom_branding': tenant.plan in ['professional', 'enterprise'],
            'advanced_permissions': tenant.plan == 'enterprise',
            'priority_support': tenant.plan in ['professional', 'enterprise'],
            'backup_retention_days': 7 if tenant.plan == 'starter' else 30,
            'api_rate_limit': 1000 if tenant.plan == 'starter' else 10000,
        }
        
        tenant.features = default_features
        tenant.save()
    
    @staticmethod
    def send_welcome_email(tenant, user):
        """Send welcome email to new tenant"""
        context = {
            'tenant': tenant,
            'user': user,
            'login_url': f"https://{tenant.subdomain}.{settings.DOMAIN}/admin/login"
        }
        
        subject = f"Welcome to {settings.SITE_NAME}!"
        message = render_to_string('emails/tenant_welcome.html', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=message
        )


class TenantUserManagementService:
    """Service for tenant user management"""
    
    @staticmethod
    def invite_user(tenant, inviter, email, role):
        """Invite a user to join tenant"""
        # Check if invitation already exists
        existing_invitation = TenantInvitation.objects.filter(
            tenant=tenant,
            email=email,
            status='pending'
        ).first()
        
        if existing_invitation:
            # Resend existing invitation
            invitation = existing_invitation
            invitation.expires_at = timezone.now() + timedelta(days=7)
            invitation.save()
        else:
            # Create new invitation
            invitation = TenantInvitation.objects.create(
                tenant=tenant,
                email=email,
                role=role,
                invited_by=inviter,
                token=str(uuid.uuid4()),
                expires_at=timezone.now() + timedelta(days=7)
            )
        
        # Send invitation email
        TenantUserManagementService.send_invitation_email(invitation)
        
        return invitation
    
    @staticmethod
    def send_invitation_email(invitation):
        """Send invitation email"""
        context = {
            'invitation': invitation,
            'accept_url': f"https://{invitation.tenant.subdomain}.{settings.DOMAIN}/admin/accept-invitation/{invitation.token}"
        }
        
        subject = f"Invitation to join {invitation.tenant.name}"
        message = render_to_string('emails/tenant_invitation.html', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            html_message=message
        )
    
    @staticmethod
    def accept_invitation(token, user_data):
        """Accept tenant invitation"""
        try:
            invitation = TenantInvitation.objects.get(
                token=token,
                status='pending',
                expires_at__gt=timezone.now()
            )
            
            with transaction.atomic():
                # Create user
                user = TenantUser.objects.create_user(
                    tenant=invitation.tenant,
                    username=user_data['username'],
                    email=invitation.email,
                    password=user_data['password'],
                    role=invitation.role,
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', '')
                )
                
                # Update invitation
                invitation.status = 'accepted'
                invitation.accepted_at = timezone.now()
                invitation.save()
                
                return user
                
        except TenantInvitation.DoesNotExist:
            raise ValueError("Invalid or expired invitation")


class TenantBillingService:
    """Service for tenant billing and subscription management"""
    
    @staticmethod
    def create_subscription(tenant, plan_data):
        """Create subscription for tenant"""
        subscription = TenantSubscription.objects.create(
            tenant=tenant,
            plan_name=plan_data['name'],
            billing_cycle=plan_data['billing_cycle'],
            amount=Decimal(plan_data['amount']),
            currency=plan_data.get('currency', 'USD'),
            next_billing_date=timezone.now() + timedelta(days=30)
        )
        
        # Update tenant status
        tenant.status = 'active'
        tenant.plan = plan_data['plan_type']
        tenant.subscription_starts_at = timezone.now()
        tenant.save()
        
        return subscription
    
    @staticmethod
    def calculate_usage_cost(tenant, usage_period):
        """Calculate usage-based costs"""
        usage = TenantUsage.objects.filter(
            tenant=tenant,
            period_start__gte=usage_period['start'],
            period_end__lte=usage_period['end']
        ).first()
        
        if not usage:
            return Decimal('0.00')
        
        # Base plan cost
        plan_costs = {
            'starter': Decimal('29.00'),
            'professional': Decimal('99.00'),
            'enterprise': Decimal('299.00'),
        }
        
        base_cost = plan_costs.get(tenant.plan, Decimal('0.00'))
        
        # Additional usage costs
        overage_cost = Decimal('0.00')
        
        # Users overage
        if usage.users_count > tenant.max_users:
            overage_users = usage.users_count - tenant.max_users
            overage_cost += overage_users * Decimal('5.00')
        
        # Storage overage
        if usage.storage_used_gb > tenant.max_storage_gb:
            overage_storage = usage.storage_used_gb - tenant.max_storage_gb
            overage_cost += overage_storage * Decimal('0.50')
        
        return base_cost + overage_cost
    
    @staticmethod
    def process_billing(tenant):
        """Process billing for tenant"""
        subscription = tenant.subscription
        
        if not subscription:
            return False
        
        # Calculate amount
        usage_period = {
            'start': subscription.last_billing_date or subscription.created_at,
            'end': timezone.now()
        }
        
        amount = TenantBillingService.calculate_usage_cost(tenant, usage_period)
        
        # Process payment (integrate with Stripe, PayPal, etc.)
        payment_success = TenantBillingService.process_payment(subscription, amount)
        
        if payment_success:
            subscription.last_billing_date = timezone.now()
            subscription.next_billing_date = timezone.now() + timedelta(days=30)
            subscription.payment_status = 'paid'
            subscription.save()
            
            return True
        else:
            subscription.payment_status = 'failed'
            subscription.save()
            
            # Send payment failed notification
            TenantBillingService.send_payment_failed_notification(tenant)
            
            return False
    
    @staticmethod
    def process_payment(subscription, amount):
        """Process payment (placeholder for payment gateway integration)"""
        # Integrate with Stripe, PayPal, or other payment processors
        # This is a placeholder implementation
        return True
    
    @staticmethod
    def send_payment_failed_notification(tenant):
        """Send payment failed notification"""
        context = {'tenant': tenant}
        
        subject = "Payment Failed - Action Required"
        message = render_to_string('emails/payment_failed.html', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[tenant.contact_email],
            html_message=message
        )


class TenantAnalyticsService:
    """Service for tenant analytics and reporting"""
    
    @staticmethod
    def get_tenant_dashboard_stats(tenant):
        """Get dashboard statistics for tenant"""
        stats = {
            'users_count': tenant.users.count(),
            'active_users_count': tenant.users.filter(is_active=True).count(),
            'storage_used': TenantAnalyticsService.calculate_storage_usage(tenant),
            'api_calls_today': TenantAnalyticsService.get_api_calls_count(tenant, 'today'),
            'subscription_status': tenant.status,
            'days_until_renewal': TenantAnalyticsService.days_until_renewal(tenant),
        }
        
        return stats
    
    @staticmethod
    def calculate_storage_usage(tenant):
        """Calculate storage usage for tenant"""
        # This would calculate actual storage usage
        # Placeholder implementation
        return Decimal('0.5')  # GB
    
    @staticmethod
    def get_api_calls_count(tenant, period):
        """Get API calls count for period"""
        # This would get actual API calls from logs
        # Placeholder implementation
        return 150
    
    @staticmethod
    def days_until_renewal(tenant):
        """Calculate days until subscription renewal"""
        if tenant.subscription and tenant.subscription.next_billing_date:
            delta = tenant.subscription.next_billing_date - timezone.now()
            return delta.days
        return None
    
    @staticmethod
    def generate_usage_report(tenant, period_start, period_end):
        """Generate detailed usage report"""
        usage_records = TenantUsage.objects.filter(
            tenant=tenant,
            period_start__gte=period_start,
            period_end__lte=period_end
        )
        
        report = {
            'tenant': tenant.name,
            'period': {
                'start': period_start,
                'end': period_end
            },
            'usage_summary': {
                'total_users': max([u.users_count for u in usage_records], default=0),
                'total_storage': sum([u.storage_used_gb for u in usage_records]),
                'total_api_calls': sum([u.api_calls_count for u in usage_records]),
                'avg_response_time': sum([u.avg_response_time or 0 for u in usage_records]) / len(usage_records) if usage_records else 0,
            },
            'daily_usage': [
                {
                    'date': usage.period_start.date(),
                    'users': usage.users_count,
                    'storage': usage.storage_used_gb,
                    'api_calls': usage.api_calls_count,
                    'response_time': usage.avg_response_time,
                }
                for usage in usage_records
            ]
        }
        
        return report


class TenantBackupService:
    """Service for tenant backup and disaster recovery"""
    
    @staticmethod
    def create_backup(tenant, backup_type='full'):
        """Create backup for tenant"""
        backup = TenantBackup.objects.create(
            tenant=tenant,
            backup_type=backup_type,
            status='pending'
        )
        
        # Start backup process asynchronously
        create_tenant_backup_task.delay(backup.id)
        
        return backup
    
    @staticmethod
    def restore_backup(tenant, backup_id):
        """Restore tenant from backup"""
        backup = TenantBackup.objects.get(id=backup_id, tenant=tenant)
        
        if backup.status != 'completed':
            raise ValueError("Backup is not completed")
        
        # Start restore process asynchronously
        restore_tenant_backup_task.delay(backup.id)
        
        return True


@shared_task
def create_tenant_backup_task(backup_id):
    """Celery task to create tenant backup"""
    backup = TenantBackup.objects.get(id=backup_id)
    backup.status = 'running'
    backup.started_at = timezone.now()
    backup.save()
    
    try:
        # Create backup directory
        backup_dir = os.path.join(settings.BACKUP_ROOT, str(backup.tenant.id))
        os.makedirs(backup_dir, exist_ok=True)
        
        # Export tenant data
        backup_data = {
            'tenant': {
                'id': str(backup.tenant.id),
                'name': backup.tenant.name,
                'settings': backup.tenant.custom_settings,
                'features': backup.tenant.features,
            },
            'users': [
                {
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'preferences': user.preferences,
                }
                for user in backup.tenant.users.all()
            ],
            # Add more data as needed
        }
        
        # Save backup file
        backup_file = os.path.join(backup_dir, f"backup_{backup.id}.json")
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        # Update backup record
        backup.file_path = backup_file
        backup.file_size = os.path.getsize(backup_file)
        backup.status = 'completed'
        backup.progress_percentage = 100
        backup.completed_at = timezone.now()
        backup.save()
        
    except Exception as e:
        backup.status = 'failed'
        backup.error_message = str(e)
        backup.save()


@shared_task
def restore_tenant_backup_task(backup_id):
    """Celery task to restore tenant backup"""
    backup = TenantBackup.objects.get(id=backup_id)
    
    try:
        # Load backup data
        with open(backup.file_path, 'r') as f:
            backup_data = json.load(f)
        
        # Restore tenant data
        tenant = backup.tenant
        tenant.custom_settings = backup_data['tenant']['settings']
        tenant.features = backup_data['tenant']['features']
        tenant.save()
        
        # Restore users (if needed)
        # This would be more complex in a real implementation
        
    except Exception as e:
        # Log error
        pass


@shared_task
def update_tenant_usage_task():
    """Celery task to update tenant usage statistics"""
    for tenant in Tenant.objects.filter(is_active=True):
        # Calculate current usage
        users_count = tenant.users.count()
        storage_used = TenantAnalyticsService.calculate_storage_usage(tenant)
        api_calls = TenantAnalyticsService.get_api_calls_count(tenant, 'today')
        
        # Create or update usage record
        today = timezone.now().date()
        usage, created = TenantUsage.objects.get_or_create(
            tenant=tenant,
            period_start=datetime.combine(today, datetime.min.time()),
            period_end=datetime.combine(today, datetime.max.time()),
            defaults={
                'users_count': users_count,
                'storage_used_gb': storage_used,
                'api_calls_count': api_calls,
            }
        )
        
        if not created:
            usage.users_count = users_count
            usage.storage_used_gb = storage_used
            usage.api_calls_count = api_calls
            usage.save()


@shared_task
def process_tenant_billing_task():
    """Celery task to process tenant billing"""
    # Get tenants with billing due
    due_date = timezone.now().date()
    subscriptions = TenantSubscription.objects.filter(
        next_billing_date__date=due_date,
        tenant__status='active'
    )
    
    for subscription in subscriptions:
        TenantBillingService.process_billing(subscription.tenant)