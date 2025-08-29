# Performance Monitoring Demo

This module provides a comprehensive demonstration of the performance monitoring capabilities in the e-commerce platform.

## Features

The performance demo showcases:

- **Database Operations Monitoring**: Tracks query execution times and identifies slow queries
- **API Request Performance**: Monitors endpoint response times and memory usage
- **Concurrent Operations**: Tests thread safety and parallel execution performance
- **Memory Usage Tracking**: Monitors memory consumption during intensive operations
- **Error Scenario Handling**: Demonstrates monitoring during error conditions
- **Performance Reporting**: Generates detailed reports with recommendations

## Usage

### Running the Demo

#### Via Django Management Command
```bash
# Basic demo execution
python manage.py run_performance_demo

# Save results to file
python manage.py run_performance_demo --output-file performance_results.json

# Verbose output
python manage.py run_performance_demo --verbose
```

#### Via Python Script
```python
from apps.debugging.performance_demo import PerformanceDemo

# Create and run demo
demo = PerformanceDemo()
results = demo.run_full_demo()

# Or run individual scenarios
db_results = demo.simulate_database_operations()
api_results = demo.simulate_api_requests()
```

### Demo Scenarios

#### 1. Database Operations
- Simulates fast queries (100ms)
- Simulates slow queries (1.5s)
- Demonstrates N+1 query patterns
- Tracks query execution times

#### 2. API Request Simulation
- Tests multiple endpoint types
- Varies response times (0.1s to 2.0s)
- Monitors memory usage per request
- Tracks API performance metrics

#### 3. Concurrent Operations
- Spawns 5 worker threads
- Tests thread safety of monitoring
- Simulates parallel database access
- Measures concurrent performance

#### 4. Memory Intensive Operations
- Processes 100,000 records
- Tracks memory allocation patterns
- Monitors peak memory usage
- Demonstrates memory cleanup

#### 5. Error Scenarios
- Simulates database timeouts
- Tests memory overflow conditions
- Handles API error conditions
- Validates error monitoring

## Output Format

The demo generates a comprehensive report including:

```json
{
  "demo_execution": {
    "timestamp": "2024-01-01T12:00:00",
    "scenarios_run": 5,
    "successful_scenarios": 5,
    "failed_scenarios": 0
  },
  "scenario_results": [...],
  "performance_report": {
    "summary": {
      "total_operations": 25,
      "avg_execution_time": 0.86,
      "max_execution_time": 2.0,
      "min_execution_time": 0.1,
      "avg_memory_usage": 45.2,
      "max_memory_usage": 150.0
    },
    "detailed_metrics": [...],
    "recommendations": [
      "⚠️ Found 2 slow operations (>1s). Consider optimization.",
      "💾 Found 1 high memory operations (>100MB). Review memory efficiency."
    ]
  }
}
```

## Performance Recommendations

The demo automatically generates recommendations based on:

- **Slow Operations**: Operations taking >1 second
- **High Memory Usage**: Operations using >100MB
- **N+1 Query Patterns**: Multiple database queries in sequence
- **Error Rates**: Frequency of error conditions

## Integration with Monitoring System

The demo integrates with the main performance monitoring system:

```python
from apps.debugging.performance_monitoring import PerformanceMonitor

# The demo uses the same monitoring infrastructure
monitor = PerformanceMonitor()

# All metrics are collected using the standard monitoring API
with monitor.measure_execution_time("operation_name"):
    # Your code here
    pass

monitor.track_memory_usage("memory_checkpoint")
```

## Testing

Run the demo tests:

```bash
# Run all demo tests
python manage.py test apps.debugging.test_performance_demo

# Run specific test cases
python manage.py test apps.debugging.test_performance_demo.PerformanceDemoTestCase.test_simulate_database_operations
```

## Customization

### Adding New Scenarios

```python
class CustomPerformanceDemo(PerformanceDemo):
    def simulate_custom_operation(self):
        """Add your custom performance scenario"""
        with self.monitor.measure_execution_time("custom_operation"):
            # Your custom code here
            pass
        
        return {
            "operation": "custom_operation",
            "status": "completed"
        }
```

### Custom Metrics

```python
# Add custom metrics to the monitoring
demo = PerformanceDemo()
demo.monitor.add_custom_metric("custom_metric", value=123)
```

## Best Practices

1. **Regular Monitoring**: Run the demo regularly to establish performance baselines
2. **Environment Testing**: Test in different environments (dev, staging, production)
3. **Load Testing**: Combine with load testing tools for comprehensive analysis
4. **Trend Analysis**: Compare results over time to identify performance degradation
5. **Optimization**: Use recommendations to guide performance optimization efforts

## Troubleshooting

### Common Issues

1. **Database Connection Errors**: Ensure database is running and accessible
2. **Memory Errors**: Increase available memory for large-scale testing
3. **Thread Safety**: Monitor for race conditions in concurrent scenarios
4. **Timeout Issues**: Adjust timeout settings for slow operations

### Debug Mode

Enable debug logging for detailed monitoring information:

```python
import logging
logging.getLogger('apps.debugging').setLevel(logging.DEBUG)

demo = PerformanceDemo()
results = demo.run_full_demo()
```