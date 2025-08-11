# Management command for running performance automation
from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio

from ...automation import PerformanceAutomation, SelfHealingSystem

class Command(BaseCommand):
    help = 'Run performance automation and self-healing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            choices=['automation', 'self-healing', 'both'],
            default='both',
            help='Mode to run'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no actual changes)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting performance automation in {options["mode"]} mode')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('Running in DRY-RUN mode - no changes will be made')
            )
        
        try:
            if options['mode'] in ['automation', 'both']:
                # Run performance automation
                automation = PerformanceAutomation()
                asyncio.run(automation.run_automation_cycle())
                
                self.stdout.write(
                    self.style.SUCCESS('Performance automation cycle completed')
                )
            
            if options['mode'] in ['self-healing', 'both']:
                # Run self-healing system
                healing = SelfHealingSystem()
                healing_actions = asyncio.run(healing.monitor_and_heal())
                
                self.stdout.write(
                    self.style.SUCCESS(f'Self-healing completed: {len(healing_actions)} actions taken')
                )
                
                for action in healing_actions:
                    status_style = self.style.SUCCESS if action['status'] == 'completed' else self.style.ERROR
                    self.stdout.write(
                        status_style(f"- {action['issue_type']}: {action['action']} ({action['status']})")
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Automation failed: {str(e)}')
            )