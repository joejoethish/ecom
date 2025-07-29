import { ComponentType, lazy } from 'react';

/**
 * Helper function for lazy loading components with TypeScript support
 * @param factory - Factory function that imports the component
 * @param name - Name of the exported component
 * @returns Lazy loaded component
 */
export function lazyImport<
  T extends ComponentType<any>,
  I extends { [K2 in K]: T },
  K extends keyof I
>(factory: () => Promise<I>, name: K): I {
  return Object.create({
    [name]: lazy(() => factory().then((module) => ({ default: module[name] }))),
  });
}

/**
 * Example usage:
 * const { ProductCard } = lazyImport(() => import('@/components/products/ProductCard'), 'ProductCard');
 */