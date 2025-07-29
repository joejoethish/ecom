"""
Models for logging and monitoring.
"""
from django.db import models
from django.utils import timezone


class SystemLog(models.Model):
    """
    Model for storing system logs in the database.
    """
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    logger_name = models.CharField(max_length=100)
    message = models.TextField()
    source = models.CharField(max_length=50, default='system')
    event_type = models.CharField(max_length=50, default='general')
    user_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_path = models.CharField(max_length=255, null=True, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['source']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user_id']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class BusinessMetric(models.Model):
    """
    Model for storing business metrics.
    """
    name = models.CharField(max_length=100)
    value = models.FloatField()
    dimensions = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.value} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class PerformanceMetric(models.Model):
    """
    Model for storing performance metrics.
    """
    name = models.CharField(max_length=100)
    value = models.FloatField()
    endpoint = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=10, null=True, blank=True)
    response_time = models.IntegerField(help_text="Response time in milliseconds")
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.endpoint} - {self.response_time}ms"


class SecurityEvent(models.Model):
    """
    Model for storing security events.
    """
    event_type = models.CharField(max_length=50)
    user_id = models.IntegerField(null=True, blank=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_path = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['user_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.username or 'anonymous'} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"