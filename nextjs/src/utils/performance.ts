/**
 * Performance monitoring utilities
 */

/**
 * Measures component render time
 * @param componentName - Name of the component being measured
 * @param callback - Function to execute and measure
 * @returns Result of the callback function
 */
export function measureRenderTime<T>(componentName: string, callback: () => T): T {
  if (process.env.NODE_ENV === 'production') {
    return callback();
  }

  const startTime = performance.now();
  const result = callback();
  const endTime = performance.now();
  
  console.log(`[Performance] ${componentName} rendered in ${(endTime - startTime).toFixed(2)}ms`);
  
  return result;
}

/**
 * Reports a web vital metric to analytics
 * @param metric - The web vital metric to report
 */
export function reportWebVitals(metric: any) {
  // In a real app, you would send this to your analytics service
  // Example: sendToAnalytics(metric);
  
  if (process.env.NODE_ENV !== 'production') {
    console.log(`[Web Vital] ${metric.name}: ${metric.value}`);
  }
}

/**
 * Tracks a user interaction for performance monitoring
 * @param name - Name of the interaction
 * @param interactionId - Optional ID for the interaction
 * @returns Function to call when the interaction is complete
 */
export function trackInteraction(name: string, interactionId?: string): () => void {
  if (process.env.NODE_ENV === 'production') {
    return () => {};
  }
  
  const startTime = performance.now();
  const id = interactionId || `interaction-${Date.now()}`;
  
  return () => {
    const duration = performance.now() - startTime;
    console.log(`[Interaction] ${name} (${id}) took ${duration.toFixed(2)}ms`);
  };
}

/**
 * Creates a performance observer for long tasks
 * @returns Cleanup function to disconnect the observer
 */
export function observeLongTasks(): () => void {
  if (typeof window === 'undefined' || typeof PerformanceObserver === 'undefined') {
    return () => {};
  }
  
  try {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        console.warn(`[Long Task] Duration: ${entry.duration.toFixed(2)}ms`, entry);
      });
    });
    
    observer.observe({ entryTypes: ['longtask'] });
    
    return () => observer.disconnect();
  } catch (e) {
    console.error('Failed to observe long tasks:', e);
    return () => {};
  }
}