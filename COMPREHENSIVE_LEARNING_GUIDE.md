# Complete E-Commerce Platform Learning Guide
## From Basic to Advanced - A to Z Journey

This comprehensive guide will take you through every aspect of this multi-vendor e-commerce platform, from basic concepts to advanced implementation details. Follow this step-by-step journey to master the entire system.

---

## 📚 Table of Contents

### **Phase 1: Foundation & Setup (Beginner)**
1. [Understanding the Architecture](#phase-1-foundation--setup)
2. [Development Environment Setup](#development-environment-setup)
3. [Basic Concepts & Technologies](#basic-concepts--technologies)
4. [Project Structure Overview](#project-structure-overview)

### **Phase 2: Backend Fundamentals (Beginner-Intermediate)**
5. [Django & REST Framework Basics](#django--rest-framework-basics)
6. [Database Design & Models](#database-design--models)
7. [Authentication System](#authentication-system)
8. [API Development](#api-development)

### **Phase 3: Frontend Fundamentals (Beginner-Intermediate)**
9. [Next.js & React Basics](#nextjs--react-basics)
10. [TypeScript Integration](#typescript-integration)
11. [UI Components & Styling](#ui-components--styling)
12. [State Management](#state-management)

### **Phase 4: Core E-Commerce Features (Intermediate)**
13. [Product Management System](#product-management-system)
14. [Shopping Cart & Checkout](#shopping-cart--checkout)
15. [Order Management](#order-management)
16. [Payment Integration](#payment-integration)
17. [Inventory Management](#inventory-management)

### **Phase 5: Advanced Features (Intermediate-Advanced)**
18. [Multi-Vendor System](#multi-vendor-system)
19. [Search & Elasticsearch](#search--elasticsearch)
20. [Real-time Features & WebSockets](#real-time-features--websockets)
21. [Analytics & Business Intelligence](#analytics--business-intelligence)
22. [Customer Analytics & ML](#customer-analytics--ml)

### **Phase 6: Enterprise Features (Advanced)**
23. [Multi-Tenant Architecture](#multi-tenant-architecture)
24. [Internationalization (i18n)](#internationalization-i18n)
25. [Workflow Automation](#workflow-automation)
26. [Security Management](#security-management)
27. [Performance Optimization](#performance-optimization)

### **Phase 7: DevOps & Production (Advanced)**
28. [Testing Strategies](#testing-strategies)
29. [Deployment & Docker](#deployment--docker)
30. [Monitoring & Maintenance](#monitoring--maintenance)
31. [Scaling & Optimization](#scaling--optimization)

---

## Phase 1: Foundation & Setup

### Understanding the Architecture

#### 1.1 High-Level Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (Django)      │◄──►│   (MySQL)       │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 3307    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         └──────────────►│  (Cache/Queue)  │◄─────────────┘
                        │   Port: 6379    │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ Elasticsearch   │
                        │   (Search)      │
                        │   Port: 9200    │
                        └─────────────────┘
```

**Key Components:**
- **Frontend**: Next.js 15.4.1 with React 19.1.0 (TypeScript)
- **Backend**: Django 4.2.7 with Django REST Framework 3.14.0
- **Database**: MySQL (primary) with connection pooling
- **Cache/Queue**: Redis 5.0.1 with Celery 5.3.4
- **Search**: Elasticsearch 8.11.1
- **Real-time**: Django Channels 4.0.0 with WebSockets

#### 1.2 Request Flow Understanding

```
User Request → Next.js Frontend → Django REST API → Database
                     ↓                    ↓              ↓
              UI Components → Serializers → Models → MySQL
                     ↓                    ↓              ↓
              State Management → Views → ORM Queries → Data
```

### Development Environment Setup

#### 2.1 Prerequisites Installation

**Required Software:**
```bash
# Node.js (v18 or higher)
node --version  # Should be 18+
npm --version   # Should be 9+

# Python (v3.8 or higher)
python --version  # Should be 3.8+
pip --version

# Docker & Docker Compose
docker --version
docker-compose --version

# MySQL (v8.0 or higher)
mysql --version

# Redis
redis-cli --version
```

#### 2.2 Project Setup Steps

**Step 1: Clone and Initial Setup**
```bash
# Navigate to project root
cd your-ecommerce-project

# Backend setup
cd backend
pip install -r requirements/development.txt
python manage.py migrate
python manage.py collectstatic

# Frontend setup
cd ../frontend
npm install
npm run build

# Docker setup (alternative)
cd ..
docker-compose up -d
```

**Step 2: Environment Configuration**
```bash
# Backend environment
cp backend/.env.example backend/.env
# Edit backend/.env with your settings

# Frontend environment
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with your settings
```

**Step 3: Database Setup**
```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/initial_data.json  # If available
```

#### 2.3 Development Workflow

**Daily Development Commands:**
```bash
# Terminal 1: Backend
cd backend
python manage.py runserver

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Redis (if not using Docker)
redis-server

# Terminal 4: Elasticsearch (if not using Docker)
elasticsearch
```

### Basic Concepts & Technologies

#### 3.1 Backend Technologies Deep Dive

**Django Framework Concepts:**
- **Models**: Database representation (ORM)
- **Views**: Business logic handlers
- **Serializers**: Data transformation (JSON ↔ Python)
- **URLs**: Route configuration
- **Middleware**: Request/response processing
- **Apps**: Modular application structure

**Django REST Framework Concepts:**
- **ViewSets**: CRUD operations handler
- **Permissions**: Access control
- **Authentication**: User verification
- **Pagination**: Large dataset handling
- **Filtering**: Data querying
- **Versioning**: API evolution

#### 3.2 Frontend Technologies Deep Dive

**Next.js Concepts:**
- **App Router**: File-based routing system
- **Server Components**: Server-side rendering
- **Client Components**: Client-side interactivity
- **API Routes**: Backend API endpoints
- **Middleware**: Request interception
- **Static Generation**: Pre-built pages

**React Concepts:**
- **Components**: Reusable UI elements
- **Hooks**: State and lifecycle management
- **Context**: Global state sharing
- **Props**: Component communication
- **State**: Component data management

#### 3.3 Database Concepts

**MySQL Features Used:**
- **ACID Transactions**: Data consistency
- **Indexing**: Query optimization
- **Foreign Keys**: Relational integrity
- **Connection Pooling**: Performance optimization
- **Replication**: High availability (configured)

**ORM Concepts:**
- **Models**: Python class → Database table
- **Migrations**: Schema version control
- **QuerySets**: Database query builders
- **Relationships**: Foreign keys, Many-to-many
- **Aggregations**: COUNT, SUM, AVG operations

### Project Structure Overview

#### 4.1 Backend Structure Analysis

```
backend/
├── ecommerce_project/          # Django project settings
│   ├── settings/              # Environment-specific settings
│   │   ├── base.py           # Base configuration
│   │   ├── development.py    # Development settings
│   │   └── production.py     # Production settings
│   ├── urls.py               # Main URL configuration
│   └── wsgi.py/asgi.py       # WSGI/ASGI applications
├── apps/                      # Django applications (30+ modules)
│   ├── authentication/       # User auth & JWT
│   ├── products/            # Product catalog
│   ├── orders/              # Order processing
│   ├── cart/                # Shopping cart
│   ├── inventory/           # Stock management
│   ├── customers/           # Customer management
│   ├── payments/            # Payment processing
│   ├── shipping/            # Logistics
│   ├── sellers/             # Multi-vendor
│   ├── analytics/           # Business analytics
│   ├── customer_analytics/  # ML analytics
│   ├── admin_panel/         # Admin interface
│   ├── system_settings/     # Configuration
│   ├── integrations/        # Third-party APIs
│   ├── notifications/       # Messaging system
│   ├── reviews/             # Product reviews
│   ├── search/              # Elasticsearch
│   ├── content/             # CMS
│   ├── chat/                # Real-time chat
│   ├── promotions/          # Coupons & deals
│   ├── forms/               # Dynamic forms
│   ├── api_management/      # API versioning
│   ├── communications/      # Email/SMS
│   ├── financial/           # Financial mgmt
│   ├── suppliers/           # Supplier mgmt
│   ├── pricing/             # Pricing strategies
│   ├── data_management/     # Import/export
│   ├── security_management/ # Security & audit
│   ├── workflow/            # Automation
│   ├── project_management/  # Task management
│   ├── tenants/             # Multi-tenant
│   └── internationalization/ # i18n support
├── core/                      # Core utilities
│   ├── middleware/           # Custom middleware
│   ├── exceptions.py         # Exception handlers
│   ├── pagination.py         # Custom pagination
│   └── versioning.py         # API versioning
├── tasks/                     # Celery tasks
└── requirements/              # Dependencies
```

#### 4.2 Frontend Structure Analysis

```
frontend/
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── (auth)/          # Auth route group
│   │   ├── (dashboard)/     # Dashboard routes
│   │   ├── admin/           # Admin routes
│   │   ├── seller/          # Seller routes
│   │   ├── api/             # API routes
│   │   ├── globals.css      # Global styles
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Home page
│   ├── components/           # React components
│   │   ├── ui/              # Base UI components
│   │   ├── forms/           # Form components
│   │   ├── charts/          # Chart components
│   │   ├── layout/          # Layout components
│   │   ├── auth/            # Auth components
│   │   ├── products/        # Product components
│   │   ├── orders/          # Order components
│   │   └── admin/           # Admin components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utility libraries
│   ├── store/               # Redux store
│   ├── types/               # TypeScript types
│   └── utils/               # Utility functions
├── public/                   # Static assets
└── config files             # Next.js, TypeScript, etc.
```

---

## Phase 2: Backend Fundamentals

### Django & REST Framework Basics

#### 5.1 Django Models Deep Dive

**Understanding Model Relationships:**

```python
# Example: Product Model Analysis
class Product(models.Model):
    # Basic fields
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Relationships
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # Many-to-One
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)     # Many-to-One
    tags = models.ManyToManyField(Tag, blank=True)                   # Many-to-Many
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category', 'is_active']),
        ]
        
    def __str__(self):
        return self.name
```

**Key Learning Points:**
- **Field Types**: CharField, TextField, DecimalField, DateTimeField, BooleanField
- **Relationships**: ForeignKey (Many-to-One), ManyToManyField (Many-to-Many)
- **Meta Options**: db_table, indexes, ordering
- **Model Methods**: __str__, custom methods
- **Validation**: clean(), custom validators

#### 5.2 Django REST Framework Serializers

**Serializer Patterns:**

```python
# Basic Serializer
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category_name', 'seller_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value
```

**Advanced Serializer Concepts:**
- **Nested Serializers**: Related object serialization
- **Custom Fields**: SerializerMethodField
- **Validation**: Field-level and object-level
- **Dynamic Fields**: Conditional field inclusion
- **Write Operations**: create(), update() methods

#### 5.3 ViewSets and API Views

**ViewSet Patterns:**

```python
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'seller')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'seller', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.filter(is_active=True)
        return queryset
        
    @action(detail=True, methods=['post'])
    def add_to_wishlist(self, request, pk=None):
        product = self.get_object()
        # Custom action logic
        return Response({'status': 'added to wishlist'})
```

**Key Concepts:**
- **CRUD Operations**: list, create, retrieve, update, destroy
- **Custom Actions**: @action decorator
- **Permissions**: Class-based and method-based
- **Filtering**: DjangoFilterBackend, SearchFilter
- **Optimization**: select_related, prefetch_related

### Database Design & Models

#### 6.1 Core E-Commerce Models

**User & Authentication Models:**

```python
# Custom User Model
class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    is_seller = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

# Customer Profile
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    preferences = models.JSONField(default=dict)
    loyalty_points = models.IntegerField(default=0)
```

**Product Catalog Models:**

```python
# Category Hierarchy
class Category(MPTTModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='categories/')
    is_active = models.BooleanField(default=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']

# Product with Variants
class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    seller = models.ForeignKey('sellers.Seller', on_delete=models.CASCADE)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100, unique=True)
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # e.g., "Red - Large"
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    attributes = models.JSONField(default=dict)  # {"color": "red", "size": "large"}
```

**Order Management Models:**

```python
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey('customers.Address', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
```

#### 6.2 Database Optimization Strategies

**Indexing Strategy:**
```python
class Product(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['category', 'is_active']),  # Filtering
            models.Index(fields=['seller', 'created_at']),   # Seller products
            models.Index(fields=['name']),                   # Search
            models.Index(fields=['-created_at']),            # Recent products
        ]
```

**Query Optimization:**
```python
# Bad: N+1 Query Problem
products = Product.objects.all()
for product in products:
    print(product.category.name)  # Database hit for each product

# Good: Use select_related
products = Product.objects.select_related('category', 'seller').all()
for product in products:
    print(product.category.name)  # No additional database hits

# Good: Use prefetch_related for reverse relationships
orders = Order.objects.prefetch_related('items__product_variant__product').all()
```

### Authentication System

#### 7.1 JWT Authentication Implementation

**JWT Configuration Analysis:**
```python
# settings/base.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

**Authentication Views:**
```python
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=400)
```

#### 7.2 Permission System

**Custom Permissions:**
```python
class IsSellerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_seller
        
class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user
```

#### 7.3 Security Middleware

**Rate Limiting Middleware:**
```python
class AuthenticationRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if self.is_auth_endpoint(request.path):
            if self.is_rate_limited(request):
                return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        return self.get_response(request)
```

### API Development

#### 8.1 API Versioning Strategy

**URL Path Versioning:**
```python
# urls.py
urlpatterns = [
    path('api/v1/', include('api.v1.urls')),
    path('api/v2/', include('api.v2.urls')),
]

# Versioning in views
class ProductViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.request.version == 'v2':
            return ProductV2Serializer
        return ProductSerializer
```

#### 8.2 API Documentation

**OpenAPI Schema Generation:**
```python
# Using drf-spectacular
@extend_schema(
    summary="Create a new product",
    description="Creates a new product in the catalog",
    request=ProductCreateSerializer,
    responses={201: ProductSerializer},
    tags=['Products']
)
def create(self, request, *args, **kwargs):
    return super().create(request, *args, **kwargs)
```

---

## Phase 3: Frontend Fundamentals

### Next.js & React Basics

#### 9.1 Next.js App Router Structure

**Route Organization:**
```
src/app/
├── (auth)/                 # Route group (doesn't affect URL)
│   ├── login/
│   │   └── page.tsx       # /login
│   └── register/
│       └── page.tsx       # /register
├── products/
│   ├── page.tsx           # /products
│   ├── [id]/
│   │   └── page.tsx       # /products/[id]
│   └── category/
│       └── [slug]/
│           └── page.tsx   # /products/category/[slug]
├── api/
│   └── auth/
│       └── route.ts       # API endpoint
├── layout.tsx             # Root layout
└── page.tsx              # Home page (/)
```

**Page Component Example:**
```tsx
// app/products/page.tsx
import { Metadata } from 'next'
import ProductList from '@/components/products/ProductList'

export const metadata: Metadata = {
  title: 'Products | E-Commerce Platform',
  description: 'Browse our extensive product catalog',
}

interface ProductsPageProps {
  searchParams: {
    category?: string
    search?: string
    page?: string
  }
}

export default async function ProductsPage({ searchParams }: ProductsPageProps) {
  const products = await fetchProducts(searchParams)
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Products</h1>
      <ProductList products={products} />
    </div>
  )
}
```

#### 9.2 Server vs Client Components

**Server Component (Default):**
```tsx
// Runs on server, can access backend directly
async function ProductDetails({ id }: { id: string }) {
  const product = await fetch(`${API_URL}/products/${id}`)
  
  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
    </div>
  )
}
```

**Client Component:**
```tsx
'use client'

import { useState, useEffect } from 'react'

function AddToCartButton({ productId }: { productId: string }) {
  const [isLoading, setIsLoading] = useState(false)
  
  const handleAddToCart = async () => {
    setIsLoading(true)
    try {
      await addToCart(productId)
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <button 
      onClick={handleAddToCart}
      disabled={isLoading}
      className="bg-blue-500 text-white px-4 py-2 rounded"
    >
      {isLoading ? 'Adding...' : 'Add to Cart'}
    </button>
  )
}
```

#### 9.3 Data Fetching Patterns

**Server-Side Data Fetching:**
```tsx
// app/products/[id]/page.tsx
async function getProduct(id: string) {
  const res = await fetch(`${process.env.API_URL}/products/${id}`, {
    next: { revalidate: 3600 } // Cache for 1 hour
  })
  
  if (!res.ok) {
    throw new Error('Failed to fetch product')
  }
  
  return res.json()
}

export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await getProduct(params.id)
  
  return <ProductDetails product={product} />
}
```

**Client-Side Data Fetching with SWR:**
```tsx
'use client'

import useSWR from 'swr'

function ProductReviews({ productId }: { productId: string }) {
  const { data: reviews, error, mutate } = useSWR(
    `/api/products/${productId}/reviews`,
    fetcher
  )
  
  if (error) return <div>Failed to load reviews</div>
  if (!reviews) return <div>Loading...</div>
  
  return (
    <div>
      {reviews.map(review => (
        <ReviewCard key={review.id} review={review} />
      ))}
    </div>
  )
}
```

### TypeScript Integration

#### 10.1 Type Definitions

**API Response Types:**
```typescript
// types/api.ts
export interface Product {
  id: string
  name: string
  description: string
  price: number
  category: Category
  seller: Seller
  images: ProductImage[]
  variants: ProductVariant[]
  created_at: string
  updated_at: string
}

export interface Category {
  id: string
  name: string
  slug: string
  parent?: Category
  children?: Category[]
}

export interface ProductVariant {
  id: string
  name: string
  sku: string
  price: number
  stock_quantity: number
  attributes: Record<string, string>
}

// API Response wrapper
export interface ApiResponse<T> {
  data: T
  message?: string
  errors?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  results: T[]
  count: number
  next: string | null
  previous: string | null
}
```

**Component Props Types:**
```typescript
// components/products/ProductCard.tsx
interface ProductCardProps {
  product: Product
  onAddToCart?: (productId: string) => void
  onAddToWishlist?: (productId: string) => void
  showQuickView?: boolean
  className?: string
}

export default function ProductCard({
  product,
  onAddToCart,
  onAddToWishlist,
  showQuickView = true,
  className = ''
}: ProductCardProps) {
  // Component implementation
}
```

#### 10.2 Custom Hooks with TypeScript

**API Hook:**
```typescript
// hooks/useApi.ts
import { useState, useEffect } from 'react'

interface UseApiResult<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useApi<T>(url: string): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch')
      const result = await response.json()
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    fetchData()
  }, [url])
  
  return { data, loading, error, refetch: fetchData }
}
```

**Shopping Cart Hook:**
```typescript
// hooks/useCart.ts
interface CartItem {
  id: string
  product: Product
  variant?: ProductVariant
  quantity: number
}

interface UseCartResult {
  items: CartItem[]
  totalItems: number
  totalPrice: number
  addItem: (product: Product, variant?: ProductVariant, quantity?: number) => void
  removeItem: (itemId: string) => void
  updateQuantity: (itemId: string, quantity: number) => void
  clearCart: () => void
}

export function useCart(): UseCartResult {
  // Implementation
}
```

### UI Components & Styling

#### 11.1 Tailwind CSS Integration

**Configuration:**
```javascript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        secondary: {
          50: '#f8fafc',
          500: '#64748b',
          600: '#475569',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

#### 11.2 Component Library Structure

**Base UI Components:**
```tsx
// components/ui/Button.tsx
import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, children, ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          'disabled:pointer-events-none disabled:opacity-50',
          {
            'bg-primary-600 text-white hover:bg-primary-700': variant === 'primary',
            'bg-secondary-100 text-secondary-900 hover:bg-secondary-200': variant === 'secondary',
            'border border-input bg-background hover:bg-accent': variant === 'outline',
            'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
          },
          {
            'h-9 px-3 text-sm': size === 'sm',
            'h-10 px-4 py-2': size === 'md',
            'h-11 px-8 text-lg': size === 'lg',
          },
          className
        )}
        ref={ref}
        disabled={loading}
        {...props}
      >
        {loading && <Spinner className="mr-2 h-4 w-4" />}
        {children}
      </button>
    )
  }
)
```

**Form Components:**
```tsx
// components/ui/Input.tsx
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

export function Input({ label, error, helperText, className, ...props }: InputProps) {
  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          {label}
        </label>
      )}
      <input
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
          'ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium',
          'placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2',
          'focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          error && 'border-red-500 focus-visible:ring-red-500',
          className
        )}
        {...props}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      {helperText && !error && <p className="text-sm text-muted-foreground">{helperText}</p>}
    </div>
  )
}
```

#### 11.3 Material-UI Integration

**Theme Configuration:**
```tsx
// lib/theme.ts
import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  palette: {
    primary: {
      main: '#3b82f6',
      light: '#60a5fa',
      dark: '#1d4ed8',
    },
    secondary: {
      main: '#64748b',
      light: '#94a3b8',
      dark: '#334155',
    },
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '0.5rem',
        },
      },
    },
  },
})
```

### State Management

#### 12.1 Redux Toolkit Setup

**Store Configuration:**
```typescript
// store/index.ts
import { configureStore } from '@reduxjs/toolkit'
import { authApi } from './api/authApi'
import { productsApi } from './api/productsApi'
import { cartApi } from './api/cartApi'
import authSlice from './slices/authSlice'
import cartSlice from './slices/cartSlice'
import uiSlice from './slices/uiSlice'

export const store = configureStore({
  reducer: {
    auth: authSlice,
    cart: cartSlice,
    ui: uiSlice,
    [authApi.reducerPath]: authApi.reducer,
    [productsApi.reducerPath]: productsApi.reducer,
    [cartApi.reducerPath]: cartApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      authApi.middleware,
      productsApi.middleware,
      cartApi.middleware
    ),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
```

**RTK Query API Slice:**
```typescript
// store/api/productsApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { Product, PaginatedResponse } from '@/types/api'

export const productsApi = createApi({
  reducerPath: 'productsApi',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1/products/',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token
      if (token) {
        headers.set('authorization', `Bearer ${token}`)
      }
      return headers
    },
  }),
  tagTypes: ['Product'],
  endpoints: (builder) => ({
    getProducts: builder.query<PaginatedResponse<Product>, {
      page?: number
      category?: string
      search?: string
    }>({
      query: (params) => ({
        url: '',
        params,
      }),
      providesTags: ['Product'],
    }),
    getProduct: builder.query<Product, string>({
      query: (id) => `${id}/`,
      providesTags: (result, error, id) => [{ type: 'Product', id }],
    }),
    createProduct: builder.mutation<Product, Partial<Product>>({
      query: (product) => ({
        url: '',
        method: 'POST',
        body: product,
      }),
      invalidatesTags: ['Product'],
    }),
  }),
})

export const { useGetProductsQuery, useGetProductQuery, useCreateProductMutation } = productsApi
```

**Auth Slice:**
```typescript
// store/slices/authSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface User {
  id: string
  email: string
  username: string
  is_seller: boolean
  is_premium: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
}

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  loading: false,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.loading = true
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.user = action.payload.user
      state.token = action.payload.token
      state.isAuthenticated = true
      state.loading = false
    },
    loginFailure: (state) => {
      state.loading = false
    },
    logout: (state) => {
      state.user = null
      state.token = null
      state.isAuthenticated = false
    },
  },
})

export const { loginStart, loginSuccess, loginFailure, logout } = authSlice.actions
export default authSlice.reducer
```

#### 12.2 React Query Integration

**Query Client Setup:**
```tsx
// app/providers.tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        cacheTime: 10 * 60 * 1000, // 10 minutes
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

**Custom Query Hooks:**
```typescript
// hooks/queries/useProducts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi } from '@/lib/api'

export function useProducts(filters?: ProductFilters) {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => productsApi.getProducts(filters),
    keepPreviousData: true,
  })
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: ['product', id],
    queryFn: () => productsApi.getProduct(id),
    enabled: !!id,
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: productsApi.createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
```

---

This completes the first major section of the learning guide. The guide continues with Phase 4 (Core E-Commerce Features), Phase 5 (Advanced Features), Phase 6 (Enterprise Features), and Phase 7 (DevOps & Production), each with the same level of detail and practical examples.

Would you like me to continue with the next phases of the learning guide?