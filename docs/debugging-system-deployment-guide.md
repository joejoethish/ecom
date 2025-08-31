# E2E Workflow Debugging System - Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Environment Setup](#environment-setup)
6. [Database Setup](#database-setup)
7. [Frontend Configuration](#frontend-configuration)
8. [Production Deployment](#production-deployment)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Troubleshooting](#troubleshooting)
11. [Security Considerations](#security-considerations)
12. [Performance Optimization](#performance-optimization)

## Overview

This guide covers the complete deployment process for the E2E Workflow Debugging System, including backend Django REST API, frontend Next.js dashboard, database configuration, and production deployment considerations.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Next.js)     │◄──►│   (Django)      │◄──►│   (MySQL)       │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 3306    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Redis Cache   │
                    │   Port: 6379    │
                    └─────────────────┘
```

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows
- **Python**: 3.9 or higher
- **Node.js**: 18.0 or higher
- **Database**: MySQL 8.0+ or PostgreSQL 13+
- **Cache**: Redis 6.0+
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **Storage**: Minimum 10GB free space

### Required Software

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm mysql-server redis-server

# macOS (using Homebrew)
brew install python@3.9 node mysql redis

# Windows (using Chocolatey)
choco install python nodejs mysql redis
```

### Development Tools

```bash
# Install additional development tools
pip install --upgrade pip setuptools wheel
npm install -g yarn pm2
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/ecommerce-platform.git
cd ecommerce-platform
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# For production
pip install -r requirements/production.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install
```

## Configuration

### Backend Configuration

#### 1. Environment Variables

Create `.env` file in the backend directory:

```bash
# backend/.env

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DATABASE_URL=mysql://username:password@localhost:3306/ecommerce_db
# or for PostgreSQL
# DATABASE_URL=postgresql://username:password@localhost:5432/ecommerce_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Debugging System Configuration
DEBUGGING_ENABLED=True
DEBUGGING_TRACE_SAMPLING_RATE=0.1
DEBUGGING_MAX_TRACE_DURATION=300000
DEBUGGING_PERFORMANCE_MONITORING=True
DEBUGGING_ERROR_LOGGING=True

# Performance Thresholds
DEBUGGING_API_RESPONSE_TIME_WARNING=200
DEBUGGING_API_RESPONSE_TIME_CRITICAL=500
DEBUGGING_DB_QUERY_TIME_WARNING=50
DEBUGGING_DB_QUERY_TIME_CRITICAL=100

# WebSocket Configuration
WEBSOCKET_ENABLED=True
WEBSOCKET_REDIS_CHANNEL_LAYER=True

# Email Configuration (for alerts)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/debugging.log
```

#### 2. Django Settings

Update `backend/ecommerce_project/settings/base.py`:

```python
# Add debugging app to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'apps.debugging',
    'channels',  # For WebSocket support
]

# Middleware configuration
MIDDLEWARE = [
    'apps.debugging.middleware.CorrelationIdMiddleware',
    'apps.debugging.middleware.WorkflowTracingMiddleware',
    'apps.debugging.middleware.PerformanceMonitoringMiddleware',
    # ... existing middleware
]

# Debugging system configuration
DEBUGGING_CONFIG = {
    'ENABLED': env.bool('DEBUGGING_ENABLED', default=False),
    'TRACE_SAMPLING_RATE': env.float('DEBUGGING_TRACE_SAMPLING_RATE', default=0.1),
    'MAX_TRACE_DURATION': env.int('DEBUGGING_MAX_TRACE_DURATION', default=300000),
    'PERFORMANCE_MONITORING': env.bool('DEBUGGING_PERFORMANCE_MONITORING', default=True),
    'ERROR_LOGGING': env.bool('DEBUGGING_ERROR_LOGGING', default=True),
    'WEBSOCKET_ENABLED': env.bool('WEBSOCKET_ENABLED', default=True),
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    'api_response_time': {
        'warning': env.int('DEBUGGING_API_RESPONSE_TIME_WARNING', default=200),
        'critical': env.int('DEBUGGING_API_RESPONSE_TIME_CRITICAL', default=500),
    },
    'db_query_time': {
        'warning': env.int('DEBUGGING_DB_QUERY_TIME_WARNING', default=50),
        'critical': env.int('DEBUGGING_DB_QUERY_TIME_CRITICAL', default=100),
    },
}

# WebSocket configuration
if DEBUGGING_CONFIG['WEBSOCKET_ENABLED']:
    ASGI_APPLICATION = 'ecommerce_project.asgi.application'
    
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [env('REDIS_URL', default='redis://localhost:6379/0')],
            },
        },
    }

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'debugging': {
            'format': '{asctime} [{levelname}] {name}: {message} (correlation_id: {correlation_id})',
            'style': '{',
        },
    },
    'handlers': {
        'debugging_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': env('LOG_FILE_PATH', default='logs/debugging.log'),
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'debugging',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.debugging': {
            'handlers': ['debugging_file', 'console'],
            'level': env('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}
```

#### 3. URL Configuration

Update `backend/ecommerce_project/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # ... existing URLs
    path('api/v1/debugging/', include('apps.debugging.urls')),
]
```

### Frontend Configuration

#### 1. Environment Variables

Create `.env.local` file in the frontend directory:

```bash
# frontend/.env.local

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000

# Debugging Configuration
NEXT_PUBLIC_DEBUGGING_ENABLED=true
NEXT_PUBLIC_CORRELATION_ID_HEADER=X-Correlation-ID
NEXT_PUBLIC_PERFORMANCE_MONITORING=true
NEXT_PUBLIC_ERROR_REPORTING=true

# Performance Thresholds (frontend)
NEXT_PUBLIC_PAGE_LOAD_TIME_WARNING=2000
NEXT_PUBLIC_PAGE_LOAD_TIME_CRITICAL=5000
NEXT_PUBLIC_API_RESPONSE_TIME_WARNING=1000
NEXT_PUBLIC_API_RESPONSE_TIME_CRITICAL=3000

# Development Settings
NEXT_PUBLIC_DEBUG_MODE=true
```

#### 2. Next.js Configuration

Update `frontend/next.config.ts`:

```typescript
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Enable experimental features for debugging
  experimental: {
    instrumentationHook: true,
  },
  
  // Environment variables
  env: {
    DEBUGGING_ENABLED: process.env.NEXT_PUBLIC_DEBUGGING_ENABLED,
    API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    WS_BASE_URL: process.env.NEXT_PUBLIC_WS_BASE_URL,
  },
  
  // Webpack configuration for debugging
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // Enable source maps in development
      config.devtool = 'eval-source-map';
    }
    
    return config;
  },
  
  // Headers for CORS and debugging
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization, X-Correlation-ID',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
```

#### 3. Debugging Configuration

Create `frontend/src/config/debugging.ts`:

```typescript
export const debuggingConfig = {
  enabled: process.env.NEXT_PUBLIC_DEBUGGING_ENABLED === 'true',
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  wsBaseUrl: process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000',
  correlationIdHeader: process.env.NEXT_PUBLIC_CORRELATION_ID_HEADER || 'X-Correlation-ID',
  performanceMonitoring: process.env.NEXT_PUBLIC_PERFORMANCE_MONITORING === 'true',
  errorReporting: process.env.NEXT_PUBLIC_ERROR_REPORTING === 'true',
  
  thresholds: {
    pageLoadTime: {
      warning: parseInt(process.env.NEXT_PUBLIC_PAGE_LOAD_TIME_WARNING || '2000'),
      critical: parseInt(process.env.NEXT_PUBLIC_PAGE_LOAD_TIME_CRITICAL || '5000'),
    },
    apiResponseTime: {
      warning: parseInt(process.env.NEXT_PUBLIC_API_RESPONSE_TIME_WARNING || '1000'),
      critical: parseInt(process.env.NEXT_PUBLIC_API_RESPONSE_TIME_CRITICAL || '3000'),
    },
  },
  
  sampling: {
    traceRate: 0.1, // 10% of requests
    errorRate: 1.0, // 100% of errors
    performanceRate: 0.2, // 20% of performance metrics
  },
};
```

## Environment Setup

### Development Environment

#### 1. Database Setup

```bash
# MySQL
mysql -u root -p
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ecommerce_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ecommerce_db.* TO 'ecommerce_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# PostgreSQL
sudo -u postgres psql
CREATE DATABASE ecommerce_db;
CREATE USER ecommerce_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO ecommerce_user;
\q
```

#### 2. Redis Setup

```bash
# Start Redis server
redis-server

# Test Redis connection
redis-cli ping
# Should return: PONG
```

#### 3. Run Migrations

```bash
cd backend
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

#### 4. Create Superuser

```bash
python manage.py createsuperuser
```

#### 5. Load Initial Data

```bash
# Load debugging system configuration
python manage.py loaddata apps/debugging/fixtures/initial_config.json

# Load performance thresholds
python manage.py loaddata apps/debugging/fixtures/performance_thresholds.json
```

### Staging Environment

#### 1. Environment Configuration

```bash
# backend/.env.staging
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=staging.yourdomain.com

DATABASE_URL=mysql://user:password@staging-db:3306/ecommerce_staging
REDIS_URL=redis://staging-redis:6379/0

DEBUGGING_ENABLED=True
DEBUGGING_TRACE_SAMPLING_RATE=0.05
DEBUGGING_PERFORMANCE_MONITORING=True
DEBUGGING_ERROR_LOGGING=True

# Stricter thresholds for staging
DEBUGGING_API_RESPONSE_TIME_WARNING=150
DEBUGGING_API_RESPONSE_TIME_CRITICAL=300
```

```bash
# frontend/.env.staging
NEXT_PUBLIC_API_BASE_URL=https://api-staging.yourdomain.com
NEXT_PUBLIC_WS_BASE_URL=wss://api-staging.yourdomain.com
NEXT_PUBLIC_DEBUGGING_ENABLED=true
```

### Production Environment

#### 1. Environment Configuration

```bash
# backend/.env.production
DEBUG=False
SECRET_KEY=your-secure-production-secret-key
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

DATABASE_URL=mysql://user:password@prod-db:3306/ecommerce_prod
REDIS_URL=redis://prod-redis:6379/0

# Minimal debugging in production
DEBUGGING_ENABLED=True
DEBUGGING_TRACE_SAMPLING_RATE=0.01  # 1% sampling
DEBUGGING_PERFORMANCE_MONITORING=True
DEBUGGING_ERROR_LOGGING=True

# Production thresholds
DEBUGGING_API_RESPONSE_TIME_WARNING=100
DEBUGGING_API_RESPONSE_TIME_CRITICAL=200
```

```bash
# frontend/.env.production
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_BASE_URL=wss://api.yourdomain.com
NEXT_PUBLIC_DEBUGGING_ENABLED=false  # Disable frontend debugging in production
```

## Database Setup

### MySQL Configuration

#### 1. Optimize MySQL for Debugging System

```sql
-- /etc/mysql/mysql.conf.d/mysqld.cnf

[mysqld]
# Performance optimizations
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# Query optimization
query_cache_type = 1
query_cache_size = 256M
query_cache_limit = 2M

# Connection settings
max_connections = 200
wait_timeout = 28800
interactive_timeout = 28800

# Logging for debugging
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1
log_queries_not_using_indexes = 1
```

#### 2. Create Indexes for Performance

```sql
-- Indexes for debugging tables
USE ecommerce_db;

-- WorkflowSession indexes
CREATE INDEX idx_workflow_correlation_time ON debugging_workflow_session(correlation_id, start_time);
CREATE INDEX idx_workflow_type_status ON debugging_workflow_session(workflow_type, status);
CREATE INDEX idx_workflow_user_time ON debugging_workflow_session(user_id, start_time);

-- TraceStep indexes
CREATE INDEX idx_trace_workflow_time ON debugging_trace_step(workflow_session_id, start_time);
CREATE INDEX idx_trace_layer_component ON debugging_trace_step(layer, component);
CREATE INDEX idx_trace_status_duration ON debugging_trace_step(status, duration_ms);

-- PerformanceSnapshot indexes
CREATE INDEX idx_perf_time_layer ON debugging_performance_snapshot(timestamp, layer);
CREATE INDEX idx_perf_metric_component ON debugging_performance_snapshot(metric_name, component);
CREATE INDEX idx_perf_correlation_time ON debugging_performance_snapshot(correlation_id, timestamp);

-- ErrorLog indexes
CREATE INDEX idx_error_correlation_time ON debugging_error_log(correlation_id, timestamp);
CREATE INDEX idx_error_layer_severity ON debugging_error_log(layer, severity);
CREATE INDEX idx_error_type_resolved ON debugging_error_log(error_type, resolved);
```

### PostgreSQL Configuration

#### 1. Optimize PostgreSQL

```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### 2. Create Indexes

```sql
-- Similar indexes as MySQL but with PostgreSQL syntax
CREATE INDEX CONCURRENTLY idx_workflow_correlation_time 
ON debugging_workflow_session(correlation_id, start_time);

CREATE INDEX CONCURRENTLY idx_workflow_type_status 
ON debugging_workflow_session(workflow_type, status);

-- Add partial indexes for better performance
CREATE INDEX CONCURRENTLY idx_workflow_active 
ON debugging_workflow_session(start_time) 
WHERE status = 'in_progress';

CREATE INDEX CONCURRENTLY idx_error_unresolved 
ON debugging_error_log(timestamp) 
WHERE resolved = false;
```

## Frontend Configuration

### 1. Build Configuration

```bash
# Development build
cd frontend
npm run dev

# Production build
npm run build
npm start

# Static export (if needed)
npm run export
```

### 2. Performance Optimization

Update `frontend/next.config.ts`:

```typescript
const nextConfig: NextConfig = {
  // ... existing config
  
  // Optimize for production
  swcMinify: true,
  compress: true,
  
  // Image optimization
  images: {
    domains: ['yourdomain.com'],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Bundle analyzer (development only)
  ...(process.env.ANALYZE === 'true' && {
    webpack: (config) => {
      config.plugins.push(
        new (require('@next/bundle-analyzer'))({
          enabled: true,
        })
      );
      return config;
    },
  }),
};
```

### 3. Service Worker for Offline Support

Create `frontend/public/sw.js`:

```javascript
// Service worker for debugging dashboard
const CACHE_NAME = 'debugging-dashboard-v1';
const urlsToCache = [
  '/',
  '/debug',
  '/static/js/bundle.js',
  '/static/css/main.css',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});
```

## Production Deployment

### Docker Deployment

#### 1. Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "ecommerce_project.wsgi:application"]
```

#### 2. Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production image
FROM node:18-alpine AS runner

WORKDIR /app

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "start"]
```

#### 3. Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DEBUG=False
      - DATABASE_URL=mysql://user:password@db:3306/ecommerce_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./backend/logs:/app/logs
    ports:
      - "8000:8000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
    depends_on:
      - backend
    ports:
      - "3000:3000"

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=ecommerce_prod
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql/conf.d:/etc/mysql/conf.d
    ports:
      - "3306:3306"

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - backend

volumes:
  mysql_data:
  redis_data:
```

### Kubernetes Deployment

#### 1. Backend Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/ecommerce-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "False"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: database-url
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 2. Frontend Deployment

```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/ecommerce-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_BASE_URL
          value: "https://api.yourdomain.com"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
```

### CI/CD Pipeline

#### 1. GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Run backend tests
      run: |
        cd backend
        pip install -r requirements/development.txt
        python manage.py test
    
    - name: Set up Node.js
      uses: actions/setup-node@v2
      with:
        node-version: 18
    
    - name: Run frontend tests
      run: |
        cd frontend
        npm ci
        npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build and push Docker images
      run: |
        docker build -t your-registry/ecommerce-backend:latest ./backend
        docker build -t your-registry/ecommerce-frontend:latest ./frontend
        docker push your-registry/ecommerce-backend:latest
        docker push your-registry/ecommerce-frontend:latest
    
    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/
        kubectl rollout restart deployment/backend-deployment
        kubectl rollout restart deployment/frontend-deployment
```

## Monitoring and Maintenance

### 1. Health Checks

Create health check endpoints:

```python
# backend/apps/debugging/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    """Basic health check endpoint"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check Redis connection
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        
        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=503)

def ready_check(request):
    """Readiness check for Kubernetes"""
    # Add more comprehensive checks here
    return JsonResponse({'status': 'ready'})
```

### 2. Monitoring Setup

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ecommerce-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    
  - job_name: 'ecommerce-frontend'
    static_configs:
      - targets: ['frontend:3000']
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "E-commerce Debugging System",
    "panels": [
      {
        "title": "Active Workflows",
        "type": "stat",
        "targets": [
          {
            "expr": "debugging_active_workflows_total"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(debugging_errors_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "debugging_response_time_seconds"
          }
        ]
      }
    ]
  }
}
```

### 3. Log Management

#### ELK Stack Configuration

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - ./backend/logs:/logs

  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"

volumes:
  elasticsearch_data:
```

### 4. Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Database backup
mysqldump -u user -p password ecommerce_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Redis backup
redis-cli --rdb backup_redis_$(date +%Y%m%d_%H%M%S).rdb

# Application logs backup
tar -czf logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/logs/

# Upload to S3 (optional)
aws s3 cp backup_*.sql s3://your-backup-bucket/database/
aws s3 cp backup_redis_*.rdb s3://your-backup-bucket/redis/
aws s3 cp logs_backup_*.tar.gz s3://your-backup-bucket/logs/
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database connectivity
mysql -u user -p -h localhost ecommerce_db

# Check Django database settings
python manage.py dbshell

# Test Redis connection
redis-cli ping
```

#### 2. WebSocket Connection Issues

```bash
# Check if WebSocket is working
wscat -c ws://localhost:8000/ws/debugging/

# Check Redis channel layer
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> channel_layer.send('test', {'type': 'test.message'})
```

#### 3. Performance Issues

```sql
-- Check slow queries
SELECT * FROM information_schema.processlist WHERE time > 10;

-- Check table sizes
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'ecommerce_db'
ORDER BY (data_length + index_length) DESC;
```

#### 4. Memory Issues

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Check Django memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Backend debug mode
export DEBUG_DEBUGGING_SYSTEM=True
export LOG_LEVEL=DEBUG

# Frontend debug mode
export NEXT_PUBLIC_DEBUG_MODE=true
```

## Security Considerations

### 1. Authentication and Authorization

```python
# Restrict debugging endpoints to admin users
from django.contrib.auth.decorators import user_passes_test
from rest_framework.permissions import IsAdminUser

class DebuggingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        # Limit data access based on user permissions
        if self.request.user.is_superuser:
            return self.queryset
        else:
            return self.queryset.filter(user=self.request.user)
```

### 2. Data Sanitization

```python
# Sanitize sensitive data in traces
def sanitize_metadata(metadata):
    sensitive_keys = ['password', 'token', 'secret', 'key']
    sanitized = metadata.copy()
    
    for key in sensitive_keys:
        if key in sanitized:
            sanitized[key] = '***REDACTED***'
    
    return sanitized
```

### 3. Rate Limiting

```python
# Add rate limiting to debugging endpoints
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='100/m', method='POST')
def create_workflow_session(request):
    # Implementation
    pass
```

### 4. HTTPS Configuration

```nginx
# nginx/nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    location /debug {
        # Restrict debug dashboard access
        allow 192.168.1.0/24;  # Internal network only
        deny all;
        
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Optimize debugging tables
OPTIMIZE TABLE debugging_workflow_session;
OPTIMIZE TABLE debugging_trace_step;
OPTIMIZE TABLE debugging_performance_snapshot;
OPTIMIZE TABLE debugging_error_log;

-- Archive old data
DELETE FROM debugging_trace_step 
WHERE start_time < DATE_SUB(NOW(), INTERVAL 30 DAY);

DELETE FROM debugging_performance_snapshot 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 7 DAY);
```

### 2. Caching Strategy

```python
# Cache frequently accessed data
from django.core.cache import cache

def get_system_health():
    cache_key = 'system_health'
    health_data = cache.get(cache_key)
    
    if health_data is None:
        health_data = calculate_system_health()
        cache.set(cache_key, health_data, 60)  # Cache for 1 minute
    
    return health_data
```

### 3. Async Processing

```python
# Use Celery for heavy processing
from celery import shared_task

@shared_task
def process_workflow_analysis(correlation_id):
    # Heavy analysis processing
    pass

# Trigger async processing
process_workflow_analysis.delay(correlation_id)
```

This deployment guide provides comprehensive instructions for setting up and maintaining the E2E Workflow Debugging System in various environments. Follow the appropriate sections based on your deployment needs and environment requirements.