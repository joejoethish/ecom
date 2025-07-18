"""
Tests for product serializers.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.products.models import Category, Product, ProductImage
from apps.products.serializers import (
    CategorySerializer, CategoryListSerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateUpdateSerializer, ProductImageSerializer
)

User = get_user_model()


class ProductSerializerTestCase(TestCase):
    """Base test case for product serializer tests."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        
        # Create categories
        self.parent_category = Category.objects.create(
            name='Electronics',
            description='Electronic products',
            is_active=True
        )
        self.child_category = Category.objects.create(
            name='Smartphones',
            description='Mobile phones and smartphones',
            parent=self.parent_category,
            is_active=True
        )

        # Create products
        self.product = Product.objects.create(
            name='iPhone 15',
            description='Latest iPhone model with advanced features',
            short_description='Apple\'s newest smartphone',
            category=self.child_category,
            brand='Apple',
            sku='IPHONE15-001',
            price=Decimal('999.99'),
            discount_price=Decimal('899.99'),
            weight=Decimal('0.2'),
            dimensions={'length': 15, 'width': 7, 'height': 0.8},
            is_active=True,
            is_featured=True,
            status='active',
            tags='smartphone, apple, ios, mobile',
            meta_title='iPhone 15 - Latest Apple Smartphone',
            meta_description='Buy the latest iPhone 15 with advanced features'
        )

        # Create product images
        self.primary_image = ProductImage.objects.create(
            product=self.product,
            image='products/iphone15-main.jpg',
            alt_text='iPhone 15 main image',
            is_primary=True,
            sort_order=1
        )
        self.secondary_image = ProductImage.objects.create(
            product=self.product,
            image='products/iphone15-back.jpg',
            alt_text='iPhone 15 back view',
            is_primary=False,
            sort_order=2
        )


