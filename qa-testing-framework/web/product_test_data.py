"""
Product Test Data Management

Provides test data creation and management for product browsing tests
including products, categories, and search scenarios.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

try:
    from ..core.models import TestProduct, ProductVariant, TestUser
    from ..core.interfaces import UserRole
    from ..core.data_manager import TestDataManager
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from core.models import TestProduct, ProductVariant, TestUser
    from core.interfaces import UserRole
    from core.data_manager import TestDataManager


class ProductTestDataManager:
    """Manages test data specifically for product browsing tests"""
    
    def __init__(self, data_manager: TestDataManager):
        self.data_manager = data_manager
        self.test_products = []
        self.test_categories = []
        self.test_users = []
    
    def create_test_categories(self) -> List[Dict[str, Any]]:
        """Create test product categories"""
        categories = [
            {
                "id": "electronics",
                "name": "Electronics",
                "subcategories": [
                    {"id": "laptops", "name": "Laptops"},
                    {"id": "phones", "name": "Mobile Phones"},
                    {"id": "tablets", "name": "Tablets"},
                    {"id": "accessories", "name": "Accessories"}
                ]
            },
            {
                "id": "clothing",
                "name": "Clothing",
                "subcategories": [
                    {"id": "mens", "name": "Men's Clothing"},
                    {"id": "womens", "name": "Women's Clothing"},
                    {"id": "kids", "name": "Kids' Clothing"},
                    {"id": "shoes", "name": "Shoes"}
                ]
            },
            {
                "id": "books",
                "name": "Books",
                "subcategories": [
                    {"id": "fiction", "name": "Fiction"},
                    {"id": "non_fiction", "name": "Non-Fiction"},
                    {"id": "textbooks", "name": "Textbooks"},
                    {"id": "ebooks", "name": "E-Books"}
                ]
            },
            {
                "id": "home_garden",
                "name": "Home & Garden",
                "subcategories": [
                    {"id": "furniture", "name": "Furniture"},
                    {"id": "decor", "name": "Home Decor"},
                    {"id": "kitchen", "name": "Kitchen"},
                    {"id": "garden", "name": "Garden"}
                ]
            },
            {
                "id": "sports",
                "name": "Sports & Outdoors",
                "subcategories": [
                    {"id": "fitness", "name": "Fitness Equipment"},
                    {"id": "outdoor", "name": "Outdoor Gear"},
                    {"id": "team_sports", "name": "Team Sports"},
                    {"id": "water_sports", "name": "Water Sports"}
                ]
            }
        ]
        
        self.test_categories = categories
        return categories
    
    def create_test_products(self, count: int = 50) -> List[TestProduct]:
        """Create test products for browsing tests"""
        if not self.test_categories:
            self.create_test_categories()
        
        products = []
        brands = ["TechCorp", "StyleBrand", "HomeMax", "SportsPro", "BookWorld", "QualityGoods"]
        
        for i in range(count):
            # Select random category and subcategory
            category = random.choice(self.test_categories)
            subcategory = random.choice(category["subcategories"])
            
            # Generate product based on category
            product_data = self._generate_product_by_category(
                i + 1, category, subcategory, random.choice(brands)
            )
            
            product = TestProduct(**product_data)
            products.append(product)
        
        self.test_products = products
        return products
    
    def _generate_product_by_category(self, product_id: int, category: Dict, subcategory: Dict, brand: str) -> Dict[str, Any]:
        """Generate product data based on category"""
        base_price = random.uniform(10, 1000)
        stock = random.randint(0, 100)
        
        # Category-specific product generation
        if category["id"] == "electronics":
            return self._generate_electronics_product(product_id, subcategory, brand, base_price, stock)
        elif category["id"] == "clothing":
            return self._generate_clothing_product(product_id, subcategory, brand, base_price, stock)
        elif category["id"] == "books":
            return self._generate_book_product(product_id, subcategory, brand, base_price, stock)
        elif category["id"] == "home_garden":
            return self._generate_home_product(product_id, subcategory, brand, base_price, stock)
        elif category["id"] == "sports":
            return self._generate_sports_product(product_id, subcategory, brand, base_price, stock)
        else:
            return self._generate_generic_product(product_id, category, subcategory, brand, base_price, stock)
    
    def _generate_electronics_product(self, product_id: int, subcategory: Dict, brand: str, price: float, stock: int) -> Dict[str, Any]:
        """Generate electronics product"""
        if subcategory["id"] == "laptops":
            name = f"{brand} {random.choice(['Pro', 'Air', 'Gaming', 'Business'])} Laptop"
            description = f"High-performance laptop with {random.choice(['Intel i5', 'Intel i7', 'AMD Ryzen'])} processor"
            variants = [
                ProductVariant(
                    id=f"var_{product_id}_1",
                    name="8GB RAM / 256GB SSD",
                    sku=f"LAP-{product_id}-256",
                    price=price,
                    attributes={"ram": "8GB", "storage": "256GB SSD"},
                    stock_quantity=stock
                ),
                ProductVariant(
                    id=f"var_{product_id}_2",
                    name="16GB RAM / 512GB SSD",
                    sku=f"LAP-{product_id}-512",
                    price=price * 1.3,
                    attributes={"ram": "16GB", "storage": "512GB SSD"},
                    stock_quantity=stock // 2
                )
            ]
        elif subcategory["id"] == "phones":
            name = f"{brand} {random.choice(['X', 'Pro', 'Max', 'Plus'])} Smartphone"
            description = f"Latest smartphone with {random.choice(['64GB', '128GB', '256GB'])} storage"
            variants = [
                ProductVariant(
                    id=f"var_{product_id}_1",
                    name="64GB",
                    sku=f"PHN-{product_id}-64",
                    price=price,
                    attributes={"storage": "64GB", "color": "Black"},
                    stock_quantity=stock
                ),
                ProductVariant(
                    id=f"var_{product_id}_2",
                    name="128GB",
                    sku=f"PHN-{product_id}-128",
                    price=price * 1.2,
                    attributes={"storage": "128GB", "color": "White"},
                    stock_quantity=stock // 2
                )
            ]
        else:
            name = f"{brand} {subcategory['name']} Device"
            description = f"Quality {subcategory['name'].lower()} from {brand}"
            variants = []
        
        return {
            "id": f"prod_{product_id}",
            "name": name,
            "description": description,
            "category": "Electronics",
            "subcategory": subcategory["name"],
            "price": price,
            "stock_quantity": stock,
            "variants": variants,
            "attributes": {"brand": brand, "warranty": "1 year"},
            "images": [f"/images/product_{product_id}_1.jpg", f"/images/product_{product_id}_2.jpg"]
        }
    
    def _generate_clothing_product(self, product_id: int, subcategory: Dict, brand: str, price: float, stock: int) -> Dict[str, Any]:
        """Generate clothing product"""
        if subcategory["id"] == "mens":
            name = f"{brand} Men's {random.choice(['T-Shirt', 'Shirt', 'Jeans', 'Jacket'])}"
        elif subcategory["id"] == "womens":
            name = f"{brand} Women's {random.choice(['Dress', 'Blouse', 'Skirt', 'Pants'])}"
        elif subcategory["id"] == "kids":
            name = f"{brand} Kids' {random.choice(['T-Shirt', 'Shorts', 'Dress', 'Jacket'])}"
        else:
            name = f"{brand} {random.choice(['Sneakers', 'Boots', 'Sandals', 'Dress Shoes'])}"
        
        description = f"Comfortable and stylish {name.lower()} made from quality materials"
        
        # Create size variants
        sizes = ["XS", "S", "M", "L", "XL"] if subcategory["id"] != "shoes" else ["7", "8", "9", "10", "11"]
        colors = ["Black", "White", "Blue", "Red", "Gray"]
        
        variants = []
        for i, size in enumerate(sizes[:3]):  # Limit to 3 sizes
            for j, color in enumerate(colors[:2]):  # Limit to 2 colors
                variants.append(ProductVariant(
                    id=f"var_{product_id}_{i}_{j}",
                    name=f"{size} - {color}",
                    sku=f"CLO-{product_id}-{size}-{color[:3].upper()}",
                    price=price,
                    attributes={"size": size, "color": color},
                    stock_quantity=stock // len(sizes)
                ))
        
        return {
            "id": f"prod_{product_id}",
            "name": name,
            "description": description,
            "category": "Clothing",
            "subcategory": subcategory["name"],
            "price": price,
            "stock_quantity": stock,
            "variants": variants,
            "attributes": {"brand": brand, "material": random.choice(["Cotton", "Polyester", "Blend"])},
            "images": [f"/images/product_{product_id}_1.jpg", f"/images/product_{product_id}_2.jpg"]
        }
    
    def _generate_book_product(self, product_id: int, subcategory: Dict, brand: str, price: float, stock: int) -> Dict[str, Any]:
        """Generate book product"""
        authors = ["John Smith", "Jane Doe", "Michael Johnson", "Sarah Wilson", "David Brown"]
        
        if subcategory["id"] == "fiction":
            titles = ["The Great Adventure", "Mystery of the Lost City", "Love in Paris", "The Final Chapter"]
        elif subcategory["id"] == "non_fiction":
            titles = ["How to Succeed", "The Art of Leadership", "Science Explained", "History Unveiled"]
        elif subcategory["id"] == "textbooks":
            titles = ["Mathematics 101", "Physics Fundamentals", "Chemistry Basics", "Biology Essentials"]
        else:
            titles = ["Digital Reading", "E-Book Guide", "Online Learning", "Tech Trends"]
        
        name = f"{random.choice(titles)} by {random.choice(authors)}"
        description = f"An engaging {subcategory['name'].lower()} book that will captivate readers"
        
        # Books typically don't have variants, but might have format options
        variants = [
            ProductVariant(
                id=f"var_{product_id}_1",
                name="Paperback",
                sku=f"BOOK-{product_id}-PB",
                price=price,
                attributes={"format": "Paperback", "pages": random.randint(200, 500)},
                stock_quantity=stock
            ),
            ProductVariant(
                id=f"var_{product_id}_2",
                name="Hardcover",
                sku=f"BOOK-{product_id}-HC",
                price=price * 1.5,
                attributes={"format": "Hardcover", "pages": random.randint(200, 500)},
                stock_quantity=stock // 3
            )
        ]
        
        return {
            "id": f"prod_{product_id}",
            "name": name,
            "description": description,
            "category": "Books",
            "subcategory": subcategory["name"],
            "price": price,
            "stock_quantity": stock,
            "variants": variants,
            "attributes": {"publisher": brand, "language": "English", "isbn": f"978-{random.randint(1000000000, 9999999999)}"},
            "images": [f"/images/product_{product_id}_1.jpg"]
        }
    
    def _generate_home_product(self, product_id: int, subcategory: Dict, brand: str, price: float, stock: int) -> Dict[str, Any]:
        """Generate home & garden product"""
        if subcategory["id"] == "furniture":
            items = ["Chair", "Table", "Sofa", "Bed", "Dresser"]
        elif subcategory["id"] == "decor":
            items = ["Lamp", "Vase", "Picture Frame", "Mirror", "Candle"]
        elif subcategory["id"] == "kitchen":
            items = ["Blender", "Toaster", "Coffee Maker", "Microwave", "Cookware Set"]
        else:
            items = ["Plant Pot", "Garden Tool", "Watering Can", "Fertilizer", "Seeds"]
        
        name = f"{brand} {random.choice(items)}"
        description = f"High-quality {name.lower()} perfect for your home"
        
        return {
            "id": f"prod_{product_id}",
            "name": name,
            "description": description,
            "category": "Home & Garden",
            "subcategory": subcategory["name"],
            "price": price,
            "stock_quantity": stock,
            "variants": [],
            "attributes": {"brand": brand, "material": random.choice(["Wood", "Metal", "Plastic", "Glass"])},
            "images": [f"/images/product_{product_id}_1.jpg", f"/images/product_{product_id}_2.jpg"]
        }
    
    def _generate_sports_product(self, product_id: int, subcategory: Dict, brand: str, price: float, stock: int) -> Dict[str, Any]:
        """Generate sports & outdoors product"""
        if subcategory["id"] == "fitness":
            items = ["Dumbbell Set", "Yoga Mat", "Treadmill", "Exercise Bike", "Resistance Bands"]
        elif subcategory["id"] == "outdoor":
            items = ["Tent", "Sleeping Bag", "Backpack", "Hiking Boots", "Camping Stove"]
        elif subcategory["id"] == "team_sports":
            items = ["Soccer Ball", "Basketball", "Football", "Baseball Glove", "Tennis Racket"]
        else:
            items = ["Swimsuit", "Goggles", "Life Jacket", "Surfboard", "Diving Mask"]
        
        name = f"{brand} {random.choice(items)}"
        description = f"Professional-grade {name.lower()} for sports enthusiasts"
        
        return {
            "id": f"prod_{product_id}",
            "name": name,
            "description": description,
            "category": "Sports & Outdoors",
            "subcategory": subcategory["name"],
            "price": price,
            "stock_quantity": stock,
            "variants": [],
            "attributes": {"brand": brand, "sport": subcategory["name"]},
            "images": [f"/images/product_{product_id}_1.jpg", f"/images/product_{product_id}_2.jpg"]
        }
    
    def _generate_generic_product(self, product_id: int, category: Dict, subcategory: Dict, brand: str, price: float, stock: int) -> Dict[str, Any]:
        """Generate generic product"""
        name = f"{brand} {subcategory['name']} Product"
        description = f"Quality {subcategory['name'].lower()} from {brand}"
        
        return {
            "id": f"prod_{product_id}",
            "name": name,
            "description": description,
            "category": category["name"],
            "subcategory": subcategory["name"],
            "price": price,
            "stock_quantity": stock,
            "variants": [],
            "attributes": {"brand": brand},
            "images": [f"/images/product_{product_id}_1.jpg"]
        }
    
    def create_search_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test scenarios for search functionality"""
        scenarios = [
            {
                "name": "Valid keyword search",
                "search_terms": ["laptop", "phone", "shirt", "book", "chair"],
                "expected_results": "Should return relevant products"
            },
            {
                "name": "Invalid keyword search",
                "search_terms": ["xyzinvalid", "notfound123", "randomtext"],
                "expected_results": "Should show no results or suggestions"
            },
            {
                "name": "Empty search",
                "search_terms": ["", "   "],
                "expected_results": "Should handle gracefully"
            },
            {
                "name": "Partial keyword search",
                "search_terms": ["lap", "pho", "boo"],
                "expected_results": "Should show search suggestions"
            },
            {
                "name": "Brand search",
                "search_terms": ["TechCorp", "StyleBrand", "HomeMax"],
                "expected_results": "Should return products from specific brands"
            },
            {
                "name": "Category search",
                "search_terms": ["electronics", "clothing", "books"],
                "expected_results": "Should return products from specific categories"
            },
            {
                "name": "Special characters search",
                "search_terms": ["@#$%", "!@#", "***"],
                "expected_results": "Should handle special characters gracefully"
            },
            {
                "name": "Long search query",
                "search_terms": ["very long search query with multiple words that might exceed normal limits"],
                "expected_results": "Should handle long queries appropriately"
            }
        ]
        
        return scenarios
    
    def create_filter_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test scenarios for filtering functionality"""
        scenarios = [
            {
                "name": "Price range filter",
                "filters": [
                    {"type": "price", "min": 10, "max": 50},
                    {"type": "price", "min": 100, "max": 500},
                    {"type": "price", "min": 0, "max": 1000}
                ],
                "expected_results": "Products should be filtered by price range"
            },
            {
                "name": "Brand filter",
                "filters": [
                    {"type": "brand", "value": "TechCorp"},
                    {"type": "brand", "value": "StyleBrand"}
                ],
                "expected_results": "Products should be filtered by brand"
            },
            {
                "name": "Category filter",
                "filters": [
                    {"type": "category", "value": "Electronics"},
                    {"type": "category", "value": "Clothing"}
                ],
                "expected_results": "Products should be filtered by category"
            },
            {
                "name": "Availability filter",
                "filters": [
                    {"type": "availability", "value": "in_stock"},
                    {"type": "availability", "value": "out_of_stock"}
                ],
                "expected_results": "Products should be filtered by availability"
            },
            {
                "name": "Multiple filters combination",
                "filters": [
                    {"type": "price", "min": 50, "max": 200},
                    {"type": "brand", "value": "TechCorp"},
                    {"type": "availability", "value": "in_stock"}
                ],
                "expected_results": "Products should match all applied filters"
            }
        ]
        
        return scenarios
    
    def create_test_users_for_browsing(self) -> List[TestUser]:
        """Create test users for product browsing tests"""
        users = [
            TestUser(
                id="guest_user",
                user_type=UserRole.GUEST,
                email="guest@example.com",
                password="password123",
                first_name="Guest",
                last_name="User"
            ),
            TestUser(
                id="registered_user",
                user_type=UserRole.REGISTERED,
                email="registered@example.com",
                password="password123",
                first_name="Registered",
                last_name="User"
            ),
            TestUser(
                id="premium_user",
                user_type=UserRole.PREMIUM,
                email="premium@example.com",
                password="password123",
                first_name="Premium",
                last_name="User"
            )
        ]
        
        self.test_users = users
        return users
    
    def get_products_by_category(self, category: str) -> List[TestProduct]:
        """Get products filtered by category"""
        return [p for p in self.test_products if p.category.lower() == category.lower()]
    
    def get_products_by_price_range(self, min_price: float, max_price: float) -> List[TestProduct]:
        """Get products filtered by price range"""
        return [p for p in self.test_products if min_price <= p.price <= max_price]
    
    def get_products_by_brand(self, brand: str) -> List[TestProduct]:
        """Get products filtered by brand"""
        return [p for p in self.test_products if p.attributes.get("brand", "").lower() == brand.lower()]
    
    def search_products(self, search_term: str) -> List[TestProduct]:
        """Search products by name or description"""
        search_term = search_term.lower()
        results = []
        
        for product in self.test_products:
            if (search_term in product.name.lower() or 
                search_term in product.description.lower() or
                search_term in product.category.lower() or
                search_term in product.subcategory.lower()):
                results.append(product)
        
        return results
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        self.test_products.clear()
        self.test_categories.clear()
        self.test_users.clear()
        print("Product test data cleaned up")