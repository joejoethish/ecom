"""
Web-based migration monitoring interface.
Provides real-time migration progress tracking and control via HTTP API.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View

from .zero_downtime_migration import MigrationStage

logger = logging.getLogger(__name__)


class MigrationMonitorAPI:
    """API for migration monitoring and control"""
    
    CACHE_PREFIX = "migration_progress_"
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_active_migrations() -> List[Dict[str, Any]]:
        """Get list of active migrations"""
        try:
            # Get all migration cache keys
            if hasattr(cache, 'keys'):
                cache_keys = cache.keys(f"{MigrationMonitorAPI.CACHE_PREFIX}*")
            else:
                # Fallback for cache backends that don't support keys()
                cache_keys = []
            
            active_migrations = []
            
            for cache_key in cache_keys:
                migration_data = cache.get(cache_key)
                if migration_data:
                    migration_id = cache_key.replace(MigrationMonitorAPI.CACHE_PREFIX, '')
                    migration_data['migration_id'] = migration_id
                    active_migrations.append(migration_data)
            
            return active_migrations
            
        except Exception as e:
            logger.error(f"Error getting active migrations: {e}")
            return []
    
    @staticmethod
    def get_migration_status(migration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific migration"""
        try:
            cache_key = f"{MigrationMonitorAPI.CACHE_PREFIX}{migration_id}"
            migration_data = cache.get(cache_key)
            
            if migration_data:
                migration_data['migration_id'] = migration_id
                return migration_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting migration status for {migration_id}: {e}")
            return None
    
    @staticmethod
    def get_migration_history() -> List[Dict[str, Any]]:
        """Get migration history from log files"""
        try:
            migration_logs_dir = settings.BASE_DIR / 'migration_logs'
            if not migration_logs_dir.exists():
                return []
            
            history = []
            
            # Look for migration report files
            for report_file in migration_logs_dir.glob('migration_report_*.json'):
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                        history.append(report_data)
                except Exception as e:
                    logger.warning(f"Error reading migration report {report_file}: {e}")
            
            # Sort by completion time
            history.sort(key=lambda x: x.get('completion_time', ''), reverse=True)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting migration history: {e}")
            return []
    
    @staticmethod
    def calculate_migration_statistics(migrations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate migration statistics"""
        if not migrations:
            return {
                'total_migrations': 0,
                'successful_migrations': 0,
                'failed_migrations': 0,
                'average_duration': 0,
                'total_records_migrated': 0
            }
        
        successful = [m for m in migrations if m.get('success', False)]
        failed = [m for m in migrations if not m.get('success', False)]
        
        # Calculate average duration for successful migrations
        durations = []
        total_records = 0
        
        for migration in successful:
            metrics = migration.get('metrics', {})
            if metrics.get('elapsed_time_seconds'):
                durations.append(metrics['elapsed_time_seconds'])
            if metrics.get('records_migrated'):
                total_records += metrics['records_migrated']
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_migrations': len(migrations),
            'successful_migrations': len(successful),
            'failed_migrations': len(failed),
            'success_rate': len(successful) / len(migrations) * 100 if migrations else 0,
            'average_duration': avg_duration,
            'total_records_migrated': total_records
        }


@method_decorator(csrf_exempt, name='dispatch')
class MigrationMonitorView(View):
    """Web view for migration monitoring"""
    
    def get(self, request, migration_id=None):
        """Get migration status or list of migrations"""
        try:
            if migration_id:
                # Get specific migration status
                status = MigrationMonitorAPI.get_migration_status(migration_id)
                if status:
                    return JsonResponse({
                        'success': True,
                        'data': status
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Migration not found'
                    }, status=404)
            else:
                # Get all active migrations
                active_migrations = MigrationMonitorAPI.get_active_migrations()
                return JsonResponse({
                    'success': True,
                    'data': {
                        'active_migrations': active_migrations,
                        'count': len(active_migrations)
                    }
                })
                
        except Exception as e:
            logger.error(f"Error in migration monitor view: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MigrationHistoryView(View):
    """Web view for migration history"""
    
    def get(self, request):
        """Get migration history and statistics"""
        try:
            history = MigrationMonitorAPI.get_migration_history()
            statistics = MigrationMonitorAPI.calculate_migration_statistics(history)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'history': history,
                    'statistics': statistics
                }
            })
            
        except Exception as e:
            logger.error(f"Error in migration history view: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MigrationControlView(View):
    """Web view for migration control operations"""
    
    def post(self, request, migration_id, action):
        """Control migration (stop, rollback, etc.)"""
        try:
            # Validate action
            valid_actions = ['stop', 'rollback', 'pause', 'resume']
            if action not in valid_actions:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid action. Valid actions: {valid_actions}'
                }, status=400)
            
            # Check if migration exists
            status = MigrationMonitorAPI.get_migration_status(migration_id)
            if not status:
                return JsonResponse({
                    'success': False,
                    'error': 'Migration not found'
                }, status=404)
            
            # TODO: Implement actual migration control
            # This would require IPC mechanism or database coordination
            # For now, just log the request
            logger.info(f"Migration control request: {action} for migration {migration_id}")
            
            return JsonResponse({
                'success': True,
                'message': f'Migration {action} requested',
                'migration_id': migration_id,
                'action': action
            })
            
        except Exception as e:
            logger.error(f"Error in migration control view: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


def migration_dashboard(request):
    """Render migration dashboard HTML"""
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Migration Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            transition: width 0.3s ease;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-running { background-color: #2196F3; color: white; }
        .status-completed { background-color: #4CAF50; color: white; }
        .status-failed { background-color: #f44336; color: white; }
        .status-rolled-back { background-color: #FF9800; color: white; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .metric {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        .refresh-btn {
            background: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .refresh-btn:hover {
            background: #1976D2;
        }
        .error {
            color: #f44336;
            background: #ffebee;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Zero-Downtime Migration Dashboard</h1>
            <button class="refresh-btn" onclick="refreshData()">Refresh</button>
        </div>
        
        <div id="loading" class="loading">Loading migration data...</div>
        <div id="error" class="error" style="display: none;"></div>
        
        <div id="active-migrations" style="display: none;">
            <div class="card">
                <h2>Active Migrations</h2>
                <div id="active-migrations-list"></div>
            </div>
        </div>
        
        <div id="statistics" style="display: none;">
            <div class="card">
                <h2>Migration Statistics</h2>
                <div class="grid" id="statistics-grid"></div>
            </div>
        </div>
        
        <div id="history" style="display: none;">
            <div class="card">
                <h2>Recent Migrations</h2>
                <div id="history-list"></div>
            </div>
        </div>
    </div>

    <script>
        let refreshInterval;
        
        function showError(message) {
            document.getElementById('error').textContent = message;
            document.getElementById('error').style.display = 'block';
            document.getElementById('loading').style.display = 'none';
        }
        
        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
        
        function formatDuration(seconds) {
            if (!seconds) return 'N/A';
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            return `${hours}h ${minutes}m ${secs}s`;
        }
        
        function formatNumber(num) {
            return new Intl.NumberFormat().format(num);
        }
        
        function getStatusBadge(stage, success, rollbackTriggered) {
            if (rollbackTriggered) return '<span class="status-badge status-rolled-back">Rolled Back</span>';
            if (stage === 'completed') return '<span class="status-badge status-completed">Completed</span>';
            if (stage === 'failed') return '<span class="status-badge status-failed">Failed</span>';
            return '<span class="status-badge status-running">Running</span>';
        }
        
        function renderActiveMigrations(migrations) {
            const container = document.getElementById('active-migrations-list');
            
            if (migrations.length === 0) {
                container.innerHTML = '<p>No active migrations</p>';
                return;
            }
            
            let html = '';
            migrations.forEach(migration => {
                const progress = migration.progress_percentage || 0;
                const stage = migration.stage || 'unknown';
                const stageName = stage.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                
                html += `
                    <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong>Migration ID: ${migration.migration_id || 'Unknown'}</strong>
                            ${getStatusBadge(stage, false, false)}
                        </div>
                        <div><strong>Stage:</strong> ${stageName}</div>
                        <div><strong>Progress:</strong> ${progress.toFixed(1)}%</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px;">
                            <div><strong>Records:</strong> ${formatNumber(migration.records_migrated || 0)} / ${formatNumber(migration.total_records || 0)}</div>
                            <div><strong>Speed:</strong> ${formatNumber(migration.migration_speed || 0)} rec/s</div>
                            <div><strong>Errors:</strong> ${migration.error_count || 0}</div>
                            <div><strong>ETA:</strong> ${migration.estimated_completion ? new Date(migration.estimated_completion).toLocaleTimeString() : 'N/A'}</div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function renderStatistics(stats) {
            const container = document.getElementById('statistics-grid');
            
            const metrics = [
                { label: 'Total Migrations', value: stats.total_migrations || 0 },
                { label: 'Successful', value: stats.successful_migrations || 0 },
                { label: 'Failed', value: stats.failed_migrations || 0 },
                { label: 'Success Rate', value: `${(stats.success_rate || 0).toFixed(1)}%` },
                { label: 'Avg Duration', value: formatDuration(stats.average_duration) },
                { label: 'Total Records', value: formatNumber(stats.total_records_migrated || 0) }
            ];
            
            let html = '';
            metrics.forEach(metric => {
                html += `
                    <div class="metric">
                        <div class="metric-value">${metric.value}</div>
                        <div class="metric-label">${metric.label}</div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function renderHistory(history) {
            const container = document.getElementById('history-list');
            
            if (history.length === 0) {
                container.innerHTML = '<p>No migration history available</p>';
                return;
            }
            
            let html = '';
            history.slice(0, 10).forEach(migration => {  // Show last 10
                const completionTime = migration.completion_time ? 
                    new Date(migration.completion_time).toLocaleString() : 'Unknown';
                const duration = migration.metrics ? 
                    formatDuration(migration.metrics.elapsed_time_seconds) : 'N/A';
                const records = migration.metrics ? 
                    formatNumber(migration.metrics.records_migrated || 0) : '0';
                
                html += `
                    <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong>Migration ID: ${migration.migration_id || 'Unknown'}</strong>
                            ${getStatusBadge(migration.final_stage, migration.success, migration.rollback_triggered)}
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                            <div><strong>Completed:</strong> ${completionTime}</div>
                            <div><strong>Duration:</strong> ${duration}</div>
                            <div><strong>Records:</strong> ${records}</div>
                            <div><strong>Final Stage:</strong> ${(migration.final_stage || '').replace(/_/g, ' ')}</div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        async function loadData() {
            try {
                hideError();
                
                // Load active migrations
                const activeResponse = await fetch('/api/migration/monitor/');
                const activeData = await activeResponse.json();
                
                if (activeData.success) {
                    document.getElementById('active-migrations').style.display = 'block';
                    renderActiveMigrations(activeData.data.active_migrations);
                }
                
                // Load history and statistics
                const historyResponse = await fetch('/api/migration/history/');
                const historyData = await historyResponse.json();
                
                if (historyData.success) {
                    document.getElementById('statistics').style.display = 'block';
                    document.getElementById('history').style.display = 'block';
                    renderStatistics(historyData.data.statistics);
                    renderHistory(historyData.data.history);
                }
                
                document.getElementById('loading').style.display = 'none';
                
            } catch (error) {
                showError('Failed to load migration data: ' + error.message);
            }
        }
        
        function refreshData() {
            loadData();
        }
        
        function startAutoRefresh() {
            refreshInterval = setInterval(loadData, 5000);  // Refresh every 5 seconds
        }
        
        function stopAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
            startAutoRefresh();
        });
        
        // Stop auto-refresh when page is hidden
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopAutoRefresh();
            } else {
                startAutoRefresh();
            }
        });
    </script>
</body>
</html>
    """
    
    return HttpResponse(dashboard_html, content_type='text/html')


# URL patterns for migration monitoring
def get_migration_monitor_urls():
    """Get URL patterns for migration monitoring"""
    from django.urls import path
    
    return [
        path('api/migration/monitor/', MigrationMonitorView.as_view(), name='migration_monitor'),
        path('api/migration/monitor/<str:migration_id>/', MigrationMonitorView.as_view(), name='migration_monitor_detail'),
        path('api/migration/history/', MigrationHistoryView.as_view(), name='migration_history'),
        path('api/migration/control/<str:migration_id>/<str:action>/', MigrationControlView.as_view(), name='migration_control'),
        path('migration/dashboard/', migration_dashboard, name='migration_dashboard'),
    ]