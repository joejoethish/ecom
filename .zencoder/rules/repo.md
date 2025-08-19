---
description: Repository Information Overview
alwaysApply: true
---

# Repository Information Overview

## Repository Summary
A multi-component e-commerce platform with Next.js frontend, Django backend, and comprehensive QA testing framework. The system includes web, mobile, and API components with Docker containerization for development and deployment.

## Repository Structure
- **frontend/**: Next.js 15 application with TypeScript and React 19
- **backend/**: Django 4.2 REST API with Celery for async tasks
- **mobile/**: Mobile application component
- **qa-testing-framework/**: Comprehensive testing suite for web, mobile, and API
- **nginx/**: Web server configuration for production deployment
- **docs/**: Documentation files

## Projects

### Frontend (Next.js Application)
**Configuration File**: package.json

#### Language & Runtime
**Language**: TypeScript/JavaScript
**Version**: TypeScript 5.x
**Framework**: Next.js 15.4.1, React 19.1.0
**Package Manager**: npm

#### Dependencies
**Main Dependencies**:
- React 19.1.0
- Next.js 15.4.1
- Redux Toolkit 2.8.2
- Material UI 7.3.1
- React Query 5.84.2
- Chart.js 4.5.0
- next-auth 4.24.11

#### Build & Installation
```bash
npm install
npm run build
npm start
```

#### Docker
**Dockerfile**: frontend/Dockerfile
**Image**: Node 20 Alpine
**Configuration**: Multi-stage build with separate deps, builder, and runner stages

#### Testing
**Framework**: Jest 29.7.0 with React Testing Library
**Test Location**: src/__tests__/
**Configuration**: jest.config.js, jest.setup.js
**Run Command**:
```bash
npm test
npm run test:components
npm run test:integration
```

### Backend (Django REST API)
**Configuration File**: requirements/base.txt

#### Language & Runtime
**Language**: Python
**Version**: Python 3.11
**Framework**: Django 4.2.7, Django REST Framework 3.14.0
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- Django 4.2.7
- Django REST Framework 3.14.0
- Celery 5.3.4
- Redis 5.0.1
- Channels 4.0.0
- Elasticsearch DSL 8.11.0
- mysqlclient 2.2.0

#### Build & Installation
```bash
pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver
```

#### Docker
**Dockerfile**: backend/Dockerfile
**Image**: Python 3.11 Slim
**Configuration**: Production setup with Gunicorn

#### Testing
**Framework**: Django Test Framework with pytest
**Test Location**: backend/tests/
**Configuration**: pytest.ini
**Run Command**:
```bash
pytest
```

### QA Testing Framework
**Configuration File**: requirements.txt

#### Language & Runtime
**Language**: Python
**Version**: Python 3.x
**Framework**: pytest 7.4.0+
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- selenium 4.15.0+
- appium-python-client 3.1.0+
- pytest 7.4.0+
- mysql-connector-python 8.2.0+
- allure-pytest 2.13.0+

#### Structure
- **core/**: Framework foundation with interfaces and utilities
- **web/**: Web testing with Selenium
- **mobile/**: Mobile testing with Appium
- **api/**: API testing module
- **database/**: Database testing components
- **config/**: Environment configurations

#### Testing
**Framework**: pytest with custom extensions
**Test Location**: Multiple directories (api/, web/, mobile/)
**Run Command**:
```bash
pytest
python -m qa_testing_framework.web.run_auth_tests
python -m qa_testing_framework.mobile.run_mobile_auth_tests
```

### Infrastructure
**Configuration File**: docker-compose.yml

#### Services
- **PostgreSQL**: Database (v15)
- **Redis**: Cache and message broker (v7)
- **Elasticsearch**: Search engine (v8.11.1)
- **Nginx**: Web server for production

#### Docker Configuration
**Development**:
```bash
docker-compose up
```

**Production**:
```bash
docker-compose -f docker-compose.prod.yml up
```