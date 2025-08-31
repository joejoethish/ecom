# Test data factory and management
import factory
import factory.fuzzy
from faker import Faker
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

fake = Faker()
User = get_user_model()

class BaseFactory(factory.django.DjangoModelFactory):
    """Base factory with common functionality"""
    
    @classmethod
    def create_batch_with_relations(cls, size: int, **kwargs) -> List:
        """Create batch of objects with proper relations"""
        return [cls.create(**kwargs) for _ in range(size)]

class UserFactory(BaseFactory):
    """Factory for User model"""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    date_joined = factory.Faker('date_time_this_year', tzinfo=None)

class AdminUserFactory(UserFactory):
    """Factory for admin users"""
    
    username = factory.Sequence(lambda n: f'admin{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@admin.com')
    is_staff = True
    is_superuser = True

class CategoryFactory(BaseFactory):
    """Factory for Category model"""
    
    class Meta:
        model = 'products.Category'
        django_get_or_create = ('name',)
    
    name = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=200)
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    is_active = True
    sort_order = factory.Sequence(lambda n: n)
    
    @factory.post_generation
    def parent(self, create, extracted, **kwargs):
        """Optionally set parent category"""
        if extracted:
            self.parent = extracted

class BrandFactory(BaseFactory):
    """Factory for Brand model"""
    
    class Meta:
        model = 'products.Brand'
        django_get_or_create = ('name',)
    
    name = factory.Faker('company')
    description = factory.Faker('text', max_nb_chars=200)
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    is_active = True

class ProductFactory(BaseFactory):
    """Factory for Product model"""
    
    class Meta:
        model = 'products.Product'
        django_get_or_create = ('sku',)
    
    name = factory.Faker('catch_phrase')
    description = factory.Faker('text', max_nb_chars=500)
    short_description = factory.Faker('text', max_nb_chars=100)
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    sku = factory.Sequence(lambda n: f'PROD-{n:06d}')
    
    # Pricing
    cost_price = factory.fuzzy.FuzzyDecimal(10.00, 100.00, 2)
    price = factory.LazyAttribute(lambda obj: obj.cost_price * Decimal('1.5'))  # 50% markup
    discount_price = factory.LazyAttribute(lambda obj: obj.price * Decimal('0.9'))  # 10% discount
    
    # Inventory
    stock_quantity = factory.fuzzy.FuzzyInteger(0, 1000)
    low_stock_threshold = factory.fuzzy.FuzzyInteger(5, 20)
    
    # Physical properties
    weight = factory.fuzzy.FuzzyDecimal(0.1, 50.0, 2)
    
    # SEO
    meta_title = factory.LazyAttribute(lambda obj: obj.name)
    meta_description = factory.LazyAttribute(lambda obj: obj.short_description)
    meta_keywords = factory.Faker('words', nb=5)
    
    # Status
    status = factory.fuzzy.FuzzyChoice(['draft', 'active', 'inactive', 'discontinued'])
    is_featured = factory.fuzzy.FuzzyChoice([True, False])
    is_digital = factory.fuzzy.FuzzyChoice([True, False])
    
    # Relations
    category = factory.SubFactory(CategoryFactory)
    brand = factory.SubFactory(BrandFactory)
    
    @factory.post_generation
    def dimensions(self, create, extracted, **kwargs):
        """Set product dimensions"""
        if create:
            self.dimensions = {
                'length': round(random.uniform(1.0, 50.0), 2),
                'width': round(random.uniform(1.0, 50.0), 2),
                'height': round(random.uniform(1.0, 50.0), 2),
            }

class CustomerFactory(UserFactory):
    """Factory for Customer users"""
    
    username = factory.Sequence(lambda n: f'customer{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@customer.com')
    phone = factory.Faker('phone_number')
    
    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        """Create customer profile"""
        if create:
            # Create customer profile if model exists
            pass

