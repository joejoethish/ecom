# Design Document

## Overview

The Dynamic Categories system provides a comprehensive category management solution with hierarchical organization, real-time updates, and multi-role access. The system supports unlimited nesting levels, drag-and-drop reordering, and seamless integration with the existing product catalog.

## Architecture

### System Components
1. **Category Management API**: RESTful endpoints for CRUD operations
2. **Hierarchical Data Model**: Nested set model for efficient tree operations
3. **Admin Interface**: React-based category management dashboard
4. **Frontend Integration**: Category navigation and product filtering
5. **Real-time Updates**: WebSocket integration for live category changes
6. **Audit System**: Comprehensive logging and change tracking

### Data Flow
1. **Admin Operations**: Admin creates/edits categories → API validates → Database updates → Real-time broadcast
2. **Frontend Display**: User requests categories → API returns hierarchy → Frontend renders navigation
3. **Product Association**: Seller assigns categories → Validation → Database update → Search index update

## Components and Interfaces

### Backend Components

#### 1. Category Model (Enhanced Nested Set)
```python
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    
    # Nested set model fields for efficient tree operations
    lft = models.PositiveIntegerField()
    rght = models.PositiveIntegerField()
    tree_id = models.PositiveIntegerField()
    level = models.PositiveIntegerField()
    
    # Metadata fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

#### 2. Category Audit Model
```python
class CategoryAudit(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    action = models.CharField(max_length=20)  # CREATE, UPDATE, DELETE, MOVE
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    old_values = models.JSONField(null=True)
    new_values = models.JSONField(null=True)
    ip_address = models.GenericIPAddressField()
```

#### 3. Product-Category Association
```python
class ProductCategory(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

#### 4. Category Service Layer
```python
class CategoryService:
    def create_category(self, data, user):
        # Validate data, generate slug, insert into tree
    
    def update_category(self, category_id, data, user):
        # Update category, handle parent changes, audit log
    
    def delete_category(self, category_id, user, reassign_to=None):
        # Check dependencies, reassign products, remove from tree
    
    def move_category(self, category_id, new_parent_id, user):
        # Validate move, update tree structure, audit log
    
    def get_category_tree(self, include_inactive=False):
        # Return hierarchical category structure
    
    def get_category_breadcrumbs(self, category_id):
        # Return path from root to category
```

#### 5. API Endpoints
- `GET /api/v1/categories/`: List categories with hierarchy
- `POST /api/v1/categories/`: Create new category
- `GET /api/v1/categories/{id}/`: Get category details
- `PUT /api/v1/categories/{id}/`: Update category
- `DELETE /api/v1/categories/{id}/`: Delete category
- `POST /api/v1/categories/{id}/move/`: Move category in hierarchy
- `GET /api/v1/categories/{id}/products/`: Get products in category
- `GET /api/v1/categories/audit/`: Get audit logs

### Frontend Components

#### 1. Category Management Dashboard
```typescript
interface CategoryManagerProps {
  categories: CategoryTree[];
  onCategoryCreate: (data: CategoryFormData) => void;
  onCategoryUpdate: (id: string, data: CategoryFormData) => void;
  onCategoryDelete: (id: string, reassignTo?: string) => void;
  onCategoryMove: (id: string, newParentId: string) => void;
}

const CategoryManager: React.FC<CategoryManagerProps> = ({...}) => {
  // Tree view with drag-and-drop
  // Category form modal
  // Bulk operations
  // Search and filtering
};
```

#### 2. Category Tree Component
```typescript
interface CategoryTreeProps {
  categories: CategoryNode[];
  selectedCategory?: string;
  onCategorySelect: (category: CategoryNode) => void;
  onCategoryMove?: (draggedId: string, targetId: string) => void;
  isDragEnabled?: boolean;
}

const CategoryTree: React.FC<CategoryTreeProps> = ({...}) => {
  // Recursive tree rendering
  // Drag and drop functionality
  // Expand/collapse states
  // Context menu actions
};
```

#### 3. Category Form Component
```typescript
interface CategoryFormProps {
  category?: Category;
  parentCategories: Category[];
  onSubmit: (data: CategoryFormData) => void;
  onCancel: () => void;
}

const CategoryForm: React.FC<CategoryFormProps> = ({...}) => {
  // Form validation
  // Image upload
  // Parent category selection
  // SEO metadata fields
};
```

#### 4. Frontend Category Navigation
```typescript
interface CategoryNavigationProps {
  categories: CategoryTree[];
  currentCategory?: string;
  onCategorySelect: (categoryId: string) => void;
}

const CategoryNavigation: React.FC<CategoryNavigationProps> = ({...}) => {
  // Hierarchical menu
  // Breadcrumb navigation
  // Mobile-responsive design
  // Search integration
};
```

## Data Models

### Database Schema

#### categories
```sql
CREATE TABLE categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    image VARCHAR(255),
    parent_id BIGINT,
    lft INT UNSIGNED NOT NULL,
    rght INT UNSIGNED NOT NULL,
    tree_id INT UNSIGNED NOT NULL,
    level INT UNSIGNED NOT NULL,
    meta_title VARCHAR(200),
    meta_description TEXT,
    display_order INT UNSIGNED DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    created_by_id BIGINT,
    INDEX idx_parent (parent_id),
    INDEX idx_tree (tree_id, lft, rght),
    INDEX idx_slug (slug),
    INDEX idx_active (is_active),
    INDEX idx_featured (is_featured),
    FOREIGN KEY (parent_id) REFERENCES categories(id),
    FOREIGN KEY (created_by_id) REFERENCES auth_user(id)
);
```

#### category_audit
```sql
CREATE TABLE category_audit (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category_id BIGINT NOT NULL,
    action VARCHAR(20) NOT NULL,
    user_id BIGINT,
    timestamp DATETIME NOT NULL,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    INDEX idx_category_timestamp (category_id, timestamp),
    INDEX idx_user_timestamp (user_id, timestamp),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);
```

#### product_categories
```sql
CREATE TABLE product_categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    assigned_at DATETIME NOT NULL,
    assigned_by_id BIGINT,
    UNIQUE KEY unique_product_category (product_id, category_id),
    INDEX idx_product (product_id),
    INDEX idx_category (category_id),
    INDEX idx_primary (is_primary),
    FOREIGN KEY (product_id) REFERENCES products_product(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (assigned_by_id) REFERENCES auth_user(id)
);
```

### API Response Formats

#### Category Tree Response
```typescript
interface CategoryTreeResponse {
  success: boolean;
  data: {
    categories: CategoryNode[];
    total_count: number;
  };
}

interface CategoryNode {
  id: string;
  name: string;
  slug: string;
  description?: string;
  image?: string;
  level: number;
  is_active: boolean;
  is_featured: boolean;
  product_count: number;
  children: CategoryNode[];
  breadcrumbs: BreadcrumbItem[];
}
```

#### Category Form Data
```typescript
interface CategoryFormData {
  name: string;
  slug?: string;
  description?: string;
  parent_id?: string;
  image?: File;
  meta_title?: string;
  meta_description?: string;
  display_order?: number;
  is_active: boolean;
  is_featured: boolean;
}
```

## Error Handling

### Backend Error Scenarios
1. **Circular Reference**: Prevent category from being its own ancestor
2. **Slug Conflicts**: Handle duplicate slugs within same parent
3. **Orphaned Products**: Manage products when categories are deleted
4. **Tree Corruption**: Detect and repair nested set inconsistencies
5. **Concurrent Modifications**: Handle simultaneous category updates

### Frontend Error Handling
1. **Network Failures**: Retry with exponential backoff
2. **Validation Errors**: Display field-specific error messages
3. **Permission Denied**: Redirect to appropriate access level
4. **Tree Loading Failures**: Show partial tree with error indicators
5. **Image Upload Failures**: Provide alternative upload methods

### Error Codes
- `CATEGORY_NOT_FOUND`: Category ID doesn't exist
- `CIRCULAR_REFERENCE`: Parent assignment would create loop
- `SLUG_CONFLICT`: Slug already exists in parent
- `HAS_PRODUCTS`: Category has associated products
- `HAS_SUBCATEGORIES`: Category has child categories
- `TREE_CORRUPTION`: Nested set model inconsistency

## Testing Strategy

### Backend Testing

#### Unit Tests
- Category model validation and constraints
- Nested set tree operations (insert, move, delete)
- Slug generation and uniqueness
- Audit logging functionality
- Permission checking logic

#### Integration Tests
- API endpoint responses and error handling
- Database transaction integrity
- File upload and image processing
- WebSocket real-time updates
- Search index synchronization

#### Performance Tests
- Large category tree loading
- Bulk category operations
- Concurrent user modifications
- Database query optimization
- Memory usage with deep hierarchies

### Frontend Testing

#### Component Tests
- Category tree rendering and interaction
- Form validation and submission
- Drag and drop functionality
- Modal and dialog behavior
- Responsive design adaptation

#### Integration Tests
- API service integration
- State management updates
- Route navigation
- Real-time update handling
- Error boundary behavior

#### E2E Tests
- Complete category management workflow
- Product assignment process
- Frontend navigation experience
- Admin permission enforcement
- Mobile device compatibility

## Security Considerations

### Access Control
- Role-based permissions for category management
- Seller restrictions on category assignment
- Admin-only access to system categories
- Audit trail for all modifications
- IP-based access logging

### Data Validation
- Input sanitization for all text fields
- Image file type and size validation
- Slug format enforcement
- HTML content filtering in descriptions
- SQL injection prevention

### Performance Optimization
- Database indexing for tree queries
- Caching of category hierarchies
- Lazy loading of deep tree branches
- Image optimization and CDN integration
- Search index optimization