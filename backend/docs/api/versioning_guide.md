# API Versioning Guide

## Overview

This guide explains how API versioning works in the E-Commerce Platform API. Versioning allows us to evolve the API over time while maintaining backward compatibility for existing clients.

## Versioning Strategy

The E-Commerce Platform API uses URL-based versioning as the primary versioning strategy, with additional support for header-based versioning. This approach provides clear visibility of the API version being used and allows for easy testing in browsers and tools.

### Current API Versions

| Version | Status | Sunset Date |
|---------|--------|-------------|
| v1 | Deprecated | TBD |
| v2 | Current | N/A |

## URL-Based Versioning

URL-based versioning is the primary versioning method. All API endpoints are prefixed with `/api/{version}/` where `{version}` is the API version (e.g., `v1`, `v2`).

### Examples

```http
# API v1 (Deprecated)
GET /api/v1/products/

# API v2 (Current)
GET /api/v2/products/
```

## Header-Based Versioning

In addition to URL-based versioning, you can also specify the API version using HTTP headers. This is useful for clients that cannot easily change the URL structure.

### Using the X-API-Version Header

```http
GET /api/products/
X-API-Version: v2
```

### Using the Accept Header

```http
GET /api/products/
Accept: application/vnd.api+json;version=v2
```

## Version Precedence

When multiple versioning methods are used, the following precedence applies:

1. URL-based versioning (highest priority)
2. X-API-Version header
3. Accept header with version parameter
4. Default version (lowest priority)

## Version-Specific Features

Each API version may have different features and capabilities. The following table outlines the key differences between API versions:

| Feature | v1 | v2 |
|---------|----|----|
| Advanced Search | ❌ | ✅ |
| Bulk Operations | ❌ | ✅ |
| Enhanced Analytics | ❌ | ✅ |
| Product Recommendations | ❌ | ✅ |
| Detailed Availability | ❌ | ✅ |
| Breadcrumb Navigation | ❌ | ✅ |

## Version Headers

All API responses include version-related headers:

- `X-API-Version`: The version used for the request
- `X-API-Supported-Versions`: List of all supported API versions
- `X-API-Deprecation-Warning`: Warning message if the version is deprecated
- `X-API-Sunset-Date`: Date when the version will be removed (for deprecated versions)
- `X-API-Recommended-Version`: Recommended version to use (for deprecated versions)

## Handling Breaking Changes

Breaking changes are only introduced in new API versions. The following are considered breaking changes:

- Removing or renaming endpoints
- Removing or renaming fields in responses
- Changing field types or formats
- Adding required request parameters
- Changing the behavior of existing endpoints

## Migration Guide

### Migrating from v1 to v2

To migrate from API v1 to v2, follow these steps:

1. Update all API endpoint URLs to use `/api/v2/` instead of `/api/v1/`
2. Update client code to handle new response formats
3. Take advantage of new v2 features like enhanced search and bulk operations
4. Test thoroughly before deploying to production

#### Key Differences in v2

- Enhanced product responses with additional fields
- More comprehensive category information with breadcrumb support
- Advanced search capabilities with additional filters
- Detailed product availability information
- Product recommendations and trending products
- Bulk operations for improved performance

## Versioning Best Practices

1. **Always specify the version**: Always explicitly specify the API version in requests
2. **Use the latest version**: Use the latest API version for new integrations
3. **Test version changes**: Thoroughly test when upgrading to a new API version
4. **Monitor deprecation notices**: Pay attention to deprecation warnings and sunset dates
5. **Plan for migrations**: Plan ahead for migrating to new API versions

## Sunset Policy

When an API version is deprecated:

1. A deprecation warning is added to all responses
2. A sunset date is announced at least 6 months in advance
3. Documentation is updated to recommend migration to the latest version
4. Support for the deprecated version continues until the sunset date
5. After the sunset date, the deprecated version may be removed

## Example: Version-Specific Endpoint Behavior

Some endpoints may have different behavior or return different data depending on the API version. For example:

### Product Related Endpoint

```http
# v1: Returns related products from the same category only
GET /api/v1/products/product-slug/related/

# v2: Returns related products from the same category, parent category, and child categories
GET /api/v2/products/product-slug/related/
```

### Advanced Search Endpoint

```http
# v1: Basic search with limited filters
GET /api/v1/products/advanced_search/?q=search_term

# v2: Enhanced search with additional filters
GET /api/v2/products/advanced_search/?q=search_term&min_rating=4&availability=in_stock
```

## Testing Different Versions

To test different API versions:

1. **URL-based testing**: Simply change the version in the URL path
2. **Header-based testing**: Use the X-API-Version header with tools like Postman or curl

```bash
# Testing with curl using URL versioning
curl -X GET "https://api.example.com/api/v2/products/"

# Testing with curl using header versioning
curl -X GET "https://api.example.com/api/products/" -H "X-API-Version: v2"
```

## Support

If you have questions about API versioning or need assistance migrating between versions, please contact our API support team at api-support@example.com.