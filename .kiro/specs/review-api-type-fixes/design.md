# Design Document

## Overview

This design addresses the type inconsistencies in the review API by standardizing all methods to return `ApiResponse<T>` format and updating the useReviews hook to handle these responses correctly. The solution ensures type safety and consistent error handling across all review-related operations.

## Architecture

The fix involves two main components:

1. **Review API Service Layer**: Standardize return types to always use `ApiResponse<T>` wrapper
2. **useReviews Hook**: Update response handling logic to work with standardized API responses

## Components and Interfaces

### Review API Service Updates

The following methods need to be updated to return `ApiResponse<T>` format:

- `getReviews()`: Change from `Promise<PaginatedResponse<Review>>` to `Promise<ApiResponse<PaginatedResponse<Review>>>`
- `getProductReviews()`: Change from `Promise<PaginatedResponse<Review>>` to `Promise<ApiResponse<PaginatedResponse<Review>>>`
- `getReview()`: Change from `Promise<Review>` to `Promise<ApiResponse<Review>>`
- `createReview()`: Change from `Promise<Review>` to `Promise<ApiResponse<Review>>`
- `updateReview()`: Change from `Promise<Review>` to `Promise<ApiResponse<Review>>`
- `deleteReview()`: Change from `Promise<void>` to `Promise<ApiResponse<void>>`

### useReviews Hook Updates

The hook needs to be updated to handle the new response format:

1. **Response Processing**: All API calls will need to check `response.success` and access `response.data`
2. **Error Handling**: Use `response.error?.message` for error messages
3. **Data Extraction**: For paginated responses, access `response.data.results` and `response.data.pagination`

## Data Models

### Current ApiResponse Interface
```typescript
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code: string;
    status_code: number;
    details?: any;
  };
}
```

### Current PaginatedResponse Interface
```typescript
interface PaginatedResponse<T> {
  pagination: PaginationInfo;
  results: T[];
  success: boolean;
}
```

### Updated PaginatedResponse Interface
The `success` property should be removed from `PaginatedResponse<T>` since it will be wrapped in `ApiResponse<T>`:

```typescript
interface PaginatedResponse<T> {
  pagination: PaginationInfo;
  results: T[];
}
```

## Error Handling

### API Service Layer Error Handling
- All methods will return `ApiResponse<T>` format
- Methods that currently throw errors will continue to do so for consistency
- Error messages will be extracted from the API response when available

### Hook Layer Error Handling
- Check `response.success` before accessing data
- Use `response.error?.message` for error messages with fallbacks
- Maintain existing error state management patterns

## Testing Strategy

### Unit Tests for API Service
- Test that all methods return `ApiResponse<T>` format
- Verify error handling for failed responses
- Ensure data is properly wrapped in the response format

### Unit Tests for useReviews Hook
- Test successful API calls with new response format
- Test error handling with failed API responses
- Verify state updates work correctly with new data access patterns
- Test pagination data extraction from nested response structure

### Integration Tests
- Test end-to-end review operations with updated types
- Verify TypeScript compilation passes without errors
- Test error scenarios to ensure proper error propagation

## Implementation Approach

1. **Phase 1**: Update reviewApi service methods to return consistent `ApiResponse<T>` format
2. **Phase 2**: Update useReviews hook to handle the new response format
3. **Phase 3**: Remove unused `PaginatedResponse` import and clean up types
4. **Phase 4**: Test all functionality to ensure no regressions