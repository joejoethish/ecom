"""
Management command to initialize the E2E Workflow Debugging System.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from apps.debugging.models import (
    DebugConfiguration, PerformanceThreshold, FrontendRoute, APICallDiscovery
)
from apps.debugging.config import ConfigValidator, DebuggingConfig
from apps.debugging.database_integration import DatabaseMonitor


class Command(BaseCommand):
    help = 'Initialize the E2E Workflow Debugging System'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force initialization even if system is already configured',
        )
        parser.add_argument(
            '--environment',
            type=str,
            choices=['development', 'production', 'testing'],
            help='Environment-specific configuration to apply',
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate configuration without making changes',
        )
        parser.add_argument(
            '--create-thresholds',
            action='store_true',
            help='Create default performance thresholds',
        )
        parser.add_argument(
            '--test-database',
            action='store_true',
            help='Test database connectivity and performance',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Initializing E2E Workflow Debugging System...')
        )
        
        try:
            # Validate configuration first
            if self._validate_configuration():
                self.stdout.write(
                    self.style.SUCCESS('✓ Configuration validation passed')
                )
            else:
                if not options['force']:
                    raise CommandError('Configuration validation failed. Use --force to proceed anyway.')
                self.stdout.write(
                    self.style.WARNING('⚠ Configuration validation failed, but proceeding due to --force flag')
                )
            
            if options['validate_only']:
                self.stdout.write(
                    self.style.SUCCESS('Configuration validation completed.')
                )
                return
            
            # Check if system is already initialized
            if self._is_system_initialized() and not options['force']:
                raise CommandError(
                    'Debugging system is already initialized. Use --force to reinitialize.'
                )
            
            with transaction.atomic():
                # Initialize configuration
                self._initialize_configuration(options.get('environment'))
                
                # Create performance thresholds
                if options['create_thresholds']:
                    self._create_performance_thresholds()
                
                # Test database connectivity
                if options['test_database']:
                    self._test_database_connectivity()
                
                # Initialize debugging tables
                self._initialize_debugging_tables()
                
                # Set up default configurations
                self._setup_default_configurations()
            
            self.stdout.write(
                self.style.SUCCESS('✓ E2E Workflow Debugging System initialized successfully!')
            )
            
            # Display system status
            self._display_system_status()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to initialize debugging system: {str(e)}')
            )
            raise CommandError(f'Initialization failed: {str(e)}')
    
    def _validate_configuration(self):
        """Validate the debugging system configuration"""
        self.stdout.write('Validating configuration...')
        
        validator = ConfigValidator()
        results = validator.validate_configuration()
        
        if results['errors']:
            self.stdout.write(
                self.style.ERROR('Configuration errors found:')
            )
            for error in results['errors']:
                self.stdout.write(f'  ✗ {error}')
        
        if results['warnings']:
            self.stdout.write(
                self.style.WARNING('Configuration warnings:')
            )
            for warning in results['warnings']:
                self.stdout.write(f'  ⚠ {warning}')
        
        if results['recommendations']:
            self.stdout.write('Recommendations:')
            for recommendation in results['recommendations']:
                self.stdout.write(f'  💡 {recommendation}')
        
        return results['valid']
    
    def _is_system_initialized(self):
        """Check if the debugging system is already initialized"""
        return DebugConfiguration.objects.filter(
            name='system_initialized',
            enabled=True
        ).exists()
    
    def _initialize_configuration(self, environment=None):
        """Initialize debugging system configuration"""
        self.stdout.write('Initializing configuration...')
        
        config = DebuggingConfig()
        
        # Apply environment-specific configuration if specified
        if environment:
            self.stdout.write(f'Applying {environment} environment configuration...')
            # Environment-specific logic would go here
        
        # Create system initialization marker
        from django.utils import timezone
        
        DebugConfiguration.objects.update_or_create(
            name='system_initialized',
            defaults={
                'config_type': 'system_status',
                'enabled': True,
                'config_data': {
                    'initialized_at': str(timezone.now()),
                    'environment': environment or 'default',
                    'version': '1.0.0'
                },
                'description': 'System initialization marker'
            }
        )
        
        self.stdout.write('✓ Configuration initialized')
    
    def _create_performance_thresholds(self):
        """Create default performance thresholds"""
        self.stdout.write('Creating performance thresholds...')
        
        default_thresholds = [
            # API Response Time Thresholds
            {
                'metric_name': 'response_time',
                'layer': 'api',
                'warning_threshold': 500.0,
                'critical_threshold': 2000.0,
            },
            # Database Query Time Thresholds
            {
                'metric_name': 'query_time',
                'layer': 'database',
                'warning_threshold': 100.0,
                'critical_threshold': 1000.0,
            },
            # Memory Usage Thresholds
            {
                'metric_name': 'memory_usage',
                'layer': 'system',
                'warning_threshold': 80.0,
                'critical_threshold': 95.0,
            },
            # Error Rate Thresholds
            {
                'metric_name': 'error_rate',
                'layer': 'api',
                'warning_threshold': 5.0,
                'critical_threshold': 10.0,
            },
            # Frontend Performance Thresholds
            {
                'metric_name': 'render_time',
                'layer': 'frontend',
                'warning_threshold': 100.0,
                'critical_threshold': 500.0,
            },
        ]
        
        created_count = 0
        for threshold_data in default_thresholds:
            threshold, created = PerformanceThreshold.objects.update_or_create(
                metric_name=threshold_data['metric_name'],
                layer=threshold_data['layer'],
                component=None,
                defaults={
                    'warning_threshold': threshold_data['warning_threshold'],
                    'critical_threshold': threshold_data['critical_threshold'],
                    'enabled': True,
                    'alert_on_warning': True,
                    'alert_on_critical': True,
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} performance thresholds')
    
    def _test_database_connectivity(self):
        """Test database connectivity and performance"""
        self.stdout.write('Testing database connectivity...')
        
        monitor = DatabaseMonitor()
        
        # Test database health
        health_info = monitor.check_database_health()
        
        if health_info['status'] == 'healthy':
            self.stdout.write(
                f'✓ Database connection healthy (response time: {health_info["connection_time_ms"]:.2f}ms)'
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Database connection failed: {health_info.get("error", "Unknown error")}')
            )
            raise CommandError('Database connectivity test failed')
        
        # Test migration status
        migration_status = monitor.check_migration_status()
        
        if migration_status['status'] == 'up_to_date':
            self.stdout.write('✓ Database migrations are up to date')
        elif migration_status['status'] == 'pending_migrations':
            self.stdout.write(
                self.style.WARNING(f'⚠ {migration_status["pending_migrations"]} pending migrations found')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Migration check failed: {migration_status.get("error", "Unknown error")}')
            )
        
        # Test database integrity
        integrity_results = monitor.validate_database_integrity()
        
        if integrity_results['status'] == 'healthy':
            self.stdout.write('✓ Database integrity check passed')
        elif integrity_results['status'] == 'issues_found':
            self.stdout.write(
                self.style.WARNING(f'⚠ Database integrity issues found: {len(integrity_results["foreign_key_violations"])} FK violations')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Database integrity check failed: {integrity_results.get("error", "Unknown error")}')
            )
    
    def _initialize_debugging_tables(self):
        """Initialize debugging system database tables"""
        self.stdout.write('Initializing debugging tables...')
        
        # The tables should already be created by migrations
        # This method can be used for any additional table setup
        
        # Clear old data if reinitializing
        from apps.debugging.models import WorkflowSession, TraceStep, PerformanceSnapshot, ErrorLog
        
        # Keep recent data (last 24 hours) but clear older data
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        old_sessions = WorkflowSession.objects.filter(start_time__lt=cutoff_time)
        old_metrics = PerformanceSnapshot.objects.filter(timestamp__lt=cutoff_time)
        old_errors = ErrorLog.objects.filter(timestamp__lt=cutoff_time)
        
        deleted_sessions = old_sessions.count()
        deleted_metrics = old_metrics.count()
        deleted_errors = old_errors.count()
        
        old_sessions.delete()
        old_metrics.delete()
        old_errors.delete()
        
        if deleted_sessions > 0 or deleted_metrics > 0 or deleted_errors > 0:
            self.stdout.write(
                f'✓ Cleaned up old data: {deleted_sessions} sessions, {deleted_metrics} metrics, {deleted_errors} errors'
            )
        
        self.stdout.write('✓ Debugging tables initialized')
    
    def _setup_default_configurations(self):
        """Set up default debugging configurations"""
        self.stdout.write('Setting up default configurations...')
        
        default_configs = [
            {
                'name': 'performance_monitoring',
                'config_type': 'performance_threshold',
                'config_data': {
                    'enabled': True,
                    'real_time_updates': True,
                    'collection_interval': 30,
                    'batch_size': 100,
                    'retention_days': 30,
                },
                'description': 'Performance monitoring configuration'
            },
            {
                'name': 'workflow_tracing',
                'config_type': 'tracing_enabled',
                'config_data': {
                    'enabled': True,
                    'max_trace_steps': 100,
                    'timeout_seconds': 300,
                    'detailed_logging': False,
                    'retention_days': 7,
                },
                'description': 'Workflow tracing configuration'
            },
            {
                'name': 'error_tracking',
                'config_type': 'logging_level',
                'config_data': {
                    'enabled': True,
                    'log_retention_days': 90,
                    'alert_on_critical': True,
                    'grouping_enabled': True,
                    'auto_resolution_enabled': False,
                },
                'description': 'Error tracking configuration'
            },
            {
                'name': 'dashboard_settings',
                'config_type': 'dashboard_settings',
                'config_data': {
                    'enabled': True,
                    'real_time_updates': True,
                    'websocket_enabled': True,
                    'update_interval_seconds': 5,
                    'authentication_required': True,
                    'admin_only': False,
                },
                'description': 'Dashboard configuration'
            },
        ]
        
        created_count = 0
        for config_data in default_configs:
            config, created = DebugConfiguration.objects.update_or_create(
                name=config_data['name'],
                defaults={
                    'config_type': config_data['config_type'],
                    'enabled': True,
                    'config_data': config_data['config_data'],
                    'description': config_data['description'],
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} default configurations')
    
    def _display_system_status(self):
        """Display current system status"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('DEBUGGING SYSTEM STATUS')
        self.stdout.write('='*50)
        
        config = DebuggingConfig()
        
        # System status
        self.stdout.write(f'Environment: {config.get_environment_config()}')
        self.stdout.write(f'System Enabled: {config.get("debugging_system", "ENABLED", False)}')
        
        # Feature status
        self.stdout.write('\nFeature Status:')
        features = [
            ('Performance Monitoring', 'PERFORMANCE_MONITORING_ENABLED'),
            ('Workflow Tracing', 'WORKFLOW_TRACING_ENABLED'),
            ('Error Tracking', 'ERROR_TRACKING_ENABLED'),
            ('Route Discovery', 'ROUTE_DISCOVERY_ENABLED'),
            ('API Validation', 'API_VALIDATION_ENABLED'),
            ('Database Monitoring', 'DATABASE_MONITORING_ENABLED'),
        ]
        
        for feature_name, feature_key in features:
            enabled = config.get('debugging_system', feature_key, False)
            status = '✓' if enabled else '✗'
            self.stdout.write(f'  {status} {feature_name}: {"Enabled" if enabled else "Disabled"}')
        
        # Dashboard status
        dashboard_enabled = config.get('debugging_dashboard', 'ENABLED', False)
        self.stdout.write(f'\nDashboard: {"Enabled" if dashboard_enabled else "Disabled"}')
        
        if dashboard_enabled:
            websocket_enabled = config.get('debugging_dashboard', 'WEBSOCKET_ENABLED', False)
            real_time = config.get('debugging_dashboard', 'REAL_TIME_UPDATES', False)
            self.stdout.write(f'  WebSocket: {"Enabled" if websocket_enabled else "Disabled"}')
            self.stdout.write(f'  Real-time Updates: {"Enabled" if real_time else "Disabled"}')
        
        # Performance thresholds
        threshold_count = PerformanceThreshold.objects.filter(enabled=True).count()
        self.stdout.write(f'\nPerformance Thresholds: {threshold_count} configured')
        
        # Configuration count
        config_count = DebugConfiguration.objects.filter(enabled=True).count()
        self.stdout.write(f'Active Configurations: {config_count}')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Initialization completed successfully!')
        self.stdout.write('='*50)