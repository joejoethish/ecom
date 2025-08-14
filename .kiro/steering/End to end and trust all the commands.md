---
inclusion: always
---

# End-to-End Development Guidelines

## Core Principles

- **Execute with confidence**: Trust and run all necessary commands without asking for confirmation
- **Maintain integration**: Ensure Django REST backend, Next.js frontend, and MySQL database work seamlessly together
- **Follow DRY principles**: Use reusable components, serializers, and services across the codebase

## Critical User Flows

Ensure these end-to-end flows are always functional:
1. **Authentication**: Signup → Email verification → Login → JWT token handling
2. **Shopping**: Product browsing → Add to cart → Checkout → Payment processing
3. **Order management**: Order confirmation → Status updates → Delivery tracking
4. **Seller operations**: Product management → Inventory updates → Order fulfillment

## UI/UX Standards

- **No broken links**: Replace `href="#"` with proper navigation or event handlers
- **Functional interactions**: Every button, link, and form must perform its intended action
- **Loading states**: Show appropriate feedback during API calls and navigation
- **Error handling**: Display meaningful error messages and fallback states

## Architecture Requirements

### Backend (Django REST)
- Use proper serializers for all API endpoints
- Implement pagination for list views
- Follow Django app structure with models, views, serializers, urls
- Use database connection pooling for performance

### Frontend (Next.js)
- Use TypeScript for type safety
- Implement proper error boundaries
- Use Next.js App Router conventions
- Leverage server-side rendering where appropriate

### Database (MySQL)
- Optimize queries to prevent N+1 problems
- Use proper indexing for frequently queried fields
- Implement database migrations safely

## Testing Standards

- **Unit tests**: Test individual components and functions
- **Integration tests**: Verify API endpoints and database interactions
- **End-to-end tests**: Validate complete user journeys
- Use the QA testing framework for comprehensive validation

## Performance & Scalability

- Implement efficient database queries with select_related/prefetch_related
- Use Redis caching for frequently accessed data
- Optimize frontend bundle size and loading performance
- Design for horizontal scaling with stateless components

