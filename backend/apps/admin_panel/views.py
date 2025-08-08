"""
Database views for admin panel complex queries and dashboard data.
"""
from django.db import models


class AdminDashboardStatsView(models.Model):
    """
    Database view for dashboard statistics.
    """
    total_orders = models.IntegerField()
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    total_customers = models.IntegerField()
    total_products = models.IntegerField()
    pending_orders = models.IntegerField()
    low_stock_products = models.IntegerField()
    active_sessions = models.IntegerField()
    failed_logins_today = models.IntegerField()
    
    class Meta:
        managed = False  # This is a database view
        db_table = 'admin_dashboard_stats_view'


class AdminActivitySummaryView(models.Model):
    """
    Database view for activity summary by admin user.
    """
    admin_user_id = models.UUIDField()
    admin_username = models.CharField(max_length=150)
    total_actions = models.IntegerField()
    actions_today = models.IntegerField()
    last_activity = models.DateTimeField()
    most_common_action = models.CharField(max_length=20)
    
    class Meta:
        managed = False
        db_table = 'admin_activity_summary_view'


class SecurityAlertsView(models.Model):
    """
    Database view for security alerts and suspicious activities.
    """
    alert_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=10)
    count = models.IntegerField()
    latest_occurrence = models.DateTimeField()
    affected_users = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'security_alerts_view'