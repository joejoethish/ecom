"""
Tests for product models.
"""
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.text import slugify
from apps.products.models import Category, Product, ProductImage


class CategoryModelTest(TestCase):
    """Test cases for Category model."""

    def setUp(self):
        """Set up test data."""
        self.parent_category = Category.objects.create(
            name="Electronics",
            description="Electronic products"
        )
        self.child_category = Category.objects.create(
            name="Smartphones",
            description="Mobile phones and smartphones",
            parent=self.parent_category
        )

    def test_category_creation(self):
        """Test basic category creation."""
        category = Category.objects.create(
            name="Books",
            description="Books and literature"
        )
        self.assertEqual(category.name, "Books")
        self.assertEqual(category.description, "Books and literature")
        self.assertTrue(category.is_active)
        self.assertIsNone(category.parent)
        self.assertEqual(category.slug, "books")

    def test_category_slug_auto_generation(self):
        """Test that slug is automatically generated from name."""
        category = Category.objects.create(name="Home & Garden")
        self.assertEqual(category.slug, "home-garden")

    def test_category_hierarchical_structure(self):
        """Test parent-child relationship."""
        self.assertEqual(self.child_category.parent, self.parent_category)
        self.assertIn(self.child_category, self.parent_category.children.all())

    def test_category_full_name_property(self):
        """Test full_name property for hierarchical display."""
        self.assertEqual(self.parent_category.full_name, "Electronics")
        self.assertEqual(self.child_category.full_name, "Electronics > Smartphones")

    def test_category_get_descendants(self):
        """Test get_descendants method."""
        grandchild = Category.objects.create(
            name="Android Phones",
            parent=self.child_category
        )
        descendants = self.parent_category.get_descendants()
        self.assertIn(self.child_category, descendants)
        self.assertIn(grandchild, descendants)

    def test_category_unique_slug(self):
        """Test that slug must be unique."""
        Category.objects.create(name="Test Category", slug="test-slug")
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Another Category", slug="test-slug")

    def test_category_str_representation(self):
        """Test string representation of category."""
        self.assertEqual(str(self.parent_category), "Electronics")

    def test_category_ordering(self):
        """Test category ordering by sort_order and name."""
        cat1 = Category.objects.create(name="Z Category", sort_order=1)
        cat2 = Category.objects.create(name="A Category", sort_order=2)
        cat3 = Category.objects.create(name="B Category", sort_order=1)
        
        categories = list(Category.objects.all())
        # Should be ordered by sort_order first, then by name
        self.assertTrue(categories.index(cat3) < categories.index(cat1))
        self.assertTrue(categories.index(cat1) < categories.index(cat2))


