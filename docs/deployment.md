# E-Commerce Platform Deployment Guide

This document provides comprehensive instructions for deploying the e-commerce platform in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Testing Environment Setup](#testing-environment-setup)
4. [Production Deployment](#production-deployment)
   - [Docker-based Deployment](#docker-based-deployment)
   - [Cloud Provider Deployment](#cloud-provider-deployment)
5. [Environment Variables](#environment-variables)
6. [Database Migration](#database-migration)
7. [Static Files](#static-files)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Backup and Recovery](#backup-and-recovery)
10. [Scaling Considerations](#scaling-considerations)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose
- Git
- Access to deployment environment (AWS, Azure, GCP, etc.)
- Domain name and SSL certificate
- Database credentials
- Payment gateway API keys
- Email service credentials
- Redis instance
- Elasticsearch instance

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/ecommerce-platform.git
   cd ecommerce-platform
   ```

2. Create environment files:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

3. Start the development environment:
   ```bash
   docker-compose up
   ```

4. Access the applications:
   - Backend API: http://localhost:8000/api/v1/
   - Frontend: http://localhost:3000/
   - API Documentation: http://localhost:8000/api/v1/docs/

## Testing Environment Setup

1. Run the test suite:
   ```bash
   # Backend tests
   docker-compose run --rm backend python manage.py test
   
   # Frontend tests
   docker-compose run --rm frontend npm test
   ```

2. Run integration tests:
   ```bash
   docker-compose run --rm backend python manage.py test tests.integration
   ```

3. Run performance tests:
   ```bash
   docker-compose run --rm backend python tests/integration/test_performance.py
   ```

## Production Deployment

### Docker-based Deployment

1. Build production images:
   ```bash
   docker build -t ecommerce-backend:latest ./backend
   docker build -t ecommerce-frontend:latest ./frontend
   ```

2. Push to container registry:
   ```bash
   docker tag ecommerce-backend:latest your-registry/ecommerce-backend:latest
   docker tag ecommerce-frontend:latest your-registry/ecommerce-frontend:latest
   docker push your-registry/ecommerce-backend:latest
   docker push your-registry/ecommerce-frontend:latest
   ```

3. Deploy using Docker Compose or Kubernetes:
   - For Docker Compose, use `docker-compose.prod.yml`
   - For Kubernetes, use the manifests in the `k8s/` directory

### Cloud Provider Deployment

#### AWS Deployment

1. Set up infrastructure using Terraform or CloudFormation
2. Configure AWS ECS or EKS for container orchestration
3. Set up RDS for PostgreSQL database
4. Configure ElastiCache for Redis
5. Set up Amazon Elasticsearch Service
6. Configure S3 for static files and media storage
7. Set up CloudFront for CDN
8. Configure Route 53 for DNS
9. Set up AWS Certificate Manager for SSL
10. Configure AWS CloudWatch for monitoring and logging

#### Azure Deployment

1. Set up Azure Container Instances or AKS
2. Configure Azure Database for PostgreSQL
3. Set up Azure Cache for Redis
4. Configure Azure Elasticsearch
5. Set up Azure Blob Storage for static files and media
6. Configure Azure CDN
7. Set up Azure DNS
8. Configure Azure Application Gateway with SSL
9. Set up Azure Monitor for monitoring and logging

#### GCP Deployment

1. Set up Google Kubernetes Engine (GKE)
2. Configure Cloud SQL for PostgreSQL
3. Set up Memorystore for Redis
4. Configure Elasticsearch on GCP
5. Set up Cloud Storage for static files and media
6. Configure Cloud CDN
7. Set up Cloud DNS
8. Configure SSL with Cloud Load Balancing
9. Set up Cloud Monitoring and Logging

## Environment Variables

### Backend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `0` for production |
| `SECRET_KEY` | Django secret key | `your-secret-key` |
| `DJANGO_SETTINGS_MODULE` | Settings module | `ecommerce_project.settings.production` |
| `ALLOWED_HOSTS` | Allowed hosts | `example.com,www.example.com` |
| `DB_HOST` | Database host | `your-db-host` |
| `DB_NAME` | Database name | `ecommerce` |
| `DB_USER` | Database user | `ecommerce_user` |
| `DB_PASS` | Database password | `your-password` |
| `REDIS_HOST` | Redis host | `your-redis-host` |
| `ELASTICSEARCH_HOST` | Elasticsearch host | `your-elasticsearch-host` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `your-access-key` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `your-secret-key` |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name | `your-bucket-name` |
| `EMAIL_HOST` | SMTP host | `smtp.example.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP user | `your-email@example.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | `your-password` |
| `RAZORPAY_KEY_ID` | Razorpay key ID | `your-key-id` |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret | `your-key-secret` |
| `STRIPE_PUBLIC_KEY` | Stripe public key | `your-public-key` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `your-secret-key` |
| `SENTRY_DSN` | Sentry DSN | `your-sentry-dsn` |

### Frontend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://api.example.com/api/v1` |
| `NEXT_PUBLIC_SITE_URL` | Frontend site URL | `https://example.com` |
| `NEXT_PUBLIC_STRIPE_PUBLIC_KEY` | Stripe public key | `your-public-key` |
| `NEXT_PUBLIC_RAZORPAY_KEY_ID` | Razorpay key ID | `your-key-id` |
| `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` | Google Analytics ID | `UA-XXXXXXXXX-X` |
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN | `your-sentry-dsn` |

## Database Migration

1. Run migrations:
   ```bash
   python manage.py migrate
   ```

2. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

3. Load initial data:
   ```bash
   python manage.py loaddata initial_data
   ```

## Static Files

1. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

2. Configure static file serving:
   - In development: Django's built-in static file server
   - In production: Nginx, AWS S3, or other static file hosting

## Monitoring and Logging

1. Configure Sentry for error tracking:
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.django import DjangoIntegration

   sentry_sdk.init(
       dsn="your-sentry-dsn",
       integrations=[DjangoIntegration()],
       traces_sample_rate=0.1,
       send_default_pii=True
   )
   ```

2. Set up logging:
   - Configure Django logging to file or service
   - Set up log rotation
   - Configure alerts for critical errors

3. Set up monitoring:
   - Server metrics (CPU, memory, disk)
   - Application metrics (response time, error rate)
   - Business metrics (orders, revenue)

## Backup and Recovery

1. Database backup:
   ```bash
   pg_dump -U postgres -d ecommerce > backup.sql
   ```

2. Media files backup:
   ```bash
   aws s3 sync s3://your-bucket-name/media/ ./backup/media/
   ```

3. Recovery procedure:
   ```bash
   psql -U postgres -d ecommerce < backup.sql
   aws s3 sync ./backup/media/ s3://your-bucket-name/media/
   ```

## Scaling Considerations

1. Horizontal scaling:
   - Deploy multiple instances of the application
   - Use a load balancer to distribute traffic
   - Configure session persistence with Redis

2. Database scaling:
   - Use read replicas for read-heavy operations
   - Consider database sharding for large datasets
   - Implement connection pooling

3. Caching strategy:
   - Use Redis for caching
   - Implement cache invalidation
   - Consider CDN for static assets and media

4. Elasticsearch scaling:
   - Configure proper sharding and replication
   - Monitor and optimize query performance
   - Consider dedicated Elasticsearch cluster

## Troubleshooting

### Common Issues

1. Database connection issues:
   - Check database credentials
   - Verify network connectivity
   - Check database server status

2. Redis connection issues:
   - Verify Redis server is running
   - Check Redis connection settings
   - Ensure proper authentication

3. Elasticsearch issues:
   - Check Elasticsearch cluster health
   - Verify index mappings
   - Monitor query performance

4. Static files not loading:
   - Check static file configuration
   - Verify file permissions
   - Check CDN configuration

5. Payment gateway issues:
   - Verify API keys
   - Check webhook configuration
   - Monitor payment logs

### Debugging Tools

1. Django Debug Toolbar (development only)
2. Django Silk for profiling
3. Redis Commander for Redis inspection
4. Elasticsearch Kibana for Elasticsearch monitoring
5. pgAdmin for PostgreSQL management