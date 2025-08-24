/**
 * Tests for Route Discovery API Service
 */

import {
  triggerRouteDiscovery,
  getRouteDiscoveryResults,
  getDependencyMap,
  getRoutesByType,
  getAPICallsForRoute,
  validateRouteDiscovery,
  RouteInfo,
  APICall,
  RouteDiscoveryResult,
  DependencyMap
} from '../routeDiscoveryApi';

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('Route Discovery API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('mock-token');
  });

  describe('triggerRouteDiscovery', () => {
    it('should successfully trigger route discovery', async () => {
      const mockResponse: RouteDiscoveryResult = {
        routes: [],
        totalRoutes: 0,
        apiCallsCount: 0,
        lastScanned: '2024-01-01T00:00:00Z',
        scanDuration: 1000
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await triggerRouteDiscovery();

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/debugging/route-discovery/scan/',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token',
          }),
        })
      );
    });

    it('should handle API errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const result = await triggerRouteDiscovery();

      expect(result.success).toBe(false);
      expect(result.error).toContain('HTTP error! status: 500');
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await triggerRouteDiscovery();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network error');
    });
  });

  describe('getRouteDiscoveryResults', () => {
    it('should successfully get discovery results', async () => {
      const mockRoutes: RouteInfo[] = [
        {
          path: '/',
          type: 'page',
          component: 'HomePage',
          apiCalls: [
            {
              method: 'GET',
              endpoint: '/api/products',
              authentication: true,
            }
          ],
          dependencies: []
        }
      ];

      const mockResponse: RouteDiscoveryResult = {
        routes: mockRoutes,
        totalRoutes: 1,
        apiCallsCount: 1,
        lastScanned: '2024-01-01T00:00:00Z',
        scanDuration: 1000
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getRouteDiscoveryResults();

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockResponse);
      expect(result.data?.routes).toHaveLength(1);
      expect(result.data?.routes[0].path).toBe('/');
    });
  });

  describe('getDependencyMap', () => {
    it('should successfully get dependency map', async () => {
      const mockDependencyMap: DependencyMap = {
        frontend_routes: [
          {
            path: '/',
            type: 'page',
            component: 'HomePage',
            apiCalls: [],
            dependencies: []
          }
        ],
        api_endpoints: ['/api/products', '/api/auth/login'],
        dependencies: [
          {
            frontend_route: '/',
            api_endpoint: '/api/products',
            method: 'GET',
            component: 'HomePage'
          }
        ]
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDependencyMap,
      });

      const result = await getDependencyMap();

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockDependencyMap);
      expect(result.data?.dependencies).toHaveLength(1);
    });
  });

  describe('getRoutesByType', () => {
    it('should successfully get routes by type', async () => {
      const mockRoutes: RouteInfo[] = [
        {
          path: '/api/products',
          type: 'api',
          component: 'ProductsAPI',
          apiCalls: [],
          dependencies: []
        }
      ];

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ results: mockRoutes }),
      });

      const result = await getRoutesByType('api');

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockRoutes);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/debugging/route-discovery/routes/?type=api',
        expect.any(Object)
      );
    });
  });

  describe('getAPICallsForRoute', () => {
    it('should successfully get API calls for a route', async () => {
      const mockAPICall: APICall = {
        method: 'GET',
        endpoint: '/api/products',
        authentication: true,
        component: 'ProductList',
        lineNumber: 25
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [mockAPICall],
      });

      const result = await getAPICallsForRoute('/products');

      expect(result.success).toBe(true);
      expect(result.data).toEqual([mockAPICall]);
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('routes/%2Fproducts/api-calls/'),
        expect.any(Object)
      );
    });

    it('should handle route not found', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      const result = await getAPICallsForRoute('/nonexistent');

      expect(result.success).toBe(false);
      expect(result.error).toContain('HTTP error! status: 404');
    });
  });

  describe('validateRouteDiscovery', () => {
    it('should successfully validate route discovery', async () => {
      const mockValidationResult = {
        totalRoutes: 10,
        validRoutes: 8,
        invalidRoutes: 2,
        errors: ['Component file not found: /path/to/missing.tsx']
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockValidationResult,
      });

      const result = await validateRouteDiscovery();

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockValidationResult);
      expect(result.data?.totalRoutes).toBe(10);
      expect(result.data?.validRoutes).toBe(8);
      expect(result.data?.invalidRoutes).toBe(2);
    });
  });

  describe('Error handling', () => {
    it('should handle missing authentication token', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      const result = await triggerRouteDiscovery();

      expect(result.success).toBe(false);
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer null',
          }),
        })
      );
    });

    it('should handle malformed JSON response', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      const result = await getRouteDiscoveryResults();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid JSON');
    });
  });

  describe('URL encoding', () => {
    it('should properly encode route paths with special characters', async () => {
      const routePath = '/products/[id]/reviews';
      
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

      await getAPICallsForRoute(routePath);

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(encodeURIComponent(routePath)),
        expect.any(Object)
      );
    });
  });

  describe('API response structure validation', () => {
    it('should handle responses with different structures', async () => {
      // Test when API returns data directly vs wrapped in results
      const mockData = [{ path: '/', type: 'page', component: 'Home', apiCalls: [], dependencies: [] }];
      
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData, // Direct array
      });

      const result = await getRoutesByType('page');

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockData);
    });
  });
});