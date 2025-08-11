from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class CacheConfiguration(models.Model):
    """Configuration for different cache strategies"""
    CACHE_TYPES = [
        ('redis', 'Redis'),
        ('memcached', 'Memcached'),
        ('database', 'Database'),
        ('file', 'File System'),
        ('cdn', 'CDN'),
    ]
    
    CACHE_STRATEGIES = [
        ('write_through', 'Write Through'),
        ('write_back', 'Write Back'),
        ('write_around', 'Write Around'),
        ('cache_aside', 'Cache Aside'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    cache_type = models.CharField(max_length=20, choices=CACHE_TYPES)
    strategy = models.CharField(max_length=20, choices=CACHE_STRATEGIES)
    ttl_seconds = models.IntegerField(default=3600)  # Time to live
    max_size_mb = models.IntegerField(default=100)
    compression_enabled = models.BooleanField(default=True)
    encryption_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    config_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.cache_type})"


class CacheMetrics(models.Model):
    """Cache performance metrics and statistics"""
    cache_name = models.CharField(max_length=100)
    cache_type = models.CharField(max_length=20)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Hit/Miss Statistics
    hit_count = models.BigIntegerField(default=0)
    miss_count = models.BigIntegerField(default=0)
    hit_ratio = models.FloatField(default=0.0)
    
    # Performance Metrics
    avg_response_time_ms = models.FloatField(default=0.0)
    max_response_time_ms = models.FloatField(default=0.0)
    min_response_time_ms = models.FloatField(default=0.0)
    
    # Memory Usage
    memory_used_mb = models.FloatField(default=0.0)
    memory_total_mb = models.FloatField(default=0.0)
    memory_usage_percent = models.FloatField(default=0.0)
    
    # Operations
    get_operations = models.BigIntegerField(default=0)
    set_operations = models.BigIntegerField(default=0)
    delete_operations = models.BigIntegerField(default=0)
    
    # Network (for distributed caches)
    network_bytes_in = models.BigIntegerField(default=0)
    network_bytes_out = models.BigIntegerField(default=0)
    
    # Error Tracking
    error_count = models.IntegerField(default=0)
    timeout_count = models.IntegerField(default=0)
    
    class Meta:
        indexes = [
            models.Index(fields=['cache_name', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.cache_name} - {self.timestamp}"


class CacheInvalidation(models.Model):
    """Track cache invalidation events"""
    INVALIDATION_TYPES = [
        ('manual', 'Manual'),
        ('ttl_expired', 'TTL Expired'),
        ('dependency', 'Dependency Changed'),
        ('pattern', 'Pattern Match'),
        ('bulk', 'Bulk Operation'),
        ('system', 'System Event'),
    ]
    
    cache_key = models.CharField(max_length=500)
    cache_name = models.CharField(max_length=100)
    invalidation_type = models.CharField(max_length=20, choices=INVALIDATION_TYPES)
    reason = models.TextField()
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['cache_name', 'timestamp']),
            models.Index(fields=['cache_key']),
        ]

    def __str__(self):
        return f"{self.cache_key} - {self.invalidation_type}"


class CacheWarming(models.Model):
    """Cache warming and preloading configurations"""
    WARMING_TYPES = [
        ('scheduled', 'Scheduled'),
        ('event_driven', 'Event Driven'),
        ('manual', 'Manual'),
        ('predictive', 'Predictive'),
    ]
    
    name = models.CharField(max_length=100)
    cache_name = models.CharField(max_length=100)
    warming_type = models.CharField(max_length=20, choices=WARMING_TYPES)
    schedule_cron = models.CharField(max_length=100, blank=True)
    query_pattern = models.TextField()
    priority = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['priority', 'name']

    def __str__(self):
        return f"{self.name} - {self.cache_name}"


class CacheAlert(models.Model):
    """Cache monitoring alerts and notifications"""
    ALERT_TYPES = [
        ('high_miss_ratio', 'High Miss Ratio'),
        ('memory_usage', 'High Memory Usage'),
        ('slow_response', 'Slow Response Time'),
        ('error_rate', 'High Error Rate'),
        ('connection_failure', 'Connection Failure'),
        ('capacity_limit', 'Capacity Limit Reached'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    cache_name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    message = models.TextField()
    threshold_value = models.FloatField()
    current_value = models.FloatField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['cache_name', 'created_at']),
            models.Index(fields=['severity', 'is_resolved']),
        ]

    def __str__(self):
        return f"{self.cache_name} - {self.alert_type} ({self.severity})"


class CacheOptimization(models.Model):
    """Cache optimization recommendations and actions"""
    OPTIMIZATION_TYPES = [
        ('ttl_adjustment', 'TTL Adjustment'),
        ('memory_reallocation', 'Memory Reallocation'),
        ('compression_tuning', 'Compression Tuning'),
        ('eviction_policy', 'Eviction Policy'),
        ('partitioning', 'Cache Partitioning'),
        ('prefetching', 'Prefetching Strategy'),
    ]
    
    cache_name = models.CharField(max_length=100)
    optimization_type = models.CharField(max_length=30, choices=OPTIMIZATION_TYPES)
    current_config = models.JSONField()
    recommended_config = models.JSONField()
    expected_improvement = models.TextField()
    impact_score = models.FloatField()  # 0-100 scale
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    results = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-impact_score', '-created_at']

    def __str__(self):
        return f"{self.cache_name} - {self.optimization_type}"