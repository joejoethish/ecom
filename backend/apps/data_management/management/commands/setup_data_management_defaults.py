from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from apps.data_management.models import (
    DataMapping, DataQualityRule, DataLineage
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up default data management configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing configurations',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up data management defaults...')
        
        if options['reset']:
            self.stdout.write('Resetting existing configurations...')
            DataMapping.objects.all().delete()
            DataQualityRule.objects.all().delete()
            DataLineage.objects.all().delete()
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        # Create default data mappings
        self.create_default_mappings(admin_user)
        
        # Create default quality rules
        self.create_default_quality_rules(admin_user)
        
        # Create default lineage entries
        self.create_default_lineage()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up data management defaults')
        )

    def create_default_mappings(self, user):
        """Create default data mappings"""
        self.stdout.write('Creating default data mappings...')
        
        # Product mapping
        try:
            product_ct = ContentType.objects.get(model='product')
            DataMapping.objects.get_or_create(
                name='Standard Product Import',
                target_model='product',
                content_type=product_ct,
                created_by=user,
                defaults={
                    'description': 'Standard mapping for product imports',
                    'field_mappings': {
                        'name': 'product_name',
                        'description': 'product_description',
                        'price': 'unit_price',
                        'sku': 'product_sku',
                        'category': 'category_name',
                    },
                    'default_values': {
                        'is_active': True,
                        'status': 'active',
                    },
                    'validation_rules': {
                        'name': {'required': True, 'max_length': 200},
                        'price': {'required': True, 'min_value': 0},
                        'sku': {'required': True, 'unique': True},
                    },
                }
            )
        except ContentType.DoesNotExist:
            self.stdout.write('Product content type not found, skipping...')
        
        # Customer mapping
        try:
            customer_ct = ContentType.objects.get(model='customer')
            DataMapping.objects.get_or_create(
                name='Standard Customer Import',
                target_model='customer',
                content_type=customer_ct,
                created_by=user,
                defaults={
                    'description': 'Standard mapping for customer imports',
                    'field_mappings': {
                        'first_name': 'first_name',
                        'last_name': 'last_name',
                        'email': 'email_address',
                        'phone': 'phone_number',
                    },
                    'validation_rules': {
                        'email': {'required': True, 'format': 'email'},
                        'first_name': {'required': True},
                        'last_name': {'required': True},
                    },
                }
            )
        except ContentType.DoesNotExist:
            self.stdout.write('Customer content type not found, skipping...')

    def create_default_quality_rules(self, user):
        """Create default data quality rules"""
        self.stdout.write('Creating default quality rules...')
        
        # Email validation rule
        DataQualityRule.objects.get_or_create(
            name='Email Format Validation',
            target_model='customer',
            target_field='email',
            created_by=user,
            defaults={
                'description': 'Validates email format',
                'rule_type': 'format',
                'rule_config': {
                    'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                },
                'severity': 'error',
            }
        )
        
        # Price validation rule
        DataQualityRule.objects.get_or_create(
            name='Price Range Validation',
            target_model='product',
            target_field='price',
            created_by=user,
            defaults={
                'description': 'Validates product price is positive',
                'rule_type': 'range',
                'rule_config': {
                    'min_value': 0,
                    'max_value': 999999.99
                },
                'severity': 'error',
            }
        )
        
        # Required field rule
        DataQualityRule.objects.get_or_create(
            name='Product Name Required',
            target_model='product',
            target_field='name',
            created_by=user,
            defaults={
                'description': 'Product name is required',
                'rule_type': 'required',
                'rule_config': {},
                'severity': 'error',
            }
        )

    def create_default_lineage(self):
        """Create default data lineage entries"""
        self.stdout.write('Creating default data lineage...')
        
        # Product import lineage
        DataLineage.objects.get_or_create(
            source_name='product_import_csv',
            source_field='product_name',
            target_name='product',
            target_field='name',
            defaults={
                'source_type': 'file',
                'target_type': 'table',
                'transformation_type': 'direct_mapping',
                'transformation_config': {
                    'mapping_type': 'one_to_one',
                    'validation': True,
                }
            }
        )
        
        # Customer import lineage
        DataLineage.objects.get_or_create(
            source_name='customer_import_csv',
            source_field='email_address',
            target_name='customer',
            target_field='email',
            defaults={
                'source_type': 'file',
                'target_type': 'table',
                'transformation_type': 'direct_mapping',
                'transformation_config': {
                    'mapping_type': 'one_to_one',
                    'validation': True,
                    'format_validation': 'email',
                }
            }
        )