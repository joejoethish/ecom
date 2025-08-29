"""
Performance Monitoring Demo

This script demonstrates the capabilities of the performance monitoring service
by generating sample performance data and testing various monitoring scenarios.
"""

import time
import random
import threading
from typing import Dict, List, Any
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from apps.debugging.performance_monitoring import PerformanceMonitor


class PerformanceDemo:
    """Demo class to showcase performance monitoring capabilities"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.results = []
    
    def simulate_database_operations(self) -> Dict[str, Any]:
        """Simulate various database operations with different performance characteristics"""
        print("🔍 Simulating database operations...")
        
        # Fast query simulation
        with self.monitor.measure_execution_time("fast_query"):
            time.sleep(0.1)  # Simulate 100ms query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        
        # Slow query simulation
        with self.monitor.measure_execution_time("slow_query"):
            time.sleep(1.5)  # Simulate 1.5s query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        
        # N+1 query simulation
        with self.monitor.measure_execution_time("n_plus_one_queries"):
            for i in range(10):
                time.sleep(0.05)  # Simulate multiple small queries
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
        
        return {
            "operation": "database_operations",
            "queries_executed": 12,
            "total_time": "~2.1s"
        }
    
    def simulate_api_requests(self) -> Dict[str, Any]:
        """Simulate API request processing with various response times"""
        print("🌐 Simulating API requests...")
        
        endpoints = [
            ("GET /api/products/", 0.2),
            ("POST /api/orders/", 0.8),
            ("GET /api/users/profile/", 0.1),
            ("PUT /api/inventory/update/", 1.2),
            ("GET /api/analytics/dashboard/", 2.0)
        ]
        
        for endpoint, duration in endpoints:
            with self.monitor.measure_execution_time(f"api_request_{endpoint.split('/')[-2]}"):
                time.sleep(duration)
                # Simulate memory usage
                self.monitor.track_memory_usage(f"memory_api_{endpoint.split('/')[-2]}")
        
        return {
            "operation": "api_requests",
            "endpoints_tested": len(endpoints),
            "avg_response_time": "0.86s"
        }
    
    def simulate_concurrent_operations(self) -> Dict[str, Any]:
        """Simulate concurrent operations to test thread safety"""
        print("⚡ Simulating concurrent operations...")
        
        def worker_task(worker_id: int):
            """Worker function for concurrent execution"""
            with self.monitor.measure_execution_time(f"concurrent_worker_{worker_id}"):
                # Simulate work
                time.sleep(random.uniform(0.5, 1.5))
                
                # Simulate memory allocation
                data = [i for i in range(random.randint(1000, 5000))]
                self.monitor.track_memory_usage(f"worker_{worker_id}_memory")
                
                # Simulate database operation
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
        
        # Create and start threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return {
            "operation": "concurrent_operations",
            "threads_executed": 5,
            "completion": "success"
        }
    
    def simulate_memory_intensive_operations(self) -> Dict[str, Any]:
        """Simulate memory-intensive operations"""
        print("💾 Simulating memory-intensive operations...")
        
        with self.monitor.measure_execution_time("memory_intensive_operation"):
            # Simulate large data processing
            large_data = []
            for i in range(100000):
                large_data.append({
                    'id': i,
                    'data': f"sample_data_{i}",
                    'timestamp': timezone.now().isoformat()
                })
            
            self.monitor.track_memory_usage("large_data_processing")
            
            # Simulate data transformation
            processed_data = [item for item in large_data if item['id'] % 2 == 0]
            self.monitor.track_memory_usage("data_transformation")
            
            # Clean up
            del large_data
            del processed_data
        
        return {
            "operation": "memory_intensive_operations",
            "records_processed": 100000,
            "memory_peak": "tracked"
        }
    
    def simulate_error_scenarios(self) -> Dict[str, Any]:
        """Simulate various error scenarios for monitoring"""
        print("❌ Simulating error scenarios...")
        
        error_scenarios = [
            ("database_timeout", lambda: time.sleep(3)),
            ("memory_overflow", lambda: [i for i in range(1000000)]),
            ("api_error", lambda: time.sleep(0.5)),
        ]
        
        for scenario_name, scenario_func in error_scenarios:
            try:
                with self.monitor.measure_execution_time(f"error_scenario_{scenario_name}"):
                    scenario_func()
                    self.monitor.track_memory_usage(f"error_{scenario_name}")
            except Exception as e:
                print(f"  ⚠️  Caught expected error in {scenario_name}: {type(e).__name__}")
        
        return {
            "operation": "error_scenarios",
            "scenarios_tested": len(error_scenarios),
            "errors_handled": "success"
        }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report"""
        print("📊 Generating performance report...")
        
        # Get performance metrics
        metrics = self.monitor.get_performance_metrics()
        
        # Calculate summary statistics
        execution_times = [m['duration'] for m in metrics if 'duration' in m]
        memory_usage = [m['memory_mb'] for m in metrics if 'memory_mb' in m]
        
        report = {
            "summary": {
                "total_operations": len(metrics),
                "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
                "max_execution_time": max(execution_times) if execution_times else 0,
                "min_execution_time": min(execution_times) if execution_times else 0,
                "avg_memory_usage": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                "max_memory_usage": max(memory_usage) if memory_usage else 0,
            },
            "detailed_metrics": metrics,
            "recommendations": self._generate_recommendations(metrics)
        }
        
        return report
    
    def _generate_recommendations(self, metrics: List[Dict[str, Any]]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        # Analyze execution times
        slow_operations = [m for m in metrics if m.get('duration', 0) > 1.0]
        if slow_operations:
            recommendations.append(
                f"⚠️  Found {len(slow_operations)} slow operations (>1s). Consider optimization."
            )
        
        # Analyze memory usage
        high_memory_ops = [m for m in metrics if m.get('memory_mb', 0) > 100]
        if high_memory_ops:
            recommendations.append(
                f"💾 Found {len(high_memory_ops)} high memory operations (>100MB). Review memory efficiency."
            )
        
        # Check for N+1 queries
        query_operations = [m for m in metrics if 'query' in m.get('operation_name', '').lower()]
        if len(query_operations) > 5:
            recommendations.append(
                "🔍 Multiple database queries detected. Check for N+1 query patterns."
            )
        
        if not recommendations:
            recommendations.append("✅ Performance looks good! No major issues detected.")
        
        return recommendations
    
    def run_full_demo(self) -> Dict[str, Any]:
        """Run the complete performance monitoring demo"""
        print("🚀 Starting Performance Monitoring Demo")
        print("=" * 50)
        
        demo_results = []
        
        # Run all demo scenarios
        scenarios = [
            self.simulate_database_operations,
            self.simulate_api_requests,
            self.simulate_concurrent_operations,
            self.simulate_memory_intensive_operations,
            self.simulate_error_scenarios
        ]
        
        for scenario in scenarios:
            try:
                result = scenario()
                demo_results.append(result)
                print(f"✅ {result['operation']} completed successfully")
            except Exception as e:
                error_result = {
                    "operation": scenario.__name__,
                    "status": "error",
                    "error": str(e)
                }
                demo_results.append(error_result)
                print(f"❌ {scenario.__name__} failed: {e}")
        
        # Generate final report
        performance_report = self.generate_performance_report()
        
        final_results = {
            "demo_execution": {
                "timestamp": timezone.now().isoformat(),
                "scenarios_run": len(scenarios),
                "successful_scenarios": len([r for r in demo_results if r.get('status') != 'error']),
                "failed_scenarios": len([r for r in demo_results if r.get('status') == 'error'])
            },
            "scenario_results": demo_results,
            "performance_report": performance_report
        }
        
        print("\n" + "=" * 50)
        print("📈 Demo Summary:")
        print(f"  • Scenarios executed: {final_results['demo_execution']['scenarios_run']}")
        print(f"  • Successful: {final_results['demo_execution']['successful_scenarios']}")
        print(f"  • Failed: {final_results['demo_execution']['failed_scenarios']}")
        print(f"  • Total operations monitored: {performance_report['summary']['total_operations']}")
        print(f"  • Average execution time: {performance_report['summary']['avg_execution_time']:.3f}s")
        
        print("\n🎯 Recommendations:")
        for rec in performance_report['recommendations']:
            print(f"  {rec}")
        
        return final_results


def run_demo():
    """Convenience function to run the performance demo"""
    demo = PerformanceDemo()
    return demo.run_full_demo()


if __name__ == "__main__":
    # Run demo if executed directly
    results = run_demo()
    print(f"\n✨ Demo completed! Check the results above for detailed performance insights.")