# Mobile and Device Performance Monitoring
from django.utils import timezone
from datetime import timedelta
import json
import logging
from user_agents import parse

from .models import PerformanceMetric, UserExperienceMetrics

logger = logging.getLogger(__name__)

class MobilePerformanceMonitor:
    """Mobile device performance monitoring"""
    
    def __init__(self):
        self.device_categories = {
            'mobile': ['phone', 'smartphone'],
            'tablet': ['tablet', 'ipad'],
            'desktop': ['pc', 'desktop', 'laptop'],
            'other': ['bot', 'crawler', 'unknown']
        }
    
    def track_mobile_metrics(self, request, response_time, additional_metrics=None):
        """Track mobile-specific performance metrics"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        parsed_ua = parse(user_agent)
        
        device_info = self._extract_device_info(parsed_ua)
        network_info = self._extract_network_info(request)
        
        # Create mobile performance metric
        metric_data = {
            'metric_type': 'mobile_performance',
            'name': 'Mobile Response Time',
            'value': response_time,
            'unit': 'ms',
            'source': 'mobile_app',
            'endpoint': request.path,
            'user_agent': user_agent,
            'ip_address': self._get_client_ip(request),
            'metadata': {
                'device_info': device_info,
                'network_info': network_info,
                'screen_size': request.META.get('HTTP_X_SCREEN_SIZE'),
                'app_version': request.META.get('HTTP_X_APP_VERSION'),
                'os_version': f"{parsed_ua.os.family} {parsed_ua.os.version_string}",
                'browser_version': f"{parsed_ua.browser.family} {parsed_ua.browser.version_string}",
                **(additional_metrics or {})
            }
        }
        
        PerformanceMetric.objects.create(**metric_data)
        
        # Track user experience metrics for mobile
        self._track_mobile_ux_metrics(request, device_info, additional_metrics)
    
    def _extract_device_info(self, parsed_ua):
        """Extract device information from user agent"""
        device_type = 'other'
        
        if parsed_ua.is_mobile:
            device_type = 'mobile'
        elif parsed_ua.is_tablet:
            device_type = 'tablet'
        elif parsed_ua.is_pc:
            device_type = 'desktop'
        
        return {
            'type': device_type,
            'brand': parsed_ua.device.brand or 'Unknown',
            'model': parsed_ua.device.model or 'Unknown',
            'family': parsed_ua.device.family or 'Unknown',
            'is_mobile': parsed_ua.is_mobile,
            'is_tablet': parsed_ua.is_tablet,
            'is_touch_capable': parsed_ua.is_touch_capable,
            'is_bot': parsed_ua.is_bot
        }
    
    def _extract_network_info(self, request):
        """Extract network information from request headers"""
        return {
            'connection_type': request.META.get('HTTP_X_CONNECTION_TYPE'),
            'effective_type': request.META.get('HTTP_X_EFFECTIVE_CONNECTION_TYPE'),
            'downlink': request.META.get('HTTP_X_DOWNLINK'),
            'rtt': request.META.get('HTTP_X_RTT'),
            'save_data': request.META.get('HTTP_X_SAVE_DATA') == 'on'
        }
    
    def _track_mobile_ux_metrics(self, request, device_info, additional_metrics):
        """Track mobile user experience metrics"""
        if additional_metrics and 'ux_metrics' in additional_metrics:
            ux_data = additional_metrics['ux_metrics']
            
            UserExperienceMetrics.objects.create(
                session_id=request.session.session_key or 'anonymous',
                user_id=str(request.user.id) if request.user.is_authenticated else None,
                page_url=request.build_absolute_uri(),
                page_load_time=ux_data.get('page_load_time', 0),
                dom_content_loaded=ux_data.get('dom_content_loaded', 0),
                first_contentful_paint=ux_data.get('first_contentful_paint', 0),
                largest_contentful_paint=ux_data.get('largest_contentful_paint', 0),
                first_input_delay=ux_data.get('first_input_delay', 0),
                cumulative_layout_shift=ux_data.get('cumulative_layout_shift', 0),
                time_to_interactive=ux_data.get('time_to_interactive', 0),
                device_type=device_info['type'],
                browser=device_info.get('browser', 'Unknown'),
                os=device_info.get('os', 'Unknown'),
                screen_resolution=request.META.get('HTTP_X_SCREEN_SIZE', 'Unknown'),
                connection_type=request.META.get('HTTP_X_CONNECTION_TYPE'),
                geographic_location=self._get_geographic_location(request)
            )
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_geographic_location(self, request):
        """Get geographic location from IP (mock implementation)"""
        # This would integrate with a GeoIP service
        return request.META.get('HTTP_X_COUNTRY_CODE', 'Unknown')
    
    def analyze_mobile_performance(self, days=7):
        """Analyze mobile performance trends"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get mobile metrics
        mobile_metrics = PerformanceMetric.objects.filter(
            metric_type='mobile_performance',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        analysis = {
            'device_performance': self._analyze_by_device_type(mobile_metrics),
            'network_performance': self._analyze_by_network_type(mobile_metrics),
            'os_performance': self._analyze_by_os(mobile_metrics),
            'geographic_performance': self._analyze_by_geography(mobile_metrics),
            'recommendations': []
        }
        
        # Generate mobile-specific recommendations
        analysis['recommendations'] = self._generate_mobile_recommendations(analysis)
        
        return analysis
    
    def _analyze_by_device_type(self, metrics):
        """Analyze performance by device type"""
        device_stats = {}
        
        for metric in metrics:
            device_info = metric.metadata.get('device_info', {})
            device_type = device_info.get('type', 'unknown')
            
            if device_type not in device_stats:
                device_stats[device_type] = {
                    'count': 0,
                    'total_time': 0,
                    'response_times': []
                }
            
            device_stats[device_type]['count'] += 1
            device_stats[device_type]['total_time'] += metric.value
            device_stats[device_type]['response_times'].append(metric.value)
        
        # Calculate averages and percentiles
        for device_type, stats in device_stats.items():
            if stats['count'] > 0:
                stats['avg_response_time'] = stats['total_time'] / stats['count']
                stats['p95_response_time'] = self._calculate_percentile(stats['response_times'], 95)
                stats['p99_response_time'] = self._calculate_percentile(stats['response_times'], 99)
        
        return device_stats
    
    def _analyze_by_network_type(self, metrics):
        """Analyze performance by network type"""
        network_stats = {}
        
        for metric in metrics:
            network_info = metric.metadata.get('network_info', {})
            connection_type = network_info.get('connection_type', 'unknown')
            
            if connection_type not in network_stats:
                network_stats[connection_type] = {
                    'count': 0,
                    'total_time': 0,
                    'response_times': []
                }
            
            network_stats[connection_type]['count'] += 1
            network_stats[connection_type]['total_time'] += metric.value
            network_stats[connection_type]['response_times'].append(metric.value)
        
        # Calculate statistics
        for connection_type, stats in network_stats.items():
            if stats['count'] > 0:
                stats['avg_response_time'] = stats['total_time'] / stats['count']
                stats['p95_response_time'] = self._calculate_percentile(stats['response_times'], 95)
        
        return network_stats
    
    def _analyze_by_os(self, metrics):
        """Analyze performance by operating system"""
        os_stats = {}
        
        for metric in metrics:
            os_version = metric.metadata.get('os_version', 'Unknown')
            
            if os_version not in os_stats:
                os_stats[os_version] = {
                    'count': 0,
                    'total_time': 0,
                    'response_times': []
                }
            
            os_stats[os_version]['count'] += 1
            os_stats[os_version]['total_time'] += metric.value
            os_stats[os_version]['response_times'].append(metric.value)
        
        # Calculate statistics
        for os_version, stats in os_stats.items():
            if stats['count'] > 0:
                stats['avg_response_time'] = stats['total_time'] / stats['count']
        
        return os_stats
    
    def _analyze_by_geography(self, metrics):
        """Analyze performance by geographic location"""
        geo_stats = {}
        
        for metric in metrics:
            # This would use actual geographic data
            location = 'Unknown'  # Placeholder
            
            if location not in geo_stats:
                geo_stats[location] = {
                    'count': 0,
                    'total_time': 0,
                    'response_times': []
                }
            
            geo_stats[location]['count'] += 1
            geo_stats[location]['total_time'] += metric.value
            geo_stats[location]['response_times'].append(metric.value)
        
        return geo_stats
    
    def _calculate_percentile(self, data, percentile):
        """Calculate percentile for a list of values"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _generate_mobile_recommendations(self, analysis):
        """Generate mobile-specific performance recommendations"""
        recommendations = []
        
        # Check mobile vs desktop performance
        device_perf = analysis['device_performance']
        
        if 'mobile' in device_perf and 'desktop' in device_perf:
            mobile_avg = device_perf['mobile'].get('avg_response_time', 0)
            desktop_avg = device_perf['desktop'].get('avg_response_time', 0)
            
            if mobile_avg > desktop_avg * 1.5:  # Mobile 50% slower
                recommendations.append({
                    'type': 'mobile_optimization',
                    'priority': 'high',
                    'issue': 'Mobile performance significantly slower than desktop',
                    'recommendation': 'Implement mobile-specific optimizations: image compression, lazy loading, reduced JavaScript bundle size'
                })
        
        # Check network-specific issues
        network_perf = analysis['network_performance']
        
        if '2g' in network_perf or '3g' in network_perf:
            recommendations.append({
                'type': 'network_optimization',
                'priority': 'medium',
                'issue': 'Slow network connections detected',
                'recommendation': 'Implement progressive loading, offline capabilities, and data-saving features'
            })
        
        return recommendations


class CDNPerformanceMonitor:
    """CDN and geographic performance monitoring"""
    
    def __init__(self):
        self.cdn_endpoints = [
            'https://cdn1.example.com',
            'https://cdn2.example.com',
            'https://cdn3.example.com'
        ]
    
    def monitor_cdn_performance(self):
        """Monitor CDN performance across regions"""
        results = {}
        
        for endpoint in self.cdn_endpoints:
            results[endpoint] = self._test_cdn_endpoint(endpoint)
        
        return {
            'timestamp': timezone.now(),
            'cdn_results': results,
            'recommendations': self._generate_cdn_recommendations(results)
        }
    
    def _test_cdn_endpoint(self, endpoint):
        """Test individual CDN endpoint performance"""
        # Mock implementation - would use actual HTTP requests
        import random
        
        return {
            'response_time': random.uniform(50, 200),
            'availability': random.choice([True, True, True, False]),  # 75% uptime
            'cache_hit_rate': random.uniform(85, 98),
            'bandwidth': random.uniform(100, 500),  # Mbps
            'geographic_performance': {
                'us-east': random.uniform(20, 80),
                'us-west': random.uniform(30, 90),
                'europe': random.uniform(100, 200),
                'asia': random.uniform(150, 300)
            }
        }
    
    def _generate_cdn_recommendations(self, results):
        """Generate CDN optimization recommendations"""
        recommendations = []
        
        for endpoint, data in results.items():
            if not data['availability']:
                recommendations.append({
                    'type': 'cdn_availability',
                    'priority': 'critical',
                    'endpoint': endpoint,
                    'issue': 'CDN endpoint unavailable',
                    'recommendation': 'Investigate CDN endpoint health and failover mechanisms'
                })
            
            if data['cache_hit_rate'] < 90:
                recommendations.append({
                    'type': 'cdn_caching',
                    'priority': 'medium',
                    'endpoint': endpoint,
                    'issue': f"Low cache hit rate: {data['cache_hit_rate']:.1f}%",
                    'recommendation': 'Review caching policies and TTL settings'
                })
        
        return recommendations


class ThirdPartyServiceMonitor:
    """Third-party service performance monitoring"""
    
    def __init__(self):
        self.services = {
            'payment_gateway': 'https://api.stripe.com',
            'email_service': 'https://api.sendgrid.com',
            'analytics': 'https://www.google-analytics.com',
            'cdn': 'https://cdn.cloudflare.com'
        }
    
    def monitor_third_party_services(self):
        """Monitor third-party service performance"""
        results = {}
        
        for service_name, endpoint in self.services.items():
            results[service_name] = self._monitor_service(service_name, endpoint)
        
        return {
            'timestamp': timezone.now(),
            'service_results': results,
            'overall_health': self._calculate_overall_health(results),
            'recommendations': self._generate_service_recommendations(results)
        }
    
    def _monitor_service(self, service_name, endpoint):
        """Monitor individual third-party service"""
        # Mock implementation - would use actual HTTP requests
        import random
        
        return {
            'response_time': random.uniform(100, 1000),
            'availability': random.choice([True, True, True, True, False]),  # 80% uptime
            'error_rate': random.uniform(0, 5),
            'last_check': timezone.now(),
            'status_code': random.choice([200, 200, 200, 500, 503])
        }
    
    def _calculate_overall_health(self, results):
        """Calculate overall third-party service health"""
        total_services = len(results)
        healthy_services = sum(1 for result in results.values() if result['availability'])
        
        return {
            'health_percentage': (healthy_services / total_services) * 100,
            'total_services': total_services,
            'healthy_services': healthy_services,
            'unhealthy_services': total_services - healthy_services
        }
    
    def _generate_service_recommendations(self, results):
        """Generate third-party service recommendations"""
        recommendations = []
        
        for service_name, data in results.items():
            if not data['availability']:
                recommendations.append({
                    'type': 'service_availability',
                    'priority': 'critical',
                    'service': service_name,
                    'issue': 'Service unavailable',
                    'recommendation': f'Implement fallback mechanisms for {service_name}'
                })
            
            if data['response_time'] > 5000:  # 5 seconds
                recommendations.append({
                    'type': 'service_performance',
                    'priority': 'high',
                    'service': service_name,
                    'issue': f"Slow response time: {data['response_time']:.0f}ms",
                    'recommendation': f'Consider alternative providers or caching for {service_name}'
                })
            
            if data['error_rate'] > 2:  # 2% error rate
                recommendations.append({
                    'type': 'service_reliability',
                    'priority': 'medium',
                    'service': service_name,
                    'issue': f"High error rate: {data['error_rate']:.1f}%",
                    'recommendation': f'Investigate error patterns and implement retry logic for {service_name}'
                })
        
        return recommendations