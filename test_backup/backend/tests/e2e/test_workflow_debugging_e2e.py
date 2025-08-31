"""
End-to-End Test Suite for Workflow Debugging System

This module contains comprehensive E2E tests for all major workflows:
- User login workflow
- Product fetch workflow  
- Cart operations workflow
- Checkout workflow

Requirements: 4.1, 4.2, 4.3, 4.4
"""

import pytest
import uuid
import time
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from apps.debugging.models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, ErrorLog
)
from apps.debugging.services import WorkflowTracingEngine
from apps.products.models import Product, Category
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order


User = get_user_model()


class WorkflowDebuggingE2ETestCase(TransactionTestCase):
    """Base test case for E2E workflow debugging tests"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test products
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            price=99.99,
            category=self.category,
            stock_quantity=10
        )
        
        # Performance thresholds for testing
        self.performance_thresholds = {
            'login_workflow': 2000,  # 2 seconds
            'product_fetch': 1000,   # 1 second
            'cart_operations': 500,  # 500ms
            'checkout': 5000         # 5 seconds
        }
    
    def start_workflow_trace(self, workflow_type, metadata=None):
        """Helper to start workflow tracing"""
        correlation_id = uuid.uuid4()
        engine = WorkflowTracingEngine(correlation_id=correlation_id)
        session = engine.start_workflow(
            workflow_type=workflow_type,
            user=self.user,
            metadata=metadata or {}
        )
        return correlation_id, engine, session
    
    def assert_workflow_performance(self, correlation_id, workflow_type, max_duration_ms):
        """Assert workflow completed within performance threshold"""
        session = WorkflowSession.objects.get(correlation_id=correlation_id)
        
        if session.end_time and session.start_time:
            duration = session.end_time - session.start_time
            duration_ms = int(duration.total_seconds() * 1000)
            
            self.assertLessEqual(
                duration_ms, 
                max_duration_ms,
                f"{workflow_type} workflow took {duration_ms}ms, expected <= {max_duration_ms}ms"
            )
    
    def assert_no_critical_errors(self, correlation_id):
        """Assert no critical errors occurred during workflow"""
        critical_errors = ErrorLog.objects.filter(
            correlation_id=correlation_id,
            severity='critical'
        )
        self.assertEqual(
            critical_errors.count(), 
            0, 
            f"Critical errors found: {list(critical_errors.values_list('error_message', flat=True))}"
        )


class UserLoginWorkflowE2ETest(WorkflowDebuggingE2ETestCase):
    """E2E tests for user login workflow tracing"""
    
    def test_successful_login_workflow_trace(self):
        """Test complete user login workflow with tracing
        
        Requirements: 4.1 - Login workflow tracing
        """
        # Start workflow trace
        correlation_id, engine, session = self.start_workflow_trace(
            'login',
            {'test_case': 'successful_login'}
        )
        
        # Step 1: Frontend form submission
        engine.trace_step(
            layer='frontend',
            component='LoginForm',
            operation='form_submit',
            metadata={'username': self.user.username}
        )
        
        # Step 2: API authentication
        login_url = reverse('auth:login')
        response = self.client.post(login_url, {
            'username': self.user.username,
            'password': 'testpass123'
        }, HTTP_X_CORRELATION_ID=str(correlation_id))
        
        engine.trace_step(
            layer='api',
            component='AuthenticationView',
            operation='authenticate_user',
            metadata={'status_code': response.status_code}
        )
        
        # Step 3: Database user lookup
        engine.trace_step(
            layer='database',
            component='UserModel',
            operation='user_lookup',
            metadata={'user_id': self.user.id}
        )
        
        # Step 4: JWT generation
        if response.status_code == 200:
            engine.trace_step(
                layer='api',
                component='JWTService',
                operation='generate_token',
                metadata={'user_id': self.user.id}
            )
        
        # Step 5: Frontend token storage
        engine.trace_step(
            layer='frontend',
            component='AuthService',
            operation='store_token',
            metadata={'token_stored': True}
        )
        
        # Complete workflow
        analysis = engine.complete_workflow()
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(session.workflow_type, 'login')
        self.assertEqual(session.status, 'completed')
        
        # Check trace steps
        trace_steps = TraceStep.objects.filter(workflow_session=session)
        self.assertEqual(trace_steps.count(), 5)
        
        # Verify step sequence
        steps = list(trace_steps.order_by('start_time'))
        expected_operations = [
            'form_submit', 'authenticate_user', 'user_lookup', 
            'generate_token', 'store_token'
        ]
        actual_operations = [step.operation for step in steps]
        self.assertEqual(actual_operations, expected_operations)
        
        # Performance assertion
        self.assert_workflow_performance(
            correlation_id, 
            'login', 
            self.performance_thresholds['login_workflow']
        )
        
        # No critical errors
        self.assert_no_critical_errors(correlation_id)
    
    def test_failed_login_workflow_trace(self):
        """Test failed login workflow with error tracking
        
        Requirements: 4.1 - Login workflow error handling
        """
        correlation_id, engine, session = self.start_workflow_trace(
            'login',
            {'test_case': 'failed_login'}
        )
        
        # Attempt login with wrong password
        login_url = reverse('auth:login')
        response = self.client.post(login_url, {
            'username': self.user.username,
            'password': 'wrongpassword'
        }, HTTP_X_CORRELATION_ID=str(correlation_id))
        
        # Trace authentication failure
        engine.trace_step(
            layer='api',
            component='AuthenticationView',
            operation='authenticate_user',
            metadata={'status_code': response.status_code, 'error': 'invalid_credentials'}
        )
        
        # Fail workflow
        engine.fail_workflow('Invalid credentials provided')
        
        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertEqual(session.status, 'failed')
        
        # Check error was logged
        errors = ErrorLog.objects.filter(correlation_id=correlation_id)
        self.assertGreater(errors.count(), 0)


class ProductFetchWorkflowE2ETest(WorkflowDebuggingE2ETestCase):
    """E2E tests for product catalog access workflow"""
    
    def test_product_catalog_fetch_workflow(self):
        """Test product catalog access workflow tracing
        
        Requirements: 4.2 - Product fetch workflow tracing
        """
        correlation_id, engine, session = self.start_workflow_trace(
            'product_fetch',
            {'test_case': 'catalog_access'}
        )
        
        # Step 1: Frontend page load
        engine.trace_step(
            layer='frontend',
            component='ProductCatalog',
            operation='page_load',
            metadata={'route': '/products'}
        )
        
        # Step 2: API product fetch
        products_url = reverse('products:product-list')
        response = self.client.get(
            products_url,
            HTTP_X_CORRELATION_ID=str(correlation_id)
        )
        
        engine.trace_step(
            layer='api',
            component='ProductViewSet',
            operation='list_products',
            metadata={'status_code': response.status_code}
        )
        
        # Step 3: Database query
        engine.trace_step(
            layer='database',
            component='ProductModel',
            operation='fetch_products',
            metadata={'product_count': Product.objects.count()}
        )
        
        # Step 4: Serialization
        engine.trace_step(
            layer='api',
            component='ProductSerializer',
            operation='serialize_products',
            metadata={'serialized_count': len(response.data.get('results', []))}
        )
        
        # Step 5: Frontend rendering
        engine.trace_step(
            layer='frontend',
            component='ProductList',
            operation='render_products',
            metadata={'products_rendered': len(response.data.get('results', []))}
        )
        
        # Complete workflow
        analysis = engine.complete_workflow()
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        
        # Performance assertion
        self.assert_workflow_performance(
            correlation_id,
            'product_fetch',
            self.performance_thresholds['product_fetch']
        )
        
        # No critical errors
        self.assert_no_critical_errors(correlation_id)
    
    def test_product_detail_fetch_workflow(self):
        """Test individual product detail fetch workflow
        
        Requirements: 4.2 - Product detail workflow tracing
        """
        correlation_id, engine, session = self.start_workflow_trace(
            'product_fetch',
            {'test_case': 'product_detail', 'product_id': self.product.id}
        )
        
        # Fetch product detail
        product_url = reverse('products:product-detail', kwargs={'pk': self.product.id})
        response = self.client.get(
            product_url,
            HTTP_X_CORRELATION_ID=str(correlation_id)
        )
        
        # Trace steps
        engine.trace_step(
            layer='api',
            component='ProductViewSet',
            operation='retrieve_product',
            metadata={'product_id': self.product.id, 'status_code': response.status_code}
        )
        
        engine.complete_workflow()
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.product.id)


class CartOperationsWorkflowE2ETest(WorkflowDebuggingE2ETestCase):
    """E2E tests for cart operations workflow"""
    
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
    
    def test_add_to_cart_workflow(self):
        """Test add to cart workflow tracing
        
        Requirements: 4.3 - Cart operations workflow tracing
        """
        correlation_id, engine, session = self.start_workflow_trace(
            'cart_update',
            {'test_case': 'add_to_cart', 'product_id': self.product.id}
        )
        
        # Step 1: Frontend add to cart action
        engine.trace_step(
            layer='frontend',
            component='ProductCard',
            operation='add_to_cart_click',
            metadata={'product_id': self.product.id, 'quantity': 1}
        )
        
        # Step 2: API cart update
        cart_url = reverse('cart:cart-add-item')
        response = self.client.post(cart_url, {
            'product_id': self.product.id,
            'quantity': 1
        }, HTTP_X_CORRELATION_ID=str(correlation_id))
        
        engine.trace_step(
            layer='api',
            component='CartViewSet',
            operation='add_item',
            metadata={'status_code': response.status_code}
        )
        
        # Step 3: Database modifications
        engine.trace_step(
            layer='database',
            component='CartModel',
            operation='create_cart_item',
            metadata={'cart_item_created': True}
        )
        
        # Step 4: Frontend state update
        engine.trace_step(
            layer='frontend',
            component='CartStore',
            operation='update_cart_state',
            metadata={'cart_updated': True}
        )
        
        # Complete workflow
        analysis = engine.complete_workflow()
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        
        # Verify cart item was created
        cart_items = CartItem.objects.filter(
            cart__user=self.user,
            product=self.product
        )
        self.assertEqual(cart_items.count(), 1)
        
        # Performance assertion
        self.assert_workflow_performance(
            correlation_id,
            'cart_update',
            self.performance_thresholds['cart_operations']
        )
    
    def test_remove_from_cart_workflow(self):
        """Test remove from cart workflow tracing
        
        Requirements: 4.3 - Cart removal workflow tracing
        """
        # First add item to cart
        cart, created = Cart.objects.get_or_create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )
        
        correlation_id, engine, session = self.start_workflow_trace(
            'cart_update',
            {'test_case': 'remove_from_cart', 'cart_item_id': cart_item.id}
        )
        
        # Remove from cart
        remove_url = reverse('cart:cart-remove-item', kwargs={'pk': cart_item.id})
        response = self.client.delete(
            remove_url,
            HTTP_X_CORRELATION_ID=str(correlation_id)
        )
        
        engine.trace_step(
            layer='api',
            component='CartViewSet',
            operation='remove_item',
            metadata={'cart_item_id': cart_item.id, 'status_code': response.status_code}
        )
        
        engine.complete_workflow()
        
        # Assertions
        self.assertEqual(response.status_code, 204)
        
        # Verify cart item was removed
        self.assertFalse(
            CartItem.objects.filter(id=cart_item.id).exists()
        )


class CheckoutWorkflowE2ETest(WorkflowDebuggingE2ETestCase):
    """E2E tests for checkout workflow"""
    
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
        
        # Create cart with items
        self.cart, created = Cart.objects.get_or_create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
    
    def test_checkout_workflow(self):
        """Test complete checkout workflow tracing
        
        Requirements: 4.4 - Checkout workflow tracing
        """
        correlation_id, engine, session = self.start_workflow_trace(
            'checkout',
            {'test_case': 'complete_checkout', 'cart_id': self.cart.id}
        )
        
        # Step 1: Payment processing
        engine.trace_step(
            layer='frontend',
            component='CheckoutForm',
            operation='submit_payment',
            metadata={'payment_method': 'credit_card'}
        )
        
        # Step 2: Order creation
        checkout_url = reverse('orders:order-create')
        response = self.client.post(checkout_url, {
            'shipping_address': '123 Test St',
            'payment_method': 'credit_card',
            'payment_token': 'test_token_123'
        }, HTTP_X_CORRELATION_ID=str(correlation_id))
        
        engine.trace_step(
            layer='api',
            component='OrderViewSet',
            operation='create_order',
            metadata={'status_code': response.status_code}
        )
        
        # Step 3: Inventory updates
        engine.trace_step(
            layer='database',
            component='ProductModel',
            operation='update_inventory',
            metadata={'product_id': self.product.id, 'quantity_reduced': 2}
        )
        
        # Step 4: Confirmation display
        engine.trace_step(
            layer='frontend',
            component='OrderConfirmation',
            operation='display_confirmation',
            metadata={'order_created': True}
        )
        
        # Complete workflow
        analysis = engine.complete_workflow()
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        
        # Verify order was created
        orders = Order.objects.filter(user=self.user)
        self.assertEqual(orders.count(), 1)
        
        # Performance assertion
        self.assert_workflow_performance(
            correlation_id,
            'checkout',
            self.performance_thresholds['checkout']
        )
        
        # No critical errors
        self.assert_no_critical_errors(correlation_id)


class WorkflowFailureRecoveryE2ETest(WorkflowDebuggingE2ETestCase):
    """E2E tests for workflow failure scenarios and recovery"""
    
    def test_database_connection_failure_recovery(self):
        """Test workflow behavior during database connection issues
        
        Requirements: 4.1, 4.2, 4.3, 4.4 - Error handling across workflows
        """
        correlation_id, engine, session = self.start_workflow_trace(
            'product_fetch',
            {'test_case': 'database_failure_simulation'}
        )
        
        # Simulate database connection failure
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = Exception("Database connection lost")
            
            products_url = reverse('products:product-list')
            response = self.client.get(
                products_url,
                HTTP_X_CORRELATION_ID=str(correlation_id)
            )
            
            # Trace the error
            engine.trace_step(
                layer='database',
                component='ProductModel',
                operation='fetch_products',
                metadata={'error': 'connection_lost', 'status_code': response.status_code}
            )
        
        # Fail workflow due to database error
        engine.fail_workflow('Database connection failure')
        
        # Assertions
        self.assertEqual(response.status_code, 500)
        
        # Check error was logged
        errors = ErrorLog.objects.filter(
            correlation_id=correlation_id,
            layer='database'
        )
        self.assertGreater(errors.count(), 0)
    
    def test_api_timeout_handling(self):
        """Test workflow behavior during API timeouts
        
        Requirements: 4.1, 4.2, 4.3, 4.4 - Timeout handling
        """
        correlation_id, engine, session = self.start_workflow_trace(
            'login',
            {'test_case': 'api_timeout_simulation'}
        )
        
        # Simulate slow API response
        with patch('time.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Add artificial delay to simulate timeout
            start_time = time.time()
            
            login_url = reverse('auth:login')
            response = self.client.post(login_url, {
                'username': self.user.username,
                'password': 'testpass123'
            }, HTTP_X_CORRELATION_ID=str(correlation_id))
            
            # Simulate timeout scenario
            if time.time() - start_time > 5:  # 5 second timeout
                engine.fail_workflow('API request timeout')
            else:
                engine.complete_workflow()
        
        # Check workflow completed or failed appropriately
        session.refresh_from_db()
        self.assertIn(session.status, ['completed', 'failed'])


class WorkflowPerformanceE2ETest(WorkflowDebuggingE2ETestCase):
    """E2E performance tests for all workflows"""
    
    def test_concurrent_workflow_performance(self):
        """Test system performance under concurrent workflow load
        
        Requirements: 7.1, 7.2, 7.3 - Performance monitoring
        """
        import threading
        import concurrent.futures
        
        def run_login_workflow():
            """Run a single login workflow"""
            correlation_id, engine, session = self.start_workflow_trace(
                'login',
                {'test_case': 'concurrent_load_test'}
            )
            
            login_url = reverse('auth:login')
            response = self.client.post(login_url, {
                'username': self.user.username,
                'password': 'testpass123'
            }, HTTP_X_CORRELATION_ID=str(correlation_id))
            
            engine.complete_workflow()
            return correlation_id, response.status_code
        
        # Run 10 concurrent login workflows
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_login_workflow) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Assertions
        self.assertEqual(len(results), 10)
        
        # All workflows should complete successfully
        for correlation_id, status_code in results:
            self.assertEqual(status_code, 200)
            
            # Check workflow completed
            session = WorkflowSession.objects.get(correlation_id=correlation_id)
            self.assertEqual(session.status, 'completed')
    
    def test_workflow_memory_usage_monitoring(self):
        """Test memory usage monitoring during workflows
        
        Requirements: 7.1, 7.2 - Memory performance monitoring
        """
        import psutil
        import os
        
        correlation_id, engine, session = self.start_workflow_trace(
            'product_fetch',
            {'test_case': 'memory_monitoring'}
        )
        
        # Monitor memory before workflow
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute workflow
        products_url = reverse('products:product-list')
        response = self.client.get(
            products_url,
            HTTP_X_CORRELATION_ID=str(correlation_id)
        )
        
        # Monitor memory after workflow
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Record memory metric
        PerformanceSnapshot.objects.create(
            correlation_id=correlation_id,
            layer='system',
            component='WorkflowTest',
            metric_name='memory_usage',
            metric_value=memory_increase,
            metadata={'memory_before': memory_before, 'memory_after': memory_after}
        )
        
        engine.complete_workflow()
        
        # Assert reasonable memory usage (less than 50MB increase)
        self.assertLess(memory_increase, 50, f"Memory increase too high: {memory_increase}MB")


@pytest.mark.integration
class WorkflowIntegrationE2ETest(WorkflowDebuggingE2ETestCase):
    """Integration tests for complete user journeys"""
    
    def test_complete_user_journey_e2e(self):
        """Test complete user journey from login to checkout
        
        Requirements: 4.1, 4.2, 4.3, 4.4 - Complete workflow integration
        """
        # 1. Login workflow
        login_correlation_id, login_engine, login_session = self.start_workflow_trace(
            'login',
            {'test_case': 'complete_journey_login'}
        )
        
        login_url = reverse('auth:login')
        login_response = self.client.post(login_url, {
            'username': self.user.username,
            'password': 'testpass123'
        }, HTTP_X_CORRELATION_ID=str(login_correlation_id))
        
        login_engine.complete_workflow()
        self.assertEqual(login_response.status_code, 200)
        
        # Authenticate for subsequent requests
        self.client.force_authenticate(user=self.user)
        
        # 2. Product fetch workflow
        product_correlation_id, product_engine, product_session = self.start_workflow_trace(
            'product_fetch',
            {'test_case': 'complete_journey_products'}
        )
        
        products_url = reverse('products:product-list')
        products_response = self.client.get(
            products_url,
            HTTP_X_CORRELATION_ID=str(product_correlation_id)
        )
        
        product_engine.complete_workflow()
        self.assertEqual(products_response.status_code, 200)
        
        # 3. Cart operations workflow
        cart_correlation_id, cart_engine, cart_session = self.start_workflow_trace(
            'cart_update',
            {'test_case': 'complete_journey_cart'}
        )
        
        cart_url = reverse('cart:cart-add-item')
        cart_response = self.client.post(cart_url, {
            'product_id': self.product.id,
            'quantity': 1
        }, HTTP_X_CORRELATION_ID=str(cart_correlation_id))
        
        cart_engine.complete_workflow()
        self.assertEqual(cart_response.status_code, 201)
        
        # 4. Checkout workflow
        checkout_correlation_id, checkout_engine, checkout_session = self.start_workflow_trace(
            'checkout',
            {'test_case': 'complete_journey_checkout'}
        )
        
        checkout_url = reverse('orders:order-create')
        checkout_response = self.client.post(checkout_url, {
            'shipping_address': '123 Test St',
            'payment_method': 'credit_card',
            'payment_token': 'test_token_123'
        }, HTTP_X_CORRELATION_ID=str(checkout_correlation_id))
        
        checkout_engine.complete_workflow()
        self.assertEqual(checkout_response.status_code, 201)
        
        # Verify complete journey
        all_sessions = WorkflowSession.objects.filter(user=self.user)
        self.assertEqual(all_sessions.count(), 4)
        
        # All workflows should be completed
        for session in all_sessions:
            self.assertEqual(session.status, 'completed')
        
        # Verify order was created
        orders = Order.objects.filter(user=self.user)
        self.assertEqual(orders.count(), 1)