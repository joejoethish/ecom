import time
import statistics
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Avg, Count, Sum, Max, Min
from django.utils import timezone
from datetime import timedelta
from .models import CacheMetrics, CacheConfiguration, CacheOptimization, CacheAlert
from .cache_manager import cache_manager
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class CacheOptimizer:
    """Advanced cache optimization and performance tuning"""
    
    def __init__(self):
        self.optimization_threshold = 0.7  # 70% efficiency threshold
        self.alert_thresholds = {
            'hit_ratio': 0.8,
            'memory_usage': 0.85,
            'response_time': 100,  # ms
            'error_rate': 0.05,
        }
    
    def analyze_cache_performance(self, cache_name: str, days: int = 7) -> Dict[str, Any]:
        """Comprehensive cache performance analysis"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            metrics = CacheMetrics.objects.filter(
                cache_name=cache_name,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')
            
            if not metrics.exists():
                return {'error': 'No metrics data available'}
            
            analysis = {
                'cache_name': cache_name,
                'analysis_period': f'{days} days',
                'total_metrics': metrics.count(),
                'performance_summary': self._calculate_performance_summary(metrics),
                'trends': self._analyze_trends(metrics),
                'bottlenecks': self._identify_bottlenecks(metrics),
                'recommendations': self._generate_recommendations(cache_name, metrics),
                'optimization_score': self._calculate_optimization_score(metrics),
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Cache performance analysis failed: {e}")
            return {'error': str(e)}
    
    def optimize_cache_configuration(self, cache_name: str) -> Dict[str, Any]:
        """Automatically optimize cache configuration based on usage patterns"""
        try:
            config = CacheConfiguration.objects.get(name=cache_name)
            analysis = self.analyze_cache_performance(cache_name)
            
            if 'error' in analysis:
                return analysis
            
            optimizations = []
            
            # TTL Optimization
            ttl_optimization = self._optimize_ttl(cache_name, analysis)
            if ttl_optimization:
                optimizations.append(ttl_optimization)
            
            # Memory Optimization
            memory_optimization = self._optimize_memory(cache_name, analysis)
            if memory_optimization:
                optimizations.append(memory_optimization)
            
            # Compression Optimization
            compression_optimization = self._optimize_compression(cache_name, analysis)
            if compression_optimization:
                optimizations.append(compression_optimization)
            
            # Eviction Policy Optimization
            eviction_optimization = self._optimize_eviction_policy(cache_name, analysis)
            if eviction_optimization:
                optimizations.append(eviction_optimization)
            
            # Save optimization recommendations
            for opt in optimizations:
                CacheOptimization.objects.create(
                    cache_name=cache_name,
                    optimization_type=opt['type'],
                    current_config=opt['current_config'],
                    recommended_config=opt['recommended_config'],
                    expected_improvement=opt['expected_improvement'],
                    impact_score=opt['impact_score']
                )
            
            return {
                'cache_name': cache_name,
                'optimizations_found': len(optimizations),
                'optimizations': optimizations,
                'total_impact_score': sum(opt['impact_score'] for opt in optimizations)
            }
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {'error': str(e)}
    
    def apply_optimization(self, optimization_id: int, user=None) -> Dict[str, Any]:
        """Apply a specific optimization recommendation"""
        try:
            optimization = CacheOptimization.objects.get(id=optimization_id)
            
            if optimization.is_applied:
                return {'error': 'Optimization already applied'}
            
            config = CacheConfiguration.objects.get(name=optimization.cache_name)
            
            # Backup current configuration
            backup_config = {
                'ttl_seconds': config.ttl_seconds,
                'max_size_mb': config.max_size_mb,
                'compression_enabled': config.compression_enabled,
                'config_json': config.config_json.copy()
            }
            
            # Apply recommended configuration
            recommended = optimization.recommended_config
            
            if optimization.optimization_type == 'ttl_adjustment':
                config.ttl_seconds = recommended.get('ttl_seconds', config.ttl_seconds)
            elif optimization.optimization_type == 'memory_reallocation':
                config.max_size_mb = recommended.get('max_size_mb', config.max_size_mb)
            elif optimization.optimization_type == 'compression_tuning':
                config.compression_enabled = recommended.get('compression_enabled', config.compression_enabled)
            
            # Update config JSON with any additional settings
            config.config_json.update(recommended.get('additional_config', {}))
            
            config.save()
            
            # Mark optimization as applied
            optimization.is_applied = True
            optimization.applied_at = timezone.now()
            optimization.applied_by = user
            optimization.save()
            
            return {
                'success': True,
                'optimization_id': optimization_id,
                'backup_config': backup_config,
                'applied_config': recommended
            }
            
        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            return {'error': str(e)}
    
    def monitor_cache_health(self, cache_name: str) -> Dict[str, Any]:
        """Monitor cache health and generate alerts"""
        try:
            stats = cache_manager.get_cache_stats(cache_name)
            
            if not stats:
                return {'error': 'Unable to get cache stats'}
            
            alerts = []
            health_score = 100
            
            # Check hit ratio
            hit_ratio = stats.get('hit_ratio', 0)
            if hit_ratio < self.alert_thresholds['hit_ratio']:
                severity = 'critical' if hit_ratio < 0.5 else 'high'
                alerts.append(self._create_alert(
                    cache_name, 'high_miss_ratio', severity,
                    f'Hit ratio is {hit_ratio:.2%}, below threshold of {self.alert_thresholds["hit_ratio"]:.2%}',
                    self.alert_thresholds['hit_ratio'], hit_ratio
                ))
                health_score -= 30
            
            # Check memory usage
            memory_usage = stats.get('memory_usage_percent', 0) / 100
            if memory_usage > self.alert_thresholds['memory_usage']:
                severity = 'critical' if memory_usage > 0.95 else 'high'
                alerts.append(self._create_alert(
                    cache_name, 'memory_usage', severity,
                    f'Memory usage is {memory_usage:.2%}, above threshold of {self.alert_thresholds["memory_usage"]:.2%}',
                    self.alert_thresholds['memory_usage'], memory_usage
                ))
                health_score -= 25
            
            # Check response time
            response_time = stats.get('avg_response_time_ms', 0)
            if response_time > self.alert_thresholds['response_time']:
                severity = 'high' if response_time > 200 else 'medium'
                alerts.append(self._create_alert(
                    cache_name, 'slow_response', severity,
                    f'Average response time is {response_time:.2f}ms, above threshold of {self.alert_thresholds["response_time"]}ms',
                    self.alert_thresholds['response_time'], response_time
                ))
                health_score -= 20
            
            # Check error rate
            error_count = stats.get('error_count', 0)
            total_operations = stats.get('get_operations', 0) + stats.get('set_operations', 0)
            error_rate = error_count / max(total_operations, 1)
            
            if error_rate > self.alert_thresholds['error_rate']:
                severity = 'critical' if error_rate > 0.1 else 'high'
                alerts.append(self._create_alert(
                    cache_name, 'error_rate', severity,
                    f'Error rate is {error_rate:.2%}, above threshold of {self.alert_thresholds["error_rate"]:.2%}',
                    self.alert_thresholds['error_rate'], error_rate
                ))
                health_score -= 25
            
            health_score = max(0, health_score)
            
            return {
                'cache_name': cache_name,
                'health_score': health_score,
                'status': self._get_health_status(health_score),
                'alerts': alerts,
                'stats': stats,
                'recommendations': self._get_health_recommendations(health_score, alerts)
            }
            
        except Exception as e:
            logger.error(f"Cache health monitoring failed: {e}")
            return {'error': str(e)}
    
    def benchmark_cache_performance(self, cache_name: str, test_duration: int = 60) -> Dict[str, Any]:
        """Benchmark cache performance with synthetic load"""
        try:
            results = {
                'cache_name': cache_name,
                'test_duration': test_duration,
                'operations': {
                    'get': {'count': 0, 'total_time': 0, 'errors': 0},
                    'set': {'count': 0, 'total_time': 0, 'errors': 0},
                    'delete': {'count': 0, 'total_time': 0, 'errors': 0}
                },
                'response_times': []
            }
            
            start_time = time.time()
            operation_count = 0
            
            while time.time() - start_time < test_duration:
                operation_count += 1
                test_key = f"benchmark_key_{operation_count}"
                test_value = f"benchmark_value_{operation_count}_{'x' * 100}"
                
                # Test SET operation
                set_start = time.time()
                try:
                    success = cache_manager.set(test_key, test_value, cache_name)
                    set_time = (time.time() - set_start) * 1000  # Convert to ms
                    results['operations']['set']['count'] += 1
                    results['operations']['set']['total_time'] += set_time
                    results['response_times'].append(set_time)
                    
                    if not success:
                        results['operations']['set']['errors'] += 1
                        
                except Exception as e:
                    results['operations']['set']['errors'] += 1
                    logger.warning(f"Benchmark SET error: {e}")
                
                # Test GET operation
                get_start = time.time()
                try:
                    value = cache_manager.get(test_key, cache_name)
                    get_time = (time.time() - get_start) * 1000
                    results['operations']['get']['count'] += 1
                    results['operations']['get']['total_time'] += get_time
                    results['response_times'].append(get_time)
                    
                    if value != test_value:
                        results['operations']['get']['errors'] += 1
                        
                except Exception as e:
                    results['operations']['get']['errors'] += 1
                    logger.warning(f"Benchmark GET error: {e}")
                
                # Test DELETE operation (every 10th operation)
                if operation_count % 10 == 0:
                    delete_start = time.time()
                    try:
                        success = cache_manager.delete(test_key, cache_name)
                        delete_time = (time.time() - delete_start) * 1000
                        results['operations']['delete']['count'] += 1
                        results['operations']['delete']['total_time'] += delete_time
                        results['response_times'].append(delete_time)
                        
                        if not success:
                            results['operations']['delete']['errors'] += 1
                            
                    except Exception as e:
                        results['operations']['delete']['errors'] += 1
                        logger.warning(f"Benchmark DELETE error: {e}")
            
            # Calculate statistics
            if results['response_times']:
                results['statistics'] = {
                    'avg_response_time': statistics.mean(results['response_times']),
                    'median_response_time': statistics.median(results['response_times']),
                    'min_response_time': min(results['response_times']),
                    'max_response_time': max(results['response_times']),
                    'p95_response_time': np.percentile(results['response_times'], 95),
                    'p99_response_time': np.percentile(results['response_times'], 99),
                }
            
            # Calculate throughput
            total_operations = sum(op['count'] for op in results['operations'].values())
            results['throughput'] = {
                'operations_per_second': total_operations / test_duration,
                'total_operations': total_operations,
                'error_rate': sum(op['errors'] for op in results['operations'].values()) / max(total_operations, 1)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Cache benchmarking failed: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_summary(self, metrics) -> Dict[str, Any]:
        """Calculate performance summary from metrics"""
        aggregated = metrics.aggregate(
            avg_hit_ratio=Avg('hit_ratio'),
            avg_response_time=Avg('avg_response_time_ms'),
            avg_memory_usage=Avg('memory_usage_percent'),
            total_operations=Sum('get_operations') + Sum('set_operations'),
            total_errors=Sum('error_count')
        )
        
        return {
            'average_hit_ratio': aggregated['avg_hit_ratio'] or 0,
            'average_response_time_ms': aggregated['avg_response_time'] or 0,
            'average_memory_usage_percent': aggregated['avg_memory_usage'] or 0,
            'total_operations': aggregated['total_operations'] or 0,
            'total_errors': aggregated['total_errors'] or 0,
            'error_rate': (aggregated['total_errors'] or 0) / max(aggregated['total_operations'] or 1, 1)
        }
    
    def _analyze_trends(self, metrics) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        try:
            if metrics.count() < 2:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Convert to lists for analysis
            timestamps = [m.timestamp.timestamp() for m in metrics]
            hit_ratios = [m.hit_ratio for m in metrics]
            response_times = [m.avg_response_time_ms for m in metrics]
            memory_usage = [m.memory_usage_percent for m in metrics]
            
            # Calculate trends using linear regression
            X = np.array(timestamps).reshape(-1, 1)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            trends = {}
            
            # Hit ratio trend
            if hit_ratios:
                lr_hit = LinearRegression().fit(X_scaled, hit_ratios)
                trends['hit_ratio_trend'] = 'improving' if lr_hit.coef_[0] > 0 else 'declining'
                trends['hit_ratio_slope'] = float(lr_hit.coef_[0])
            
            # Response time trend
            if response_times:
                lr_response = LinearRegression().fit(X_scaled, response_times)
                trends['response_time_trend'] = 'improving' if lr_response.coef_[0] < 0 else 'declining'
                trends['response_time_slope'] = float(lr_response.coef_[0])
            
            # Memory usage trend
            if memory_usage:
                lr_memory = LinearRegression().fit(X_scaled, memory_usage)
                trends['memory_usage_trend'] = 'increasing' if lr_memory.coef_[0] > 0 else 'decreasing'
                trends['memory_usage_slope'] = float(lr_memory.coef_[0])
            
            return trends
            
        except Exception as e:
            logger.warning(f"Trend analysis failed: {e}")
            return {'error': 'Trend analysis failed'}
    
    def _identify_bottlenecks(self, metrics) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Analyze hit ratio bottlenecks
        low_hit_ratio_metrics = metrics.filter(hit_ratio__lt=0.7)
        if low_hit_ratio_metrics.exists():
            bottlenecks.append({
                'type': 'low_hit_ratio',
                'severity': 'high',
                'description': f'Hit ratio below 70% in {low_hit_ratio_metrics.count()} measurements',
                'impact': 'High cache miss rate leading to increased backend load'
            })
        
        # Analyze response time bottlenecks
        slow_response_metrics = metrics.filter(avg_response_time_ms__gt=100)
        if slow_response_metrics.exists():
            bottlenecks.append({
                'type': 'slow_response',
                'severity': 'medium',
                'description': f'Response time above 100ms in {slow_response_metrics.count()} measurements',
                'impact': 'Increased latency affecting user experience'
            })
        
        # Analyze memory bottlenecks
        high_memory_metrics = metrics.filter(memory_usage_percent__gt=85)
        if high_memory_metrics.exists():
            bottlenecks.append({
                'type': 'high_memory_usage',
                'severity': 'high',
                'description': f'Memory usage above 85% in {high_memory_metrics.count()} measurements',
                'impact': 'Risk of cache evictions and performance degradation'
            })
        
        return bottlenecks
    
    def _generate_recommendations(self, cache_name: str, metrics) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations = []
        summary = self._calculate_performance_summary(metrics)
        
        # Hit ratio recommendations
        if summary['average_hit_ratio'] < 0.8:
            recommendations.append({
                'type': 'increase_ttl',
                'priority': 'high',
                'description': 'Consider increasing TTL to improve hit ratio',
                'expected_impact': 'Improved hit ratio and reduced backend load'
            })
        
        # Response time recommendations
        if summary['average_response_time_ms'] > 50:
            recommendations.append({
                'type': 'optimize_serialization',
                'priority': 'medium',
                'description': 'Consider optimizing data serialization or using compression',
                'expected_impact': 'Reduced response time and improved throughput'
            })
        
        # Memory recommendations
        if summary['average_memory_usage_percent'] > 80:
            recommendations.append({
                'type': 'increase_memory',
                'priority': 'high',
                'description': 'Consider increasing cache memory allocation',
                'expected_impact': 'Reduced evictions and improved hit ratio'
            })
        
        return recommendations
    
    def _calculate_optimization_score(self, metrics) -> float:
        """Calculate overall optimization score (0-100)"""
        summary = self._calculate_performance_summary(metrics)
        
        # Weight different metrics
        hit_ratio_score = summary['average_hit_ratio'] * 40
        response_time_score = max(0, (100 - summary['average_response_time_ms']) / 100) * 30
        memory_score = max(0, (100 - summary['average_memory_usage_percent']) / 100) * 20
        error_score = max(0, (1 - summary['error_rate']) * 100) * 10
        
        total_score = hit_ratio_score + response_time_score + memory_score + error_score
        return min(100, max(0, total_score))
    
    def _optimize_ttl(self, cache_name: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize TTL based on usage patterns"""
        try:
            config = CacheConfiguration.objects.get(name=cache_name)
            current_ttl = config.ttl_seconds
            
            hit_ratio = analysis['performance_summary']['average_hit_ratio']
            
            if hit_ratio < 0.7:
                # Increase TTL to improve hit ratio
                recommended_ttl = int(current_ttl * 1.5)
                return {
                    'type': 'ttl_adjustment',
                    'current_config': {'ttl_seconds': current_ttl},
                    'recommended_config': {'ttl_seconds': recommended_ttl},
                    'expected_improvement': f'Increase hit ratio from {hit_ratio:.2%} to ~{hit_ratio * 1.2:.2%}',
                    'impact_score': 75
                }
            elif hit_ratio > 0.95:
                # Decrease TTL to free up memory
                recommended_ttl = int(current_ttl * 0.8)
                return {
                    'type': 'ttl_adjustment',
                    'current_config': {'ttl_seconds': current_ttl},
                    'recommended_config': {'ttl_seconds': recommended_ttl},
                    'expected_improvement': 'Reduce memory usage while maintaining good hit ratio',
                    'impact_score': 40
                }
            
            return None
            
        except Exception as e:
            logger.error(f"TTL optimization failed: {e}")
            return None
    
    def _optimize_memory(self, cache_name: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize memory allocation"""
        try:
            config = CacheConfiguration.objects.get(name=cache_name)
            current_memory = config.max_size_mb
            
            memory_usage = analysis['performance_summary']['average_memory_usage_percent']
            
            if memory_usage > 85:
                # Increase memory allocation
                recommended_memory = int(current_memory * 1.3)
                return {
                    'type': 'memory_reallocation',
                    'current_config': {'max_size_mb': current_memory},
                    'recommended_config': {'max_size_mb': recommended_memory},
                    'expected_improvement': f'Reduce memory pressure from {memory_usage:.1f}% to ~{memory_usage * 0.8:.1f}%',
                    'impact_score': 80
                }
            elif memory_usage < 50:
                # Decrease memory allocation
                recommended_memory = int(current_memory * 0.8)
                return {
                    'type': 'memory_reallocation',
                    'current_config': {'max_size_mb': current_memory},
                    'recommended_config': {'max_size_mb': recommended_memory},
                    'expected_improvement': 'Optimize memory usage without affecting performance',
                    'impact_score': 30
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return None
    
    def _optimize_compression(self, cache_name: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize compression settings"""
        try:
            config = CacheConfiguration.objects.get(name=cache_name)
            current_compression = config.compression_enabled
            
            response_time = analysis['performance_summary']['average_response_time_ms']
            memory_usage = analysis['performance_summary']['average_memory_usage_percent']
            
            if not current_compression and memory_usage > 70:
                # Enable compression to save memory
                return {
                    'type': 'compression_tuning',
                    'current_config': {'compression_enabled': current_compression},
                    'recommended_config': {'compression_enabled': True},
                    'expected_improvement': f'Reduce memory usage by ~30-50%',
                    'impact_score': 60
                }
            elif current_compression and response_time > 100:
                # Disable compression to improve response time
                return {
                    'type': 'compression_tuning',
                    'current_config': {'compression_enabled': current_compression},
                    'recommended_config': {'compression_enabled': False},
                    'expected_improvement': f'Improve response time by ~20-30%',
                    'impact_score': 50
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Compression optimization failed: {e}")
            return None
    
    def _optimize_eviction_policy(self, cache_name: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize cache eviction policy"""
        try:
            config = CacheConfiguration.objects.get(name=cache_name)
            current_policy = config.config_json.get('eviction_policy', 'lru')
            
            hit_ratio = analysis['performance_summary']['average_hit_ratio']
            
            if hit_ratio < 0.8 and current_policy == 'lru':
                # Try LFU policy for better hit ratio
                return {
                    'type': 'eviction_policy',
                    'current_config': {'eviction_policy': current_policy},
                    'recommended_config': {'eviction_policy': 'lfu'},
                    'expected_improvement': 'Potentially improve hit ratio by keeping frequently used items',
                    'impact_score': 45
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Eviction policy optimization failed: {e}")
            return None
    
    def _create_alert(self, cache_name: str, alert_type: str, severity: str, 
                     message: str, threshold: float, current: float) -> CacheAlert:
        """Create a cache alert"""
        return CacheAlert.objects.create(
            cache_name=cache_name,
            alert_type=alert_type,
            severity=severity,
            message=message,
            threshold_value=threshold,
            current_value=current
        )
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status based on score"""
        if health_score >= 90:
            return 'excellent'
        elif health_score >= 75:
            return 'good'
        elif health_score >= 50:
            return 'fair'
        elif health_score >= 25:
            return 'poor'
        else:
            return 'critical'
    
    def _get_health_recommendations(self, health_score: float, alerts: List) -> List[str]:
        """Get health improvement recommendations"""
        recommendations = []
        
        if health_score < 75:
            recommendations.append('Consider running cache optimization analysis')
        
        if any(alert.alert_type == 'high_miss_ratio' for alert in alerts):
            recommendations.append('Review cache TTL settings and data access patterns')
        
        if any(alert.alert_type == 'memory_usage' for alert in alerts):
            recommendations.append('Consider increasing cache memory or implementing better eviction policies')
        
        if any(alert.alert_type == 'slow_response' for alert in alerts):
            recommendations.append('Optimize data serialization or consider disabling compression')
        
        return recommendations


# Global optimizer instance
cache_optimizer = CacheOptimizer()