"""
Tests for the log aggregation system
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from .aggregation import (
    LogAggregationService, 
    AggregatedLogEntry, 
    LogLevel, 
    LogSource,
    log_frontend_entry,
    log_backend_entry,
    log_database_entry
)

class LogAggregationServiceTests(TestCase):
    """Test the log aggregation service"""
    
    def setUp(self):
        self.service = LogAggregationService()
        self.correlation_id = 'test-correlation-123'
        cache.clear()  # Clear cache before each test
    
    def test_add_log_entry(self):
        """Test adding a log entry"""
        entry = AggregatedLogEntry(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message='Test message',
            source=LogSource.FRONTEND,
            correlation_id=self.correlation_id,
            user_id='user123'
        )
        
        self.service.add_log_entry(entry)
        
        # Verify entry was stored
        logs = self.service.get_logs_by_correlation_id(self.correlation_id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['message'], 'Test message')
        self.assertEqual(logs[0]['source'], 'frontend')
    
    def test_get_workflow_trace(self):
        """Test getting a complete workflow trace"""
        # Add multiple log entries
        entries = [
            AggregatedLogEntry(
                timestamp=datetime.now(),
                level=LogLevel.INFO,
                message='Frontend action',
                source=LogSource.FRONTEND,
                correlation_id=self.correlation_id,
                user_action='click',
                component='button'
            ),
            AggregatedLogEntry(
                timestamp=datetime.now() + timedelta(milliseconds=100),
                level=LogLevel.INFO,
                message='API call',
                source=LogSource.BACKEND,
                correlation_id=self.correlation_id,
                request_method='POST',
                request_url='/api/test/',
                response_time=150
            ),
            AggregatedLogEntry(
                timestamp=datetime.now() + timedelta(milliseconds=200),
                level=LogLevel.INFO,
                message='Database query',
                source=LogSource.DATABASE,
                correlation_id=self.correlation_id,
                sql_query='SELECT * FROM test',
                query_duration=50
            )
        ]
        
        for entry in entries:
            self.service.add_log_entry(entry)
        
        # Get workflow trace
        trace = self.service.get_workflow_trace(self.correlation_id)
        
        self.assertEqual(trace['correlation_id'], self.correlation_id)
        self.assertEqual(len(trace['entries']), 3)
        self.assertEqual(trace['analysis']['api_calls'], 1)
        self.assertEqual(trace['analysis']['database_queries'], 1)
        self.assertEqual(trace['analysis']['user_interactions'], 1)
    
    def test_error_pattern_analysis(self):
        """Test error pattern detection"""
        # Add error entries
        error_entries = [
            AggregatedLogEntry(
                timestamp=datetime.now(),
                level=LogLevel.ERROR,
                message='Database connection failed',
                source=LogSource.DATABASE,
                correlation_id='error-1'
            ),
            AggregatedLogEntry(
                timestamp=datetime.now(),
                level=LogLevel.ERROR,
                message='Database connection failed',
                source=LogSource.DATABASE,
                correlation_id='error-2'
            ),
            AggregatedLogEntry(
                timestamp=datetime.now(),
                level=LogLevel.ERROR,
                message='API timeout',
                source=LogSource.BACKEND,
                correlation_id='error-3'
            )
        ]
        
        for entry in error_entries:
            self.service.add_log_entry(entry)
        
        # Get error patterns
        patterns = self.service.get_error_patterns(hours=1)
        
        self.assertEqual(patterns['total_errors'], 3)
        self.assertGreater(patterns['unique_patterns'], 0)
    
    def test_performance_issue_detection(self):
        """Test detection of performance issues"""
        # Add slow query
        slow_query_entry = AggregatedLogEntry(
            timestamp=datetime.now(),
            level=LogLevel.WARN,
            message='Slow database query',
            source=LogSource.DATABASE,
            correlation_id=self.correlation_id,
            sql_query='SELECT * FROM large_table',
            query_duration=500  # 500ms - slow
        )
        
        # Add slow API call
        slow_api_entry = AggregatedLogEntry(
            timestamp=datetime.now(),
            level=LogLevel.WARN,
            message='Slow API response',
            source=LogSource.BACKEND,
            correlation_id=self.correlation_id,
            request_url='/api/slow/',
            response_time=2000  # 2 seconds - slow
        )
        
        self.service.add_log_entry(slow_query_entry)
        self.service.add_log_entry(slow_api_entry)
        
        # Get workflow trace with performance analysis
        trace = self.service.get_workflow_trace(self.correlation_id)
        
        performance_issues = trace['analysis']['performance_issues']
        self.assertEqual(len(performance_issues), 2)
        
        # Check for slow query issue
        slow_query_issue = next(
            (issue for issue in performance_issues if issue['type'] == 'slow_query'), 
            None
        )
        self.assertIsNotNone(slow_query_issue)
        self.assertEqual(slow_query_issue['duration'], 500)
        
        # Check for slow API call issue
        slow_api_issue = next(
            (issue for issue in performance_issues if issue['type'] == 'slow_api_call'), 
            None
        )
        self.assertIsNotNone(slow_api_issue)
        self.assertEqual(slow_api_issue['duration'], 2000)

class LogAggregationAPITests(TestCase):
    """Test the log aggregation API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.correlation_id = 'test-api-correlation-123'
        cache.clear()
    
    def test_receive_frontend_logs(self):
        """Test receiving logs from frontend"""
        logs_data = {
            'logs': [
                {
                    'level': 'info',
                    'message': 'User clicked button',
                    'correlationId': self.correlation_id,
                    'userId': 'user123',
                    'sessionId': 'session123',
                    'action': 'click',
                    'component': 'submit-button',
                    'pageUrl': 'https://example.com/page',
                    'userAgent': 'Mozilla/5.0...'
                },
                {
                    'level': 'error',
                    'message': 'API call failed',
                    'correlationId': self.correlation_id,
                    'context': {'error_code': 500}
                }
            ]
        }
        
        response = self.client.post(
            reverse('logs:api_frontend_logs'),
            data=json.dumps(logs_data),
            content_type='application/json',
            HTTP_X_CORRELATION_ID=self.correlation_id
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['processed_logs'], 2)
    
    def test_get_aggregated_logs(self):
        """Test retrieving aggregated logs"""
        # First add some logs
        log_frontend_entry(
            correlation_id=self.correlation_id,
            level='info',
            message='Test frontend log',
            user_id='user123'
        )
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Get logs by correlation ID
        response = self.client.get(
            reverse('logs:api_logs'),
            {'correlation_id': self.correlation_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['logs'][0]['message'], 'Test frontend log')
    
    def test_get_workflow_trace(self):
        """Test getting workflow trace"""
        # Add logs for workflow
        log_frontend_entry(
            correlation_id=self.correlation_id,
            level='info',
            message='User interaction',
            user_action='click'
        )
        
        log_backend_entry(
            correlation_id=self.correlation_id,
            level='info',
            message='API processing',
            request_method='POST'
        )
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Get workflow trace
        response = self.client.get(
            reverse('logs:api_workflow_trace', args=[self.correlation_id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['correlation_id'], self.correlation_id)
        self.assertEqual(len(data['entries']), 2)
        self.assertIn('analysis', data)
    
    def test_get_error_patterns(self):
        """Test getting error patterns"""
        # Add error logs
        log_backend_entry(
            correlation_id='error-1',
            level='error',
            message='Database error occurred'
        )
        
        log_backend_entry(
            correlation_id='error-2',
            level='error',
            message='Database error occurred'
        )
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Get error patterns
        response = self.client.get(
            reverse('logs:api_error_patterns'),
            {'hours': 1}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['total_errors'], 0)
        self.assertIn('patterns', data)
    
    def test_cleanup_old_logs(self):
        """Test cleaning up old logs"""
        # Add some logs
        log_frontend_entry(
            correlation_id=self.correlation_id,
            level='info',
            message='Old log entry'
        )
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Cleanup logs
        response = self.client.post(
            reverse('logs:api_cleanup_logs'),
            data=json.dumps({'hours': 0}),  # Clean all logs
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('cleaned_entries', data)

class LogHelperFunctionTests(TestCase):
    """Test the helper functions for logging"""
    
    def setUp(self):
        self.correlation_id = 'test-helper-123'
        cache.clear()
    
    def test_log_frontend_entry(self):
        """Test frontend logging helper"""
        log_frontend_entry(
            correlation_id=self.correlation_id,
            level='info',
            message='Frontend test',
            user_id='user123',
            user_action='click',
            component='button'
        )
        
        service = LogAggregationService()
        logs = service.get_logs_by_correlation_id(self.correlation_id)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['source'], 'frontend')
        self.assertEqual(logs[0]['user_action'], 'click')
    
    def test_log_backend_entry(self):
        """Test backend logging helper"""
        log_backend_entry(
            correlation_id=self.correlation_id,
            level='info',
            message='Backend test',
            request_method='GET',
            request_url='/api/test/',
            response_status=200
        )
        
        service = LogAggregationService()
        logs = service.get_logs_by_correlation_id(self.correlation_id)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['source'], 'backend')
        self.assertEqual(logs[0]['request_method'], 'GET')
    
    def test_log_database_entry(self):
        """Test database logging helper"""
        log_database_entry(
            correlation_id=self.correlation_id,
            level='info',
            message='Database test',
            sql_query='SELECT * FROM test',
            query_duration=25.5
        )
        
        service = LogAggregationService()
        logs = service.get_logs_by_correlation_id(self.correlation_id)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['source'], 'database')
        self.assertEqual(logs[0]['sql_query'], 'SELECT * FROM test')
        self.assertEqual(logs[0]['query_duration'], 25.5)