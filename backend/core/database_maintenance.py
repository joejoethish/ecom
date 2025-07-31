"""
Database Maintenance and Cleanup System for MySQL Integration

This module provides comprehensive database maintenance capabilities including:
- Automated index maintenance and optimization
- Old data archiving and cleanup procedures
- Database statistics collection and analysis
- Maintenance scheduling and monitoring
- Performance optimization recommendations
"""

import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from django.db import connections, connection, transaction
from django.db.utils import OperationalError, DatabaseError
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


@dataclass
class MaintenanceTask:
    """Database maintenance task data structure"""
    task_id: str
    task_name: str
    task_type: str  # index_maintenance, data_cleanup, statistics, optimization
    database_alias: str
    status: str  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    rows_affected: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        if data['started_at']:
            data['started_at'] = self.started_at.isoformat()
        if data['completed_at']:
            data['completed_at'] = self.completed_at.isoformat()
        return data


@dataclass
class IndexMaintenanceResult:
    """Index maintenance operation result"""
    table_name: str
    index_name: str
    operation: str  # analyze, optimize, rebuild
    before_size_mb: float
    after_size_mb: float
    duration_seconds: float
    rows_processed: int
    fragmentation_before: float
    fragmentation_after: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class CleanupResult:
    """Data cleanup operation result"""
    table_name: str
    cleanup_type: str  # archive, delete, purge
    rows_affected: int
    data_size_freed_mb: float
    duration_seconds: float
    criteria: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class DatabaseStatistics:
    """Database statistics collection result"""
    database_alias: str
    timestamp: datetime
    total_tables: int
    total_indexes: int
    total_size_mb: float
    data_size_mb: float
    index_size_mb: float
    fragmentation_percent: float
    table_statistics: Dict[str, Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class IndexMaintenanceManager:
    """Manages database index maintenance operations"""
    
    def __init__(self, database_alias: str = 'default'):
        self.database_alias = database_alias
        self.maintenance_thresholds = {
            'fragmentation_threshold': getattr(settings, 'DB_FRAGMENTATION_THRESHOLD', 30.0),
            'size_threshold_mb': getattr(settings, 'DB_INDEX_SIZE_THRESHOLD', 100.0),
            'analyze_threshold_days': getattr(settings, 'DB_ANALYZE_THRESHOLD_DAYS', 7),
        }
    
    def analyze_all_tables(self) -> List[IndexMaintenanceResult]:
        """Analyze all tables and update statistics"""
        results = []
        
        try:
            db_connection = connections[self.database_alias]
            
            with db_connection.cursor() as cursor:
                # Get all tables in the database
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_type = 'BASE TABLE'
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                
                for table_name in tables:
                    try:
                        result = self._analyze_table(cursor, table_name)
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Failed to analyze table {table_name}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Failed to analyze tables: {e}")
            raise
        
        return results
    
    def _analyze_table(self, cursor, table_name: str) -> Optional[IndexMaintenanceResult]:
        """Analyze a specific table"""
        start_time = time.time()
        
        try:
            # Get table size before analysis
            cursor.execute(f"""
                SELECT 
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                    ROUND((data_length / 1024 / 1024), 2) AS data_size_mb,
                    ROUND((index_length / 1024 / 1024), 2) AS index_size_mb,
                    table_rows
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, [table_name])
            
            table_info = cursor.fetchone()
            if not table_info:
                return None
            
            before_size_mb = float(table_info[0] or 0)
            rows_processed = int(table_info[3] or 0)
            
            # Run ANALYZE TABLE
            cursor.execute(f"ANALYZE TABLE `{table_name}`")
            analyze_result = cursor.fetchall()
            
            # Get fragmentation information
            fragmentation_before = self._get_table_fragmentation(cursor, table_name)
            
            duration_seconds = time.time() - start_time
            
            return IndexMaintenanceResult(
                table_name=table_name,
                index_name='ALL',
                operation='analyze',
                before_size_mb=before_size_mb,
                after_size_mb=before_size_mb,  # ANALYZE doesn't change size
                duration_seconds=duration_seconds,
                rows_processed=rows_processed,
                fragmentation_before=fragmentation_before,
                fragmentation_after=fragmentation_before
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {e}")
            return None
    
    def optimize_fragmented_tables(self) -> List[IndexMaintenanceResult]:
        """Optimize tables with high fragmentation"""
        results = []
        
        try:
            db_connection = connections[self.database_alias]
            
            with db_connection.cursor() as cursor:
                # Find fragmented tables
                fragmented_tables = self._find_fragmented_tables(cursor)
                
                for table_name, fragmentation in fragmented_tables:
                    try:
                        result = self._optimize_table(cursor, table_name)
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Failed to optimize table {table_name}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Failed to optimize fragmented tables: {e}")
            raise
        
        return results
    
    def _find_fragmented_tables(self, cursor) -> List[Tuple[str, float]]:
        """Find tables with high fragmentation"""
        cursor.execute(f"""
            SELECT 
                table_name,
                ROUND(data_free / (data_length + index_length + data_free) * 100, 2) as fragmentation
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_type = 'BASE TABLE'
            AND (data_length + index_length) > {self.maintenance_thresholds['size_threshold_mb'] * 1024 * 1024}
            AND data_free / (data_length + index_length + data_free) * 100 > {self.maintenance_thresholds['fragmentation_threshold']}
            ORDER BY fragmentation DESC
        """)
        
        return cursor.fetchall()
    
    def _optimize_table(self, cursor, table_name: str) -> Optional[IndexMaintenanceResult]:
        """Optimize a specific table"""
        start_time = time.time()
        
        try:
            # Get table info before optimization
            cursor.execute(f"""
                SELECT 
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                    table_rows,
                    ROUND(data_free / (data_length + index_length + data_free) * 100, 2) as fragmentation
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, [table_name])
            
            before_info = cursor.fetchone()
            if not before_info:
                return None
            
            before_size_mb = float(before_info[0] or 0)
            rows_processed = int(before_info[1] or 0)
            fragmentation_before = float(before_info[2] or 0)
            
            # Run OPTIMIZE TABLE
            cursor.execute(f"OPTIMIZE TABLE `{table_name}`")
            optimize_result = cursor.fetchall()
            
            # Get table info after optimization
            cursor.execute(f"""
                SELECT 
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                    ROUND(data_free / (data_length + index_length + data_free) * 100, 2) as fragmentation
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, [table_name])
            
            after_info = cursor.fetchone()
            after_size_mb = float(after_info[0] or 0) if after_info else before_size_mb
            fragmentation_after = float(after_info[1] or 0) if after_info else fragmentation_before
            
            duration_seconds = time.time() - start_time
            
            logger.info(f"Optimized table {table_name}: {before_size_mb}MB -> {after_size_mb}MB, "
                       f"fragmentation: {fragmentation_before}% -> {fragmentation_after}%")
            
            return IndexMaintenanceResult(
                table_name=table_name,
                index_name='ALL',
                operation='optimize',
                before_size_mb=before_size_mb,
                after_size_mb=after_size_mb,
                duration_seconds=duration_seconds,
                rows_processed=rows_processed,
                fragmentation_before=fragmentation_before,
                fragmentation_after=fragmentation_after
            )
            
        except Exception as e:
            logger.error(f"Failed to optimize table {table_name}: {e}")
            return None
    
    def _get_table_fragmentation(self, cursor, table_name: str) -> float:
        """Get table fragmentation percentage"""
        try:
            cursor.execute(f"""
                SELECT ROUND(data_free / (data_length + index_length + data_free) * 100, 2) as fragmentation
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, [table_name])
            
            result = cursor.fetchone()
            return float(result[0] or 0) if result else 0.0
            
        except Exception as e:
            logger.debug(f"Could not get fragmentation for {table_name}: {e}")
            return 0.0
    
    def rebuild_indexes(self, table_names: List[str] = None) -> List[IndexMaintenanceResult]:
        """Rebuild indexes for specified tables or all tables"""
        results = []
        
        try:
            db_connection = connections[self.database_alias]
            
            with db_connection.cursor() as cursor:
                if not table_names:
                    # Get all tables
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE() 
                        AND table_type = 'BASE TABLE'
                    """)
                    table_names = [row[0] for row in cursor.fetchall()]
                
                for table_name in table_names:
                    try:
                        # For MySQL, we use ALTER TABLE ... ENGINE=InnoDB to rebuild
                        result = self._rebuild_table_indexes(cursor, table_name)
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Failed to rebuild indexes for {table_name}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Failed to rebuild indexes: {e}")
            raise
        
        return results
    
    def _rebuild_table_indexes(self, cursor, table_name: str) -> Optional[IndexMaintenanceResult]:
        """Rebuild indexes for a specific table"""
        start_time = time.time()
        
        try:
            # Get table info before rebuild
            cursor.execute(f"""
                SELECT 
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                    table_rows
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, [table_name])
            
            before_info = cursor.fetchone()
            if not before_info:
                return None
            
            before_size_mb = float(before_info[0] or 0)
            rows_processed = int(before_info[1] or 0)
            
            # Rebuild table (this rebuilds all indexes)
            cursor.execute(f"ALTER TABLE `{table_name}` ENGINE=InnoDB")
            
            # Get table info after rebuild
            cursor.execute(f"""
                SELECT ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, [table_name])
            
            after_info = cursor.fetchone()
            after_size_mb = float(after_info[0] or 0) if after_info else before_size_mb
            
            duration_seconds = time.time() - start_time
            
            logger.info(f"Rebuilt indexes for table {table_name}: {before_size_mb}MB -> {after_size_mb}MB")
            
            return IndexMaintenanceResult(
                table_name=table_name,
                index_name='ALL',
                operation='rebuild',
                before_size_mb=before_size_mb,
                after_size_mb=after_size_mb,
                duration_seconds=duration_seconds,
                rows_processed=rows_processed,
                fragmentation_before=0.0,  # Will be 0 after rebuild
                fragmentation_after=0.0
            )
            
        except Exception as e:
            logger.error(f"Failed to rebuild indexes for {table_name}: {e}")
            return None


class DataCleanupManager:
    """Manages old data archiving and cleanup procedures"""
    
    def __init__(self, database_alias: str = 'default'):
        self.database_alias = database_alias
        self.cleanup_rules = self._load_cleanup_rules()
    
    def _load_cleanup_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load data cleanup rules from settings"""
        return getattr(settings, 'DATABASE_CLEANUP_RULES', {
            'django_session': {
                'table': 'django_session',
                'date_column': 'expire_date',
                'retention_days': 30,
                'cleanup_type': 'delete'
            },
            'admin_logentry': {
                'table': 'django_admin_log',
                'date_column': 'action_time',
                'retention_days': 90,
                'cleanup_type': 'archive'
            },
            'auth_user_old_passwords': {
                'table': 'auth_user_old_passwords',
                'date_column': 'created_at',
                'retention_days': 365,
                'cleanup_type': 'delete'
            },
            'notifications': {
                'table': 'notifications_notification',
                'date_column': 'created_at',
                'retention_days': 60,
                'cleanup_type': 'delete',
                'additional_criteria': 'is_read = 1'
            },
            'audit_logs': {
                'table': 'audit_log',
                'date_column': 'timestamp',
                'retention_days': 180,
                'cleanup_type': 'archive'
            },
            'password_reset_attempts': {
                'table': 'auth_password_reset_attempt',
                'date_column': 'created_at',
                'retention_days': 30,
                'cleanup_type': 'delete'
            }
        })
    
    def cleanup_old_data(self, dry_run: bool = False) -> List[CleanupResult]:
        """Clean up old data according to configured rules"""
        results = []
        
        for rule_name, rule_config in self.cleanup_rules.items():
            try:
                result = self._cleanup_table_data(rule_config, dry_run)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to cleanup {rule_name}: {e}")
                continue
        
        return results
    
    def _cleanup_table_data(self, rule_config: Dict[str, Any], dry_run: bool = False) -> Optional[CleanupResult]:
        """Clean up data for a specific table"""
        table_name = rule_config['table']
        date_column = rule_config['date_column']
        retention_days = rule_config['retention_days']
        cleanup_type = rule_config['cleanup_type']
        additional_criteria = rule_config.get('additional_criteria', '')
        
        start_time = time.time()
        
        try:
            db_connection = connections[self.database_alias]
            
            with db_connection.cursor() as cursor:
                # Check if table exists
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s
                """, [table_name])
                
                if cursor.fetchone()[0] == 0:
                    logger.warning(f"Table {table_name} does not exist, skipping cleanup")
                    return None
                
                # Calculate cutoff date
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                # Build WHERE clause
                where_clause = f"{date_column} < %s"
                params = [cutoff_date]
                
                if additional_criteria:
                    where_clause += f" AND {additional_criteria}"
                
                # Count rows to be affected
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE {where_clause}", params)
                rows_to_affect = cursor.fetchone()[0]
                
                if rows_to_affect == 0:
                    logger.info(f"No old data found in {table_name}")
                    return None
                
                # Get data size before cleanup
                cursor.execute(f"""
                    SELECT ROUND((data_length / 1024 / 1024), 2) AS data_size_mb
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s
                """, [table_name])
                
                before_size = cursor.fetchone()
                before_size_mb = float(before_size[0] or 0) if before_size else 0.0
                
                if dry_run:
                    logger.info(f"DRY RUN: Would {cleanup_type} {rows_to_affect} rows from {table_name}")
                    data_size_freed_mb = 0.0
                else:
                    # Perform cleanup based on type
                    if cleanup_type == 'delete':
                        cursor.execute(f"DELETE FROM `{table_name}` WHERE {where_clause}", params)
                    elif cleanup_type == 'archive':
                        # For archiving, we would typically move to an archive table
                        # For now, we'll just delete (in production, implement proper archiving)
                        cursor.execute(f"DELETE FROM `{table_name}` WHERE {where_clause}", params)
                    
                    # Get data size after cleanup
                    cursor.execute(f"""
                        SELECT ROUND((data_length / 1024 / 1024), 2) AS data_size_mb
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE() 
                        AND table_name = %s
                    """, [table_name])
                    
                    after_size = cursor.fetchone()
                    after_size_mb = float(after_size[0] or 0) if after_size else 0.0
                    data_size_freed_mb = before_size_mb - after_size_mb
                
                duration_seconds = time.time() - start_time
                
                criteria = f"{date_column} < {cutoff_date.strftime('%Y-%m-%d')}"
                if additional_criteria:
                    criteria += f" AND {additional_criteria}"
                
                logger.info(f"Cleaned up {rows_to_affect} rows from {table_name}, "
                           f"freed {data_size_freed_mb:.2f}MB")
                
                return CleanupResult(
                    table_name=table_name,
                    cleanup_type=cleanup_type,
                    rows_affected=rows_to_affect,
                    data_size_freed_mb=data_size_freed_mb,
                    duration_seconds=duration_seconds,
                    criteria=criteria
                )
                
        except Exception as e:
            logger.error(f"Failed to cleanup {table_name}: {e}")
            return None
    
    def archive_old_orders(self, days_old: int = 365, dry_run: bool = False) -> Optional[CleanupResult]:
        """Archive old completed orders"""
        start_time = time.time()
        
        try:
            db_connection = connections[self.database_alias]
            
            with db_connection.cursor() as cursor:
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                # Count orders to archive
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM orders_order 
                    WHERE created_at < %s 
                    AND status IN ('completed', 'delivered', 'cancelled')
                """, [cutoff_date])
                
                rows_to_archive = cursor.fetchone()[0]
                
                if rows_to_archive == 0:
                    return None
                
                if not dry_run:
                    # In a real implementation, you would move to an archive table
                    # For now, we'll just mark them as archived
                    cursor.execute("""
                        UPDATE orders_order 
                        SET archived = TRUE 
                        WHERE created_at < %s 
                        AND status IN ('completed', 'delivered', 'cancelled')
                        AND archived = FALSE
                    """, [cutoff_date])
                
                duration_seconds = time.time() - start_time
                
                return CleanupResult(
                    table_name='orders_order',
                    cleanup_type='archive',
                    rows_affected=rows_to_archive,
                    data_size_freed_mb=0.0,  # Not actually deleting
                    duration_seconds=duration_seconds,
                    criteria=f"created_at < {cutoff_date.strftime('%Y-%m-%d')} AND status completed"
                )
                
        except Exception as e:
            logger.error(f"Failed to archive old orders: {e}")
            return None