class CategorySerializerTest(ProductSerializerTestCase):
    """Test cases for Category serializers."""

    def test_category_serializer_basic_fields(self):
        """Test basic category serializer fields."""
        serializer = CategorySerializer(self.parent_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Electronics')
        self.assertEqual(data['slug'], 'electronics')
        self.assertEqual(data['description'], 'Electronic products')
        self.assertTrue(data['is_active'])
        self.assertIsNone(data['parent'])
        self.assertIsNone(data['parent_name'])
        self.assertEqual(data['full_name'], 'Electronics')

    def test_category_serializer_with_parent(self):
        """Test category serializer with parent relationship."""
        serializer = CategorySerializer(self.child_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Smartphones')
        self.assertEqual(data['parent'], str(self.parent_category.id))
        self.assertEqual(data['parent_name'], 'Electronics')
        self.assertEqual(data['full_name'], 'Electronics > Smartphones')

    def test_category_serializer_children(self):
        """Test category serializer children field."""
        serializer = CategorySerializer(self.parent_category)
        data = serializer.data
        
        self.assertIn('children', data)
        self.assertEqual(len(data['children']), 1)
        self.assertEqual(data['children'][0]['name'], 'Smartphones')

    def test_category_serializer_products_count(self):
        """Test category serializer products_count field."""
        serializer = CategorySerializer(self.child_category)
        data = serializer.data
        
        self.assertIn('products_count', data)
        self.assertEqual(data['products_count'], 1)  # One product in child category

    def test_category_list_serializer(self):
        """Test CategoryListSerializer (without nested children)."""
        serializer = CategoryListSerializer(self.parent_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Electronics')
        self.assertNotIn('children', data)  # Should not include children
        self.assertIn('products_count', data)

    def test_category_serializer_inactive_children(self):
        """Test that inactive children are not included."""
        # Create inactive child category
        inactive_child = Category.objects.create(
            name='Inactive Child',
            parent=self.parent_category,
            is_active=False
        )
        
        serializer = CategorySerializer(self.parent_category)
        data = serializer.data
        
        # Should only include active children
        child_names = [child['name'] for child in data['children']]
        self.assertIn('Smartphones', child_names)
        self.assertNotIn('Inactive Child', child_names)


class ProductImageSerializerTest(ProductSerializerTestCase):
    """Test cases for ProductImage serializer."""

    def test_product_image_serializer(self):
        """Test ProductImage serializer."""
        serializer = ProductImageSerializer(self.primary_image)
        data = serializer.data
        
        self.assertEqual(data['image'], 'products/iphone15-main.jpg')
        self.assertEqual(data['alt_text'], 'iPhone 15 main image')
        self.assertTrue(data['is_primary'])
        self.assertEqual(data['sort_order'], 1)


class ProductListSerializerTest(ProductSerializerTestCase):
    """Test cases for ProductListSerializer."""

    def test_product_list_serializer_basic_fields(self):
        """Test basic fields in product list serializer."""
        request = self.factory.get('/')
        serializer = ProductListSerializer(self.product, context={'request': request})
        data = serializer.data
        
        self.assertEqual(data['name'], 'iPhone 15')
        self.assertEqual(data['slug'], 'iphone-15')
        self.assertEqual(data['short_description'], 'Apple\'s newest smartphone')
        self.assertEqual(data['brand'], 'Apple')
        self.assertEqual(data['sku'], 'IPHONE15-001')
        self.assertEqual(float(data['price']), 999.99)
        self.assertEqual(float(data['discount_price']), 899.99)
        self.assertEqual(float(data['effective_price']), 899.99)
        self.assertTrue(data['is_featured'])
        self.assertEqual(data['status'], 'active')

    def test_product_list_serializer_category(self):
        """Test category field in product list serializer."""
        request = self.factory.get('/')
        serializer = ProductListSerializer(self.product, context={'request': request})
        data = serializer.data
        
        self.assertIn('category', data)
        self.assertEqual(data['category']['name'], 'Smartphones')
        self.assertEqual(data['category']['parent_name'], 'Electronics')

    def test_product_list_serializer_primary_image(self):
        """Test primary_image field in product list serializer."""
        request = self.factory.get('/')
        serializer = ProductListSerializer(self.product, context={'request': request})
        data = serializer.data
        
        self.assertIn('primary_image', data)
        self.assertIsNotNone(data['primary_image'])
        self.assertEqual(data['primary_image']['image'], 'products/iphone15-main.jpg')
        self.assertTrue(data['primary_image']['is_primary'])

    def test_product_list_serializer_tags_list(self):
        """Test tags_list field in product list serializer."""
        request = self.factory.get('/')
        serializer = ProductListSerializer(self.product, context={'request': request})
        data = serializer.data
        
        self.assertIn('tags_list', data)
        expected_tags = ['smartphone', 'apple', 'ios', 'mobile']
        self.assertEqual(data['tags_list'], expected_tags)

    def test_product_list_serializer_discount_percentage(self):
        """Test discount_percentage calculation."""
        request = self.factory.get('/')
        serializer = ProductListSerializer(self.product, context={'request': request})
        data = serializer.data
        
        expected_discount = round(((999.99 - 899.99) / 999.99) * 100, 2)
        self.assertEqual(float(data['discount_percentage']), expected_discount)

    def test_product_list_serializer_no_primary_image(self):
        """Test product list serializer when no primary image exists."""
        # Remove primary image
        self.primary_image.delete()
        
        request = self.factory.get('/')
        serializer = ProductListSerializer(self.product, context={'request': request})
        data = serializer.data
        
        self.assertIsNone(data['primary_image'])


class ProductDetailSerializerTest(ProductSerializerTestCase):
    """Test cases for ProductDetailSerializer."""

    def test_product_detail_serializer_all_fields(self):
        """Test all fields in product detail serializer."""
        request = self.factory.get('/')
        serializer = ProductDetailSerializer(self.product, context={'request': request})
        data = serializer.data
        
        # Basic fields
        self.assertEqual(data['name'], 'iPhone 15')
        self.assertEqual(data['slug'], 'iphone-15')
        self.assertEqual(data['description'], 'Latest iPhone model with advanced features')
        self.assertEqual(data['short_description'], 'Apple\'s newest smartphone')
        self.assertEqual(data['brand'], 'Apple')
        self.assertEqual(data['sku'], 'IPHONE15-001')
        
        # Price fields
        self.assertEqual(float(data['price']), 999.99)
        self.assertEqual(float(data['discount_price']), 899.99)
        self.assertEqual(float(data['effective_price']), 899.99)
        
        # Physical attributes
        self.assertEqual(float(data['weight']), 0.2)
        self.assertEqual(data['dimensions'], {'length': 15, 'width': 7, 'height': 0.8})
        
        # Status fields
        self.assertTrue(data['is_active'])
        self.assertTrue(data['is_featured'])
        self.assertEqual(data['status'], 'active')
        
        # SEO fields
        self.assertEqual(data['meta_title'], 'iPhone 15 - Latest Apple Smartphone')
        self.assertEqual(data['meta_description'], 'Buy the latest iPhone 15 with advanced features')
        
        # Tags
        self.assertEqual(data['tags'], 'smartphone, apple, ios, mobile')
        self.assertEqual(data['tags_list'], ['smartphone', 'apple', 'ios', 'mobile'])

    def test_product_detail_serializer_category(self):
        """Test category field in product detail serializer."""
        request = self.factory.get('/')
        serializer = ProductDetailSerializer(self.product, context={'request': request})
        data = serializer.data
        
        self.assertIn('category', data)
        category_data = data['category']
        self.assertEqual(category_data['name'], 'Smartphones')
        self.assertEqual(category_data['parent_name'], 'Electronics')
        self.assertEqual(category_data['full_name'], 'Electronics > Smartphones')

    def test_product_detail_serializer_images(self):
        """Test images field in product detail serializer."""
        request = self.factory.get('/')
        serializer = ProductDetailSerializer(self.product, context={'request': request})
        data = serializer.data
        
        self.assertIn('images', data)
        self.assertEqual(len(data['images']), 2)
        
        # Check images are ordered correctly
        images = data['images']
        self.assertEqual(images[0]['sort_order'], 1)
        self.assertEqual(images[1]['sort_order'], 2)
        
        # Check primary image
        primary_images = [img for img in images if img['is_primary']]
        self.assertEqual(len(primary_images), 1)
        self.assertEqual(primary_images[0]['image'], 'products/iphone15-main.jpg')

    def test_product_detail_serializer_primary_image(self):
        """Test primary_image field in product detail serializer."""
        request = self.factory.get('/')
        serializer = ProductDetailSerializer(self.product, context={'request': request})
        data = serializer.data
        
        self.assertIn('primary_image', data)
        primary_image = data['primary_image']
        self.assertEqual(primary_image['image'], 'products/iphone15-main.jpg')
        self.assertTrue(primary_image['is_primary'])


class ProductCreateUpdateSerializerTest(ProductSerializerTestCase):
    """Test cases for ProductCreateUpdateSerializer."""

    def test_product_create_serializer_valid_data(self):
        """Test creating a product with valid data."""
        data = {
            'name': 'New Test Product',
            'description': 'A new product for testing',
            'short_description': 'Test product',
            'category_id': str(self.child_category.id),
            'brand': 'TestBrand',
            'sku': 'TEST-001',
            'price': '199.99',
            'discount_price': '179.99',
            'weight': '0.5',
            'dimensions': {'length': 10, 'width': 5, 'height': 2},
            'is_active': True,
            'is_featured': False,
            'status': 'active',
            'tags': 'test, new, product',
            'meta_title': 'Test Product',
            'meta_description': 'A test product for testing'
        }
        
        serializer = ProductCreateUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        product = serializer.save()
        self.assertEqual(product.name, 'New Test Product')
        self.assertEqual(product.category, self.child_category)
        self.assertEqual(product.sku, 'TEST-001')
        self.assertEqual(product.price, Decimal('199.99'))
        self.assertEqual(product.discount_price, Decimal('179.99'))

    def test_product_create_serializer_with_images(self):
        """Test creating a product with images."""
        data = {
            'name': 'Product with Images',
            'description': 'A product with multiple images',
            'category_id': str(self.child_category.id),
            'sku': 'IMG-001',
            'price': '299.99',
            'images_data': [
                {
                    'image': 'products/test1.jpg',
                    'alt_text': 'Test image 1',
                    'is_primary': True,
                    'sort_order': 1
                },
                {
                    'image': 'products/test2.jpg',
                    'alt_text': 'Test image 2',
                    'is_primary': False,
                    'sort_order': 2
                }
            ]
        }
        
        serializer = ProductCreateUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        product = serializer.save()
        self.assertEqual(product.images.count(), 2)
        
        primary_image = product.images.filter(is_primary=True).first()
        self.assertIsNotNone(primary_image)
        self.assertEqual(primary_image.alt_text, 'Test image 1')

    def test_product_create_serializer_invalid_category(self):
        """Test creating a product with invalid category."""
        data = {
            'name': 'Invalid Category Product',
            'category_id': '00000000-0000-0000-0000-000000000000',  # Non-existent UUID
            'sku': 'INVALID-001',
            'price': '99.99'
        }
        
        serializer = ProductCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('category_id', serializer.errors)

    def test_product_create_serializer_duplicate_sku(self):
        """Test creating a product with duplicate SKU."""
        data = {
            'name': 'Duplicate SKU Product',
            'category_id': str(self.child_category.id),
            'sku': 'IPHONE15-001',  # Same as existing product
            'price': '99.99'
        }
        
        serializer = ProductCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('sku', serializer.errors)

    def test_product_create_serializer_invalid_discount_price(self):
        """Test creating a product with invalid discount price."""
        data = {
            'name': 'Invalid Discount Product',
            'category_id': str(self.child_category.id),
            'sku': 'INVALID-DISCOUNT-001',
            'price': '100.00',
            'discount_price': '150.00'  # Higher than regular price
        }
        
        serializer = ProductCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('discount_price', serializer.errors)

    def test_product_update_serializer(self):
        """Test updating a product."""
        data = {
            'name': 'Updated iPhone 15',
            'price': '1099.99',
            'discount_price': '999.99',
            'is_featured': False
        }
        
        serializer = ProductCreateUpdateSerializer(
            instance=self.product,
            data=data,
            partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        updated_product = serializer.save()
        self.assertEqual(updated_product.name, 'Updated iPhone 15')
        self.assertEqual(updated_product.price, Decimal('1099.99'))
        self.assertEqual(updated_product.discount_price, Decimal('999.99'))
        self.assertFalse(updated_product.is_featured)

    def test_product_update_serializer_with_images(self):
        """Test updating a product with new images."""
        data = {
            'name': 'Updated Product with New Images',
            'images_data': [
                {
                    'image': 'products/new1.jpg',
                    'alt_text': 'New image 1',
                    'is_primary': True,
                    'sort_order': 1
                }
            ]
        }
        
        # Product initially has 2 images
        self.assertEqual(self.product.images.count(), 2)
        
        serializer = ProductCreateUpdateSerializer(
            instance=self.product,
            data=data,
            partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        updated_product = serializer.save()
        
        # Should now have only 1 image (old ones deleted)
        self.assertEqual(updated_product.images.count(), 1)
        
        new_image = updated_product.images.first()
        self.assertEqual(new_image.alt_text, 'New image 1')
        self.assertTrue(new_image.is_primary)

    def test_product_create_serializer_to_representation(self):
        """Test that create/update serializer returns detailed representation."""
        data = {
            'name': 'Representation Test Product',
            'category_id': str(self.child_category.id),
            'sku': 'REPR-001',
            'price': '149.99'
        }
        
        serializer = ProductCreateUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        product = serializer.save()
        representation = serializer.to_representation(product)
        
        # Should include detailed fields like category with full data
        self.assertIn('category', representation)
        self.assertIn('images', representation)
        self.assertIn('effective_price', representation)
        self.assertIn('discount_percentage', representation)

    def test_product_serializer_category_validation(self):
        """Test category validation in create/update serializer."""
        # Test with inactive category
        inactive_category = Category.objects.create(
            name='Inactive Test Category',
            is_active=False
        )
        
        data = {
            'name': 'Product with Inactive Category',
            'category_id': str(inactive_category.id),
            'sku': 'INACTIVE-CAT-001',
            'price': '99.99'
        }
        
        serializer = ProductCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('category_id', serializer.errors)

    def test_product_serializer_required_fields(self):
        """Test that required fields are validated."""
        data = {}  # Empty data
        
        serializer = ProductCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        # Check that required fields are in errors
        required_fields = ['name', 'category_id', 'sku', 'price']
        for field in required_fields:
            self.assertIn(field, serializer.errors)

    def test_product_serializer_sku_validation_on_update(self):
        """Test SKU validation during update (should allow same SKU for same product)."""
        data = {
            'name': 'Updated Name',
            'sku': 'IPHONE15-001'  # Same SKU as current product
        }
        
        serializer = ProductCreateUpdateSerializer(
            instance=self.product,
            data=data,
            partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        # But should fail if trying to use another product's SKU
        other_product = Product.objects.create(
            name='Other Product',
            category=self.child_category,
            sku='OTHER-001',
            price=Decimal('99.99')
        )
        
        data['sku'] = 'OTHER-001'
        serializer = ProductCreateUpdateSerializer(
            instance=self.product,
            data=data,
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('sku', serializer.errors)