class OrderFactory(BaseFactory):
    """Factory for Order model"""
    
    class Meta:
        model = 'orders.Order'
        django_get_or_create = ('order_number',)
    
    order_number = factory.Sequence(lambda n: f'ORD-{n:08d}')
    customer = factory.SubFactory(CustomerFactory)
    
    # Pricing
    subtotal = factory.fuzzy.FuzzyDecimal(10.00, 1000.00, 2)
    tax_amount = factory.LazyAttribute(lambda obj: obj.subtotal * Decimal('0.08'))  # 8% tax
    shipping_amount = factory.fuzzy.FuzzyDecimal(0.00, 50.00, 2)
    discount_amount = factory.fuzzy.FuzzyDecimal(0.00, 100.00, 2)
    total_amount = factory.LazyAttribute(
        lambda obj: obj.subtotal + obj.tax_amount + obj.shipping_amount - obj.discount_amount
    )
    
    # Status
    status = factory.fuzzy.FuzzyChoice(['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'])
    payment_status = factory.fuzzy.FuzzyChoice(['pending', 'paid', 'failed', 'refunded'])
    payment_method = factory.fuzzy.FuzzyChoice(['credit_card', 'paypal', 'bank_transfer', 'cash_on_delivery'])
    
    # Shipping
    shipping_method = factory.fuzzy.FuzzyChoice(['standard', 'express', 'overnight'])
    tracking_number = factory.Sequence(lambda n: f'TRACK{n:010d}')
    
    # Addresses
    @factory.post_generation
    def billing_address(self, create, extracted, **kwargs):
        """Set billing address"""
        if create:
            self.billing_address = {
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'company': fake.company(),
                'address_line_1': fake.street_address(),
                'address_line_2': fake.secondary_address(),
                'city': fake.city(),
                'state': fake.state(),
                'postal_code': fake.postcode(),
                'country': fake.country_code(),
                'phone': fake.phone_number(),
            }
    
    @factory.post_generation
    def shipping_address(self, create, extracted, **kwargs):
        """Set shipping address"""
        if create:
            # 70% chance same as billing, 30% different
            if random.random() < 0.7:
                self.shipping_address = self.billing_address
            else:
                self.shipping_address = {
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'company': fake.company(),
                    'address_line_1': fake.street_address(),
                    'address_line_2': fake.secondary_address(),
                    'city': fake.city(),
                    'state': fake.state(),
                    'postal_code': fake.postcode(),
                    'country': fake.country_code(),
                    'phone': fake.phone_number(),
                }

class OrderItemFactory(BaseFactory):
    """Factory for OrderItem model"""
    
    class Meta:
        model = 'orders.OrderItem'
    
    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.fuzzy.FuzzyInteger(1, 5)
    price = factory.LazyAttribute(lambda obj: obj.product.price)
    total = factory.LazyAttribute(lambda obj: obj.price * obj.quantity)

class CouponFactory(BaseFactory):
    """Factory for Coupon model"""
    
    class Meta:
        model = 'promotions.Coupon'
        django_get_or_create = ('code',)
    
    code = factory.Sequence(lambda n: f'COUPON{n:04d}')
    name = factory.Faker('catch_phrase')
    description = factory.Faker('text', max_nb_chars=200)
    
    # Discount
    discount_type = factory.fuzzy.FuzzyChoice(['percentage', 'fixed_amount'])
    discount_value = factory.fuzzy.FuzzyDecimal(5.00, 50.00, 2)
    
    # Usage limits
    usage_limit = factory.fuzzy.FuzzyInteger(1, 1000)
    usage_count = 0
    usage_limit_per_customer = factory.fuzzy.FuzzyInteger(1, 10)
    
    # Validity
    valid_from = factory.Faker('date_time_this_month', tzinfo=None)
    valid_until = factory.LazyAttribute(
        lambda obj: obj.valid_from + timedelta(days=random.randint(7, 90))
    )
    
    # Conditions
    minimum_amount = factory.fuzzy.FuzzyDecimal(0.00, 100.00, 2)
    is_active = True

class ReviewFactory(BaseFactory):
    """Factory for Product Review model"""
    
    class Meta:
        model = 'reviews.Review'
    
    product = factory.SubFactory(ProductFactory)
    customer = factory.SubFactory(CustomerFactory)
    rating = factory.fuzzy.FuzzyInteger(1, 5)
    title = factory.Faker('sentence', nb_words=4)
    comment = factory.Faker('text', max_nb_chars=500)
    is_verified_purchase = factory.fuzzy.FuzzyChoice([True, False])
    is_approved = True
    helpful_count = factory.fuzzy.FuzzyInteger(0, 50)

