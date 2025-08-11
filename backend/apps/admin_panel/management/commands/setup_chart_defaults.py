"""
Management command to set up default chart templates and data sources.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.admin_panel.chart_models import ChartTemplate

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up default chart templates and configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing templates',
        )

    def handle(self, *args, **options):
        if options['reset']:
            ChartTemplate.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Deleted existing chart templates')
            )

        # Get or create a system user for templates
        system_user, created = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@admin.local',
                'first_name': 'System',
                'last_name': 'User',
                'is_active': False,
            }
        )

        # Default chart templates
        templates = [
            {
                'name': 'Sales Overview',
                'description': 'Daily, weekly, and monthly sales performance tracking',
                'chart_type': 'line',
                'category': 'sales',
                'data_source': 'sales_overview',
                'config': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Sales Overview'
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': 'Time Period'
                            }
                        },
                        'y': {
                            'display': True,
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Revenue ($)'
                            }
                        }
                    }
                }
            },
            {
                'name': 'Top Products',
                'description': 'Best selling products by revenue and quantity',
                'chart_type': 'bar',
                'category': 'products',
                'data_source': 'product_performance',
                'config': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Top Performing Products'
                        },
                        'legend': {
                            'display': False
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': 'Products'
                            }
                        },
                        'y': {
                            'display': True,
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Revenue ($)'
                            }
                        }
                    }
                }
            },
            {
                'name': 'Customer Distribution',
                'description': 'Customer segmentation and distribution analysis',
                'chart_type': 'pie',
                'category': 'customers',
                'data_source': 'customer_analytics',
                'config': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Customer Distribution'
                        },
                        'legend': {
                            'display': True,
                            'position': 'right'
                        }
                    }
                }
            },
            {
                'name': 'Revenue Trends',
                'description': 'Revenue trends with forecasting and analysis',
                'chart_type': 'area',
                'category': 'financial',
                'data_source': 'revenue_trends',
                'config': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Revenue Trends'
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': 'Time Period'
                            }
                        },
                        'y': {
                            'display': True,
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Revenue ($)'
                            }
                        }
                    },
                    'elements': {
                        'line': {
                            'fill': True
                        }
                    }
                }
            },
            {
                'name': 'Inventory Levels',
                'description': 'Current inventory levels and stock alerts',
                'chart_type': 'bar',
                'category': 'inventory',
                'data_source': 'inventory_levels',
                'config': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Inventory Levels'
                        },
                        'legend': {
                            'display': False
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': 'Products'
                            }
                        },
                        'y': {
                            'display': True,
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Stock Quantity'
                            }
                        }
                    }
                }
            },
            {
                'name': 'Order Status Distribution',
                'description': 'Distribution of orders by status',
                'chart_type': 'doughnut',
                'category': 'orders',
                'data_source': 'order_status',
                'config': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Order Status Distribution'
                        },
                        'legend': {
                            'display': True,
                            'position': 'bottom'
                        }
                    }
                }
            },
            {
                'name': 'Performance Metrics',
                'description': 'Multi-dimensional performance analysis',
                'chart_type': 'radar',
                'category': 'analytics',
                'data_source': 'performance_metrics',
                'config': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Performance Metrics'
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        }
                    },
                    'scales': {
                        'r': {
                            'beginAtZero': True,
                            'max': 100
                        }
                    }
                }
            },
            {
                'name': 'Monthly Comparison',
                'description': 'Month-over-month comparison analysis',
                'chart_type': 'line',
                'category': 'analytics',
                'data_source': 'monthly_comparison',
                'config': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Monthly Comparison'
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': 'Month'
                            }
                        },
                        'y': {
                            'display': True,
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Value'
                            }
                        }
                    },
                    'interaction': {
                        'mode': 'index',
                        'intersect': False
                    }
                }
            }
        ]

        created_count = 0
        for template_data in templates:
            template, created = ChartTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    **template_data,
                    'created_by': system_user,
                    'is_public': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} chart templates'
            )
        )

        # Create sample data sources configuration
        self.stdout.write('\nSample data sources that should be configured:')
        data_sources = [
            'sales_overview - Daily/weekly/monthly sales data',
            'product_performance - Product sales and performance metrics',
            'customer_analytics - Customer segmentation and behavior data',
            'revenue_trends - Revenue trends and forecasting data',
            'inventory_levels - Current inventory and stock levels',
            'order_status - Order status distribution data',
            'performance_metrics - Multi-dimensional performance data',
            'monthly_comparison - Month-over-month comparison data'
        ]
        
        for source in data_sources:
            self.stdout.write(f'  - {source}')

        self.stdout.write(
            self.style.SUCCESS('\nChart templates setup completed!')
        )