class ProductModelTest(TestCase):
    """Test cases for Product model."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic products"
        )
        self.product = Product.objects.create(
            name="iPhone 15",
            description="Latest iPhone model",
            short_description="Apple's newest smartphone",
            category=self.category,
            brand="Apple",
            sku="IPHONE15-001",
            price=Decimal('999.99'),
            weight=Decimal('0.2'),
            dimensions={'length': 15, 'width': 7, 'height': 0.8}
        )

    def test_product_creation(self):
        """Test basic product creation."""
        self.assertEqual(self.product.name, "iPhone 15")
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.price, Decimal('999.99'))
        self.assertEqual(self.product.sku, "IPHONE15-001")
        self.assertTrue(self.product.is_active)
        self.assertFalse(self.product.is_featured)
        self.assertEqual(self.product.status, 'draft')

    def test_product_slug_auto_generation(self):
        """Test that slug is automatically generated from name."""
        self.assertEqual(self.product.slug, "iphone-15")

    def test_product_effective_price_without_discount(self):
        """Test effective_price property without discount."""
        self.assertEqual(self.product.effective_price, Decimal('999.99'))

    def test_product_effective_price_with_discount(self):
        """Test effective_price property with discount."""
        self.product.discount_price = Decimal('899.99')
        self.product.save()
        self.assertEqual(self.product.effective_price, Decimal('899.99'))

    def test_product_discount_percentage(self):
        """Test discount_percentage property."""
        self.product.discount_price = Decimal('799.99')
        self.product.save()
        expected_discount = round(((999.99 - 799.99) / 999.99) * 100, 2)
        self.assertEqual(self.product.discount_percentage, expected_discount)

    def test_product_discount_percentage_no_discount(self):
        """Test discount_percentage property when no discount."""
        self.assertEqual(self.product.discount_percentage, 0)

    def test_product_get_tags_list(self):
        """Test get_tags_list method."""
        self.product.tags = "smartphone, apple, ios, mobile"
        self.product.save()
        expected_tags = ["smartphone", "apple", "ios", "mobile"]
        self.assertEqual(self.product.get_tags_list(), expected_tags)

    def test_product_get_tags_list_empty(self):
        """Test get_tags_list method with empty tags."""
        self.assertEqual(self.product.get_tags_list(), [])

    def test_product_unique_sku(self):
        """Test that SKU must be unique."""
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Another Product",
                category=self.category,
                sku="IPHONE15-001",  # Same SKU
                price=Decimal('100.00')
            )

    def test_product_unique_slug(self):
        """Test that slug must be unique."""
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="iPhone 15",  # Same name, will generate same slug
                category=self.category,
                sku="DIFFERENT-SKU",
                price=Decimal('100.00')
            )

    def test_product_price_validation(self):
        """Test that price cannot be negative."""
        product = Product(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            price=Decimal('-10.00')
        )
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_product_str_representation(self):
        """Test string representation of product."""
        self.assertEqual(str(self.product), "iPhone 15")

    def test_product_category_relationship(self):
        """Test product-category relationship."""
        self.assertIn(self.product, self.category.products.all())


class ProductImageModelTest(TestCase):
    """Test cases for ProductImage model."""

    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            sku="TEST-001",
            price=Decimal('100.00')
        )

    def test_product_image_creation(self):
        """Test basic product image creation."""
        image = ProductImage.objects.create(
            product=self.product,
            image="products/test.jpg",
            alt_text="Test product image",
            is_primary=True,
            sort_order=1
        )
        self.assertEqual(image.product, self.product)
        self.assertEqual(image.alt_text, "Test product image")
        self.assertTrue(image.is_primary)
        self.assertEqual(image.sort_order, 1)

    def test_product_image_auto_alt_text(self):
        """Test that alt_text is auto-generated if not provided."""
        image = ProductImage.objects.create(
            product=self.product,
            image="products/test.jpg",
            sort_order=1
        )
        expected_alt_text = f"{self.product.name} - Image 1"
        self.assertEqual(image.alt_text, expected_alt_text)

    def test_product_primary_image_uniqueness(self):
        """Test that only one image can be primary per product."""
        # Create first primary image
        image1 = ProductImage.objects.create(
            product=self.product,
            image="products/test1.jpg",
            is_primary=True,
            sort_order=1
        )
        self.assertTrue(image1.is_primary)

        # Create second primary image - should make first one non-primary
        image2 = ProductImage.objects.create(
            product=self.product,
            image="products/test2.jpg",
            is_primary=True,
            sort_order=2
        )
        
        # Refresh from database
        image1.refresh_from_db()
        image2.refresh_from_db()
        
        self.assertFalse(image1.is_primary)
        self.assertTrue(image2.is_primary)

    def test_product_primary_image_property(self):
        """Test product's primary_image property."""
        # No images initially
        self.assertIsNone(self.product.primary_image)

        # Create non-primary image
        image1 = ProductImage.objects.create(
            product=self.product,
            image="products/test1.jpg",
            is_primary=False,
            sort_order=1
        )
        self.assertIsNone(self.product.primary_image)

        # Create primary image
        image2 = ProductImage.objects.create(
            product=self.product,
            image="products/test2.jpg",
            is_primary=True,
            sort_order=2
        )
        self.assertEqual(self.product.primary_image, image2)

    def test_product_image_ordering(self):
        """Test product image ordering by sort_order."""
        image3 = ProductImage.objects.create(
            product=self.product,
            image="products/test3.jpg",
            sort_order=3
        )
        image1 = ProductImage.objects.create(
            product=self.product,
            image="products/test1.jpg",
            sort_order=1
        )
        image2 = ProductImage.objects.create(
            product=self.product,
            image="products/test2.jpg",
            sort_order=2
        )

        images = list(self.product.images.all())
        self.assertEqual(images[0], image1)
        self.assertEqual(images[1], image2)
        self.assertEqual(images[2], image3)

    def test_product_image_str_representation(self):
        """Test string representation of product image."""
        image = ProductImage.objects.create(
            product=self.product,
            image="products/test.jpg",
            sort_order=1
        )
        expected_str = f"{self.product.name} - Image 1"
        self.assertEqual(str(image), expected_str)

    def test_product_image_relationship(self):
        """Test product-image relationship."""
        image = ProductImage.objects.create(
            product=self.product,
            image="products/test.jpg"
        )
        self.assertIn(image, self.product.images.all())


class ProductModelIntegrationTest(TestCase):
    """Integration tests for product models working together."""

    def setUp(self):
        """Set up test data."""
        self.parent_category = Category.objects.create(name="Electronics")
        self.child_category = Category.objects.create(
            name="Smartphones",
            parent=self.parent_category
        )
        self.product = Product.objects.create(
            name="Test Smartphone",
            category=self.child_category,
            sku="SMART-001",
            price=Decimal('599.99'),
            discount_price=Decimal('499.99')
        )

    def test_product_with_category_hierarchy(self):
        """Test product with hierarchical category structure."""
        self.assertEqual(self.product.category, self.child_category)
        self.assertEqual(self.product.category.parent, self.parent_category)
        self.assertEqual(
            self.product.category.full_name, 
            "Electronics > Smartphones"
        )

    def test_product_with_multiple_images(self):
        """Test product with multiple images including primary."""
        # Create multiple images
        image1 = ProductImage.objects.create(
            product=self.product,
            image="products/phone1.jpg",
            sort_order=1
        )
        image2 = ProductImage.objects.create(
            product=self.product,
            image="products/phone2.jpg",
            is_primary=True,
            sort_order=2
        )
        image3 = ProductImage.objects.create(
            product=self.product,
            image="products/phone3.jpg",
            sort_order=3
        )

        # Test relationships
        self.assertEqual(self.product.images.count(), 3)
        self.assertEqual(self.product.primary_image, image2)
        
        # Test ordering
        images = list(self.product.images.all())
        self.assertEqual(images, [image1, image2, image3])

    def test_category_with_products_and_images(self):
        """Test category containing products with images."""
        # Create another product in the same category
        product2 = Product.objects.create(
            name="Another Smartphone",
            category=self.child_category,
            sku="SMART-002",
            price=Decimal('399.99')
        )

        # Add images to both products
        ProductImage.objects.create(
            product=self.product,
            image="products/phone1.jpg",
            is_primary=True
        )
        ProductImage.objects.create(
            product=product2,
            image="products/phone2.jpg",
            is_primary=True
        )

        # Test category has both products
        category_products = self.child_category.products.all()
        self.assertIn(self.product, category_products)
        self.assertIn(product2, category_products)
        self.assertEqual(category_products.count(), 2)

        # Test each product has its primary image
        self.assertIsNotNone(self.product.primary_image)
        self.assertIsNotNone(product2.primary_image)