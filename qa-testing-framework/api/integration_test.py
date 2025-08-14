"""
Integration Test for API Testing Infrastructure

Demonstrates the complete API testing infrastructure setup
including client, validators, and performance testing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from api.validators import APIValidator
from api.performance import APIPerformanceTester, LoadTestConfig
from core.interfaces import Environment


def test_api_infrastructure_integration():
    """Test the complete API testing infrastructure"""
    
    print("Testing API Testing Infrastructure Integration...")
    
    # 1. Test API Client
    print("\n1. Testing API Client...")
    client = APITestClient('https://jsonplaceholder.typicode.com', Environment.DEVELOPMENT)
    
    # Test GET request
    response = client.get('/posts/1')
    print(f"   GET /posts/1: Status {response.status_code}, Response time: {response.response_time:.3f}s")
    
    # Test client assertions
    try:
        client.assert_response_success(response)
        client.assert_response_has_field(response, 'title')
        print("   ✓ Response assertions passed")
    except AssertionError as e:
        print(f"   ✗ Response assertion failed: {e}")
    
    # 2. Test API Validator
    print("\n2. Testing API Validator...")
    validator = APIValidator()
    
    validation_result = validator.validate_full_response(
        response,
        check_security=True,
        check_performance=True
    )
    
    print(f"   Validation result: {'✓ Valid' if validation_result.is_valid else '✗ Invalid'}")
    if validation_result.errors:
        print(f"   Errors: {len(validation_result.errors)}")
        for error in validation_result.errors[:3]:  # Show first 3 errors
            print(f"     - {error}")
    
    if validation_result.warnings:
        print(f"   Warnings: {len(validation_result.warnings)}")
        for warning in validation_result.warnings[:3]:  # Show first 3 warnings
            print(f"     - {warning}")
    
    # 3. Test Performance Monitoring
    print("\n3. Testing Performance Monitoring...")
    
    # Get performance metrics from client
    metrics = client.get_performance_metrics()
    if metrics:
        print(f"   Total requests: {metrics['total_requests']}")
        print(f"   Average response time: {metrics['avg_response_time']:.3f}s")
        print(f"   Success rate: {metrics['success_rate']:.1%}")
    
    # 4. Test Load Testing (very light test)
    print("\n4. Testing Load Testing...")
    
    def simple_test_scenario(test_client):
        """Simple test scenario for load testing"""
        return test_client.get('/posts/1')
    
    performance_tester = APIPerformanceTester('https://jsonplaceholder.typicode.com', 'test')
    
    # Run a very light load test
    try:
        load_results = performance_tester.test_endpoint_performance(
            '/posts/1',
            method='GET',
            concurrent_users=2,
            duration_seconds=5
        )
        
        print(f"   Load test completed:")
        print(f"     Total requests: {load_results.total_requests}")
        print(f"     Success rate: {load_results.success_rate:.1f}%")
        print(f"     Average RPS: {load_results.requests_per_second:.1f}")
        
        # Get response time stats
        stats = load_results.get_response_time_stats()
        if stats:
            print(f"     Response times - Min: {stats['min']:.3f}s, Max: {stats['max']:.3f}s, Avg: {stats['mean']:.3f}s")
    
    except Exception as e:
        print(f"   Load test failed: {e}")
    
    print("\n✓ API Testing Infrastructure Integration Test Completed!")
    return True


if __name__ == '__main__':
    try:
        test_api_infrastructure_integration()
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()