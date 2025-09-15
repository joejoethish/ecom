import { measureRenderTime, trackInteraction, observeLongTasks } from '../performance';

// Mock console methods
const originalConsoleLog = console.log;
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

describe('Performance Utilities', () => {
  beforeEach(() => {
    // Mock console methods
    console.log = jest.fn();
    console.warn = jest.fn();
    console.error = jest.fn();
    
    // Mock performance API
    if (!global.performance) {
      Object.defineProperty(global, 'performance', {
        value: {
          now: jest.fn().mockReturnValue(100),
        },
        writable: true,
      });
    } else {
      global.performance.now = jest.fn().mockReturnValue(100);
    }
  });
  
  afterEach(() => {
    // Restore console methods
    console.log = originalConsoleLog;
    console.warn = originalConsoleWarn;
    console.error = originalConsoleError;
  });
  
  describe('measureRenderTime', () => {
    it('measures render time and logs in development', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'development',
        writable: true,
        configurable: true,
      });
      
      const mockCallback = jest.fn().mockReturnValue('result');
      (global.performance.now as jest.Mock)
        .mockReturnValueOnce(100)
        .mockReturnValueOnce(150);
      
      const result = measureRenderTime('TestComponent', mockCallback);
      
      expect(mockCallback).toHaveBeenCalled();
      expect(result).toBe('result');
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('[Performance] TestComponent rendered in 50.00ms')
      );
      
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalNodeEnv,
        writable: true,
        configurable: true,
      });
    });
    
    it('does not log in production', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'production',
        writable: true,
        configurable: true,
      });
      
      const mockCallback = jest.fn().mockReturnValue('result');
      
      const result = measureRenderTime('TestComponent', mockCallback);
      
      expect(mockCallback).toHaveBeenCalled();
      expect(result).toBe('result');
      expect(console.log).not.toHaveBeenCalled();
      
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalNodeEnv,
        writable: true,
        configurable: true,
      });
    });
  });
  
  describe('trackInteraction', () => {
    it('tracks interaction time and logs in development', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'development',
        writable: true,
        configurable: true,
      });
      
      (global.performance.now as jest.Mock)
        .mockReturnValueOnce(100)
        .mockReturnValueOnce(200);
      
      const endTracking = trackInteraction('ButtonClick', 'test-id');
      endTracking();
      
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('[Interaction] ButtonClick (test-id) took 100.00ms')
      );
      
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalNodeEnv,
        writable: true,
        configurable: true,
      });
    });
    
    it('does not log in production', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'production',
        writable: true,
        configurable: true,
      });
      
      const endTracking = trackInteraction('ButtonClick');
      endTracking();
      
      expect(console.log).not.toHaveBeenCalled();
      
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalNodeEnv,
        writable: true,
        configurable: true,
      });
    });
  });
  
  describe('observeLongTasks', () => {
    it('creates and returns a performance observer when available', () => {
      // Mock PerformanceObserver
      const mockDisconnect = jest.fn();
      const mockObserve = jest.fn();
      
      class MockPerformanceObserver {
        constructor(callback: any) {
          this.callback = callback;
        }
        
        callback: any;
        disconnect = mockDisconnect;
        observe = mockObserve;
        
        static supportedEntryTypes = ['longtask'];
      }
      
      global.PerformanceObserver = MockPerformanceObserver as any;
      
      const cleanup = observeLongTasks();
      
      expect(mockObserve).toHaveBeenCalledWith({ entryTypes: ['longtask'] });
      
      cleanup();
      
      expect(mockDisconnect).toHaveBeenCalled();
      
      (global as any).PerformanceObserver = undefined;
    });
    
    it('handles errors gracefully', () => {
      // Mock PerformanceObserver that throws an error
      const MockErrorObserver = jest.fn().mockImplementation(() => {
        throw new Error('Test error');
      });
      (MockErrorObserver as any).supportedEntryTypes = ['longtask'];
      global.PerformanceObserver = MockErrorObserver as any;
      
      const cleanup = observeLongTasks();
      
      expect(console.error).toHaveBeenCalledWith(
        'Failed to observe long tasks:',
        expect.any(Error)
      );
      
      cleanup(); // Should not throw
      
      (global as any).PerformanceObserver = undefined;
    });
    
    it('returns a no-op function when PerformanceObserver is not available', () => {
      // Ensure PerformanceObserver is not defined
      (global as any).PerformanceObserver = undefined;
      
      const cleanup = observeLongTasks();
      
      expect(typeof cleanup).toBe('function');
      expect(() => cleanup()).not.toThrow();
    });
  });
});