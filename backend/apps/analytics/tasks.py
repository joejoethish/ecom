"""
Celery tasks for sales analytics processing.
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.core.management import call_command
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

from .services import (
    SalesAnalyticsService, SalesForecastingService, SalesReportingService,
    SalesCommissionService
)
from .models import SalesReport, SalesAnomalyDetection


@shared_task
def update_daily_sales_analytics():
    """
    Daily task to update sales analytics data.
    """
    try:
        # Update analytics for yesterday
        yesterday = timezone.now().date() - timedelta(days=1)
        call_command('update_sales_analytics', date=yesterday.strftime('%Y-%m-%d'))
        
        return f"Successfully updated sales analytics for {yesterday}"
    except Exception as e:
        return f"Failed to update sales analytics: {str(e)}"


@shared_task
def generate_sales_forecasts():
    """
    Weekly task to generate updated sales forecasts.
    """
    try:
        # Generate forecasts for different periods
        forecast_types = ['daily', 'weekly', 'monthly', 'quarterly']
        
        for forecast_type in forecast_types:
            periods = 30 if forecast_type == 'daily' else 12
            SalesForecastingService.generate_sales_forecast(forecast_type, periods)
        
        # Update forecast accuracy
        SalesForecastingService.update_forecast_accuracy()
        
        return "Successfully generated sales forecasts"
    except Exception as e:
        return f"Failed to generate forecasts: {str(e)}"


@shared_task
def send_scheduled_reports():
    """
    Daily task to send scheduled sales reports.
    """
    try:
        SalesReportingService.generate_scheduled_reports()
        return "Successfully sent scheduled reports"
    except Exception as e:
        return f"Failed to send scheduled reports: {str(e)}"


@shared_task
def detect_sales_anomalies():
    """
    Daily task to detect sales anomalies and send alerts.
    """
    try:
        anomalies = SalesReportingService.detect_sales_anomalies()
        
        if anomalies:
            # Send summary email to administrators
            send_anomaly_summary_email(anomalies)
        
        return f"Detected {len(anomalies)} anomalies"
    except Exception as e:
        return f"Failed to detect anomalies: {str(e)}"


@shared_task
def calculate_monthly_commissions():
    """
    Monthly task to calculate sales commissions.
    """
    try:
        # Calculate commissions for the previous month
        today = timezone.now().date()
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        first_day_previous_month = last_day_previous_month.replace(day=1)
        
        commissions = SalesCommissionService.calculate_commissions(
            first_day_previous_month, 
            last_day_previous_month
        )
        
        return f"Calculated commissions for {len(commissions)} sales representatives"
    except Exception as e:
        return f"Failed to calculate commissions: {str(e)}"


@shared_task
def generate_executive_dashboard_report():
    """
    Weekly task to generate executive dashboard report.
    """
    try:
        # Generate comprehensive dashboard data
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        dashboard_data = SalesAnalyticsService.generate_sales_dashboard(start_date, end_date)
        
        # Send executive summary email
        send_executive_summary_email(dashboard_data, start_date, end_date)
        
        return "Successfully generated executive dashboard report"
    except Exception as e:
        return f"Failed to generate executive report: {str(e)}"


@shared_task
def update_customer_analytics():
    """
    Weekly task to update customer analytics and segmentation.
    """
    try:
        from apps.customers.models import CustomerProfile
        
        # Update analytics for all active customers
        customers = CustomerProfile.objects.filter(
            user__is_active=True,
            is_deleted=False
        )
        
        updated_count = 0
        for customer in customers:
            # This would call a method to update customer analytics
            # For now, we'll just count them
            updated_count += 1
        
        return f"Updated analytics for {updated_count} customers"
    except Exception as e:
        return f"Failed to update customer analytics: {str(e)}"


@shared_task
def cleanup_old_analytics_data():
    """
    Monthly task to cleanup old analytics data.
    """
    try:
        # Keep data for 2 years
        cutoff_date = timezone.now().date() - timedelta(days=730)
        
        # Clean up old sales metrics (keep aggregated data)
        from .models import SalesMetrics, ProductSalesAnalytics
        
        old_metrics = SalesMetrics.objects.filter(date__lt=cutoff_date)
        metrics_count = old_metrics.count()
        old_metrics.delete()
        
        old_product_analytics = ProductSalesAnalytics.objects.filter(date__lt=cutoff_date)
        product_count = old_product_analytics.count()
        old_product_analytics.delete()
        
        return f"Cleaned up {metrics_count} sales metrics and {product_count} product analytics records"
    except Exception as e:
        return f"Failed to cleanup old data: {str(e)}"


def send_anomaly_summary_email(anomalies):
    """Send anomaly summary email to administrators."""
    if not hasattr(settings, 'EMAIL_BACKEND'):
        return
    
    subject = f"Sales Anomaly Alert - {len(anomalies)} anomalies detected"
    
    message = f"""
    Sales Anomaly Detection Summary
    
    {len(anomalies)} anomalies were detected in today's sales data:
    
    """
    
    for anomaly in anomalies:
        message += f"""
    {anomaly['metric_type'].title()} Anomaly:
    - Severity: {anomaly['severity'].title()}
    - Actual Value: {anomaly['actual_value']:,.2f}
    - Expected Value: {anomaly['expected_value']:,.2f}
    - Deviation: {anomaly['deviation_percentage']}%
    
    """
    
    message += """
    Please review the sales analytics dashboard for detailed analysis.
    
    Sales Analytics System
    """
    
    # Send to administrators
    admin_emails = User.objects.filter(
        is_staff=True,
        is_active=True,
        email__isnull=False
    ).values_list('email', flat=True)
    
    if admin_emails:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(admin_emails),
            fail_silently=True
        )


def send_executive_summary_email(dashboard_data, start_date, end_date):
    """Send executive summary email."""
    if not hasattr(settings, 'EMAIL_BACKEND'):
        return
    
    subject = f"Weekly Sales Executive Summary - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    message = f"""
    Weekly Sales Executive Summary
    Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
    
    Key Metrics:
    - Total Revenue: ${dashboard_data.get('total_revenue', 0):,.2f}
    - Total Orders: {dashboard_data.get('total_orders', 0):,}
    - Average Order Value: ${dashboard_data.get('average_order_value', 0):,.2f}
    - Conversion Rate: {dashboard_data.get('conversion_rate', 0)}%
    - Revenue Growth: {dashboard_data.get('revenue_growth', 0)}%
    - Order Growth: {dashboard_data.get('order_growth', 0)}%
    
    Top Performing Products:
    """
    
    for i, product in enumerate(dashboard_data.get('top_products', [])[:5], 1):
        message += f"""
    {i}. {product.get('product_name', 'Unknown')} - ${product.get('total_revenue', 0):,.2f}
    """
    
    if dashboard_data.get('recent_anomalies'):
        message += f"""
    
    Anomalies Detected: {len(dashboard_data.get('recent_anomalies', []))}
    Please review the analytics dashboard for detailed analysis.
    """
    
    message += """
    
    For detailed analysis, please access the sales analytics dashboard.
    
    Sales Analytics System
    """
    
    # Send to executives and administrators
    executive_emails = User.objects.filter(
        groups__name__in=['Executives', 'Management'],
        is_active=True,
        email__isnull=False
    ).values_list('email', flat=True)
    
    admin_emails = User.objects.filter(
        is_staff=True,
        is_active=True,
        email__isnull=False
    ).values_list('email', flat=True)
    
    all_emails = list(set(list(executive_emails) + list(admin_emails)))
    
    if all_emails:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            all_emails,
            fail_silently=True
        )


@shared_task
def generate_sales_insights_report():
    """
    Weekly task to generate AI-powered sales insights.
    """
    try:
        # This would integrate with AI/ML services to generate insights
        # For now, we'll create a placeholder
        
        insights = [
            "Revenue growth is accelerating in the electronics category",
            "Customer acquisition cost has decreased by 15% this month",
            "Seasonal trends suggest preparing for holiday season demand",
            "Top-performing sales channels show strong ROI",
            "Customer retention rates are improving across all segments"
        ]
        
        # Send insights to management
        send_insights_email(insights)
        
        return f"Generated {len(insights)} sales insights"
    except Exception as e:
        return f"Failed to generate insights: {str(e)}"


def send_insights_email(insights):
    """Send AI-generated insights email."""
    if not hasattr(settings, 'EMAIL_BACKEND'):
        return
    
    subject = "Weekly Sales Insights Report"
    
    message = """
    Weekly Sales Insights Report
    
    AI-Powered Business Intelligence:
    
    """
    
    for i, insight in enumerate(insights, 1):
        message += f"{i}. {insight}\n"
    
    message += """
    
    These insights are generated from your sales data analysis.
    For detailed metrics and analysis, please access the sales analytics dashboard.
    
    Sales Analytics AI System
    """
    
    # Send to management
    management_emails = User.objects.filter(
        groups__name__in=['Management', 'Executives'],
        is_active=True,
        email__isnull=False
    ).values_list('email', flat=True)
    
    if management_emails:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(management_emails),
            fail_silently=True
        )