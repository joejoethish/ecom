"""
Management command to process scheduled promotion actions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.promotions.models import PromotionSchedule, PromotionStatus
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process scheduled promotion actions (activate, deactivate, pause, resume)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Get pending schedules that are due
        pending_schedules = PromotionSchedule.objects.filter(
            is_executed=False,
            scheduled_time__lte=now
        ).select_related('promotion')
        
        if not pending_schedules.exists():
            self.stdout.write(
                self.style.SUCCESS('No pending promotion schedules to process.')
            )
            return
        
        processed_count = 0
        error_count = 0
        
        for schedule in pending_schedules:
            try:
                promotion = schedule.promotion
                action = schedule.action
                
                if dry_run:
                    self.stdout.write(
                        f'Would {action} promotion "{promotion.name}" (ID: {promotion.id})'
                    )
                    continue
                
                # Execute the scheduled action
                if action == 'activate':
                    if promotion.status != PromotionStatus.ACTIVE:
                        promotion.status = PromotionStatus.ACTIVE
                        promotion.save()
                        result = f'Promotion activated successfully'
                    else:
                        result = f'Promotion was already active'
                
                elif action == 'deactivate':
                    if promotion.status == PromotionStatus.ACTIVE:
                        promotion.status = PromotionStatus.EXPIRED
                        promotion.save()
                        result = f'Promotion deactivated successfully'
                    else:
                        result = f'Promotion was not active'
                
                elif action == 'pause':
                    if promotion.status == PromotionStatus.ACTIVE:
                        promotion.status = PromotionStatus.PAUSED
                        promotion.save()
                        result = f'Promotion paused successfully'
                    else:
                        result = f'Promotion was not active'
                
                elif action == 'resume':
                    if promotion.status == PromotionStatus.PAUSED:
                        promotion.status = PromotionStatus.ACTIVE
                        promotion.save()
                        result = f'Promotion resumed successfully'
                    else:
                        result = f'Promotion was not paused'
                
                else:
                    result = f'Unknown action: {action}'
                
                # Mark schedule as executed
                schedule.is_executed = True
                schedule.executed_at = now
                schedule.execution_result = result
                schedule.save()
                
                processed_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Processed schedule {schedule.id}: {action} promotion "{promotion.name}" - {result}'
                    )
                )
                
                logger.info(f'Processed promotion schedule {schedule.id}: {result}')
            
            except Exception as e:
                error_count += 1
                error_message = f'Error processing schedule {schedule.id}: {str(e)}'
                
                # Mark schedule with error
                schedule.execution_result = error_message
                schedule.save()
                
                self.stdout.write(
                    self.style.ERROR(error_message)
                )
                
                logger.error(error_message, exc_info=True)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'Dry run completed. Would have processed {pending_schedules.count()} schedules.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {processed_count} schedules successfully. {error_count} errors.'
                )
            )