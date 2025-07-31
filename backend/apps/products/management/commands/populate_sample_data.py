"""
Management command to populate the database with sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product, ProductImage
from apps.reviews.models import Review
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        self.create_categories()
        
        # Create users
        self.create_users()
        
        # Create products
        self.create_products()
        
        # Create reviews
        self.create_reviews()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data')
        )

    def create_categories(self):
        """Create sample categories"""
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Electronic devices and gadgets',
                'icon': '💻',
                'href': '/category/electronics'
            },
            {
                'name': 'Fashion',
                'description': 'Clothing and accessories',
                'icon': '👗',
                'href': '/category/fashion'
            },
            {
                'name': 'Home & Kitchen',
                'description': 'Home appliances and kitchen items',
                'icon': '🏠',
                'href': '/category/home-kitchen'
            },
            {
                'name': 'Books',
                'description': 'Books and educational materials',
                'icon': '📚',
                'href': '/category/books'
            },
            {
                'name': 'Sports',
                'description': 'Sports equipment and accessories',
                'icon': '⚽',
                'href': '/category/sports'
            },
            {
                'name': 'Beauty',
                'description': 'Beauty and personal care products',
                'icon': '💄',
                'href': '/category/beauty'
            }
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_users(self):
        """Create sample users"""
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'user_type': 'admin'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user')

        # Create sample customers
        customers_data = [
            {'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Johnson'},
        ]
        
        for customer_data in customers_data:
            user, created = User.objects.get_or_create(
                email=customer_data['email'],
                defaults={
                    'username': customer_data['email'].split('@')[0],
                    'first_name': customer_data['first_name'],
                    'last_name': customer_data['last_name'],
                    'user_type': 'customer'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created customer: {user.email}')

    def create_products(self):
        """Create sample products"""
        categories = Category.objects.all()
        
        products_data = [
            {
                'name': 'iPhone 15 Pro',
                'description': 'Latest iPhone with advanced features',
                'price': Decimal('999.99'),
                'discount_price': Decimal('899.99'),
                'category': 'Electronics',
                'brand': 'Apple',
                'sku': 'IPHONE15PRO'
            },
            {
                'name': 'Samsung Galaxy S24',
                'description': 'Premium Android smartphone',
                'price': Decimal('849.99'),
                'category': 'Electronics',
                'brand': 'Samsung',
                'sku': 'GALAXYS24'
            },
            {
                'name': 'MacBook Air M3',
                'description': 'Lightweight laptop with M3 chip',
                'price': Decimal('1299.99'),
                'category': 'Electronics',
                'brand': 'Apple',
                'sku': 'MACBOOKAIRM3'
            },
            {
                'name': 'Nike Air Max 270',
                'description': 'Comfortable running shoes',
                'price': Decimal('150.00'),
                'discount_price': Decimal('120.00'),
                'category': 'Fashion',
                'brand': 'Nike',
                'sku': 'AIRMAX270'
            },
            {
                'name': 'Instant Pot Duo 7-in-1',
                'description': 'Multi-use pressure cooker',
                'price': Decimal('99.99'),
                'category': 'Home & Kitchen',
                'brand': 'Instant Pot',
                'sku': 'INSTANTPOT7IN1'
            },
            {
                'name': 'The Great Gatsby',
                'description': 'Classic American novel',
                'price': Decimal('12.99'),
                'category': 'Books',
                'brand': 'Penguin Classics',
                'sku': 'GREATGATSBY'
            }
        ]
        
        for product_data in products_data:
            try:
                category = Category.objects.get(name=product_data['category'])
                product, created = Product.objects.get_or_create(
                    sku=product_data['sku'],
                    defaults={
                        'name': product_data['name'],
                        'description': product_data['description'],
                        'price': product_data['price'],
                        'discount_price': product_data.get('discount_price'),
                        'category': category,
                        'brand': product_data['brand'],
                        'is_active': True,
                        'status': 'active'
                    }
                )
                if created:
                    self.stdout.write(f'Created product: {product.name}')
            except Category.DoesNotExist:
                self.stdout.write(f'Category {product_data["category"]} not found')

    def create_reviews(self):
        """Create sample reviews"""
        products = Product.objects.all()
        customers = User.objects.filter(user_type='customer')
        
        review_texts = [
            "Great product! Highly recommended.",
            "Good quality for the price.",
            "Excellent service and fast delivery.",
            "Product as described. Very satisfied.",
            "Could be better, but overall okay.",
            "Amazing quality! Will buy again.",
            "Fast shipping and great packaging.",
            "Exactly what I was looking for.",
        ]
        
        for product in products:
            # Create 2-5 reviews per product
            num_reviews = random.randint(2, 5)
            for _ in range(num_reviews):
                customer = random.choice(customers)
                rating = random.randint(3, 5)  # Mostly positive reviews
                review_text = random.choice(review_texts)
                
                review, created = Review.objects.get_or_create(
                    product=product,
                    user=customer,
                    defaults={
                        'rating': rating,
                        'title': f'Review for {product.name}',
                        'comment': review_text,
                        'is_verified_purchase': random.choice([True, False]),
                        'status': 'approved'
                    }
                )
                if created:
                    self.stdout.write(f'Created review for {product.name}')