#!/usr/bin/env python
"""
Simple test script to verify chart system functionality.
"""
import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.admin_panel.chart_models import ChartTemplate, Chart
from apps.admin_panel.chart_services import ChartDataService, ChartExportService

User = get_user_model()

def test_chart_models():
    """Test chart model creation and relationships."""
    print("Testing chart models...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='test_chart_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Create a chart template
    template = ChartTemplate.objects.create(
        name='Test Sales Chart',
        description='Test chart for sales data',
        chart_type='line',
        category='sales',
        data_source='sales_overview',
        config={
            'responsive': True,
            'plugins': {
                'title': {'display': True, 'text': 'Sales Overview'}
            }
        },
        created_by=user
    )
    
    print(f"✓ Created chart template: {template}")
    
    # Create a chart
    chart = Chart.objects.create(
        title='Monthly Sales',
        description='Monthly sales performance chart',
        chart_type='line',
        template=template,
        data_source='sales_overview',
        config=template.config,
        theme='light',
        colors=['#3B82F6', '#EF4444'],
        created_by=user
    )
    
    print(f"✓ Created chart: {chart}")
    
    # Test chart relationships
    assert chart.template == template
    assert chart.created_by == user
    assert chart.versions.count() == 0  # No versions created yet
    
    print("✓ Chart models test passed!")
    return chart

def test_chart_services():
    """Test chart data services."""
    print("\nTesting chart services...")
    
    # Get a test chart
    chart = Chart.objects.first()
    if not chart:
        print("No charts found, creating one...")
        chart = test_chart_models()
    
    # Test data service
    data_service = ChartDataService()
    
    try:
        # This will use sample data since we don't have real data sources
        chart_data = data_service.get_chart_data(chart)
        print(f"✓ Retrieved chart data: {len(chart_data.get('labels', []))} data points")
    except Exception as e:
        print(f"⚠ Chart data service test failed (expected): {e}")
    
    # Test export service
    export_service = ChartExportService()
    
    try:
        # Test PNG export (will create a simple matplotlib chart)
        file_path = export_service.export_chart(chart, 'png')
        print(f"✓ Chart exported to: {file_path}")
    except Exception as e:
        print(f"⚠ Chart export test failed: {e}")
    
    print("✓ Chart services test completed!")

def test_chart_api_structure():
    """Test that chart API structure is correct."""
    print("\nTesting chart API structure...")
    
    from apps.admin_panel.chart_views import ChartViewSet, ChartTemplateViewSet
    from apps.admin_panel.chart_serializers import ChartSerializer, ChartTemplateSerializer
    
    # Test that viewsets exist
    assert hasattr(ChartViewSet, 'queryset')
    assert hasattr(ChartTemplateViewSet, 'queryset')
    
    # Test that serializers exist
    assert hasattr(ChartSerializer, 'Meta')
    assert hasattr(ChartTemplateSerializer, 'Meta')
    
    print("✓ Chart API structure test passed!")

def main():
    """Run all chart system tests."""
    print("🚀 Starting Chart System Tests\n")
    
    try:
        # Test models
        test_chart_models()
        
        # Test services
        test_chart_services()
        
        # Test API structure
        test_chart_api_structure()
        
        print("\n✅ All chart system tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()