'use client';

import React from 'react';

interface SkipToContentProps {
  contentId?: string;
}

export function SkipToContent({ contentId = 'main-content' }: SkipToContentProps) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    
    const contentElement = document.getElementById(contentId);
    if (contentElement) {
      contentElement.tabIndex = -1;
      contentElement.focus();
      
      // Remove tabIndex after focus to avoid leaving a tabIndex on the element
      setTimeout(() => {
        contentElement.removeAttribute(&apos;tabIndex&apos;);
      }, 100);
    }
  };
  
  return (
    <a 
      href={`#${contentId}`}
      className="skip-to-content"
      onClick={handleClick}
    >
      Skip to content
    </a>
  );
}