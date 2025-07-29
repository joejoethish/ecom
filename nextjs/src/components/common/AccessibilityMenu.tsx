'use client';

import React, { useState } from 'react';
import { useAccessibility } from '@/components/providers/AccessibilityProvider';
import { useFocusTrap } from '@/hooks/useFocusTrap';
import { 
  Eye, 
  Type, 
  Plus as TypePlus, 
  Minus as TypeMinus, 
  Contrast, 
  RotateCcw,
  X,
  Sparkles
} from 'lucide-react';

export function AccessibilityMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const {
    highContrast,
    toggleHighContrast,
    increaseFontSize,
    decreaseFontSize,
    resetFontSize,
    reduceMotion,
    toggleReduceMotion,
    announce
  } = useAccessibility();
  
  const menuRef = useFocusTrap(isOpen);
  
  const toggleMenu = () => {
    const newState = !isOpen;
    setIsOpen(newState);
    
    if (newState) {
      announce('Accessibility menu opened', 'polite');
    } else {
      announce('Accessibility menu closed', 'polite');
    }
  };
  
  const handleHighContrastToggle = () => {
    toggleHighContrast();
    announce(`High contrast mode ${!highContrast ? 'enabled' : 'disabled'}`, 'polite');
  };
  
  const handleIncreaseFontSize = () => {
    increaseFontSize();
    announce('Font size increased', 'polite');
  };
  
  const handleDecreaseFontSize = () => {
    decreaseFontSize();
    announce('Font size decreased', 'polite');
  };
  
  const handleResetFontSize = () => {
    resetFontSize();
    announce('Font size reset to default', 'polite');
  };
  
  const handleReduceMotionToggle = () => {
    toggleReduceMotion();
    announce(`Reduced motion ${!reduceMotion ? 'enabled' : 'disabled'}`, 'polite');
  };
  
  return (
    <>
      <button
        className="fixed bottom-4 right-4 z-50 p-3 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        onClick={toggleMenu}
        aria-label="Accessibility options"
        aria-expanded={isOpen}
        aria-controls="accessibility-menu"
      >
        <Eye className="h-6 w-6" />
      </button>
      
      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="accessibility-title"
        >
          <div
            ref={menuRef}
            id="accessibility-menu"
            className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4"
          >
            <div className="flex justify-between items-center mb-4">
              <h2 id="accessibility-title" className="text-xl font-bold">
                Accessibility Options
              </h2>
              <button
                onClick={toggleMenu}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                aria-label="Close accessibility menu"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-2">Display</h3>
                <div className="space-y-2">
                  <button
                    onClick={handleHighContrastToggle}
                    className={`flex items-center justify-between w-full px-4 py-2 rounded-md ${
                      highContrast 
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' 
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}
                    aria-pressed={highContrast}
                  >
                    <span className="flex items-center">
                      <Contrast className="mr-2 h-5 w-5" />
                      High Contrast
                    </span>
                    <span className="text-sm">
                      {highContrast ? 'On' : 'Off'}
                    </span>
                  </button>
                  
                  <button
                    onClick={handleReduceMotionToggle}
                    className={`flex items-center justify-between w-full px-4 py-2 rounded-md ${
                      reduceMotion 
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' 
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}
                    aria-pressed={reduceMotion}
                  >
                    <span className="flex items-center">
                      <Sparkles className="mr-2 h-5 w-5" />
                      Reduce Motion
                    </span>
                    <span className="text-sm">
                      {reduceMotion ? 'On' : 'Off'}
                    </span>
                  </button>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-2">Text Size</h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleDecreaseFontSize}
                    className="p-2 bg-gray-100 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
                    aria-label="Decrease font size"
                  >
                    <TypeMinus className="h-5 w-5" />
                  </button>
                  
                  <button
                    onClick={handleResetFontSize}
                    className="flex-1 p-2 bg-gray-100 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 flex items-center justify-center"
                    aria-label="Reset font size"
                  >
                    <Type className="mr-2 h-5 w-5" />
                    <span>Reset</span>
                    <RotateCcw className="ml-2 h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={handleIncreaseFontSize}
                    className="p-2 bg-gray-100 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
                    aria-label="Increase font size"
                  >
                    <TypePlus className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}