class DatabaseStatisticsCollector:
    """Collects and analyzes database statistics"""
    
    def __init__(self, database_alias: str = 'default'):
        self.database_alias = database_alias
    
    def collect_database_statistics(self) -> DatabaseStatistics:
        """Collect comprehensive database statistics"""
        try:
            db_connection = connections[self.database_alias]
            
            with db_connection.cursor() as cursor:
                # Get overall database statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_tables,
                        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as total_size_mb,
                        ROUND(SUM(data_length) / 1024 / 1024, 2) as data_size_mb,
                        ROUND(SUM(index_length) / 1024 / 1024, 2) as index_size_mb,
                        ROUND(AVG(data_free / (data_length + index_length + data_free) * 100), 2) as avg_fragmentation
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_type = 'BASE TABLE'
                """)
                
                db_stats = cursor.fetchone()
                
                # Get index count
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.statistics 
                    WHERE table_schema = DATABASE()
                """)
                
                total_indexes = cursor.fetchone()[0]
                
                # Get detailed table statistics
                table_statistics = self._collect_table_statistics(cursor)
                
                return DatabaseStatistics(
                    database_alias=self.database_alias,
                    timestamp=datetime.now(),
                    total_tables=int(db_stats[0] or 0),
                    total_indexes=total_indexes,
                    total_size_mb=float(db_stats[1] or 0),
                    data_size_mb=float(db_stats[2] or 0),
                    index_size_mb=float(db_stats[3] or 0),
                    fragmentation_percent=float(db_stats[4] or 0),
                    table_statistics=table_statistics
                )
                
        except Exception as e:
            logger.error(f"Failed to collect database statistics: {e}")
            raise
    
    def _collect_table_statistics(self, cursor) -> Dict[str, Dict[str, Any]]:
        """Collect detailed statistics for each table"""
        cursor.execute("""
            SELECT 
                table_name,
                table_rows,
                ROUND((data_length / 1024 / 1024), 2) as data_size_mb,
                ROUND((index_length / 1024 / 1024), 2) as index_size_mb,
                ROUND(data_free / (data_length + index_length + data_free) * 100, 2) as fragmentation,
                engine,
                table_collation,
                create_time,
                update_time
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_type = 'BASE TABLE'
            ORDER BY (data_length + index_length) DESC
        """)
        
        table_stats = {}
        
        for row in cursor.fetchall():
            table_name = row[0]
            table_stats[table_name] = {
                'row_count': int(row[1] or 0),
                'data_size_mb': float(row[2] or 0),
                'index_size_mb': float(row[3] or 0),
                'fragmentation_percent': float(row[4] or 0),
                'engine': row[5],
                'collation': row[6],
                'created_at': row[7].isoformat() if row[7] else None,
                'updated_at': row[8].isoformat() if row[8] else None,
                'total_size_mb': float(row[2] or 0) + float(row[3] or 0)
            }
        
        return table_stats
    
    def analyze_growth_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """Analyze database growth trends"""
        try:
            # Get historical statistics from cache or database
            historical_stats = []
            
            for i in range(days_back):
                date = datetime.now() - timedelta(days=i)
                cache_key = f"db_stats_{self.database_alias}_{date.strftime('%Y%m%d')}"
                stats = cache.get(cache_key)
                
                if stats:
                    historical_stats.append(stats)
            
            if len(historical_stats) < 2:
                return {'error': 'Insufficient historical data for trend analysis'}
            
            # Calculate growth trends
            latest = historical_stats[0]
            oldest = historical_stats[-1]
            
            days_span = len(historical_stats) - 1
            
            size_growth_mb = latest['total_size_mb'] - oldest['total_size_mb']
            size_growth_rate = (size_growth_mb / oldest['total_size_mb'] * 100) if oldest['total_size_mb'] > 0 else 0
            
            return {
                'analysis_period_days': days_span,
                'size_growth_mb': size_growth_mb,
                'size_growth_rate_percent': size_growth_rate,
                'daily_growth_mb': size_growth_mb / days_span if days_span > 0 else 0,
                'projected_size_30_days': latest['total_size_mb'] + (size_growth_mb / days_span * 30),
                'fragmentation_trend': latest['fragmentation_percent'] - oldest['fragmentation_percent']
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze growth trends: {e}")
            return {'error': str(e)}


class DatabaseMaintenanceScheduler:
    """Schedules and monitors database maintenance tasks"""
    
    def __init__(self, database_alias: str = 'default'):
        self.database_alias = database_alias
        self.index_manager = IndexMaintenanceManager(database_alias)
        self.cleanup_manager = DataCleanupManager(database_alias)
        self.stats_collector = DatabaseStatisticsCollector(database_alias)
        self.maintenance_history = []
    
    def run_full_maintenance(self, dry_run: bool = False) -> Dict[str, Any]:
        """Run complete database maintenance routine"""
        maintenance_start = time.time()
        results = {
            'started_at': datetime.now().isoformat(),
            'database_alias': self.database_alias,
            'dry_run': dry_run,
            'tasks': []
        }
        
        try:
            # 1. Collect statistics before maintenance
            logger.info("Collecting database statistics...")
            stats_before = self.stats_collector.collect_database_statistics()
            results['statistics_before'] = stats_before.to_dict()
            
            # 2. Analyze and optimize tables
            logger.info("Analyzing all tables...")
            analyze_results = self.index_manager.analyze_all_tables()
            results['tasks'].append({
                'task_type': 'analyze_tables',
                'results': [r.to_dict() for r in analyze_results],
                'summary': f"Analyzed {len(analyze_results)} tables"
            })
            
            # 3. Optimize fragmented tables
            logger.info("Optimizing fragmented tables...")
            optimize_results = self.index_manager.optimize_fragmented_tables()
            results['tasks'].append({
                'task_type': 'optimize_tables',
                'results': [r.to_dict() for r in optimize_results],
                'summary': f"Optimized {len(optimize_results)} fragmented tables"
            })
            
            # 4. Clean up old data
            logger.info("Cleaning up old data...")
            cleanup_results = self.cleanup_manager.cleanup_old_data(dry_run)
            results['tasks'].append({
                'task_type': 'cleanup_data',
                'results': [r.to_dict() for r in cleanup_results],
                'summary': f"Cleaned up {sum(r.rows_affected for r in cleanup_results)} rows from {len(cleanup_results)} tables"
            })
            
            # 5. Collect statistics after maintenance
            logger.info("Collecting final statistics...")
            stats_after = self.stats_collector.collect_database_statistics()
            results['statistics_after'] = stats_after.to_dict()
            
            # 6. Calculate improvements
            size_reduction = stats_before.total_size_mb - stats_after.total_size_mb
            fragmentation_improvement = stats_before.fragmentation_percent - stats_after.fragmentation_percent
            
            results['improvements'] = {
                'size_reduction_mb': size_reduction,
                'fragmentation_improvement_percent': fragmentation_improvement,
                'total_rows_cleaned': sum(r.rows_affected for r in cleanup_results)
            }
            
            maintenance_duration = time.time() - maintenance_start
            results['completed_at'] = datetime.now().isoformat()
            results['duration_seconds'] = maintenance_duration
            results['status'] = 'completed'
            
            logger.info(f"Database maintenance completed in {maintenance_duration:.2f}s. "
                       f"Size reduction: {size_reduction:.2f}MB, "
                       f"Fragmentation improvement: {fragmentation_improvement:.2f}%")
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            results['completed_at'] = datetime.now().isoformat()
            results['duration_seconds'] = time.time() - maintenance_start
            logger.error(f"Database maintenance failed: {e}")
        
        # Store maintenance history
        self.maintenance_history.append(results)
        
        # Cache results
        cache.set(f"maintenance_result_{self.database_alias}_{int(time.time())}", results, 86400)
        
        return results
    
    def get_maintenance_recommendations(self) -> Dict[str, Any]:
        """Get maintenance recommendations based on current database state"""
        try:
            stats = self.stats_collector.collect_database_statistics()
            recommendations = []
            
            # Check fragmentation
            if stats.fragmentation_percent > 30:
                recommendations.append({
                    'type': 'high_fragmentation',
                    'priority': 'high',
                    'message': f"Database fragmentation is {stats.fragmentation_percent:.1f}%. Consider running OPTIMIZE TABLE.",
                    'action': 'optimize_tables'
                })
            
            # Check database size growth
            growth_analysis = self.stats_collector.analyze_growth_trends()
            if 'daily_growth_mb' in growth_analysis and growth_analysis['daily_growth_mb'] > 100:
                recommendations.append({
                    'type': 'rapid_growth',
                    'priority': 'medium',
                    'message': f"Database is growing rapidly ({growth_analysis['daily_growth_mb']:.1f}MB/day). Consider data archiving.",
                    'action': 'cleanup_old_data'
                })
            
            # Check for large tables
            large_tables = [
                name for name, info in stats.table_statistics.items()
                if info['total_size_mb'] > 1000
            ]
            
            if large_tables:
                recommendations.append({
                    'type': 'large_tables',
                    'priority': 'medium',
                    'message': f"Found {len(large_tables)} tables larger than 1GB. Consider partitioning or archiving.",
                    'action': 'partition_tables',
                    'affected_tables': large_tables
                })
            
            return {
                'database_alias': self.database_alias,
                'generated_at': datetime.now().isoformat(),
                'current_statistics': stats.to_dict(),
                'recommendations': recommendations,
                'growth_analysis': growth_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to generate maintenance recommendations: {e}")
            return {'error': str(e)}
    
    def get_maintenance_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get maintenance execution history"""
        return self.maintenance_history[-limit:]


# Global maintenance scheduler instance
maintenance_scheduler = DatabaseMaintenanceScheduler()


def run_database_maintenance(database_alias: str = 'default', dry_run: bool = False) -> Dict[str, Any]:
    """Run database maintenance for specified database"""
    scheduler = DatabaseMaintenanceScheduler(database_alias)
    return scheduler.run_full_maintenance(dry_run)


def get_maintenance_recommendations(database_alias: str = 'default') -> Dict[str, Any]:
    """Get maintenance recommendations for specified database"""
    scheduler = DatabaseMaintenanceScheduler(database_alias)
    return scheduler.get_maintenance_recommendations()