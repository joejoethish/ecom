"""
Unit tests for Correlation ID Middleware
"""
import uuid
import pytest
from unittest.mock import Mock, patch
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from core.middleware.correlation_id_middleware import (
    CorrelationIdMiddleware,
    CorrelationIdFilter,
    CorrelationIdManager,
    get_correlation_id,
    set_correlation_id,
    _correlation_id_storage
)


class TestCorrelationIdMiddleware(TestCase):
    """Test cases for CorrelationIdMiddleware"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.middleware = CorrelationIdMiddleware(Mock())
        
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
    
    def test_process_request_generates_correlation_id_when_none_provided(self):
        """Test that middleware generates correlation ID when none is provided"""
        request = self.factory.get('/')
        
        self.middleware.process_request(request)
        
        # Check that correlation ID was generated and set
        self.assertTrue(hasattr(request, 'correlation_id'))
        self.assertIsNotNone(request.correlation_id)
        self.assertEqual(len(request.correlation_id), 36)  # UUID length
        
        # Check that it's stored in thread-local storage
        self.assertEqual(get_correlation_id(), request.correlation_id)
    
    def test_process_request_uses_provided_correlation_id(self):
        """Test that middleware uses correlation ID from request headers"""
        correlation_id = str(uuid.uuid4())
        request = self.factory.get('/', HTTP_X_CORRELATION_ID=correlation_id)
        
        self.middleware.process_request(request)
        
        # Check that provided correlation ID was used
        self.assertEqual(request.correlation_id, correlation_id)
        self.assertEqual(get_correlation_id(), correlation_id)
    
    def test_process_request_validates_correlation_id_format(self):
        """Test that middleware validates correlation ID format"""
        invalid_correlation_id = "invalid-id-format-too-short"
        request = self.factory.get('/', HTTP_X_CORRELATION_ID=invalid_correlation_id)
        
        with patch('core.middleware.correlation_id_middleware.logger') as mock_logger:
            self.middleware.process_request(request)
            
            # Check that warning was logged
            mock_logger.warning.assert_called_once()
            
            # Check that new correlation ID was generated
            self.assertNotEqual(request.correlation_id, invalid_correlation_id)
            self.assertEqual(len(request.correlation_id), 36)  # UUID length
    
    def test_process_response_adds_correlation_id_header(self):
        """Test that middleware adds correlation ID to response headers"""
        correlation_id = str(uuid.uuid4())
        request = self.factory.get('/')
        request.correlation_id = correlation_id
        response = HttpResponse()
        
        result_response = self.middleware.process_response(request, response)
        
        # Check that correlation ID was added to response headers
        self.assertEqual(result_response['X-Correlation-ID'], correlation_id)
    
    def test_process_response_logs_request_completion(self):
        """Test that middleware logs request completion"""
        correlation_id = str(uuid.uuid4())
        request = self.factory.get('/test-path')
        request.correlation_id = correlation_id
        response = HttpResponse(status=200)
        
        with patch('core.middleware.correlation_id_middleware.logger') as mock_logger:
            self.middleware.process_response(request, response)
            
            # Check that completion was logged
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            self.assertIn(correlation_id, log_call)
            self.assertIn('Request completed', log_call)
            self.assertIn('200', log_call)
    
    def test_process_exception_logs_with_correlation_id(self):
        """Test that middleware logs exceptions with correlation ID"""
        correlation_id = str(uuid.uuid4())
        request = self.factory.get('/test-path')
        request.correlation_id = correlation_id
        exception = ValueError("Test exception")
        
        with patch('core.middleware.correlation_id_middleware.logger') as mock_logger:
            self.middleware.process_exception(request, exception)
            
            # Check that exception was logged with correlation ID
            mock_logger.error.assert_called()
            log_call = mock_logger.error.call_args[0][0]
            self.assertIn(correlation_id, log_call)
            self.assertIn('Request failed', log_call)
            self.assertIn('ValueError', log_call)
    
    def test_is_valid_correlation_id_validates_uuid_format(self):
        """Test correlation ID validation for UUID format"""
        valid_uuid = str(uuid.uuid4())
        invalid_uuid = "not-a-uuid"
        
        self.assertTrue(self.middleware._is_valid_correlation_id(valid_uuid))
        self.assertTrue(self.middleware._is_valid_correlation_id("valid-alphanumeric-123"))
        self.assertFalse(self.middleware._is_valid_correlation_id(invalid_uuid))
        self.assertFalse(self.middleware._is_valid_correlation_id(""))
        self.assertFalse(self.middleware._is_valid_correlation_id(None))
        self.assertFalse(self.middleware._is_valid_correlation_id("a" * 100))  # Too long


class TestCorrelationIdUtilities(TestCase):
    """Test cases for correlation ID utility functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
    
    def test_get_set_correlation_id(self):
        """Test getting and setting correlation ID"""
        correlation_id = str(uuid.uuid4())
        
        # Initially should be None
        self.assertIsNone(get_correlation_id())
        
        # Set correlation ID
        set_correlation_id(correlation_id)
        
        # Should return the set correlation ID
        self.assertEqual(get_correlation_id(), correlation_id)
    
    def test_correlation_id_manager_generate(self):
        """Test CorrelationIdManager.generate_correlation_id"""
        correlation_id = CorrelationIdManager.generate_correlation_id()
        
        self.assertIsNotNone(correlation_id)
        self.assertEqual(len(correlation_id), 36)  # UUID length
        
        # Should be valid UUID
        uuid.UUID(correlation_id)  # Will raise ValueError if invalid
    
    def test_correlation_id_manager_get_current(self):
        """Test CorrelationIdManager.get_current_correlation_id"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        self.assertEqual(CorrelationIdManager.get_current_correlation_id(), correlation_id)
    
    def test_correlation_id_manager_create_child(self):
        """Test CorrelationIdManager.create_child_correlation_id"""
        parent_id = str(uuid.uuid4())
        set_correlation_id(parent_id)
        
        with patch('core.middleware.correlation_id_middleware.logger') as mock_logger:
            child_id = CorrelationIdManager.create_child_correlation_id()
            
            # Should generate new UUID
            self.assertNotEqual(child_id, parent_id)
            self.assertEqual(len(child_id), 36)  # UUID length
            
            # Should log the relationship
            mock_logger.debug.assert_called()
            log_call = mock_logger.debug.call_args[0][0]
            self.assertIn(child_id, log_call)
            self.assertIn(parent_id, log_call)
    
    def test_correlation_id_manager_create_child_with_explicit_parent(self):
        """Test creating child correlation ID with explicit parent"""
        parent_id = str(uuid.uuid4())
        
        with patch('core.middleware.correlation_id_middleware.logger') as mock_logger:
            child_id = CorrelationIdManager.create_child_correlation_id(parent_id)
            
            # Should generate new UUID
            self.assertNotEqual(child_id, parent_id)
            self.assertEqual(len(child_id), 36)  # UUID length
            
            # Should log the relationship
            mock_logger.debug.assert_called()
            log_call = mock_logger.debug.call_args[0][0]
            self.assertIn(child_id, log_call)
            self.assertIn(parent_id, log_call)
    
    def test_correlation_id_manager_log_with_correlation_id(self):
        """Test logging with correlation ID"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        with patch('core.middleware.correlation_id_middleware.logger') as mock_logger:
            CorrelationIdManager.log_with_correlation_id('info', 'Test message', key='value')
            
            # Should log with correlation ID prefix
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            self.assertIn(f'[{correlation_id}]', log_call)
            self.assertIn('Test message', log_call)


