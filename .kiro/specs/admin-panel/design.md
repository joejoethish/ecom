# Design Document

## Overview

The Admin Panel is a comprehensive administrative interface built as a separate React application with role-based access control, real-time monitoring capabilities, and integrated management tools. The system provides a unified dashboard for managing users, products, orders, analytics, and system configuration while maintaining security and performance.

## Architecture

### System Architecture
1. **Admin Frontend**: Dedicated React application with admin-specific routing
2. **Admin API Layer**: Specialized endpoints with enhanced permissions and data access
3. **Real-time Dashboard**: WebSocket integration for live metrics and notifications
4. **Analytics Engine**: Data aggregation and reporting system
5. **Security Layer**: Enhanced authentication, audit logging, and access control
6. **Integration Hub**: Connections to payment, shipping, and third-party services

### Access Control Model
- **Super Admin**: Full system access including user management and system configuration
- **Admin**: Product, order, and seller management with limited system settings
- **Moderator**: Content moderation and basic user support capabilities
- **Analyst**: Read-only access to analytics and reporting features

## Components and Interfaces

### Backend Components

#### 1. Admin User Model (Extended)
```python
class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ADMIN_ROLES)
    permissions = models.JSONField(default=dict)
    last_login_ip = models.GenericIPAddressField(null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True)
    created_by = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 2. Admin Activity Log
```python
class AdminActivityLog(models.Model):
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100)
    details = models.JSONField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
