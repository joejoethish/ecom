# MySQL Database Integration Guide

This guide explains how to set up and use the MySQL database integration for the ecommerce platform.

## Overview

The platform has been configured to use MySQL as the primary database, replacing static data with dynamic data from the database. This integration includes:

- MySQL database configuration
- Dynamic API endpoints for categories and products
- Frontend services to consume dynamic data
- Database health monitoring and optimization tools

## Prerequisites

1. **MySQL Server**: Ensure MySQL server is installed and running
   - Version: MySQL 5.7+ or MySQL 8.0+
   - Port: 3307 (configurable)
   - User: root with password 'root' (configurable)

2. **Python Dependencies**: All required packages are in `requirements/base.txt`
   - `mysqlclient==2.2.0` for MySQL connectivity
   - Django MySQL backend support

## Quick Setup

### 1. Database Setup

Run the automated setup script:

```bash
cd backend
python manage.py setup_mysql
```

This will:
- Check database connection
- Run Django migrations
- Create a superuser (admin@example.com / admin123)
- Populate sample data

### 2. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Create database
mysql -u root -p -P 3307 -h 127.0.0.1
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 2. Run migrations
python manage.py makemigrations
python manage.py migrate

# 3. Create superuser
python manage.py createsuperuser

# 4. Populate sample data
python manage.py populate_sample_data
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
DB_NAME=ecommerce_db
DB_USER=root
DB_PASSWORD=root
DB_HOST=127.0.0.1
DB_PORT=3307
```

### Database Settings

The database configuration is in `ecommerce_project/settings/base.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='ecommerce_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default='root'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3307'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True,
            'sql_mode': 'STRICT_TRANS_TABLES',
            'isolation_level': 'read committed',
        },
        'CONN_MAX_AGE': 60,  # Connection pooling
        'CONN_HEALTH_CHECKS': True,
    }
}
```

## Dynamic Data APIs

### Categories API

- `GET /api/v1/categories/` - Get all categories
- `GET /api/v1/categories/featured/` - Get featured categories
- `GET /api/v1/categories/{slug}/` - Get category details
- `GET /api/v1/categories/{slug}/filters/` - Get category filters

### Products API

- `GET /api/v1/products/featured/` - Get featured products
- `GET /api/v1/products/category/{slug}/` - Get products by category
- `GET /api/v1/products/search/?q={query}` - Search products

## Frontend Integration

### Services

The frontend includes services to consume dynamic data:

- `frontend/src/services/categoriesApi.ts` - Categories API service
- `frontend/src/services/productsApi.ts` - Products API service

### React Hooks

Custom hooks for data fetching:

- `frontend/src/hooks/useCategories.ts` - Categories data hooks
- `frontend/src/hooks/useProducts.ts` - Products data hooks

### Usage Example

```typescript
import { useCategories } from '@/hooks/useCategories';

function HomePage() {
  const { featuredCategories, loading, error } = useCategories({
    featured: true,
    autoFetch: true
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {featuredCategories.map(category => (
        <div key={category.id}>
          {category.name} ({category.product_count} products)
        </div>
      ))}
    </div>
  );
}
```

## Database Health Monitoring

### Health Check

```python
from core.database import DatabaseHealthChecker

# Check connection health
health_info = DatabaseHealthChecker.check_connection()
print(health_info)

# Get database statistics
stats = DatabaseHealthChecker.get_database_stats()
print(f"Database size: {stats['database_size_mb']} MB")
print(f"Active connections: {stats['active_connections']}")
```

### Management Commands

```bash
# Check database health
python manage.py shell -c "from core.database import DatabaseHealthChecker; print(DatabaseHealthChecker.check_connection())"

# Get database stats
python manage.py shell -c "from core.database import DatabaseHealthChecker; print(DatabaseHealthChecker.get_database_stats())"
```

## Sample Data

The platform includes comprehensive sample data:

### Categories
- Electronics (with icon 💻)
- Fashion (with icon 👗)
- Home & Kitchen (with icon 🏠)
- Books (with icon 📚)
- Sports (with icon ⚽)
- Beauty (with icon 💄)

### Products
- iPhone 15 Pro ($999.99, discounted to $899.99)
- Samsung Galaxy S24 ($849.99)
- MacBook Air M3 ($1299.99)
- Nike Air Max 270 ($150.00, discounted to $120.00)
- Instant Pot Duo 7-in-1 ($99.99)
- The Great Gatsby ($12.99)

### Users
- Admin: admin@example.com / admin123
- Customers: john@example.com, jane@example.com, bob@example.com (password: password123)

### Reviews
- 2-5 reviews per product with ratings 3-5 stars

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if MySQL server is running
   - Verify host and port settings
   - Check firewall settings

2. **Authentication Failed**
   - Verify username and password
   - Check user permissions
   - Ensure user can connect from the specified host

3. **Database Not Found**
   - Create the database manually
   - Run the setup script
   - Check database name in settings

4. **Migration Errors**
   - Drop and recreate the database
   - Delete migration files and recreate them
   - Check for conflicting migrations

### Debug Commands

```bash
# Test database connection
python manage.py dbshell

# Check migration status
python manage.py showmigrations

# Create fresh migrations
python manage.py makemigrations --empty appname

# Reset database (CAUTION: This will delete all data)
python manage.py flush
```

## Performance Optimization

### Connection Pooling
- Configured with `CONN_MAX_AGE: 60` seconds
- Automatic connection health checks enabled

### Query Optimization
- Proper indexing on frequently queried fields
- Use of `select_related()` and `prefetch_related()`
- Database query logging in development

### Caching
- Consider implementing Redis caching for frequently accessed data
- Use Django's cache framework for expensive queries

## Security Considerations

1. **Database User Permissions**
   - Create dedicated database user with minimal required permissions
   - Avoid using root user in production

2. **Connection Security**
   - Use SSL/TLS for database connections in production
   - Implement proper firewall rules

3. **Data Protection**
   - Regular backups
   - Encryption at rest for sensitive data
   - Audit logging for database access

## Production Deployment

### Environment Setup
1. Create production database user with limited permissions
2. Configure SSL certificates for encrypted connections
3. Set up automated backups
4. Implement monitoring and alerting
5. Configure connection pooling for high traffic

### Scaling Considerations
1. Read replicas for improved read performance
2. Database sharding for large datasets
3. Connection pooling optimization
4. Query performance monitoring

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Django and MySQL documentation
3. Check application logs for detailed error messages
4. Use the database health check tools provided