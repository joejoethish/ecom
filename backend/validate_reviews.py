#!/usr/bin/env python
"""
Simple validation script for reviews models.
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

# Now we can import our models
from apps.reviews.models import Review, ReviewHelpfulness, ReviewImage, ReviewReport
from apps.products.models import Product, Category, ProductRating
from apps.authentication.models import User
from apps.orders.models import Order, OrderItem

def validate_models():
    """Validate that all models are properly defined."""
    print("Validating Review models...")
    
    # Check Review model
    print("✓ Review model imported successfully")
    print(f"  - Fields: {[f.name for f in Review._meta.fields]}")
    
    # Check ReviewHelpfulness model
    print("✓ ReviewHelpfulness model imported successfully")
    print(f"  - Fields: {[f.name for f in ReviewHelpfulness._meta.fields]}")
    
    # Check ReviewImage model
    print("✓ ReviewImage model imported successfully")
    print(f"  - Fields: {[f.name for f in ReviewImage._meta.fields]}")
    
    # Check ReviewReport model
    print("✓ ReviewReport model imported successfully")
    print(f"  - Fields: {[f.name for f in ReviewReport._meta.fields]}")
    
    # Check ProductRating model
    print("✓ ProductRating model imported successfully")
    print(f"  - Fields: {[f.name for f in ProductRating._meta.fields]}")
    
    print("\nAll models validated successfully!")

def test_basic_functionality():
    """Test basic model functionality."""
    print("\nTesting basic functionality...")
    
    try:
        # Create test data
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print("✓ User created successfully")
        
        category = Category.objects.create(name='Electronics')
        print("✓ Category created successfully")
        
        product = Product.objects.create(
            name='Test Product',
            category=category,
            price=99.99,
            sku='TEST001'
        )
        print("✓ Product created successfully")
        
        order = Order.objects.create(
            customer=user,
            order_number='ORD001',
            total_amount=99.99,
            status='delivered'
        )
        print("✓ Order created successfully")
        
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price=99.99,
            total_price=99.99
        )
        print("✓ OrderItem created successfully")
        
        # Create a review
        review = Review.objects.create(
            product=product,
            user=user,
            order_item=order_item,
            rating=5,
            title='Great product!',
            comment='I love this product.',
            is_verified_purchase=True
        )
        print("✓ Review created successfully")
        print(f"  - Review ID: {review.id}")
        print(f"  - Rating: {review.rating}")
        print(f"  - Status: {review.status}")
        print(f"  - Verified Purchase: {review.is_verified_purchase}")
        
        # Test review methods
        print(f"  - Helpfulness Score: {review.helpfulness_score}%")
        
        # Test product rating aggregation
        product.update_rating_aggregation()
        print("✓ Product rating aggregation updated")
        print(f"  - Average Rating: {product.average_rating}")
        print(f"  - Total Reviews: {product.total_reviews}")
        
        print("\nBasic functionality test completed successfully!")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    validate_models()
    test_basic_functionality()