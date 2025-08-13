"""
Test Data Management System for QA Testing Framework

Provides comprehensive test data management including user account creation,
product catalog population, and test data cleanup and isolation mechanisms.
"""

import uuid
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from faker import Faker

from .interfaces import IDataManager, UserRole, Environment
from .models import TestUser, TestProduct, Address, PaymentMethod, ProductVariant
from .config import get_config, get_value


class TestDataManager(IDataManager):
    """Manages test data creation, cleanup, and isolation for testing framework"""
    
    def __init__(self):
        self.faker = Faker()
        self.created_users = {}  # Track created users by environment
        self.created_products = {}  # Track created products by environment
        self.current_environment = Environment.DEVELOPMENT
        
        # Product categories and subcategories
        self.categories = {
            "Electronics": ["Smartphones", "Laptops", "Tablets", "Headphones", "Cameras"],
            "Clothing": ["Men's Wear", "Women's Wear", "Kids Wear", "Shoes", "Accessories"],
            "Home & Garden": ["Furniture", "Kitchen", "Decor", "Garden Tools", "Lighting"],
            "Books": ["Fiction", "Non-Fiction", "Educational", "Comics", "Magazines"],
            "Sports": ["Fitness", "Outdoor", "Team Sports", "Water Sports", "Winter Sports"],
            "Beauty": ["Skincare", "Makeup", "Hair Care", "Fragrances", "Tools"],
            "Automotive": ["Parts", "Accessories", "Tools", "Care Products", "Electronics"],
            "Toys": ["Educational", "Action Figures", "Board Games", "Outdoor Toys", "Electronic Toys"],
            "Health": ["Supplements", "Medical Devices", "Personal Care", "Fitness Equipment", "Wellness"],
            "Food": ["Snacks", "Beverages", "Organic", "International", "Gourmet"]
        }
        
        # User profile templates for different roles
        self.user_templates = {
            UserRole.GUEST: {"profile_completion": 0},
            UserRole.REGISTERED: {"profile_completion": 50, "orders_count": 0},
            UserRole.PREMIUM: {"profile_completion": 90, "orders_count": 10, "loyalty_points": 1000},
            UserRole.SELLER: {"profile_completion": 100, "store_name": True, "products_count": 20},
            UserRole.ADMIN: {"profile_completion": 100, "admin_permissions": ["user_management", "product_management"]},
            UserRole.SUPER_ADMIN: {"profile_completion": 100, "admin_permissions": ["all"]}
        }
    
    def setup_test_data(self, environment: Environment) -> bool:
        """Setup comprehensive test data for specified environment"""
        try:
            self.current_environment = environment
            config = get_config("test_data", environment)
            
            # Initialize tracking dictionaries for this environment
            if environment not in self.created_users:
                self.created_users[environment] = []
            if environment not in self.created_products:
                self.created_products[environment] = []
            
            # Create user accounts
            users_count = config.get("users_count", 50)
            self._create_user_accounts(users_count, environment)
            
            # Create product catalog
            products_count = config.get("products_count", 500)
            categories_count = config.get("categories_count", 20)
            self._create_product_catalog(products_count, categories_count, environment)
            
            return True
            
        except Exception as e:
            print(f"Error setting up test data for {environment.value}: {str(e)}")
            return False
    
    def cleanup_test_data(self, test_id: str) -> bool:
        """Clean up test data after execution"""
        try:
            # In a real implementation, this would connect to the database
            # and clean up data created during the test execution
            
            # For now, we'll simulate cleanup by clearing our tracking data
            # if the test_id matches our environment
            if test_id in [env.value for env in Environment]:
                env = Environment(test_id)
                if env in self.created_users:
                    del self.created_users[env]
                if env in self.created_products:
                    del self.created_products[env]
            
            return True
            
        except Exception as e:
            print(f"Error cleaning up test data for {test_id}: {str(e)}")
            return False
    
    def create_test_user(self, user_type: UserRole) -> Dict[str, Any]:
        """Create a single test user account"""
        try:
            user_id = f"test_user_{uuid.uuid4().hex[:8]}"
            email = f"{user_id}@testdomain.com"
            password = self._generate_password()
            
            # Get user template
            template = self.user_templates.get(user_type, {})
            
            # Create basic user
            user = TestUser(
                id=user_id,
                user_type=user_type,
                email=email,
                password=password,
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                phone=self.faker.phone_number()[:15],  # Limit phone number length
                profile_data=self._generate_profile_data(user_type, template),
                addresses=self._generate_addresses(user_type),
                payment_methods=self._generate_payment_methods(user_type),
                is_active=True,
                created_date=datetime.now()
            )
            
            # Track created user
            if self.current_environment not in self.created_users:
                self.created_users[self.current_environment] = []
            self.created_users[self.current_environment].append(user)
            
            return user.to_dict()
            
        except Exception as e:
            print(f"Error creating test user of type {user_type.value}: {str(e)}")
            return {}
    
    def generate_test_products(self, category: str, count: int) -> List[Dict[str, Any]]:
        """Generate test product data for specified category"""
        try:
            products = []
            
            # Get subcategories for the category
            subcategories = self.categories.get(category, [category])
            
            for i in range(count):
                product_id = f"test_product_{uuid.uuid4().hex[:8]}"
                subcategory = random.choice(subcategories)
                
                product = TestProduct(
                    id=product_id,
                    name=self._generate_product_name(category, subcategory),
                    description=self._generate_product_description(category),
                    category=category,
                    subcategory=subcategory,
                    price=self._generate_product_price(category),
                    stock_quantity=random.randint(0, 1000),
                    seller_id=self._get_random_seller_id(),
                    status=random.choice(["active", "active", "active", "inactive", "out_of_stock"]),
                    variants=self._generate_product_variants(category, subcategory),
                    images=self._generate_product_images(),
                    attributes=self._generate_product_attributes(category, subcategory),
                    created_date=datetime.now() - timedelta(days=random.randint(1, 365))
                )
                
                products.append(product.to_dict())
                
                # Track created product
                if self.current_environment not in self.created_products:
                    self.created_products[self.current_environment] = []
                self.created_products[self.current_environment].append(product)
            
            return products
            
        except Exception as e:
            print(f"Error generating test products for category {category}: {str(e)}")
            return []
    
    def get_test_users_by_role(self, user_role: UserRole, environment: Optional[Environment] = None) -> List[Dict[str, Any]]:
        """Get all test users of specified role"""
        env = environment or self.current_environment
        users = self.created_users.get(env, [])
        return [user.to_dict() for user in users if user.user_type == user_role]
    
    def get_test_products_by_category(self, category: str, environment: Optional[Environment] = None) -> List[Dict[str, Any]]:
        """Get all test products in specified category"""
        env = environment or self.current_environment
        products = self.created_products.get(env, [])
        return [product.to_dict() for product in products if product.category == category]
    
    def create_isolated_test_data(self, test_case_id: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create isolated test data for specific test case"""
        try:
            isolated_data = {
                "test_case_id": test_case_id,
                "users": [],
                "products": [],
                "created_at": datetime.now().isoformat()
            }
            
            # Create required users
            if "users" in requirements:
                for user_spec in requirements["users"]:
                    user_role = UserRole(user_spec.get("role", "registered"))
                    count = user_spec.get("count", 1)
                    
                    for _ in range(count):
                        user_data = self.create_test_user(user_role)
                        isolated_data["users"].append(user_data)
            
            # Create required products
            if "products" in requirements:
                for product_spec in requirements["products"]:
                    category = product_spec.get("category", "Electronics")
                    count = product_spec.get("count", 1)
                    
                    products = self.generate_test_products(category, count)
                    isolated_data["products"].extend(products)
            
            return isolated_data
            
        except Exception as e:
            print(f"Error creating isolated test data for {test_case_id}: {str(e)}")
            return {}
    
    def _create_user_accounts(self, count: int, environment: Environment) -> None:
        """Create specified number of user accounts across all roles"""
        # Distribution of user roles
        role_distribution = {
            UserRole.GUEST: int(count * 0.2),  # 20%
            UserRole.REGISTERED: int(count * 0.4),  # 40%
            UserRole.PREMIUM: int(count * 0.2),  # 20%
            UserRole.SELLER: int(count * 0.15),  # 15%
            UserRole.ADMIN: max(1, int(count * 0.03)),  # 3%
            UserRole.SUPER_ADMIN: max(1, int(count * 0.02))  # 2%
        }
        
        for role, role_count in role_distribution.items():
            for _ in range(role_count):
                self.create_test_user(role)
    
    def _create_product_catalog(self, products_count: int, categories_count: int, environment: Environment) -> None:
        """Create product catalog with specified number of products"""
        # Select random categories
        selected_categories = random.sample(list(self.categories.keys()), 
                                          min(categories_count, len(self.categories)))
        
        # Distribute products across categories
        products_per_category = products_count // len(selected_categories)
        remaining_products = products_count % len(selected_categories)
        
        for i, category in enumerate(selected_categories):
            count = products_per_category
            if i < remaining_products:
                count += 1
            
            self.generate_test_products(category, count)
    
    def _generate_password(self) -> str:
        """Generate a secure test password"""
        # Generate password with mix of characters
        length = random.randint(8, 12)
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(chars) for _ in range(length))
        
        # Ensure it has at least one digit and one special char
        if not any(c.isdigit() for c in password):
            password = password[:-1] + random.choice(string.digits)
        if not any(c in "!@#$%" for c in password):
            password = password[:-1] + random.choice("!@#$%")
        
        return password
    
    def _generate_profile_data(self, user_type: UserRole, template: Dict[str, Any]) -> Dict[str, Any]:
        """Generate profile data based on user type"""
        profile_data = {
            "date_of_birth": self.faker.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            "gender": random.choice(["male", "female", "other"]),
            "preferences": {
                "language": random.choice(["en", "es", "fr", "de"]),
                "currency": random.choice(["USD", "EUR", "GBP"]),
                "notifications": {
                    "email": random.choice([True, False]),
                    "sms": random.choice([True, False]),
                    "push": random.choice([True, False])
                }
            }
        }
        
        # Add role-specific data
        if user_type == UserRole.PREMIUM:
            profile_data["loyalty_points"] = template.get("loyalty_points", 0)
            profile_data["membership_tier"] = random.choice(["gold", "platinum", "diamond"])
        
        elif user_type == UserRole.SELLER:
            profile_data["store_name"] = f"{self.faker.company()} Store"
            profile_data["business_type"] = random.choice(["individual", "business", "corporation"])
            profile_data["tax_id"] = self.faker.ssn()
        
        elif user_type in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            profile_data["admin_permissions"] = template.get("admin_permissions", [])
            profile_data["department"] = random.choice(["IT", "Customer Service", "Operations", "Management"])
        
        return profile_data
    
    def _generate_addresses(self, user_type: UserRole) -> List[Address]:
        """Generate addresses for user based on type"""
        addresses = []
        
        # Number of addresses based on user type
        if user_type == UserRole.GUEST:
            return addresses  # No saved addresses for guests
        elif user_type in [UserRole.REGISTERED, UserRole.PREMIUM]:
            address_count = random.randint(1, 3)
        else:
            address_count = random.randint(1, 2)
        
        address_types = ["shipping", "billing"]
        
        for i in range(address_count):
            address = Address(
                street=self.faker.street_address(),
                city=self.faker.city(),
                state=self.faker.state(),
                postal_code=self.faker.postcode(),
                country=self.faker.country_code(),
                address_type=address_types[i % len(address_types)]
            )
            addresses.append(address)
        
        return addresses
    
    def _generate_payment_methods(self, user_type: UserRole) -> List[PaymentMethod]:
        """Generate payment methods for user based on type"""
        payment_methods = []
        
        # Number of payment methods based on user type
        if user_type == UserRole.GUEST:
            return payment_methods  # No saved payment methods for guests
        elif user_type == UserRole.PREMIUM:
            method_count = random.randint(2, 4)
        else:
            method_count = random.randint(1, 2)
        
        method_types = ["credit_card", "debit_card", "paypal", "upi"]
        
        for i in range(method_count):
            method_type = random.choice(method_types)
            details = {}
            
            if method_type in ["credit_card", "debit_card"]:
                details = {
                    "card_number": self.faker.credit_card_number(),
                    "expiry_month": random.randint(1, 12),
                    "expiry_year": random.randint(2024, 2030),
                    "cvv": random.randint(100, 999),
                    "cardholder_name": f"{self.faker.first_name()} {self.faker.last_name()}"
                }
            elif method_type == "paypal":
                details = {
                    "email": self.faker.email()
                }
            elif method_type == "upi":
                details = {
                    "upi_id": f"{self.faker.user_name()}@{random.choice(['paytm', 'googlepay', 'phonepe'])}"
                }
            
            payment_method = PaymentMethod(
                type=method_type,
                details=details,
                is_default=(i == 0)  # First method is default
            )
            payment_methods.append(payment_method)
        
        return payment_methods
    
    def _generate_product_name(self, category: str, subcategory: str) -> str:
        """Generate realistic product name"""
        brand_names = {
            "Electronics": ["TechPro", "DigitalMax", "ElectroCore", "SmartTech", "InnoDevice"],
            "Clothing": ["StyleMax", "FashionHub", "TrendWear", "ClassicStyle", "ModernFit"],
            "Home & Garden": ["HomeComfort", "GardenPro", "LivingSpace", "CozyHome", "OutdoorPlus"],
            "Books": ["BookWorld", "ReadMore", "KnowledgeHub", "StoryTime", "LearnFast"],
            "Sports": ["SportsPro", "FitMax", "ActiveLife", "GameTime", "OutdoorGear"]
        }
        
        brands = brand_names.get(category, ["Generic", "Quality", "Premium", "Standard", "Basic"])
        brand = random.choice(brands)
        
        # Generate product-specific names
        if category == "Electronics":
            if subcategory == "Smartphones":
                model = f"Model {random.choice(['X', 'Pro', 'Max', 'Ultra'])} {random.randint(10, 99)}"
            elif subcategory == "Laptops":
                model = f"{random.choice(['Book', 'Pro', 'Air', 'Gaming'])} {random.randint(13, 17)}"
            else:
                model = f"{subcategory} {random.choice(['Pro', 'Max', 'Ultra', 'Plus'])}"
        else:
            adjectives = ["Premium", "Deluxe", "Classic", "Modern", "Vintage", "Professional"]
            model = f"{random.choice(adjectives)} {subcategory}"
        
        return f"{brand} {model}"
    
    def _generate_product_description(self, category: str) -> str:
        """Generate product description"""
        descriptions = {
            "Electronics": "High-quality electronic device with advanced features and reliable performance.",
            "Clothing": "Comfortable and stylish clothing item made from premium materials.",
            "Home & Garden": "Essential item for your home and garden needs with durable construction.",
            "Books": "Engaging and informative reading material for knowledge and entertainment.",
            "Sports": "Professional-grade sports equipment for optimal performance and safety."
        }
        
        base_desc = descriptions.get(category, "Quality product with excellent features and value.")
        features = [
            "Easy to use and maintain",
            "Durable construction",
            "Excellent value for money",
            "Customer satisfaction guaranteed",
            "Fast shipping available"
        ]
        
        return f"{base_desc} {random.choice(features)}"
    
    def _generate_product_price(self, category: str) -> float:
        """Generate realistic product price based on category"""
        price_ranges = {
            "Electronics": (50, 2000),
            "Clothing": (20, 300),
            "Home & Garden": (15, 500),
            "Books": (10, 50),
            "Sports": (25, 800),
            "Beauty": (15, 150),
            "Automotive": (20, 1000),
            "Toys": (10, 200),
            "Health": (20, 300),
            "Food": (5, 100)
        }
        
        min_price, max_price = price_ranges.get(category, (10, 100))
        price = random.uniform(min_price, max_price)
        
        # Round to 2 decimal places
        return round(price, 2)
    
    def _generate_product_variants(self, category: str, subcategory: str) -> List[ProductVariant]:
        """Generate product variants based on category"""
        variants = []
        
        # Determine variant attributes based on category
        if category == "Clothing":
            sizes = ["XS", "S", "M", "L", "XL", "XXL"]
            colors = ["Black", "White", "Red", "Blue", "Green", "Gray"]
            
            for size in random.sample(sizes, random.randint(2, 4)):
                for color in random.sample(colors, random.randint(1, 3)):
                    variant_id = f"var_{uuid.uuid4().hex[:6]}"
                    variant = ProductVariant(
                        id=variant_id,
                        name=f"{size} - {color}",
                        sku=f"SKU_{variant_id.upper()}",
                        price=self._generate_product_price(category) + random.uniform(-10, 20),
                        attributes={"size": size, "color": color},
                        stock_quantity=random.randint(0, 100)
                    )
                    variants.append(variant)
        
        elif category == "Electronics":
            if subcategory in ["Smartphones", "Tablets"]:
                storages = ["64GB", "128GB", "256GB", "512GB"]
                colors = ["Black", "White", "Blue", "Red"]
                
                for storage in random.sample(storages, random.randint(2, 3)):
                    for color in random.sample(colors, random.randint(1, 2)):
                        variant_id = f"var_{uuid.uuid4().hex[:6]}"
                        variant = ProductVariant(
                            id=variant_id,
                            name=f"{storage} - {color}",
                            sku=f"SKU_{variant_id.upper()}",
                            price=self._generate_product_price(category) + (int(storage[:-2]) * 0.5),
                            attributes={"storage": storage, "color": color},
                            stock_quantity=random.randint(0, 50)
                        )
                        variants.append(variant)
        
        # Limit variants to avoid too many
        return variants[:random.randint(1, min(6, len(variants))) if variants else 0]
    
    def _generate_product_images(self) -> List[str]:
        """Generate product image URLs"""
        image_count = random.randint(1, 5)
        images = []
        
        for i in range(image_count):
            # Generate placeholder image URLs
            width = random.choice([400, 600, 800])
            height = random.choice([400, 600, 800])
            images.append(f"https://picsum.photos/{width}/{height}?random={uuid.uuid4().hex[:8]}")
        
        return images
    
    def _generate_product_attributes(self, category: str, subcategory: str) -> Dict[str, Any]:
        """Generate category-specific product attributes"""
        attributes = {
            "weight": f"{random.uniform(0.1, 10.0):.2f} kg",
            "dimensions": f"{random.randint(10, 50)}x{random.randint(10, 50)}x{random.randint(5, 30)} cm",
            "warranty": f"{random.randint(6, 36)} months"
        }
        
        # Category-specific attributes
        if category == "Electronics":
            attributes.update({
                "brand": random.choice(["TechPro", "DigitalMax", "ElectroCore"]),
                "model_year": random.randint(2020, 2024),
                "energy_rating": random.choice(["A++", "A+", "A", "B"])
            })
        
        elif category == "Clothing":
            attributes.update({
                "material": random.choice(["Cotton", "Polyester", "Wool", "Silk", "Blend"]),
                "care_instructions": "Machine wash cold, tumble dry low",
                "fit": random.choice(["Regular", "Slim", "Loose", "Athletic"])
            })
        
        elif category == "Books":
            attributes.update({
                "author": self.faker.name(),
                "publisher": f"{self.faker.company()} Publishing",
                "pages": random.randint(100, 800),
                "language": random.choice(["English", "Spanish", "French", "German"])
            })
        
        return attributes
    
    def _get_random_seller_id(self) -> str:
        """Get random seller ID from created sellers"""
        # In a real implementation, this would query the database for seller IDs
        # For now, generate a random seller ID
        return f"seller_{uuid.uuid4().hex[:8]}"