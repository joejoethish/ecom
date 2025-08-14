# Project Structure

## Root Directory Layout
```
├── backend/                 # Django REST API backend
├── frontend/               # Next.js React frontend
├── qa-testing-framework/   # Comprehensive testing framework
├── mobile/                 # React Native mobile app (placeholder)
├── nginx/                  # Nginx configuration
├── docs/                   # Project documentation
├── docker-compose.yml      # Development environment
├── docker-compose.prod.yml # Production environment
└── .env.example           # Environment variables template
```

## Backend Structure (`backend/`)
```
backend/
├── ecommerce_project/      # Django project settings
│   ├── settings/          # Environment-specific settings
│   │   ├── base.py       # Base configuration
│   │   ├── development.py # Development settings
│   │   └── production.py  # Production settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py/asgi.py   # WSGI/ASGI applications
├── apps/                  # Django applications
│   ├── authentication/   # User authentication & JWT
│   ├── products/         # Product catalog management
│   ├── orders/           # Order processing
│   ├── cart/             # Shopping cart functionality
│   ├── inventory/        # Inventory management
│   ├── customers/        # Customer management
│   ├── payments/         # Payment processing
│   ├── shipping/         # Shipping & logistics
│   ├── sellers/          # Multi-vendor seller management
│   ├── analytics/        # Analytics & reporting
│   ├── customer_analytics/ # Customer segmentation
│   ├── admin_panel/      # Admin interface
│   ├── system_settings/  # System configuration
│   ├── integrations/     # Third-party integrations
│   ├── notifications/    # Notification system
│   ├── reviews/          # Product reviews
│   ├── search/           # Elasticsearch integration
│   ├── content/          # CMS functionality
│   ├── chat/             # Real-time chat
│   ├── promotions/       # Coupons & promotions
│   ├── forms/            # Dynamic form management
│   ├── api_management/   # API versioning & docs
│   ├── communications/   # Email/SMS management
│   ├── financial/        # Financial management
│   ├── suppliers/        # Supplier management
│   ├── pricing/          # Pricing strategies
│   ├── data_management/  # Import/export tools
│   ├── security_management/ # Security & audit
│   ├── workflow/         # Workflow automation
│   ├── project_management/ # Task management
│   ├── tenants/          # Multi-tenant support
│   └── internationalization/ # i18n support
├── core/                  # Core utilities
│   ├── middleware/       # Custom middleware
│   ├── exceptions.py     # Custom exception handlers
│   ├── pagination.py     # Custom pagination
│   └── versioning.py     # API versioning
├── tasks/                 # Celery tasks
├── requirements/          # Python dependencies
│   ├── base.txt         # Base requirements
│   ├── development.txt   # Development requirements
│   └── production.txt    # Production requirements
├── static/               # Static files
├── media/                # User uploaded files
├── templates/            # Django templates
├── logs/                 # Application logs
└── manage.py             # Django management script
```

## Frontend Structure (`frontend/`)
```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── (auth)/      # Authentication routes
│   │   ├── (dashboard)/ # Dashboard routes
│   │   ├── api/         # API routes
│   │   ├── globals.css  # Global styles
│   │   ├── layout.tsx   # Root layout
│   │   └── page.tsx     # Home page
│   ├── components/       # Reusable React components
│   │   ├── ui/          # Base UI components
│   │   ├── forms/       # Form components
│   │   ├── charts/      # Chart components
│   │   └── layout/      # Layout components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utility libraries
│   ├── store/           # Redux store configuration
│   ├── types/           # TypeScript type definitions
│   └── utils/           # Utility functions
├── public/              # Static assets
├── package.json         # Node.js dependencies
├── next.config.ts       # Next.js configuration
├── tailwind.config.ts   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── jest.config.js       # Jest testing configuration
```

## QA Testing Framework (`qa-testing-framework/`)
```
qa-testing-framework/
├── core/                # Framework core components
│   ├── interfaces.py    # Base interfaces
│   ├── models.py        # Data models
│   ├── config.py        # Configuration management
│   └── utils.py         # Utility functions
├── web/                 # Web testing (Selenium/Cypress)
├── mobile/              # Mobile testing (Appium)
├── api/                 # API testing (REST)
├── database/            # Database testing
├── config/              # Environment configurations
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── tests/               # Test implementations
├── logs/                # Test execution logs
└── requirements.txt     # Python dependencies
```

## Key Conventions

### Django Apps Organization
- Each app follows Django's standard structure with models, views, serializers, urls
- Apps are feature-based, not layer-based
- Use `apps/` directory to group all Django applications
- Core utilities go in `core/` directory

### Frontend Organization
- Use Next.js App Router with TypeScript
- Components organized by feature and reusability
- Absolute imports with `@/` path mapping
- Separate directories for hooks, utilities, and types

### Configuration Management
- Environment-specific settings in separate files
- Use python-decouple for environment variables
- Docker compose for development environment
- Separate production configuration

### Testing Structure
- Backend: pytest with factory-boy for test data
- Frontend: Jest with Testing Library
- QA Framework: Comprehensive end-to-end testing
- Test files co-located with source code where appropriate

### File Naming Conventions
- Python: snake_case for files and functions
- TypeScript/JavaScript: camelCase for variables, PascalCase for components
- Django: Standard Django naming (models.py, views.py, serializers.py)
- Next.js: Standard Next.js naming (page.tsx, layout.tsx)