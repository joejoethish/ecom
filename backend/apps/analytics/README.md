# Sales Analytics and Reporting System

This comprehensive sales analytics system provides advanced reporting, forecasting, and business intelligence capabilities for the e-commerce platform.

## Features

### Core Analytics
- **Real-time Sales Dashboard** - KPIs, trends, and performance metrics
- **Revenue Analysis** - Detailed profit/loss analysis with margins
- **Customer Analytics** - Cohort analysis, lifetime value, retention tracking
- **Product Performance** - Sales tracking by product, category, and region
- **Sales Forecasting** - ML-powered predictions with seasonal adjustments

### Advanced Features
- **Sales Attribution** - Multi-channel attribution analysis
- **Funnel Analysis** - Conversion tracking and optimization
- **Anomaly Detection** - Automated alerts for unusual patterns
- **Territory Management** - Geographic sales analysis and optimization
- **Commission Tracking** - Automated commission calculation and payouts
- **Pipeline Management** - Opportunity tracking and forecasting

### Reporting & Automation
- **Scheduled Reports** - Automated report generation and delivery
- **Export Capabilities** - Multiple format support (CSV, Excel, PDF)
- **Alert System** - Real-time notifications for anomalies and goals
- **API Integration** - RESTful APIs for external BI tools

## Models

### Core Models
- `SalesMetrics` - Daily sales aggregation and KPIs
- `ProductSalesAnalytics` - Product-level performance tracking
- `CustomerAnalytics` - Customer behavior and lifetime value
- `SalesForecast` - ML-powered sales predictions

### Management Models
- `SalesGoal` - Goal setting and progress tracking
- `SalesCommission` - Commission calculation and payouts
- `SalesTerritory` - Geographic territory management
- `SalesPipeline` - Opportunity and pipeline tracking

### Reporting Models
- `SalesReport` - Scheduled report configuration
- `SalesAnomalyDetection` - Automated anomaly alerts

## Services

### Analytics Services
- `SalesAnalyticsService` - Core analytics and dashboard generation
- `SalesForecastingService` - ML-powered forecasting with accuracy tracking
- `SalesReportingService` - Automated reporting and anomaly detection

### Management Services
- `SalesCommissionService` - Commission calculation and processing
- `SalesTerritoryService` - Territory analysis and optimization
- `SalesPipelineService` - Pipeline management and forecasting

## API Endpoints

### Dashboard & Analytics
- `GET /api/analytics/sales-analytics/sales_dashboard/` - Real-time dashboard
- `GET /api/analytics/sales-analytics/revenue_analysis/` - Revenue analysis
- `GET /api/analytics/sales-analytics/customer_cohort_analysis/` - Cohort analysis
- `GET /api/analytics/sales-analytics/sales_funnel_analysis/` - Funnel analysis

### Forecasting & Predictions
- `GET /api/analytics/sales-analytics/sales_forecast/` - Sales forecasting
- `POST /api/analytics/sales-analytics/update_forecast_accuracy/` - Update accuracy

### Performance & Comparison
- `GET /api/analytics/sales-analytics/sales_performance_comparison/` - Period comparison
- `GET /api/analytics/sales-analytics/sales_attribution_analysis/` - Attribution analysis
- `GET /api/analytics/sales-analytics/product_performance_tracking/` - Product performance

### Management & Goals
- `GET /api/analytics/sales-analytics/sales_goals_tracking/` - Goal tracking
- `POST /api/analytics/sales-analytics/create_sales_goal/` - Create goals
- `GET /api/analytics/sales-analytics/commission_calculation/` - Commission calculation
- `POST /api/analytics/sales-analytics/process_commission_payouts/` - Process payouts

### Territory & Pipeline
- `GET /api/analytics/sales-analytics/territory_management/` - Territory analysis
- `GET /api/analytics/sales-analytics/pipeline_management/` - Pipeline overview
- `GET /api/analytics/sales-analytics/pipeline_forecast/` - Pipeline forecasting

### Reporting & Alerts
- `GET /api/analytics/sales-analytics/anomaly_detection/` - Anomaly alerts
- `POST /api/analytics/sales-analytics/detect_anomalies/` - Trigger detection
- `GET /api/analytics/sales-analytics/scheduled_reports/` - Report management
- `POST /api/analytics/sales-analytics/send_scheduled_reports/` - Send reports

## Management Commands

### Data Updates
```bash
python manage.py update_sales_analytics --date 2024-01-01
python manage.py update_sales_analytics --days-back 7 --force
```

### Scheduled Tasks
The system includes Celery tasks for automated processing:
- Daily analytics updates
- Sales forecast generation
- Scheduled report delivery
- Anomaly detection
- Commission calculations

## Installation & Setup

1. **Install Dependencies**
```bash
pip install pandas scikit-learn numpy
```

2. **Run Migrations**
```bash
python manage.py makemigrations analytics
python manage.py migrate
```

3. **Update Analytics Data**
```bash
python manage.py update_sales_analytics --days-back 30
```

4. **Setup Celery Tasks** (Optional)
Add to your Celery beat schedule:
```python
CELERY_BEAT_SCHEDULE = {
    'update-daily-analytics': {
        'task': 'apps.analytics.tasks.update_daily_sales_analytics',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'generate-forecasts': {
        'task': 'apps.analytics.tasks.generate_sales_forecasts',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Weekly
    },
    'send-reports': {
        'task': 'apps.analytics.tasks.send_scheduled_reports',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    'detect-anomalies': {
        'task': 'apps.analytics.tasks.detect_sales_anomalies',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
}
```

## Configuration

### Email Settings
For automated reporting, configure email settings in Django settings:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-host'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'analytics@yourcompany.com'
```

### ML Dependencies
For advanced forecasting features:
```bash
pip install pandas scikit-learn numpy
```

## Testing

Run the comprehensive test suite:
```bash
python manage.py test apps.analytics.tests.test_sales_analytics
```

The test suite covers:
- All service methods and calculations
- Model functionality and properties
- API endpoint responses
- Data integrity and validation
- Edge cases and error handling

## Performance Considerations

- **Data Aggregation**: Daily analytics updates prevent real-time calculation overhead
- **Caching**: Consider implementing Redis caching for frequently accessed metrics
- **Database Indexing**: Ensure proper indexing on date fields and foreign keys
- **Batch Processing**: Use Celery for heavy analytical computations
- **Data Retention**: Implement data cleanup for old analytical records

## Security

- **Admin Only**: All analytics endpoints require admin permissions
- **Data Privacy**: Customer data is aggregated and anonymized where possible
- **API Rate Limiting**: Consider implementing rate limiting for API endpoints
- **Audit Logging**: Track access to sensitive financial and customer data

## Monitoring

- **Health Checks**: Monitor Celery task execution and failures
- **Performance Metrics**: Track API response times and database query performance
- **Data Quality**: Monitor for missing or inconsistent analytical data
- **Alert Thresholds**: Set up monitoring for critical business metrics

## Support

For issues or questions regarding the analytics system:
1. Check the test suite for usage examples
2. Review the API documentation for endpoint details
3. Examine the services for business logic implementation
4. Consult the models for data structure understanding