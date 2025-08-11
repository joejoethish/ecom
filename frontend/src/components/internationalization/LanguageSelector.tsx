'use client';

import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, GlobeAltIcon } from '@heroicons/react/24/outline';

interface Language {
  id: string;
  code: string;
  name: string;
  native_name: string;
  flag_icon: string;
  is_active: boolean;
}

interface LanguageSelectorProps {
  currentLanguage?: string;
  onLanguageChange: (languageCode: string) => void;
  className?: string;
}

export default function LanguageSelector({
  currentLanguage = 'en',
  onLanguageChange,
  className = ''
}: LanguageSelectorProps) {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLanguages();
  }, []);

  const fetchLanguages = async () => {
    try {
      const response = await fetch('/api/internationalization/languages/active/');
      if (response.ok) {
        const data = await response.json();
        setLanguages(data);
      }
    } catch (error) {
      console.error('Error fetching languages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageSelect = (languageCode: string) => {
    onLanguageChange(languageCode);
    setIsOpen(false);
  };

  const currentLang = languages.find(lang => lang.code === currentLanguage);

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-10 w-32 bg-gray-200 rounded-md"></div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        {currentLang?.flag_icon ? (
          <span className="text-lg">{currentLang.flag_icon}</span>
        ) : (
          <GlobeAltIcon className="h-4 w-4" />
        )}
        <span>{currentLang?.native_name || currentLang?.name || 'English'}</span>
        <ChevronDownIcon className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-md shadow-lg z-50">
          <div className="py-1">
            {languages.map((language) => (
              <button
                key={language.id}
                onClick={() => handleLanguageSelect(language.code)}
                className={`flex items-center space-x-3 w-full px-4 py-2 text-sm text-left hover:bg-gray-100 ${
                  language.code === currentLanguage ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700'
                }`}
              >
                {language.flag_icon ? (
                  <span className="text-lg">{language.flag_icon}</span>
                ) : (
                  <GlobeAltIcon className="h-4 w-4" />
                )}
                <div>
                  <div className="font-medium">{language.native_name}</div>
                  <div className="text-xs text-gray-500">{language.name}</div>
                </div>
                {language.code === currentLanguage && (
                  <div className="ml-auto">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full"></div>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        ></div>
      )}
    </div>
  );
}