```

#### 3. System Configuration Model
```python
class SystemConfiguration(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField()
    category = models.CharField(max_length=50)
    is_sensitive = models.BooleanField(default=False)
    updated_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 4. Admin Dashboard Service
```python
class AdminDashboardService:
    def get_dashboard_metrics(self):
        # Real-time KPIs, sales data, user metrics
    
    def get_recent_activities(self, limit=50):
        # Recent orders, user registrations, system events
    
    def get_system_health(self):
        # Server metrics, database performance, error rates
    
    def get_security_alerts(self):
        # Failed logins, suspicious activities, security events
    
    def generate_report(self, report_type, date_range, filters):
        # Custom report generation with export capabilities
```

#### 5. Admin API Endpoints
- `GET /api/v1/admin/dashboard/`: Dashboard metrics and overview
- `GET /api/v1/admin/users/`: User management with advanced filtering
- `GET /api/v1/admin/products/`: Product oversight and moderation
- `GET /api/v1/admin/orders/`: Order management and dispute resolution
- `GET /api/v1/admin/sellers/`: Seller management and performance
- `GET /api/v1/admin/analytics/`: Analytics and reporting
- `GET /api/v1/admin/system/`: System configuration and settings
- `GET /api/v1/admin/security/`: Security monitoring and logs
- `POST /api/v1/admin/actions/`: Bulk operations and system actions

### Frontend Components

#### 1. Admin Layout and Navigation
```typescript
interface AdminLayoutProps {
  user: AdminUser;
  currentPath: string;
  notifications: Notification[];
}

const AdminLayout: React.FC<AdminLayoutProps> = ({...}) => {
  // Sidebar navigation with role-based menu items
  // Top bar with user info and notifications
  // Breadcrumb navigation
  // Real-time notification system
};
```

#### 2. Dashboard Overview
```typescript
interface DashboardProps {
  metrics: DashboardMetrics;
  recentActivities: Activity[];
  systemHealth: SystemHealth;
  securityAlerts: SecurityAlert[];
}

const Dashboard: React.FC<DashboardProps> = ({...}) => {
  // KPI cards with real-time updates
  // Charts and graphs for key metrics
  // Recent activity feed
  // System status indicators
  // Quick action buttons
};
```

#### 3. User Management Interface
```typescript
interface UserManagementProps {
  users: User[];
  filters: UserFilters;
  onUserAction: (userId: string, action: UserAction) => void;
  onBulkAction: (userIds: string[], action: BulkAction) => void;
}

const UserManagement: React.FC<UserManagementProps> = ({...}) => {
  // Advanced filtering and search
  // User details modal with activity history
  // Bulk operations for user management
  // Role and permission management
  // User communication tools
};
```

#### 4. Product Moderation Interface
```typescript
interface ProductModerationProps {
  products: Product[];
  pendingReviews: ProductReview[];
  reportedProducts: ProductReport[];
  onProductAction: (productId: string, action: ProductAction) => void;
}

const ProductModeration: React.FC<ProductModerationProps> = ({...}) => {
  // Product approval/rejection workflow
  // Bulk product operations
  // Product report handling
  // Inventory monitoring
  // Category management integration
};
```

#### 5. Analytics and Reporting
```typescript
interface AnalyticsProps {
  dateRange: DateRange;
  selectedMetrics: string[];
  onDateRangeChange: (range: DateRange) => void;
  onExportReport: (format: ExportFormat) => void;
}

const Analytics: React.FC<AnalyticsProps> = ({...}) => {
  // Interactive charts and graphs
  // Custom report builder
  // Data export functionality
  // Real-time metric updates
  // Comparative analysis tools
};
```

## Data Models

### Database Schema

#### admin_users
```sql
CREATE TABLE admin_users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL,
    permissions JSON,
    last_login_ip VARCHAR(45),
    failed_login_attempts INT UNSIGNED DEFAULT 0,
    is_locked BOOLEAN DEFAULT FALSE,
    locked_until DATETIME,
    created_by_id BIGINT,
    created_at DATETIME NOT NULL,
    INDEX idx_role (role),
    INDEX idx_locked (is_locked, locked_until),
    FOREIGN KEY (user_id) REFERENCES auth_user(id),
    FOREIGN KEY (created_by_id) REFERENCES admin_users(id)
);
```

#### admin_activity_logs
```sql
CREATE TABLE admin_activity_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    admin_user_id BIGINT NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100) NOT NULL,
    details JSON,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    timestamp DATETIME NOT NULL,
    success BOOLEAN DEFAULT TRUE,
    INDEX idx_admin_timestamp (admin_user_id, timestamp),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_action_timestamp (action, timestamp),
    FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
);
```

#### system_configurations
```sql
CREATE TABLE system_configurations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSON NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    is_sensitive BOOLEAN DEFAULT FALSE,
    updated_by_id BIGINT,
    updated_at DATETIME NOT NULL,
    INDEX idx_category (category),
    INDEX idx_key (key),
    FOREIGN KEY (updated_by_id) REFERENCES admin_users(id)
);
```

### API Response Formats

#### Dashboard Metrics Response
```typescript
interface DashboardMetricsResponse {
  success: boolean;
  data: {
    kpis: {
      total_users: number;
      active_users_today: number;
      total_orders: number;
      revenue_today: number;
      pending_products: number;
      active_sellers: number;
    };
    charts: {
      sales_trend: ChartData[];
      user_growth: ChartData[];
      order_status: PieChartData[];
    };
    recent_activities: Activity[];
    system_health: SystemHealthStatus;
  };
}
```

#### User Management Response
```typescript
interface UserManagementResponse {
  success: boolean;
  data: {
    users: AdminUserView[];
    pagination: PaginationInfo;
    filters: AvailableFilters;
    summary: UserSummaryStats;
  };
}

interface AdminUserView {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  last_login: string;
  registration_date: string;
  order_count: number;
  total_spent: number;
  is_seller: boolean;
}
```

## Error Handling

### Backend Error Scenarios
1. **Permission Denied**: Insufficient admin privileges for action
2. **Resource Not Found**: Requested user/product/order doesn't exist
3. **Concurrent Modification**: Multiple admins editing same resource
4. **System Configuration Error**: Invalid configuration values
5. **External Service Failure**: Payment/shipping service unavailable

### Frontend Error Handling
1. **Authentication Failures**: Session timeout and re-authentication
2. **Permission Errors**: Graceful degradation of UI features
3. **Network Issues**: Offline mode and retry mechanisms
4. **Data Loading Failures**: Skeleton states and error boundaries
5. **Bulk Operation Failures**: Partial success handling and rollback

### Error Codes
- `ADMIN_PERMISSION_DENIED`: Insufficient admin privileges
- `RESOURCE_LOCKED`: Resource being modified by another admin
- `BULK_OPERATION_PARTIAL`: Some items in bulk operation failed
- `SYSTEM_CONFIG_INVALID`: Configuration validation failed
- `AUDIT_LOG_FAILURE`: Failed to log admin action

## Testing Strategy

### Backend Testing

#### Unit Tests
- Admin permission checking logic
- Dashboard metric calculations
- System configuration validation
- Audit logging functionality
- Bulk operation processing

#### Integration Tests
- Admin API endpoint responses
- Role-based access control
- Real-time notification delivery
- External service integrations
- Database transaction integrity

#### Security Tests
- Admin authentication and authorization
- Audit trail completeness
- Sensitive data protection
- SQL injection prevention
- XSS protection in admin interface

### Frontend Testing

#### Component Tests
- Admin dashboard rendering
- User management interactions
- Form validation and submission
- Real-time update handling
- Role-based UI rendering

#### Integration Tests
- Admin API service integration
- Navigation and routing
- State management updates
- WebSocket connection handling
- Error boundary behavior

#### E2E Tests
- Complete admin workflows
- User management processes
- Product moderation flows
- Report generation and export
- Security and access control

## Security Considerations

### Access Control
- Multi-factor authentication for admin accounts
- Role-based permission system with granular controls
- IP-based access restrictions for sensitive operations
- Session management with automatic timeout
- Admin action approval workflows for critical operations

### Audit and Monitoring
- Comprehensive logging of all admin actions
- Real-time security monitoring and alerting
- Failed login attempt tracking and lockout
- Suspicious activity detection and response
- Regular security audit reports

### Data Protection
- Encryption of sensitive configuration data
- Secure handling of user personal information
- Data anonymization for deleted users
- Backup and recovery procedures
- Compliance with data protection regulations

### Performance and Scalability
- Efficient database queries with proper indexing
- Caching of frequently accessed admin data
- Real-time update optimization
- Bulk operation performance tuning
- Monitoring and alerting for system performance