class TestCorrelationIdFilter(TestCase):
    """Test cases for CorrelationIdFilter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.filter = CorrelationIdFilter()
        
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
    
    def test_filter_adds_correlation_id_to_record(self):
        """Test that filter adds correlation ID to log record"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Create mock log record
        record = Mock()
        
        # Apply filter
        result = self.filter.filter(record)
        
        # Should return True and add correlation_id attribute
        self.assertTrue(result)
        self.assertEqual(record.correlation_id, correlation_id)
    
    def test_filter_adds_na_when_no_correlation_id(self):
        """Test that filter adds 'N/A' when no correlation ID is set"""
        # Create mock log record
        record = Mock()
        
        # Apply filter
        result = self.filter.filter(record)
        
        # Should return True and add 'N/A' as correlation_id
        self.assertTrue(result)
        self.assertEqual(record.correlation_id, 'N/A')


class TestCorrelationIdIntegration(TestCase):
    """Integration tests for correlation ID system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.middleware = CorrelationIdMiddleware(Mock())
        
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
    
    def test_full_request_response_cycle(self):
        """Test complete request-response cycle with correlation ID"""
        # Create request
        request = self.factory.get('/test-endpoint')
        
        # Process request
        self.middleware.process_request(request)
        correlation_id = request.correlation_id
        
        # Simulate view processing
        self.assertEqual(get_correlation_id(), correlation_id)
        
        # Process response
        response = HttpResponse("Test response")
        result_response = self.middleware.process_response(request, response)
        
        # Check that correlation ID is in response headers
        self.assertEqual(result_response['X-Correlation-ID'], correlation_id)
    
    def test_correlation_id_persists_across_operations(self):
        """Test that correlation ID persists across different operations"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Simulate multiple operations
        self.assertEqual(get_correlation_id(), correlation_id)
        
        # Create child correlation ID
        child_id = CorrelationIdManager.create_child_correlation_id()
        
        # Original should still be available
        self.assertEqual(get_correlation_id(), correlation_id)
        self.assertNotEqual(child_id, correlation_id)
    
    def test_logging_integration(self):
        """Test integration with logging system"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Create log record and apply filter
        record = Mock()
        filter_instance = CorrelationIdFilter()
        filter_instance.filter(record)
        
        # Should have correlation ID
        self.assertEqual(record.correlation_id, correlation_id)
        
        # Test manager logging
        with patch('core.middleware.correlation_id_middleware.logger') as mock_logger:
            CorrelationIdManager.log_with_correlation_id('error', 'Test error')
            
            mock_logger.error.assert_called()
            log_call = mock_logger.error.call_args[0][0]
            self.assertIn(f'[{correlation_id}]', log_call)