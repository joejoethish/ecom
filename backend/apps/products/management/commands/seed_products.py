"""
Management command to seed product data for development and testing.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.products.models import Category, Product, ProductImage


class Command(BaseCommand):
    help = 'Seed product data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing product data...')
            ProductImage.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        self.stdout.write('Seeding product data...')
        
        # Create categories
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Electronic devices and gadgets',
                'children': [
                    {
                        'name': 'Smartphones',
                        'description': 'Mobile phones and smartphones',
                        'children': [
                            {'name': 'Android Phones', 'description': 'Android-based smartphones'},
                            {'name': 'iPhones', 'description': 'Apple iPhones'},
                        ]
                    },
                    {
                        'name': 'Laptops',
                        'description': 'Laptops and notebooks',
                        'children': [
                            {'name': 'Gaming Laptops', 'description': 'High-performance gaming laptops'},
                            {'name': 'Business Laptops', 'description': 'Professional business laptops'},
                        ]
                    },
                    {
                        'name': 'Tablets',
                        'description': 'Tablets and e-readers'
                    },
                    {
                        'name': 'Audio',
                        'description': 'Headphones, speakers, and audio equipment',
                        'children': [
                            {'name': 'Headphones', 'description': 'Over-ear and on-ear headphones'},
                            {'name': 'Earbuds', 'description': 'In-ear headphones and earbuds'},
                            {'name': 'Speakers', 'description': 'Bluetooth and wired speakers'},
                        ]
                    }
                ]
            },
            {
                'name': 'Fashion',
                'description': 'Clothing, shoes, and accessories',
                'children': [
                    {
                        'name': 'Men\'s Clothing',
                        'description': 'Men\'s fashion and apparel',
                        'children': [
                            {'name': 'Shirts', 'description': 'Casual and formal shirts'},
                            {'name': 'T-Shirts', 'description': 'Casual t-shirts and polos'},
                            {'name': 'Jeans', 'description': 'Denim jeans and pants'},
                        ]
                    },
                    {
                        'name': 'Women\'s Clothing',
                        'description': 'Women\'s fashion and apparel',
                        'children': [
                            {'name': 'Dresses', 'description': 'Casual and formal dresses'},
                            {'name': 'Tops', 'description': 'Blouses, shirts, and tops'},
                            {'name': 'Jeans', 'description': 'Women\'s denim and pants'},
                        ]
                    },
                    {
                        'name': 'Shoes',
                        'description': 'Footwear for men and women',
                        'children': [
                            {'name': 'Sneakers', 'description': 'Casual and athletic sneakers'},
                            {'name': 'Formal Shoes', 'description': 'Dress shoes and formal footwear'},
                            {'name': 'Sandals', 'description': 'Casual sandals and flip-flops'},
                        ]
                    }
                ]
            },
            {
                'name': 'Home & Kitchen',
                'description': 'Home appliances and kitchen essentials',
                'children': [
                    {
                        'name': 'Kitchen Appliances',
                        'description': 'Small and large kitchen appliances'
                    },
                    {
                        'name': 'Home Decor',
                        'description': 'Decorative items and furniture'
                    },
                    {
                        'name': 'Bedding',
                        'description': 'Bed sheets, pillows, and comforters'
                    }
                ]
            },
            {
                'name': 'Books',
                'description': 'Books, e-books, and educational materials',
                'children': [
                    {'name': 'Fiction', 'description': 'Novels and fictional literature'},
                    {'name': 'Non-Fiction', 'description': 'Educational and informational books'},
                    {'name': 'Textbooks', 'description': 'Academic and educational textbooks'},
                ]
            },
            {
                'name': 'Sports & Fitness',
                'description': 'Sports equipment and fitness gear',
                'children': [
                    {'name': 'Fitness Equipment', 'description': 'Home gym and fitness equipment'},
                    {'name': 'Sports Gear', 'description': 'Equipment for various sports'},
                    {'name': 'Activewear', 'description': 'Athletic clothing and accessories'},
                ]
            }
        ]

        created_categories = {}
        
        def create_category(cat_data, parent=None):
            # Check if category already exists to avoid duplicates
            category_name = cat_data['name']
            if category_name in created_categories:
                return created_categories[category_name]
            
            category = Category.objects.create(
                name=category_name,
                description=cat_data.get('description', ''),
                parent=parent,
                is_active=True
            )
            created_categories[category_name] = category
            
            if 'children' in cat_data:
                for child_data in cat_data['children']:
                    create_category(child_data, category)
            
            return category

        for category_data in categories_data:
            create_category(category_data)

        self.stdout.write(f'Created {len(created_categories)} categories.')

        # Create products
        products_data = [
            # Electronics - Smartphones
            {
                'name': 'iPhone 15 Pro',
                'description': 'The most advanced iPhone yet with titanium design, A17 Pro chip, and professional camera system.',
                'short_description': 'Latest iPhone with titanium design and A17 Pro chip',
                'category': 'iPhones',
                'brand': 'Apple',
                'sku': 'IPHONE15PRO-128',
                'price': Decimal('999.99'),
                'discount_price': Decimal('949.99'),
                'weight': Decimal('0.187'),
                'dimensions': {'length': 14.67, 'width': 7.09, 'height': 0.83},
                'tags': 'smartphone, apple, ios, premium, camera',
                'status': 'active',
                'is_featured': True
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'description': 'Premium Android smartphone with S Pen, advanced AI features, and exceptional camera capabilities.',
                'short_description': 'Premium Galaxy with S Pen and AI features',
                'category': 'Android Phones',
                'brand': 'Samsung',
                'sku': 'GALAXY-S24-ULTRA-256',
                'price': Decimal('1199.99'),
                'discount_price': Decimal('1099.99'),
                'weight': Decimal('0.232'),
                'dimensions': {'length': 16.24, 'width': 7.90, 'height': 0.86},
                'tags': 'smartphone, samsung, android, s-pen, camera',
                'status': 'active',
                'is_featured': True
            },
            {
                'name': 'Google Pixel 8',
                'description': 'Google\'s flagship smartphone with advanced AI photography and pure Android experience.',
                'short_description': 'Google flagship with AI photography',
                'category': 'Android Phones',
                'brand': 'Google',
                'sku': 'PIXEL8-128GB',
                'price': Decimal('699.99'),
                'weight': Decimal('0.187'),
                'dimensions': {'length': 15.05, 'width': 7.06, 'height': 0.89},
                'tags': 'smartphone, google, android, ai, photography',
                'status': 'active'
            },

            # Electronics - Laptops
            {
                'name': 'MacBook Pro 16-inch M3',
                'description': 'Powerful laptop with M3 chip, stunning Liquid Retina XDR display, and all-day battery life.',
                'short_description': 'MacBook Pro with M3 chip and 16-inch display',
                'category': 'Business Laptops',
                'brand': 'Apple',
                'sku': 'MBP16-M3-512',
                'price': Decimal('2499.99'),
                'discount_price': Decimal('2299.99'),
                'weight': Decimal('2.16'),
                'dimensions': {'length': 35.57, 'width': 24.81, 'height': 1.68},
                'tags': 'laptop, apple, macbook, m3, professional',
                'status': 'active',
                'is_featured': True
            },
            {
                'name': 'ASUS ROG Strix G16',
                'description': 'High-performance gaming laptop with RTX 4070, Intel i7, and 165Hz display.',
                'short_description': 'Gaming laptop with RTX 4070 and 165Hz display',
                'category': 'Gaming Laptops',
                'brand': 'ASUS',
                'sku': 'ROG-STRIX-G16-RTX4070',
                'price': Decimal('1799.99'),
                'discount_price': Decimal('1599.99'),
                'weight': Decimal('2.5'),
                'dimensions': {'length': 35.4, 'width': 25.2, 'height': 2.29},
                'tags': 'laptop, gaming, asus, rtx, intel',
                'status': 'active'
            },

            # Electronics - Audio
            {
                'name': 'Sony WH-1000XM5',
                'description': 'Industry-leading noise canceling headphones with exceptional sound quality and 30-hour battery.',
                'short_description': 'Premium noise-canceling headphones',
                'category': 'Headphones',
                'brand': 'Sony',
                'sku': 'WH1000XM5-BLACK',
                'price': Decimal('399.99'),
                'discount_price': Decimal('349.99'),
                'weight': Decimal('0.25'),
                'tags': 'headphones, sony, noise-canceling, wireless',
                'status': 'active',
                'is_featured': True
            },
            {
                'name': 'AirPods Pro (2nd generation)',
                'description': 'Apple\'s premium wireless earbuds with active noise cancellation and spatial audio.',
                'short_description': 'Premium wireless earbuds with ANC',
                'category': 'Earbuds',
                'brand': 'Apple',
                'sku': 'AIRPODS-PRO-2ND',
                'price': Decimal('249.99'),
                'weight': Decimal('0.056'),
                'tags': 'earbuds, apple, wireless, noise-canceling',
                'status': 'active'
            },

            # Fashion - Men's Clothing
            {
                'name': 'Levi\'s 501 Original Jeans',
                'description': 'Classic straight-leg jeans with authentic fit and timeless style.',
                'short_description': 'Classic straight-leg denim jeans',
                'category': 'Jeans',
                'brand': 'Levi\'s',
                'sku': 'LEVIS-501-32X32',
                'price': Decimal('89.99'),
                'discount_price': Decimal('69.99'),
                'weight': Decimal('0.6'),
                'tags': 'jeans, levis, denim, classic, mens',
                'status': 'active'
            },
            {
                'name': 'Nike Dri-FIT T-Shirt',
                'description': 'Comfortable athletic t-shirt with moisture-wicking technology.',
                'short_description': 'Athletic t-shirt with Dri-FIT technology',
                'category': 'T-Shirts',
                'brand': 'Nike',
                'sku': 'NIKE-DRIFIT-TEE-L',
                'price': Decimal('29.99'),
                'weight': Decimal('0.15'),
                'tags': 'tshirt, nike, athletic, dri-fit, mens',
                'status': 'active'
            },

            # Fashion - Shoes
            {
                'name': 'Nike Air Max 270',
                'description': 'Lifestyle sneakers with large Air unit and comfortable cushioning.',
                'short_description': 'Lifestyle sneakers with Air Max cushioning',
                'category': 'Sneakers',
                'brand': 'Nike',
                'sku': 'AIRMAX270-10',
                'price': Decimal('149.99'),
                'discount_price': Decimal('119.99'),
                'weight': Decimal('0.4'),
                'tags': 'sneakers, nike, air-max, lifestyle, comfort',
                'status': 'active'
            },
            {
                'name': 'Adidas Ultraboost 22',
                'description': 'Premium running shoes with responsive Boost cushioning and Primeknit upper.',
                'short_description': 'Premium running shoes with Boost technology',
                'category': 'Sneakers',
                'brand': 'Adidas',
                'sku': 'ULTRABOOST22-10',
                'price': Decimal('189.99'),
                'weight': Decimal('0.35'),
                'tags': 'sneakers, adidas, running, boost, primeknit',
                'status': 'active'
            },

            # Home & Kitchen
            {
                'name': 'Instant Pot Duo 7-in-1',
                'description': 'Multi-functional electric pressure cooker that replaces 7 kitchen appliances.',
                'short_description': '7-in-1 electric pressure cooker',
                'category': 'Kitchen Appliances',
                'brand': 'Instant Pot',
                'sku': 'INSTANTPOT-DUO-6QT',
                'price': Decimal('99.99'),
                'discount_price': Decimal('79.99'),
                'weight': Decimal('5.4'),
                'dimensions': {'length': 32.5, 'width': 31.5, 'height': 32.5},
                'tags': 'kitchen, pressure-cooker, instant-pot, appliance',
                'status': 'active'
            },

            # Books
            {
                'name': 'The Psychology of Money',
                'description': 'Timeless lessons on wealth, greed, and happiness by Morgan Housel.',
                'short_description': 'Bestselling book on financial psychology',
                'category': 'Non-Fiction',
                'brand': 'Harriman House',
                'sku': 'PSYCH-MONEY-PB',
                'price': Decimal('16.99'),
                'weight': Decimal('0.3'),
                'tags': 'book, finance, psychology, bestseller',
                'status': 'active'
            },

            # Sports & Fitness
            {
                'name': 'Resistance Bands Set',
                'description': 'Complete set of resistance bands for home workouts and strength training.',
                'short_description': 'Complete resistance bands workout set',
                'category': 'Fitness Equipment',
                'brand': 'FitBeast',
                'sku': 'RESISTANCE-BANDS-SET',
                'price': Decimal('29.99'),
                'discount_price': Decimal('24.99'),
                'weight': Decimal('1.2'),
                'tags': 'fitness, resistance-bands, home-workout, strength',
                'status': 'active'
            }
        ]

        created_products = []
        for product_data in products_data:
            category = created_categories.get(product_data['category'])
            if not category:
                self.stdout.write(
                    self.style.WARNING(f'Category "{product_data["category"]}" not found for product "{product_data["name"]}"')
                )
                continue

            product = Product.objects.create(
                name=product_data['name'],
                description=product_data['description'],
                short_description=product_data['short_description'],
                category=category,
                brand=product_data['brand'],
                sku=product_data['sku'],
                price=product_data['price'],
                discount_price=product_data.get('discount_price'),
                weight=product_data.get('weight'),
                dimensions=product_data.get('dimensions', {}),
                tags=product_data.get('tags', ''),
                status=product_data.get('status', 'draft'),
                is_featured=product_data.get('is_featured', False),
                is_active=True
            )
            created_products.append(product)

        self.stdout.write(f'Created {len(created_products)} products.')

        # Create sample product images (placeholder images)
        sample_images = [
            {'product_name': 'iPhone 15 Pro', 'images': ['iphone15pro_1.jpg', 'iphone15pro_2.jpg', 'iphone15pro_3.jpg']},
            {'product_name': 'Samsung Galaxy S24 Ultra', 'images': ['galaxy_s24_1.jpg', 'galaxy_s24_2.jpg']},
            {'product_name': 'MacBook Pro 16-inch M3', 'images': ['macbook_pro_1.jpg', 'macbook_pro_2.jpg']},
            {'product_name': 'Sony WH-1000XM5', 'images': ['sony_headphones_1.jpg', 'sony_headphones_2.jpg']},
            {'product_name': 'Nike Air Max 270', 'images': ['nike_airmax_1.jpg', 'nike_airmax_2.jpg']},
        ]

        created_images = 0
        for image_data in sample_images:
            try:
                product = Product.objects.get(name=image_data['product_name'])
                for i, image_name in enumerate(image_data['images']):
                    ProductImage.objects.create(
                        product=product,
                        image=f'products/{image_name}',
                        alt_text=f'{product.name} - Image {i+1}',
                        is_primary=(i == 0),  # First image is primary
                        sort_order=i + 1
                    )
                    created_images += 1
            except Product.DoesNotExist:
                continue

        self.stdout.write(f'Created {created_images} product images.')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded:\n'
                f'- {len(created_categories)} categories\n'
                f'- {len(created_products)} products\n'
                f'- {created_images} product images'
            )
        )