"""
Backup Management Views

This module provides web-based views for backup management including:
- Backup status dashboard
- Manual backup operations
- Backup listing and verification
- Restore operations (admin only)
- Scheduler management

Requirements covered:
- 3.6: Alert administrators of backup failures or issues
- Administrative interface for backup management
"""

import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib import messages
from core.backup_manager import MySQLBackupManager, BackupConfig
from core.backup_scheduler import get_backup_scheduler, initialize_backup_scheduler


logger = logging.getLogger(__name__)


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser


def get_backup_manager():
    """Get configured backup manager instance"""
    import os
    backup_dir = getattr(settings, 'BACKUP_DIR', 
                        os.path.join(settings.BASE_DIR, 'backups'))
    encryption_key = getattr(settings, 'BACKUP_ENCRYPTION_KEY', 
                            'default-key-change-in-production')
    
    config = BackupConfig(
        backup_dir=backup_dir,
        encryption_key=encryption_key,
        retention_days=getattr(settings, 'BACKUP_RETENTION_DAYS', 30),
        compression_enabled=getattr(settings, 'BACKUP_COMPRESSION_ENABLED', True),
        verify_backups=getattr(settings, 'BACKUP_VERIFY_ENABLED', True),
    )
    
    return MySQLBackupManager(config)


