"""
Unit tests for Correlation Service
"""
import uuid
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.core.cache import cache
from core.services.correlation_service import (
    CorrelationIdService,
    with_correlation_id,
    log_database_operation,
    DatabaseCorrelationMixin,
    ExternalApiCorrelationMixin,
    CeleryCorrelationMixin,
    execute_with_correlation_id,
    trace_operation
)
from core.middleware.correlation_id_middleware import (
    get_correlation_id,
    set_correlation_id,
    _correlation_id_storage
)


class TestCorrelationIdService(TestCase):
    """Test cases for CorrelationIdService"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
        
        # Clear cache
        cache.clear()
    
    def test_get_current_correlation_id(self):
        """Test getting current correlation ID"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        result = CorrelationIdService.get_current_correlation_id()
        self.assertEqual(result, correlation_id)
    
    def test_set_current_correlation_id(self):
        """Test setting current correlation ID"""
        correlation_id = str(uuid.uuid4())
        
        CorrelationIdService.set_current_correlation_id(correlation_id)
        
        self.assertEqual(get_correlation_id(), correlation_id)
    
    def test_generate_correlation_id(self):
        """Test generating new correlation ID"""
        correlation_id = CorrelationIdService.generate_correlation_id()
        
        self.assertIsNotNone(correlation_id)
        self.assertEqual(len(correlation_id), 36)  # UUID length
        
        # Should be valid UUID
        uuid.UUID(correlation_id)  # Will raise ValueError if invalid
    
    def test_create_child_correlation_id(self):
        """Test creating child correlation ID"""
        parent_id = str(uuid.uuid4())
        set_correlation_id(parent_id)
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            child_id = CorrelationIdService.create_child_correlation_id()
            
            # Should generate new UUID
            self.assertNotEqual(child_id, parent_id)
            self.assertEqual(len(child_id), 36)  # UUID length
            
            # Should log the relationship
            mock_logger.debug.assert_called()
    
    def test_create_child_correlation_id_with_explicit_parent(self):
        """Test creating child correlation ID with explicit parent"""
        parent_id = str(uuid.uuid4())
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            child_id = CorrelationIdService.create_child_correlation_id(parent_id)
            
            # Should generate new UUID
            self.assertNotEqual(child_id, parent_id)
            self.assertEqual(len(child_id), 36)  # UUID length
            
            # Should log the relationship
            mock_logger.debug.assert_called()
    
    def test_store_correlation_context(self):
        """Test storing correlation context in cache"""
        correlation_id = str(uuid.uuid4())
        context = {'user_id': 123, 'action': 'test'}
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            CorrelationIdService.store_correlation_context(correlation_id, context)
            
            # Should store in cache
            cache_key = f"{CorrelationIdService.CACHE_PREFIX}:{correlation_id}"
            cached_context = cache.get(cache_key)
            self.assertEqual(cached_context, context)
            
            # Should log the storage
            mock_logger.debug.assert_called()
    
    def test_get_correlation_context(self):
        """Test retrieving correlation context from cache"""
        correlation_id = str(uuid.uuid4())
        context = {'user_id': 123, 'action': 'test'}
        
        # Store context first
        cache_key = f"{CorrelationIdService.CACHE_PREFIX}:{correlation_id}"
        cache.set(cache_key, context)
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            result = CorrelationIdService.get_correlation_context(correlation_id)
            
            self.assertEqual(result, context)
            mock_logger.debug.assert_called()
    
    def test_get_correlation_context_not_found(self):
        """Test retrieving non-existent correlation context"""
        correlation_id = str(uuid.uuid4())
        
        result = CorrelationIdService.get_correlation_context(correlation_id)
        
        self.assertIsNone(result)
    
    def test_clear_correlation_context(self):
        """Test clearing correlation context from cache"""
        correlation_id = str(uuid.uuid4())
        context = {'user_id': 123, 'action': 'test'}
        
        # Store context first
        cache_key = f"{CorrelationIdService.CACHE_PREFIX}:{correlation_id}"
        cache.set(cache_key, context)
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            CorrelationIdService.clear_correlation_context(correlation_id)
            
            # Should be removed from cache
            cached_context = cache.get(cache_key)
            self.assertIsNone(cached_context)
            
            # Should log the clearing
            mock_logger.debug.assert_called()


