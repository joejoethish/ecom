import { BreadcrumbItem } from '@/components/common/Breadcrumb';
import { ROUTE_LABELS } from '@/constants/routes';

/**
 * Generates breadcrumb items based on the current pathname
 * @param pathname - The current pathname
 * @returns Array of breadcrumb items
 */
export function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  // Always start with home
  const breadcrumbs: BreadcrumbItem[] = [
    { label: 'Home', href: '/' }
  ];
  
  if (pathname === '/') {
    // If we're on the home page, mark it as current
    breadcrumbs[0].isCurrent = true;
    return breadcrumbs;
  }
  
  // Split the pathname into segments
  const segments = pathname.split('/').filter(Boolean);
  
  // Build up the breadcrumb trail
  let currentPath = '';
  
  segments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    
    // Get the label for this segment
    const label = getRouteLabel(segment, currentPath);
    
    // Add to breadcrumbs
    breadcrumbs.push({
      label,
      href: currentPath,
      isCurrent: index === segments.length - 1
    });
  });
  
  return breadcrumbs;
}

/**
 * Gets a human-readable label for a route segment
 * @param segment - The route segment
 * @param fullPath - The full path up to this segment
 * @returns A human-readable label
 */
function getRouteLabel(segment: string, fullPath: string): string {
  // Check if we have a predefined label for this path
  if (ROUTE_LABELS[fullPath]) {
    return ROUTE_LABELS[fullPath];
  }
  
  // Check if this is a dynamic segment (e.g., [id], [slug])
  if (segment.startsWith('[') && segment.endsWith(']')) {
    // For dynamic segments, we'd ideally fetch the actual entity name
    // For now, just clean up the parameter name
    return segment.replace(/^\[|\]$/g, '').replace(/-/g, ' ');
  }
  
  // Fallback: capitalize and format the segment
  return segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ');
}