@staff_member_required
def backup_dashboard(request):
    """Main backup dashboard view"""
    try:
        backup_manager = get_backup_manager()
        scheduler = get_backup_scheduler()
        
        # Get backup status
        backup_status = backup_manager.get_backup_status()
        
        # Get scheduler status
        scheduler_status = scheduler.get_scheduler_status() if scheduler else None
        
        # Get recent backups
        recent_backups = backup_manager.storage.list_backups()[:10]
        
        # Get recent alerts from cache
        from django.core.cache import cache
        recent_alerts = cache.get('db_alerts', [])[-10:]
        
        context = {
            'backup_status': backup_status,
            'scheduler_status': scheduler_status,
            'recent_backups': recent_backups,
            'recent_alerts': recent_alerts,
            'page_title': 'Backup Management Dashboard',
        }
        
        return render(request, 'admin/backup_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in backup dashboard: {e}")
        messages.error(request, f"Error loading backup dashboard: {e}")
        return render(request, 'admin/backup_dashboard.html', {
            'error': str(e),
            'page_title': 'Backup Management Dashboard',
        })


@staff_member_required
def backup_list(request):
    """List all backups with pagination"""
    try:
        backup_manager = get_backup_manager()
        
        # Get filter parameters
        backup_type = request.GET.get('type')
        page = request.GET.get('page', 1)
        
        # Get backups
        backups = backup_manager.storage.list_backups(backup_type)
        
        # Paginate results
        paginator = Paginator(backups, 20)
        page_obj = paginator.get_page(page)
        
        context = {
            'page_obj': page_obj,
            'backup_type': backup_type,
            'page_title': 'Backup List',
        }
        
        return render(request, 'admin/backup_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in backup list: {e}")
        messages.error(request, f"Error loading backup list: {e}")
        return render(request, 'admin/backup_list.html', {
            'error': str(e),
            'page_title': 'Backup List',
        })


@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def create_backup(request):
    """Create a new backup (AJAX endpoint)"""
    try:
        backup_type = request.POST.get('type', 'full')
        database = request.POST.get('database', 'default')
        
        backup_manager = get_backup_manager()
        
        if backup_type == 'full':
            metadata = backup_manager.create_full_backup(database)
        elif backup_type == 'incremental':
            metadata = backup_manager.create_incremental_backup(database)
        else:
            return JsonResponse({'error': 'Invalid backup type'}, status=400)
        
        return JsonResponse({
            'success': True,
            'backup_id': metadata.backup_id,
            'backup_type': metadata.backup_type,
            'size_mb': round(metadata.file_size / (1024 * 1024), 2),
            'timestamp': metadata.timestamp.isoformat(),
        })
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def verify_backup(request):
    """Verify backup integrity (AJAX endpoint)"""
    try:
        backup_id = request.POST.get('backup_id')
        if not backup_id:
            return JsonResponse({'error': 'Backup ID required'}, status=400)
        
        backup_manager = get_backup_manager()
        is_valid = backup_manager.verify_backup_integrity(backup_id)
        
        return JsonResponse({
            'success': True,
            'backup_id': backup_id,
            'is_valid': is_valid,
        })
        
    except Exception as e:
        logger.error(f"Error verifying backup: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
@csrf_exempt
def restore_backup(request):
    """Restore from backup (superuser only)"""
    try:
        backup_id = request.POST.get('backup_id')
        database = request.POST.get('database', 'default')
        target_database = request.POST.get('target_database')
        confirm = request.POST.get('confirm') == 'true'
        
        if not backup_id:
            return JsonResponse({'error': 'Backup ID required'}, status=400)
        
        if not confirm:
            return JsonResponse({'error': 'Confirmation required for restore operation'}, status=400)
        
        backup_manager = get_backup_manager()
        success = backup_manager.restore_from_backup(backup_id, database, target_database)
        
        if success:
            return JsonResponse({
                'success': True,
                'backup_id': backup_id,
                'message': 'Backup restored successfully',
            })
        else:
            return JsonResponse({'error': 'Restore operation failed'}, status=500)
        
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def cleanup_backups(request):
    """Clean up old backups (AJAX endpoint)"""
    try:
        dry_run = request.POST.get('dry_run') == 'true'
        
        backup_manager = get_backup_manager()
        
        if dry_run:
            # Simulate cleanup
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=backup_manager.config.retention_days)
            old_backups = [
                b for b in backup_manager.storage.list_backups()
                if b.timestamp < cutoff_date
            ]
            
            total_size = sum(b.file_size for b in old_backups)
            
            return JsonResponse({
                'success': True,
                'dry_run': True,
                'would_remove': len(old_backups),
                'would_free_mb': round(total_size / (1024 * 1024), 2),
                'backups': [b.backup_id for b in old_backups],
            })
        else:
            # Actual cleanup
            removed_backups = backup_manager.cleanup_old_backups()
            
            return JsonResponse({
                'success': True,
                'dry_run': False,
                'removed': len(removed_backups),
                'backups': removed_backups,
            })
        
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def backup_status_api(request):
    """Get backup system status (AJAX endpoint)"""
    try:
        backup_manager = get_backup_manager()
        scheduler = get_backup_scheduler()
        
        status = backup_manager.get_backup_status()
        
        if scheduler:
            status['scheduler'] = scheduler.get_scheduler_status()
        
        return JsonResponse(status)
        
    except Exception as e:
        logger.error(f"Error getting backup status: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def scheduler_control(request):
    """Control backup scheduler (AJAX endpoint)"""
    try:
        action = request.POST.get('action')
        
        scheduler = get_backup_scheduler()
        if not scheduler:
            scheduler = initialize_backup_scheduler()
        
        if not scheduler:
            return JsonResponse({'error': 'Scheduler not available'}, status=500)
        
        if action == 'start':
            scheduler.start()
            return JsonResponse({'success': True, 'message': 'Scheduler started'})
        elif action == 'stop':
            scheduler.stop()
            return JsonResponse({'success': True, 'message': 'Scheduler stopped'})
        elif action == 'force_full':
            success = scheduler.force_full_backup()
            if success:
                return JsonResponse({'success': True, 'message': 'Full backup started'})
            else:
                return JsonResponse({'error': 'Failed to start full backup'}, status=500)
        elif action == 'force_incremental':
            success = scheduler.force_incremental_backup()
            if success:
                return JsonResponse({'success': True, 'message': 'Incremental backup started'})
            else:
                return JsonResponse({'error': 'Failed to start incremental backup'}, status=500)
        elif action == 'force_cleanup':
            success = scheduler.force_cleanup()
            if success:
                return JsonResponse({'success': True, 'message': 'Cleanup started'})
            else:
                return JsonResponse({'error': 'Failed to start cleanup'}, status=500)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
    except Exception as e:
        logger.error(f"Error controlling scheduler: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def backup_detail(request, backup_id):
    """Show detailed information about a specific backup"""
    try:
        backup_manager = get_backup_manager()
        metadata = backup_manager.storage.load_metadata(backup_id)
        
        if not metadata:
            messages.error(request, f"Backup {backup_id} not found")
            return render(request, 'admin/backup_detail.html', {
                'error': f"Backup {backup_id} not found",
                'page_title': 'Backup Detail',
            })
        
        # Check if backup file exists
        from pathlib import Path
        backup_file_exists = Path(metadata.file_path).exists()
        
        context = {
            'metadata': metadata,
            'backup_file_exists': backup_file_exists,
            'size_mb': round(metadata.file_size / (1024 * 1024), 2),
            'page_title': f'Backup Detail - {backup_id}',
        }
        
        return render(request, 'admin/backup_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in backup detail: {e}")
        messages.error(request, f"Error loading backup detail: {e}")
        return render(request, 'admin/backup_detail.html', {
            'error': str(e),
            'page_title': 'Backup Detail',
        })


@staff_member_required
def download_backup(request, backup_id):
    """Download a backup file (for emergency purposes)"""
    try:
        backup_manager = get_backup_manager()
        metadata = backup_manager.storage.load_metadata(backup_id)
        
        if not metadata:
            return HttpResponse("Backup not found", status=404)
        
        from pathlib import Path
        backup_path = Path(metadata.file_path)
        
        if not backup_path.exists():
            return HttpResponse("Backup file not found", status=404)
        
        # Return encrypted backup file
        response = HttpResponse(
            backup_path.read_bytes(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{backup_id}.backup"'
        response['Content-Length'] = backup_path.stat().st_size
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading backup: {e}")
        return HttpResponse(f"Error downloading backup: {e}", status=500)