class TestCorrelationIdDecorators(TestCase):
    """Test cases for correlation ID decorators"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
    
    def test_with_correlation_id_decorator_generates_id(self):
        """Test that decorator generates correlation ID if none exists"""
        @with_correlation_id
        def test_function():
            return get_correlation_id()
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            result = test_function()
            
            # Should have generated and returned correlation ID
            self.assertIsNotNone(result)
            self.assertEqual(len(result), 36)  # UUID length
            
            # Should log the generation
            mock_logger.debug.assert_called()
    
    def test_with_correlation_id_decorator_uses_existing_id(self):
        """Test that decorator uses existing correlation ID"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        @with_correlation_id
        def test_function():
            return get_correlation_id()
        
        result = test_function()
        
        # Should use existing correlation ID
        self.assertEqual(result, correlation_id)
    
    def test_with_correlation_id_decorator_handles_exceptions(self):
        """Test that decorator handles exceptions properly"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        @with_correlation_id
        def test_function():
            raise ValueError("Test exception")
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            with self.assertRaises(ValueError):
                test_function()
            
            # Should log the error with correlation ID
            mock_logger.error.assert_called()
            log_call = mock_logger.error.call_args[0][0]
            self.assertIn(correlation_id, log_call)
    
    def test_trace_operation_decorator(self):
        """Test trace_operation decorator"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        @trace_operation("test_operation")
        def test_function():
            return "success"
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            result = test_function()
            
            # Should return function result
            self.assertEqual(result, "success")
            
            # Should log start and completion
            self.assertEqual(mock_logger.info.call_count, 2)
            
            # Check start log
            start_log = mock_logger.info.call_args_list[0][0][0]
            self.assertIn("Operation started", start_log)
            self.assertIn(correlation_id, start_log)
            self.assertIn("test_operation", start_log)
            
            # Check completion log
            completion_log = mock_logger.info.call_args_list[1][0][0]
            self.assertIn("Operation completed", completion_log)
            self.assertIn(correlation_id, completion_log)
    
    def test_trace_operation_decorator_handles_exceptions(self):
        """Test trace_operation decorator handles exceptions"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        @trace_operation("test_operation")
        def test_function():
            raise ValueError("Test exception")
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            with self.assertRaises(ValueError):
                test_function()
            
            # Should log start and error
            self.assertEqual(mock_logger.info.call_count, 1)  # Start only
            self.assertEqual(mock_logger.error.call_count, 1)  # Error
            
            # Check error log
            error_log = mock_logger.error.call_args[0][0]
            self.assertIn("Operation failed", error_log)
            self.assertIn(correlation_id, error_log)
            self.assertIn("test_operation", error_log)


class TestDatabaseCorrelationMixin(TestCase):
    """Test cases for DatabaseCorrelationMixin"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
    
    def test_save_logs_with_correlation_id(self):
        """Test that save method logs with correlation ID"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Create mock model instance
        mock_instance = Mock()
        mock_instance.pk = None  # New instance
        mock_instance._meta.db_table = 'test_table'
        
        # Apply mixin
        class TestModel(DatabaseCorrelationMixin):
            def __init__(self):
                self.pk = None
                self._meta = Mock()
                self._meta.db_table = 'test_table'
        
        instance = TestModel()
        
        with patch('core.services.correlation_service.log_database_operation') as mock_log:
            with patch.object(DatabaseCorrelationMixin, 'save', return_value=None):
                instance.save()
                
                # Should log INSERT operation
                mock_log.assert_called_once_with("INSERT", "test_table", correlation_id)
    
    def test_delete_logs_with_correlation_id(self):
        """Test that delete method logs with correlation ID"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Create mock model instance
        class TestModel(DatabaseCorrelationMixin):
            def __init__(self):
                self._meta = Mock()
                self._meta.db_table = 'test_table'
        
        instance = TestModel()
        
        with patch('core.services.correlation_service.log_database_operation') as mock_log:
            with patch.object(DatabaseCorrelationMixin, 'delete', return_value=None):
                instance.delete()
                
                # Should log DELETE operation
                mock_log.assert_called_once_with("DELETE", "test_table", correlation_id)


