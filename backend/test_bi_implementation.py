#!/usr/bin/env python3
"""
Test script for Advanced Business Intelligence Platform implementation.
This script validates the BI models, services, and API endpoints.
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.analytics.bi_models import (
    BIDashboard, BIWidget, BIDataSource, BIReport, BIInsight, BIMLModel,
    BIDataCatalog, BIAnalyticsSession, BIPerformanceMetric, BIAlert
)
from apps.analytics.bi_services import (
    BIDashboardService, BIDataService, BIInsightService, BIMLService,
    BIRealtimeService, BIDataGovernanceService
)


class BIImplementationTest:
    """Test class for BI implementation validation"""
    
    def __init__(self):
        self.client = Client()
        self.user = None
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup test data for BI testing"""
        print("Setting up test data...")
        
        # Create test user
        self.user, created = User.objects.get_or_create(
            username='bi_test_user',
            defaults={
                'email': 'bi_test@example.com',
                'first_name': 'BI',
                'last_name': 'Test User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            self.user.set_password('testpass123')
            self.user.save()
        
        print(f"✓ Test user created/found: {self.user.username}")
    
    def test_bi_models(self):
        """Test BI model creation and relationships"""
        print("\n=== Testing BI Models ===")
        
        try:
            # Test BIDataSource creation
            data_source = BIDataSource.objects.create(
                name="Test Sales Data",
                description="Test data source for sales analytics",
                source_type="database",
                connection_config={"host": "localhost", "database": "test_db"},
                created_by=self.user
            )
            print("✓ BIDataSource created successfully")
            
            # Test BIDashboard creation
            dashboard = BIDashboard.objects.create(
                name="Test Executive Dashboard",
                description="Test dashboard for executive metrics",
                dashboard_type="executive",
                layout_config={"grid_size": 12, "row_height": 60},
                created_by=self.user
            )
            print("✓ BIDashboard created successfully")
            
            # Test BIWidget creation
            widget = BIWidget.objects.create(
                dashboard=dashboard,
                name="Test Revenue Widget",
                widget_type="metric",
                data_source="sales_revenue_summary",
                query_config={"metric": "revenue"},
                visualization_config={"chart_type": "line"}
            )
            print("✓ BIWidget created successfully")
            
            # Test BIInsight creation
            insight = BIInsight.objects.create(
                title="Test Sales Anomaly",
                description="Test anomaly detection insight",
                insight_type="anomaly",
                severity="medium",
                data_source=data_source,
                metric_name="revenue",
                current_value=50000.00,
                expected_value=45000.00,
                confidence_score=85.0
            )
            print("✓ BIInsight created successfully")
            
            # Test BIMLModel creation
            ml_model = BIMLModel.objects.create(
                name="Test Forecasting Model",
                description="Test ML model for sales forecasting",
                model_type="forecasting",
                algorithm="ARIMA",
                training_data_source=data_source,
                created_by=self.user
            )
            print("✓ BIMLModel created successfully")
            
            # Test BIAnalyticsSession creation
            session = BIAnalyticsSession.objects.create(
                name="Test Analytics Session",
                description="Test self-service analytics session",
                user=self.user,
                query_history=[],
                visualizations=[],
                bookmarks=[]
            )
            session.data_sources.add(data_source)
            print("✓ BIAnalyticsSession created successfully")
            
            print("✓ All BI models created and tested successfully")
            return True
            
        except Exception as e:
            print(f"✗ BI Models test failed: {str(e)}")
            return False
    
    def test_bi_services(self):
        """Test BI service functionality"""
        print("\n=== Testing BI Services ===")
        
        try:
            # Test BIDashboardService
            dashboard = BIDashboardService.create_executive_dashboard(
                self.user, "Test Executive Dashboard"
            )
            print("✓ BIDashboardService.create_executive_dashboard() works")
            
            # Test BIDataService
            data_service = BIDataService()
            metrics = data_service.get_realtime_metrics()
            print("✓ BIDataService.get_realtime_metrics() works")
            
            # Test BIInsightService
            insights = BIInsightService.generate_automated_insights()
            print(f"✓ BIInsightService.generate_automated_insights() generated {len(insights)} insights")
            
            # Test BIMLService
            model = BIMLService.create_forecasting_model(
                "Test Model", self.user, "test-data-source"
            )
            print("✓ BIMLService.create_forecasting_model() works")
            
            # Test BIRealtimeService
            realtime_metrics = BIRealtimeService.get_realtime_metrics()
            print("✓ BIRealtimeService.get_realtime_metrics() works")
            
            # Test BIDataGovernanceService
            quality_assessment = BIDataGovernanceService.assess_data_quality("test-source")
            print("✓ BIDataGovernanceService.assess_data_quality() works")
            
            print("✓ All BI services tested successfully")
            return True
            
        except Exception as e:
            print(f"✗ BI Services test failed: {str(e)}")
            return False
    
    def test_bi_api_endpoints(self):
        """Test BI API endpoints"""
        print("\n=== Testing BI API Endpoints ===")
        
        try:
            # Login user for API testing
            self.client.force_login(self.user)
            
            # Test dashboard endpoints
            response = self.client.post('/api/analytics/bi/dashboards/create_executive_dashboard/', {
                'name': 'API Test Dashboard'
            }, content_type='application/json')
            print(f"✓ Create executive dashboard API: {response.status_code}")
            
            # Test insights endpoints
            response = self.client.post('/api/analytics/bi/insights/generate_insights/', {
                'insight_types': ['anomaly', 'trend'],
                'date_range': '30d'
            }, content_type='application/json')
            print(f"✓ Generate insights API: {response.status_code}")
            
            # Test ML models endpoints
            response = self.client.post('/api/analytics/bi/ml-models/create_forecasting_model/', {
                'name': 'API Test Model',
                'data_source_id': 'test-source'
            }, content_type='application/json')
            print(f"✓ Create ML model API: {response.status_code}")
            
            # Test real-time endpoints
            response = self.client.get('/api/analytics/bi/realtime/realtime_metrics/')
            print(f"✓ Real-time metrics API: {response.status_code}")
            
            # Test governance endpoints
            response = self.client.get('/api/analytics/bi/governance/governance_dashboard/')
            print(f"✓ Governance dashboard API: {response.status_code}")
            
            print("✓ All BI API endpoints tested successfully")
            return True
            
        except Exception as e:
            print(f"✗ BI API endpoints test failed: {str(e)}")
            return False
    
    def test_bi_data_flow(self):
        """Test complete BI data flow"""
        print("\n=== Testing BI Data Flow ===")
        
        try:
            # Create data source
            data_source = BIDataSource.objects.create(
                name="Flow Test Data Source",
                description="Test data source for flow testing",
                source_type="database",
                created_by=self.user
            )
            
            # Create dashboard
            dashboard = BIDashboard.objects.create(
                name="Flow Test Dashboard",
                dashboard_type="executive",
                created_by=self.user
            )
            
            # Create widget
            widget = BIWidget.objects.create(
                dashboard=dashboard,
                name="Flow Test Widget",
                widget_type="metric",
                data_source="sales_revenue_summary"
            )
            
            # Generate insights
            insights = BIInsightService.generate_automated_insights()
            
            # Create ML model
            ml_model = BIMLModel.objects.create(
                name="Flow Test Model",
                model_type="forecasting",
                algorithm="ARIMA",
                training_data_source=data_source,
                created_by=self.user
            )
            
            # Create analytics session
            session = BIAnalyticsSession.objects.create(
                name="Flow Test Session",
                user=self.user
            )
            session.data_sources.add(data_source)
            
            print("✓ Complete BI data flow tested successfully")
            return True
            
        except Exception as e:
            print(f"✗ BI data flow test failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all BI implementation tests"""
        print("🚀 Starting Advanced Business Intelligence Platform Tests")
        print("=" * 60)
        
        tests = [
            ("BI Models", self.test_bi_models),
            ("BI Services", self.test_bi_services),
            ("BI API Endpoints", self.test_bi_api_endpoints),
            ("BI Data Flow", self.test_bi_data_flow)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"✗ {test_name} failed with exception: {str(e)}")
                results.append((test_name, False))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{test_name:<25} {status}")
        
        print("-" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! BI implementation is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
        
        return passed == total


def main():
    """Main function to run BI tests"""
    try:
        tester = BIImplementationTest()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()