class TestDataManager:
    """Manage test data creation and cleanup"""
    
    def __init__(self):
        self.created_objects = []
        self.factories = {
            'user': UserFactory,
            'admin_user': AdminUserFactory,
            'customer': CustomerFactory,
            'category': CategoryFactory,
            'brand': BrandFactory,
            'product': ProductFactory,
            'order': OrderFactory,
            'order_item': OrderItemFactory,
            'coupon': CouponFactory,
            'review': ReviewFactory,
        }
    
    def create_test_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Create predefined test scenarios"""
        scenarios = {
            'basic_ecommerce': self._create_basic_ecommerce_scenario,
            'large_catalog': self._create_large_catalog_scenario,
            'order_processing': self._create_order_processing_scenario,
            'customer_analytics': self._create_customer_analytics_scenario,
            'inventory_management': self._create_inventory_management_scenario,
            'promotion_testing': self._create_promotion_testing_scenario,
            'performance_testing': self._create_performance_testing_scenario,
        }
        
        if scenario_name not in scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        return scenarios[scenario_name]()
    
    def _create_basic_ecommerce_scenario(self) -> Dict[str, Any]:
        """Create basic e-commerce test data"""
        # Create admin users
        admin = AdminUserFactory.create()
        
        # Create categories
        electronics = CategoryFactory.create(name='Electronics')
        clothing = CategoryFactory.create(name='Clothing')
        books = CategoryFactory.create(name='Books')
        
        # Create brands
        apple = BrandFactory.create(name='Apple')
        nike = BrandFactory.create(name='Nike')
        
        # Create products
        products = []
        products.extend(ProductFactory.create_batch(5, category=electronics, brand=apple))
        products.extend(ProductFactory.create_batch(5, category=clothing, brand=nike))
        products.extend(ProductFactory.create_batch(5, category=books))
        
        # Create customers
        customers = CustomerFactory.create_batch(10)
        
        # Create orders
        orders = []
        for customer in customers[:5]:
            order = OrderFactory.create(customer=customer)
            # Add order items
            selected_products = random.sample(products, random.randint(1, 3))
            for product in selected_products:
                OrderItemFactory.create(order=order, product=product)
            orders.append(order)
        
        # Create reviews
        reviews = []
        for _ in range(20):
            product = random.choice(products)
            customer = random.choice(customers)
            reviews.append(ReviewFactory.create(product=product, customer=customer))
        
        return {
            'admin': admin,
            'categories': [electronics, clothing, books],
            'brands': [apple, nike],
            'products': products,
            'customers': customers,
            'orders': orders,
            'reviews': reviews,
        }
    
    def _create_large_catalog_scenario(self) -> Dict[str, Any]:
        """Create large product catalog for testing"""
        # Create category hierarchy
        root_categories = CategoryFactory.create_batch(10)
        subcategories = []
        for root_cat in root_categories:
            subcategories.extend(
                CategoryFactory.create_batch(5, parent=root_cat)
            )
        
        # Create brands
        brands = BrandFactory.create_batch(20)
        
        # Create large number of products
        products = []
        for _ in range(1000):
            category = random.choice(subcategories)
            brand = random.choice(brands)
            products.append(ProductFactory.create(category=category, brand=brand))
        
        return {
            'root_categories': root_categories,
            'subcategories': subcategories,
            'brands': brands,
            'products': products,
        }
    
    def _create_order_processing_scenario(self) -> Dict[str, Any]:
        """Create order processing test data"""
        customers = CustomerFactory.create_batch(50)
        products = ProductFactory.create_batch(100)
        
        # Create orders in different statuses
        orders = {
            'pending': [],
            'confirmed': [],
            'processing': [],
            'shipped': [],
            'delivered': [],
            'cancelled': [],
        }
        
        for status in orders.keys():
            for _ in range(10):
                customer = random.choice(customers)
                order = OrderFactory.create(customer=customer, status=status)
                
                # Add random items
                selected_products = random.sample(products, random.randint(1, 5))
                for product in selected_products:
                    OrderItemFactory.create(order=order, product=product)
                
                orders[status].append(order)
        
        return {
            'customers': customers,
            'products': products,
            'orders': orders,
        }
    
    def _create_customer_analytics_scenario(self) -> Dict[str, Any]:
        """Create customer analytics test data"""
        # Create customers with different behaviors
        customers = {
            'new': CustomerFactory.create_batch(20),  # New customers
            'regular': CustomerFactory.create_batch(30),  # Regular customers
            'vip': CustomerFactory.create_batch(10),  # VIP customers
        }
        
        products = ProductFactory.create_batch(50)
        
        # Create orders with different patterns
        orders = []
        
        # New customers - 1-2 orders each
        for customer in customers['new']:
            for _ in range(random.randint(1, 2)):
                order = OrderFactory.create(
                    customer=customer,
                    total_amount=Decimal(random.uniform(20, 100))
                )
                orders.append(order)
        
        # Regular customers - 3-10 orders each
        for customer in customers['regular']:
            for _ in range(random.randint(3, 10)):
                order = OrderFactory.create(
                    customer=customer,
                    total_amount=Decimal(random.uniform(50, 300))
                )
                orders.append(order)
        
        # VIP customers - 10+ orders each, higher values
        for customer in customers['vip']:
            for _ in range(random.randint(10, 25)):
                order = OrderFactory.create(
                    customer=customer,
                    total_amount=Decimal(random.uniform(200, 1000))
                )
                orders.append(order)
        
        return {
            'customers': customers,
            'products': products,
            'orders': orders,
        }
    
    def _create_inventory_management_scenario(self) -> Dict[str, Any]:
        """Create inventory management test data"""
        products = []
        
        # Products with different stock levels
        stock_scenarios = [
            ('out_of_stock', 0, 0),
            ('low_stock', 1, 5),
            ('normal_stock', 20, 100),
            ('high_stock', 500, 1000),
        ]
        
        for scenario_name, min_stock, max_stock in stock_scenarios:
            for _ in range(25):
                product = ProductFactory.create(
                    stock_quantity=random.randint(min_stock, max_stock),
                    low_stock_threshold=random.randint(5, 20)
                )
                products.append(product)
        
        return {
            'products': products,
            'stock_scenarios': stock_scenarios,
        }
    
    def _create_promotion_testing_scenario(self) -> Dict[str, Any]:
        """Create promotion testing data"""
        products = ProductFactory.create_batch(50)
        customers = CustomerFactory.create_batch(30)
        
        # Create different types of coupons
        coupons = []
        
        # Percentage discounts
        for _ in range(10):
            coupons.append(CouponFactory.create(
                discount_type='percentage',
                discount_value=Decimal(random.uniform(5, 50))
            ))
        
        # Fixed amount discounts
        for _ in range(10):
            coupons.append(CouponFactory.create(
                discount_type='fixed_amount',
                discount_value=Decimal(random.uniform(5, 100))
            ))
        
        # Expired coupons
        for _ in range(5):
            coupons.append(CouponFactory.create(
                valid_until=datetime.now() - timedelta(days=random.randint(1, 30))
            ))
        
        return {
            'products': products,
            'customers': customers,
            'coupons': coupons,
        }
    
    def _create_performance_testing_scenario(self) -> Dict[str, Any]:
        """Create large dataset for performance testing"""
        # Create large numbers of each entity
        categories = CategoryFactory.create_batch(100)
        brands = BrandFactory.create_batch(50)
        products = ProductFactory.create_batch(5000)
        customers = CustomerFactory.create_batch(1000)
        
        # Create many orders
        orders = []
        for _ in range(2000):
            customer = random.choice(customers)
            order = OrderFactory.create(customer=customer)
            
            # Add multiple items per order
            selected_products = random.sample(products, random.randint(1, 10))
            for product in selected_products:
                OrderItemFactory.create(order=order, product=product)
            
            orders.append(order)
        
        return {
            'categories': categories,
            'brands': brands,
            'products': products,
            'customers': customers,
            'orders': orders,
        }
    
    def cleanup_test_data(self):
        """Clean up all created test data"""
        # This would implement cleanup logic
        # For now, we rely on Django's test database isolation
        pass
    
    def create_custom_data(self, factory_name: str, count: int, **kwargs) -> List:
        """Create custom test data using specified factory"""
        if factory_name not in self.factories:
            raise ValueError(f"Unknown factory: {factory_name}")
        
        factory_class = self.factories[factory_name]
        return factory_class.create_batch(count, **kwargs)
    
    def export_test_data(self, file_path: str, data: Dict[str, Any]):
        """Export test data to JSON file"""
        serializable_data = {}
        
        for key, value in data.items():
            if isinstance(value, list):
                serializable_data[key] = [
                    self._serialize_object(obj) for obj in value
                ]
            else:
                serializable_data[key] = self._serialize_object(value)
        
        with open(file_path, 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)
    
    def _serialize_object(self, obj) -> Dict:
        """Serialize Django model object to dict"""
        if hasattr(obj, '_meta'):
            # Django model object
            data = {}
            for field in obj._meta.fields:
                value = getattr(obj, field.name)
                if hasattr(value, 'pk'):
                    data[field.name] = value.pk
                else:
                    data[field.name] = value
            return data
        else:
            return obj