class TestExternalApiCorrelationMixin(TestCase):
    """Test cases for ExternalApiCorrelationMixin"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
    
    def test_get_correlation_headers(self):
        """Test getting correlation headers"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        mixin = ExternalApiCorrelationMixin()
        headers = mixin.get_correlation_headers()
        
        expected_headers = {
            'X-Correlation-ID': correlation_id,
            'X-Request-ID': correlation_id,
        }
        
        self.assertEqual(headers, expected_headers)
    
    def test_get_correlation_headers_no_id(self):
        """Test getting correlation headers when no ID is set"""
        mixin = ExternalApiCorrelationMixin()
        headers = mixin.get_correlation_headers()
        
        self.assertEqual(headers, {})
    
    def test_log_external_api_call(self):
        """Test logging external API calls"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        mixin = ExternalApiCorrelationMixin()
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            mixin.log_external_api_call('GET', 'https://api.example.com/test')
            
            # Should log with correlation ID
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            self.assertIn(correlation_id, log_call)
            self.assertIn('External API call', log_call)
            self.assertIn('GET', log_call)
            self.assertIn('https://api.example.com/test', log_call)


class TestUtilityFunctions(TestCase):
    """Test cases for utility functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing correlation ID
        if hasattr(_correlation_id_storage, 'correlation_id'):
            delattr(_correlation_id_storage, 'correlation_id')
    
    def test_log_database_operation(self):
        """Test logging database operations"""
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            log_database_operation('SELECT', 'users')
            
            # Should log with correlation ID
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            self.assertIn(correlation_id, log_call)
            self.assertIn('Database operation', log_call)
            self.assertIn('SELECT', log_call)
            self.assertIn('users', log_call)
    
    def test_log_database_operation_with_explicit_id(self):
        """Test logging database operations with explicit correlation ID"""
        correlation_id = str(uuid.uuid4())
        
        with patch('core.services.correlation_service.logger') as mock_logger:
            log_database_operation('UPDATE', 'products', correlation_id)
            
            # Should log with provided correlation ID
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            self.assertIn(correlation_id, log_call)
            self.assertIn('UPDATE', log_call)
            self.assertIn('products', log_call)
    
    def test_execute_with_correlation_id(self):
        """Test executing function with specific correlation ID"""
        original_id = str(uuid.uuid4())
        execution_id = str(uuid.uuid4())
        set_correlation_id(original_id)
        
        def test_function(arg1, arg2=None):
            # Should have execution correlation ID during function
            self.assertEqual(get_correlation_id(), execution_id)
            return f"{arg1}-{arg2}"
        
        result = execute_with_correlation_id(test_function, execution_id, "test", arg2="value")
        
        # Should return function result
        self.assertEqual(result, "test-value")
        
        # Should restore original correlation ID
        self.assertEqual(get_correlation_id(), original_id)
    
    def test_execute_with_correlation_id_generates_new_id(self):
        """Test executing function with generated correlation ID"""
        def test_function():
            correlation_id = get_correlation_id()
            self.assertIsNotNone(correlation_id)
            self.assertEqual(len(correlation_id), 36)  # UUID length
            return correlation_id
        
        result = execute_with_correlation_id(test_function)
        
        # Should have generated and used new correlation ID
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 36)  # UUID length
    
    def test_execute_with_correlation_id_handles_exceptions(self):
        """Test executing function with correlation ID handles exceptions"""
        original_id = str(uuid.uuid4())
        execution_id = str(uuid.uuid4())
        set_correlation_id(original_id)
        
        def test_function():
            raise ValueError("Test exception")
        
        with self.assertRaises(ValueError):
            execute_with_correlation_id(test_function, execution_id)
        
        # Should restore original correlation ID even after exception
        self.assertEqual(get_correlation_id(), original_id)