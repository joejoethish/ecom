# Technology Stack

## Frontend
- **Framework**: Next.js 15.4.1 with React 19.1.0
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 4.x
- **UI Components**: Material-UI (MUI) 7.3.1, Heroicons, Lucide React
- **State Management**: Redux Toolkit with React Query
- **Forms**: React Hook Form with Yup validation
- **Charts**: Chart.js, Recharts
- **Authentication**: NextAuth.js
- **Testing**: Jest with Testing Library

## Backend
- **Framework**: Django 4.2.7 with Django REST Framework 3.14.0
- **Language**: Python 3.x
- **Database**: MySQL (primary) with PostgreSQL support
- **Authentication**: JWT with SimpleJWT
- **API Documentation**: DRF Spectacular (OpenAPI/Swagger)
- **Task Queue**: Celery with Redis broker
- **Search**: Elasticsearch 8.11.1
- **Real-time**: Django Channels with WebSockets
- **Testing**: pytest with factory-boy

## Infrastructure
- **Containerization**: Docker with docker-compose
- **Database**: PostgreSQL 15 (development), MySQL (production)
- **Cache/Broker**: Redis 7
- **Web Server**: Nginx (production)
- **Search Engine**: Elasticsearch 8.11.1

## Development Tools
- **Code Quality**: Black, flake8, isort (Python), ESLint (JavaScript/TypeScript)
- **Testing**: pytest (backend), Jest (frontend)
- **API Testing**: Custom QA framework with Selenium, Cypress, Appium
- **Version Control**: Git with conventional commits

## Common Commands

### Frontend Development
```bash
cd frontend
npm install                    # Install dependencies
npm run dev                   # Start development server (with Turbopack)
npm run build                 # Build for production
npm run test                  # Run tests
npm run lint                  # Run linting
npm run type-check           # TypeScript type checking
```

### Backend Development
```bash
cd backend
pip install -r requirements/development.txt  # Install dependencies
python manage.py runserver                   # Start development server
python manage.py migrate                     # Run database migrations
python manage.py test                        # Run tests
python manage.py collectstatic              # Collect static files
```

### Docker Development
```bash
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose logs backend   # View backend logs
docker-compose exec backend python manage.py shell  # Django shell
```

### Testing
```bash
# Backend testing
cd backend
pytest                        # Run all tests
pytest --cov                  # Run with coverage
python -m pytest tests/      # Run specific test directory

# Frontend testing
cd frontend
npm test                      # Run Jest tests
npm run test:coverage         # Run with coverage
npm run test:components       # Test specific components

# QA Framework
cd qa-testing-framework
python -m pytest tests/      # Run QA tests
```

## Code Style Guidelines
- **Python**: Follow PEP 8, use Black formatter, maximum line length 88
- **TypeScript/JavaScript**: Use ESLint with Next.js config, Prettier formatting
- **Imports**: Use absolute imports with path mapping (@/ for src/)
- **API Versioning**: Use URL path versioning (/api/v1/, /api/v2/)
- **Database**: Use Django ORM, avoid raw SQL unless necessary