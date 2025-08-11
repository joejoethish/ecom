# Performance Monitoring Documentation and Knowledge Base
from django.utils import timezone
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)

class PerformanceDocumentation:
    """Performance monitoring documentation and knowledge base"""
    
    def __init__(self):
        self.knowledge_base = {
            'performance_metrics': {
                'response_time': {
                    'description': 'Time taken to process and respond to requests',
                    'unit': 'milliseconds',
                    'good_threshold': '< 2000ms',
                    'warning_threshold': '2000-5000ms',
                    'critical_threshold': '> 5000ms',
                    'optimization_tips': [
                        'Optimize database queries',
                        'Implement caching strategies',
                        'Use CDN for static assets',
                        'Minimize API calls',
                        'Optimize code algorithms'
                    ]
                },
                'cpu_usage': {
                    'description': 'Percentage of CPU resources being utilized',
                    'unit': 'percentage',
                    'good_threshold': '< 70%',
                    'warning_threshold': '70-85%',
                    'critical_threshold': '> 85%',
                    'optimization_tips': [
                        'Optimize CPU-intensive operations',
                        'Implement horizontal scaling',
                        'Use asynchronous processing',
                        'Profile and optimize hot code paths',
                        'Consider upgrading hardware'
                    ]
                },
                'memory_usage': {
                    'description': 'Percentage of memory resources being utilized',
                    'unit': 'percentage',
                    'good_threshold': '< 75%',
                    'warning_threshold': '75-90%',
                    'critical_threshold': '> 90%',
                    'optimization_tips': [
                        'Fix memory leaks',
                        'Optimize data structures',
                        'Implement garbage collection tuning',
                        'Use memory profiling tools',
                        'Add more RAM or scale horizontally'
                    ]
                },
                'disk_usage': {
                    'description': 'Percentage of disk space being utilized',
                    'unit': 'percentage',
                    'good_threshold': '< 80%',
                    'warning_threshold': '80-95%',
                    'critical_threshold': '> 95%',
                    'optimization_tips': [
                        'Clean up old log files',
                        'Archive historical data',
                        'Implement log rotation',
                        'Use data compression',
                        'Add more storage capacity'
                    ]
                },
                'error_rate': {
                    'description': 'Percentage of requests resulting in errors',
                    'unit': 'percentage',
                    'good_threshold': '< 1%',
                    'warning_threshold': '1-5%',
                    'critical_threshold': '> 5%',
                    'optimization_tips': [
                        'Implement proper error handling',
                        'Add input validation',
                        'Fix application bugs',
                        'Improve error logging',
                        'Implement circuit breakers'
                    ]
                }
            },
            'troubleshooting_guides': {
                'high_response_time': {
                    'symptoms': [
                        'API responses taking longer than usual',
                        'User complaints about slow page loads',
                        'Timeout errors in logs'
                    ],
                    'investigation_steps': [
                        '1. Check database query performance',
                        '2. Review application logs for errors',
                        '3. Monitor CPU and memory usage',
                        '4. Check network connectivity',
                        '5. Analyze third-party service dependencies'
                    ],
                    'common_causes': [
                        'Slow database queries',
                        'Inefficient algorithms',
                        'Network latency',
                        'Resource contention',
                        'Third-party service issues'
                    ],
                    'solutions': [
                        'Optimize database queries and add indexes',
                        'Implement caching strategies',
                        'Scale resources horizontally or vertically',
                        'Use CDN for static content',
                        'Implement asynchronous processing'
                    ]
                },
                'high_cpu_usage': {
                    'symptoms': [
                        'Server becoming unresponsive',
                        'Slow application performance',
                        'High load averages'
                    ],
                    'investigation_steps': [
                        '1. Identify CPU-intensive processes',
                        '2. Profile application code',
                        '3. Check for infinite loops or recursive calls',
                        '4. Monitor concurrent user load',
                        '5. Review recent code deployments'
                    ],
                    'common_causes': [
                        'Inefficient algorithms',
                        'Infinite loops',
                        'High concurrent load',
                        'CPU-intensive operations',
                        'Insufficient resources'
                    ],
                    'solutions': [
                        'Optimize CPU-intensive code',
                        'Implement load balancing',
                        'Use caching to reduce computation',
                        'Scale resources horizontally',
                        'Implement rate limiting'
                    ]
                },
                'memory_leaks': {
                    'symptoms': [
                        'Gradually increasing memory usage',
                        'Out of memory errors',
                        'Application crashes',
                        'Garbage collection pressure'
                    ],
                    'investigation_steps': [
                        '1. Monitor memory usage over time',
                        '2. Use memory profiling tools',
                        '3. Check for unclosed resources',
                        '4. Review object lifecycle management',
                        '5. Analyze heap dumps'
                    ],
                    'common_causes': [
                        'Unclosed database connections',
                        'Event listener leaks',
                        'Circular references',
                        'Large object retention',
                        'Improper cache management'
                    ],
                    'solutions': [
                        'Fix resource leaks',
                        'Implement proper object disposal',
                        'Use weak references where appropriate',
                        'Optimize garbage collection settings',
                        'Implement memory monitoring'
                    ]
                }
            },
            'best_practices': {
                'monitoring': [
                    'Set up comprehensive monitoring for all critical metrics',
                    'Implement alerting with appropriate thresholds',
                    'Use distributed tracing for complex systems',
                    'Monitor both technical and business metrics',
                    'Implement health checks for all services'
                ],
                'optimization': [
                    'Profile before optimizing',
                    'Focus on the biggest bottlenecks first',
                    'Implement caching at multiple levels',
                    'Use asynchronous processing where possible',
                    'Optimize database queries and indexes'
                ],
                'scaling': [
                    'Design for horizontal scaling from the start',
                    'Use load balancers to distribute traffic',
                    'Implement auto-scaling based on metrics',
                    'Use microservices for better scalability',
                    'Cache frequently accessed data'
                ],
                'incident_response': [
                    'Have a clear incident response plan',
                    'Implement automated alerting and escalation',
                    'Maintain runbooks for common issues',
                    'Conduct post-incident reviews',
                    'Keep communication channels open during incidents'
                ]
            },
            'tools_and_technologies': {
                'monitoring_tools': [
                    {
                        'name': 'Prometheus',
                        'description': 'Open-source monitoring and alerting toolkit',
                        'use_case': 'Metrics collection and storage'
                    },
                    {
                        'name': 'Grafana',
                        'description': 'Open-source analytics and monitoring platform',
                        'use_case': 'Visualization and dashboards'
                    },
                    {
                        'name': 'New Relic',
                        'description': 'Application performance monitoring platform',
                        'use_case': 'APM and infrastructure monitoring'
                    },
                    {
                        'name': 'DataDog',
                        'description': 'Cloud monitoring and analytics platform',
                        'use_case': 'Full-stack monitoring and logging'
                    }
                ],
                'profiling_tools': [
                    {
                        'name': 'Django Debug Toolbar',
                        'description': 'Debug toolbar for Django applications',
                        'use_case': 'Development-time performance analysis'
                    },
                    {
                        'name': 'py-spy',
                        'description': 'Sampling profiler for Python programs',
                        'use_case': 'Production profiling with minimal overhead'
                    },
                    {
                        'name': 'cProfile',
                        'description': 'Built-in Python profiler',
                        'use_case': 'Detailed function-level profiling'
                    }
                ],
                'load_testing_tools': [
                    {
                        'name': 'Apache JMeter',
                        'description': 'Open-source load testing tool',
                        'use_case': 'Web application load testing'
                    },
                    {
                        'name': 'Locust',
                        'description': 'Python-based load testing tool',
                        'use_case': 'Scalable load testing with Python scripts'
                    },
                    {
                        'name': 'Artillery',
                        'description': 'Modern load testing toolkit',
                        'use_case': 'API and WebSocket load testing'
                    }
                ]
            }
        }
    
    def get_metric_documentation(self, metric_type):
        """Get documentation for a specific metric type"""
        return self.knowledge_base['performance_metrics'].get(metric_type, {
            'description': 'No documentation available for this metric',
            'optimization_tips': []
        })
    
    def get_troubleshooting_guide(self, issue_type):
        """Get troubleshooting guide for a specific issue"""
        return self.knowledge_base['troubleshooting_guides'].get(issue_type, {
            'symptoms': [],
            'investigation_steps': [],
            'common_causes': [],
            'solutions': []
        })
    
    def get_best_practices(self, category):
        """Get best practices for a specific category"""
        return self.knowledge_base['best_practices'].get(category, [])
    
    def get_recommended_tools(self, tool_category):
        """Get recommended tools for a specific category"""
        return self.knowledge_base['tools_and_technologies'].get(tool_category, [])
    
    def generate_performance_report_documentation(self, report_data):
        """Generate documentation for a performance report"""
        documentation = {
            'report_summary': self._generate_report_summary(report_data),
            'metric_explanations': self._generate_metric_explanations(report_data),
            'recommendations': self._generate_recommendations(report_data),
            'next_steps': self._generate_next_steps(report_data)
        }
        
        return documentation
    
    def _generate_report_summary(self, report_data):
        """Generate a summary of the performance report"""
        summary = []
        
        if 'response_time' in report_data:
            rt_data = report_data['response_time']
            if rt_data.get('avg', 0) > 2000:
                summary.append("Response times are above recommended thresholds")
            else:
                summary.append("Response times are within acceptable limits")
        
        if 'database' in report_data:
            db_data = report_data['database']
            slow_queries = db_data.get('slow_queries', 0)
            if slow_queries > 10:
                summary.append(f"High number of slow database queries detected ({slow_queries})")
        
        return summary
    
    def _generate_metric_explanations(self, report_data):
        """Generate explanations for metrics in the report"""
        explanations = {}
        
        for metric_type in report_data.keys():
            if metric_type in self.knowledge_base['performance_metrics']:
                explanations[metric_type] = self.knowledge_base['performance_metrics'][metric_type]
        
        return explanations
    
    def _generate_recommendations(self, report_data):
        """Generate recommendations based on report data"""
        recommendations = []
        
        if 'response_time' in report_data:
            rt_data = report_data['response_time']
            if rt_data.get('avg', 0) > 2000:
                recommendations.extend([
                    'Optimize database queries to reduce response times',
                    'Implement caching strategies for frequently accessed data',
                    'Consider using a CDN for static assets'
                ])
        
        if 'database' in report_data:
            db_data = report_data['database']
            if db_data.get('slow_queries', 0) > 10:
                recommendations.extend([
                    'Review and optimize slow database queries',
                    'Add appropriate database indexes',
                    'Consider query result caching'
                ])
        
        return recommendations
    
    def _generate_next_steps(self, report_data):
        """Generate next steps based on report data"""
        next_steps = [
            'Monitor performance metrics continuously',
            'Set up alerts for critical thresholds',
            'Schedule regular performance reviews',
            'Implement recommended optimizations',
            'Conduct load testing after optimizations'
        ]
        
        return next_steps
    
    def create_runbook(self, incident_type, custom_steps=None):
        """Create a runbook for handling specific incident types"""
        base_guide = self.get_troubleshooting_guide(incident_type)
        
        runbook = {
            'incident_type': incident_type,
            'severity_assessment': {
                'critical': 'System is down or severely impacted',
                'high': 'Significant performance degradation',
                'medium': 'Noticeable performance issues',
                'low': 'Minor performance concerns'
            },
            'immediate_actions': [
                'Assess the severity of the incident',
                'Notify relevant stakeholders',
                'Begin investigation using the steps below'
            ],
            'investigation_steps': base_guide.get('investigation_steps', []),
            'common_solutions': base_guide.get('solutions', []),
            'escalation_criteria': [
                'Issue persists after initial troubleshooting',
                'Multiple systems are affected',
                'Customer impact is significant',
                'Root cause cannot be identified within 30 minutes'
            ],
            'post_incident_actions': [
                'Document the incident and resolution',
                'Update monitoring and alerting if needed',
                'Schedule a post-incident review',
                'Implement preventive measures'
            ]
        }
        
        if custom_steps:
            runbook['custom_steps'] = custom_steps
        
        return runbook
    
    def get_performance_glossary(self):
        """Get a glossary of performance monitoring terms"""
        return {
            'APM': 'Application Performance Monitoring - monitoring and managing performance of software applications',
            'SLA': 'Service Level Agreement - commitment between service provider and client',
            'SLI': 'Service Level Indicator - quantitative measure of service level',
            'SLO': 'Service Level Objective - target value for a service level indicator',
            'MTTR': 'Mean Time To Recovery - average time to restore service after failure',
            'MTBF': 'Mean Time Between Failures - average time between system failures',
            'RPS': 'Requests Per Second - measure of throughput',
            'Latency': 'Time delay between request and response',
            'Throughput': 'Number of requests processed per unit time',
            'Percentile': 'Statistical measure indicating value below which percentage of observations fall',
            'Circuit Breaker': 'Design pattern to prevent cascading failures',
            'Load Balancer': 'Device that distributes network traffic across multiple servers',
            'CDN': 'Content Delivery Network - geographically distributed servers',
            'Caching': 'Storing frequently accessed data in fast storage',
            'Horizontal Scaling': 'Adding more servers to handle increased load',
            'Vertical Scaling': 'Adding more power to existing servers',
            'Bottleneck': 'Point of congestion that limits overall performance',
            'Profiling': 'Analysis of program performance and resource usage'
        }


