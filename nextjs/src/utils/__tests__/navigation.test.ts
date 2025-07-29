import { generateBreadcrumbs } from '../navigation';
import { ROUTE_LABELS } from '@/constants/routes';

describe('Navigation Utilities', () => {
  describe('generateBreadcrumbs', () => {
    it('returns only home for root path', () => {
      const breadcrumbs = generateBreadcrumbs('/');
      
      expect(breadcrumbs).toHaveLength(1);
      expect(breadcrumbs[0]).toEqual({
        label: 'Home',
        href: '/',
        isCurrent: true
      });
    });
    
    it('generates breadcrumbs for simple paths', () => {
      const breadcrumbs = generateBreadcrumbs('/products');
      
      expect(breadcrumbs).toHaveLength(2);
      expect(breadcrumbs[0]).toEqual({
        label: 'Home',
        href: '/'
      });
      expect(breadcrumbs[1]).toEqual({
        label: ROUTE_LABELS['/products'] || 'Products',
        href: '/products',
        isCurrent: true
      });
    });
    
    it('generates breadcrumbs for nested paths', () => {
      const breadcrumbs = generateBreadcrumbs('/admin/products');
      
      expect(breadcrumbs).toHaveLength(3);
      expect(breadcrumbs[0]).toEqual({
        label: 'Home',
        href: '/'
      });
      expect(breadcrumbs[1]).toEqual({
        label: ROUTE_LABELS['/admin'] || 'Admin',
        href: '/admin'
      });
      expect(breadcrumbs[2]).toEqual({
        label: ROUTE_LABELS['/admin/products'] || 'Products',
        href: '/admin/products',
        isCurrent: true
      });
    });
    
    it('handles dynamic segments', () => {
      const breadcrumbs = generateBreadcrumbs('/products/123');
      
      expect(breadcrumbs).toHaveLength(3);
      expect(breadcrumbs[0]).toEqual({
        label: 'Home',
        href: '/'
      });
      expect(breadcrumbs[1]).toEqual({
        label: ROUTE_LABELS['/products'] || 'Products',
        href: '/products'
      });
      expect(breadcrumbs[2]).toEqual({
        label: '123',
        href: '/products/123',
        isCurrent: true
      });
    });
    
    it('formats kebab-case segments', () => {
      const breadcrumbs = generateBreadcrumbs('/about-us');
      
      expect(breadcrumbs).toHaveLength(2);
      expect(breadcrumbs[1]).toEqual({
        label: ROUTE_LABELS['/about-us'] || 'About us',
        href: '/about-us',
        isCurrent: true
      });
    });
  });
});