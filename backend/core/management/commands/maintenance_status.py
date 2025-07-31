"""
Django management command to check maintenance coordinator status
"""

import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.cache import cache

from core.ongoing_maintenance_coordinator import get_maintenance_coordinator


class Command(BaseCommand):
    help = 'Check the status of the ongoing maintenance coordinator'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['table', 'json'],
            default='table',
            help='Output format (table or json)',
        )
        parser.add_argument(
            '--schedules',
            action='store_true',
            help='Show detailed schedule information',
        )
    
    def handle(self, *args, **options):
        """Check maintenance coordinator status"""
        
        try:
            coordinator = get_maintenance_coordinator()
            status = coordinator.get_coordinator_status()
            
            if options['format'] == 'json':
                self._output_json(status, coordinator, options)
            else:
                self._output_table(status, coordinator, options)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to get maintenance status: {e}')
            )
    
    def _output_json(self, status, coordinator, options):
        """Output status in JSON format"""
        output = {
            'coordinator_status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        if options['schedules']:
            output['schedules'] = coordinator.get_maintenance_schedules()
        
        self.stdout.write(json.dumps(output, indent=2))
    
    def _output_table(self, status, coordinator, options):
        """Output status in table format"""
        
        # Main status
        self.stdout.write(
            self.style.SUCCESS('=== Maintenance Coordinator Status ===')
        )
        
        status_color = self.style.SUCCESS if status.get('coordinator_status') == 'running' else self.style.ERROR
        
        self.stdout.write(f"Status: {status_color(status.get('coordinator_status', 'unknown'))}")
        self.stdout.write(f"Active Schedules: {status.get('active_schedules', 0)}")
        self.stdout.write(f"Failed Schedules: {status.get('failed_schedules', 0)}")
        self.stdout.write(f"Monitoring Enabled: {status.get('monitoring_enabled', False)}")
        self.stdout.write(f"Backup Testing Enabled: {status.get('backup_testing_enabled', False)}")
        self.stdout.write(f"Disaster Recovery Ready: {status.get('disaster_recovery_ready', False)}")
        
        if status.get('last_maintenance_run'):
            last_run = datetime.fromisoformat(status['last_maintenance_run'])
            self.stdout.write(f"Last Maintenance: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if status.get('next_scheduled_run'):
            next_run = datetime.fromisoformat(status['next_scheduled_run'])
            self.stdout.write(f"Next Scheduled: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Schedule details
        if options['schedules']:
            self.stdout.write('\n' + self.style.SUCCESS('=== Maintenance Schedules ==='))
            
            schedules = coordinator.get_maintenance_schedules()
            
            if not schedules:
                self.stdout.write('No schedules configured')
                return
            
            # Table header
            self.stdout.write(
                f"{'Schedule ID':<25} {'Type':<15} {'Enabled':<8} {'Last Run':<20} {'Next Run':<20} {'Failures':<8}"
            )
            self.stdout.write('-' * 100)
            
            for schedule_id, schedule_data in schedules.items():
                enabled_color = self.style.SUCCESS if schedule_data.get('enabled') else self.style.ERROR
                enabled_text = enabled_color('Yes' if schedule_data.get('enabled') else 'No')
                
                last_run = 'Never'
                if schedule_data.get('last_run'):
                    last_run_dt = datetime.fromisoformat(schedule_data['last_run'])
                    last_run = last_run_dt.strftime('%Y-%m-%d %H:%M')
                
                next_run = 'Not scheduled'
                if schedule_data.get('next_run'):
                    next_run_dt = datetime.fromisoformat(schedule_data['next_run'])
                    next_run = next_run_dt.strftime('%Y-%m-%d %H:%M')
                
                failure_count = schedule_data.get('failure_count', 0)
                failure_color = self.style.ERROR if failure_count > 0 else self.style.SUCCESS
                
                self.stdout.write(
                    f"{schedule_id:<25} "
                    f"{schedule_data.get('task_type', 'unknown'):<15} "
                    f"{enabled_text:<8} "
                    f"{last_run:<20} "
                    f"{next_run:<20} "
                    f"{failure_color(str(failure_count)):<8}"
                )
        
        # Recent task status
        self._show_recent_tasks()
    
    def _show_recent_tasks(self):
        """Show recent maintenance task status"""
        self.stdout.write('\n' + self.style.SUCCESS('=== Recent Task Status ==='))
        
        # Check for recent task IDs in cache
        task_keys = [
            'daily_maintenance_task_default',
            'weekly_maintenance_task_default',
            'monthly_maintenance_tasks_default'
        ]
        
        found_tasks = False
        
        for key in task_keys:
            task_id = cache.get(key)
            if task_id:
                found_tasks = True
                task_type = key.replace('_task_default', '').replace('_tasks_default', '').replace('_', ' ').title()
                
                try:
                    from celery import current_app
                    
                    if isinstance(task_id, dict):
                        # Multiple tasks (monthly)
                        self.stdout.write(f"{task_type}:")
                        for sub_task, sub_id in task_id.items():
                            result = current_app.AsyncResult(sub_id)
                            status_color = self._get_status_color(result.status)
                            self.stdout.write(f"  {sub_task}: {status_color(result.status)}")
                    else:
                        # Single task
                        result = current_app.AsyncResult(task_id)
                        status_color = self._get_status_color(result.status)
                        self.stdout.write(f"{task_type}: {status_color(result.status)}")
                        
                except ImportError:
                    self.stdout.write(f"{task_type}: Task ID cached but Celery not available")
                except Exception as e:
                    self.stdout.write(f"{task_type}: Error checking status - {e}")
        
        if not found_tasks:
            self.stdout.write('No recent tasks found')
    
    def _get_status_color(self, status):
        """Get color style for task status"""
        if status == 'SUCCESS':
            return self.style.SUCCESS
        elif status == 'FAILURE':
            return self.style.ERROR
        elif status == 'PENDING':
            return self.style.WARNING
        else:
            return self.style.NOTICE