'use client';

import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, ClockIcon } from '@heroicons/react/24/outline';

interface Timezone {
  id: string;
  name: string;
  display_name: string;
  offset: string;
  country_code: string;
  is_active: boolean;
}

interface TimezoneSelectorProps {
  currentTimezone?: string;
  onTimezoneChange: (timezoneName: string) => void;
  className?: string;
  countryFilter?: string;
}

export default function TimezoneSelector({
  currentTimezone = 'UTC',
  onTimezoneChange,
  className = '',
  countryFilter
}: TimezoneSelectorProps) {
  const [timezones, setTimezones] = useState<Timezone[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchTimezones();
  }, [countryFilter]);

  const fetchTimezones = async () => {
    try {
      let url = '/api/internationalization/timezones/active/';
      if (countryFilter) {
        url += `?country=${countryFilter}`;
      }
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setTimezones(data);
      }
    } catch (error) {
      console.error('Error fetching timezones:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTimezoneSelect = (timezoneName: string) => {
    onTimezoneChange(timezoneName);
    setIsOpen(false);
    setSearchTerm('');
  };

  const filteredTimezones = timezones.filter(tz =>
    tz.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tz.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const currentTz = timezones.find(tz => tz.name === currentTimezone);

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-10 w-48 bg-gray-200 rounded-md"></div>
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
        <ClockIcon className="h-4 w-4" />
        <span>{currentTz?.display_name || 'UTC'}</span>
        <span className="text-xs text-gray-500">({currentTz?.offset || '+00:00'})</span>
        <ChevronDownIcon className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-md shadow-lg z-50">
          <div className="p-3 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search timezones..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div className="max-h-64 overflow-y-auto">
            {filteredTimezones.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-500">
                No timezones found
              </div>
            ) : (
              filteredTimezones.map((timezone) => (
                <button
                  key={timezone.id}
                  onClick={() => handleTimezoneSelect(timezone.name)}
                  className={`flex items-center justify-between w-full px-4 py-2 text-sm text-left hover:bg-gray-100 ${
                    timezone.name === currentTimezone ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700'
                  }`}
                >
                  <div>
                    <div className="font-medium">{timezone.display_name}</div>
                    <div className="text-xs text-gray-500">{timezone.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-mono">{timezone.offset}</div>
                    {timezone.country_code && (
                      <div className="text-xs text-gray-400">{timezone.country_code}</div>
                    )}
                    {timezone.name === currentTimezone && (
                      <div className="h-2 w-2 bg-indigo-600 rounded-full mt-1"></div>
                    )}
                  </div>
                </button>
              ))
            )}
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