class PerformanceKnowledgeBase:
    """Knowledge base for performance monitoring insights"""
    
    def __init__(self):
        self.documentation = PerformanceDocumentation()
    
    def search_knowledge_base(self, query):
        """Search the knowledge base for relevant information"""
        results = []
        query_lower = query.lower()
        
        # Search in metric documentation
        for metric_type, metric_info in self.documentation.knowledge_base['performance_metrics'].items():
            if query_lower in metric_type.lower() or query_lower in metric_info['description'].lower():
                results.append({
                    'type': 'metric',
                    'title': metric_type.replace('_', ' ').title(),
                    'content': metric_info,
                    'relevance': 'high'
                })
        
        # Search in troubleshooting guides
        for issue_type, guide_info in self.documentation.knowledge_base['troubleshooting_guides'].items():
            if query_lower in issue_type.lower():
                results.append({
                    'type': 'troubleshooting',
                    'title': issue_type.replace('_', ' ').title(),
                    'content': guide_info,
                    'relevance': 'high'
                })
        
        # Search in best practices
        for category, practices in self.documentation.knowledge_base['best_practices'].items():
            if query_lower in category.lower():
                results.append({
                    'type': 'best_practices',
                    'title': category.replace('_', ' ').title(),
                    'content': practices,
                    'relevance': 'medium'
                })
        
        return results
    
    def get_contextual_help(self, metric_type, current_value, threshold_status):
        """Get contextual help based on current metric status"""
        metric_doc = self.documentation.get_metric_documentation(metric_type)
        
        help_content = {
            'metric_info': metric_doc,
            'current_status': threshold_status,
            'recommendations': []
        }
        
        if threshold_status in ['warning', 'critical']:
            help_content['recommendations'] = metric_doc.get('optimization_tips', [])
            
            # Add specific troubleshooting guide if available
            if metric_type == 'response_time' and threshold_status == 'critical':
                help_content['troubleshooting'] = self.documentation.get_troubleshooting_guide('high_response_time')
            elif metric_type == 'cpu_usage' and threshold_status == 'critical':
                help_content['troubleshooting'] = self.documentation.get_troubleshooting_guide('high_cpu_usage')
        
        return help_content
    
    def generate_learning_resources(self, user_role, experience_level):
        """Generate personalized learning resources"""
        resources = {
            'beginner': {
                'articles': [
                    'Introduction to Performance Monitoring',
                    'Understanding Key Performance Metrics',
                    'Basic Troubleshooting Techniques'
                ],
                'tools': ['Basic monitoring dashboards', 'Simple alerting setup'],
                'next_steps': ['Learn about advanced metrics', 'Practice with monitoring tools']
            },
            'intermediate': {
                'articles': [
                    'Advanced Performance Analysis',
                    'Capacity Planning Fundamentals',
                    'Performance Optimization Strategies'
                ],
                'tools': ['APM tools', 'Load testing', 'Profiling tools'],
                'next_steps': ['Implement predictive analytics', 'Learn automation techniques']
            },
            'advanced': {
                'articles': [
                    'Machine Learning for Performance Monitoring',
                    'Advanced Capacity Planning',
                    'Performance Engineering Best Practices'
                ],
                'tools': ['Custom monitoring solutions', 'Advanced analytics', 'Automation frameworks'],
                'next_steps': ['Contribute to monitoring tools', 'Mentor others', 'Research new techniques']
            }
        }
        
        return resources.get(experience_level, resources['beginner'])