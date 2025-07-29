import { srOnly, iconButtonLabel, announce } from '../accessibility';

describe('Accessibility Utilities', () => {
  describe('srOnly', () => {
    it('returns CSS properties for screen reader only elements', () => {
      const styles = srOnly();
      
      expect(styles).toEqual({
        position: 'absolute',
        width: '1px',
        height: '1px',
        padding: '0',
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        borderWidth: '0',
      });
    });
  });
  
  describe('iconButtonLabel', () => {
    it('returns the action as the ARIA label', () => {
      expect(iconButtonLabel('Close menu')).toBe('Close menu');
      expect(iconButtonLabel('Search')).toBe('Search');
    });
  });
  
  describe('announce', () => {
    beforeEach(() => {
      // Clean up any existing live regions
      document.querySelectorAll('[aria-live]').forEach(el => el.remove());
      
      // Mock document methods
      document.getElementById = jest.fn().mockReturnValue(null);
      document.createElement = jest.fn().mockImplementation((tagName) => {
        const element = document.createElement(tagName);
        element.setAttribute = jest.fn().mockImplementation((name, value) => {
          element.setAttribute(name, value);
        });
        element.style = {} as CSSStyleDeclaration;
        return element;
      });
      document.body.appendChild = jest.fn();
    });
    
    it('creates a live region with polite priority by default', () => {
      announce('Test message');
      
      expect(document.createElement).toHaveBeenCalledWith('div');
      expect(document.body.appendChild).toHaveBeenCalled();
      
      const createdElement = (document.body.appendChild as jest.Mock).mock.calls[0][0];
      expect(createdElement.id).toBe('accessibility-announce-polite');
      expect(createdElement.getAttribute('aria-live')).toBe('polite');
      expect(createdElement.getAttribute('aria-relevant')).toBe('additions');
      expect(createdElement.getAttribute('aria-atomic')).toBe('true');
      expect(createdElement.textContent).toBe('Test message');
    });
    
    it('creates a live region with assertive priority when specified', () => {
      announce('Important message', 'assertive');
      
      const createdElement = (document.body.appendChild as jest.Mock).mock.calls[0][0];
      expect(createdElement.id).toBe('accessibility-announce-assertive');
      expect(createdElement.getAttribute('aria-live')).toBe('assertive');
      expect(createdElement.textContent).toBe('Important message');
    });
    
    it('reuses existing live region if available', () => {
      // Mock an existing live region
      const mockLiveRegion = document.createElement('div');
      mockLiveRegion.id = 'accessibility-announce-polite';
      document.getElementById = jest.fn().mockReturnValue(mockLiveRegion);
      
      announce('Another message');
      
      // Should not create a new element
      expect(document.createElement).not.toHaveBeenCalled();
      expect(document.body.appendChild).not.toHaveBeenCalled();
      
      // Should update the content of the existing element
      expect(mockLiveRegion.textContent).toBe('Another message');
    });
    
    it('does nothing in a non-browser environment', () => {
      // Simulate a non-browser environment
      const originalWindow = global.window;
      (global as any).window = undefined;
      
      announce('Test message');
      
      // Should not attempt to create or modify DOM elements
      expect(document.createElement).not.toHaveBeenCalled();
      expect(document.body.appendChild).not.toHaveBeenCalled();
      
      // Restore window
      global.window = originalWindow;
    });
  });
});