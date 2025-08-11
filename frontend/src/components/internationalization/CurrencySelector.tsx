'use client';

import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';

interface Currency {
  id: string;
  code: string;
  name: string;
  symbol: string;
  decimal_places: number;
  is_active: boolean;
  exchange_rate: string;
}

interface CurrencySelectorProps {
  currentCurrency?: string;
  onCurrencyChange: (currencyCode: string) => void;
  className?: string;
  showExchangeRate?: boolean;
}

export default function CurrencySelector({
  currentCurrency = 'USD',
  onCurrencyChange,
  className = '',
  showExchangeRate = false
}: CurrencySelectorProps) {
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrencies();
  }, []);

  const fetchCurrencies = async () => {
    try {
      const response = await fetch('/api/internationalization/currencies/active/');
      if (response.ok) {
        const data = await response.json();
        setCurrencies(data);
      }
    } catch (error) {
      console.error('Error fetching currencies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCurrencySelect = (currencyCode: string) => {
    onCurrencyChange(currencyCode);
    setIsOpen(false);
  };

  const currentCurr = currencies.find(curr => curr.code === currentCurrency);

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
        <CurrencyDollarIcon className="h-4 w-4" />
        <span>{currentCurr?.symbol || '$'} {currentCurr?.code || 'USD'}</span>
        <ChevronDownIcon className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-50">
          <div className="py-1">
            {currencies.map((currency) => (
              <button
                key={currency.id}
                onClick={() => handleCurrencySelect(currency.code)}
                className={`flex items-center justify-between w-full px-4 py-2 text-sm text-left hover:bg-gray-100 ${
                  currency.code === currentCurrency ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className="font-mono text-lg">{currency.symbol}</span>
                  <div>
                    <div className="font-medium">{currency.code}</div>
                    <div className="text-xs text-gray-500">{currency.name}</div>
                  </div>
                </div>
                <div className="text-right">
                  {showExchangeRate && currency.exchange_rate !== '1.000000' && (
                    <div className="text-xs text-gray-500">
                      Rate: {parseFloat(currency.exchange_rate).toFixed(4)}
                    </div>
                  )}
                  {currency.code === currentCurrency && (
                    <div className="h-2 w-2 bg-indigo-600 rounded-full"></div>
                  )}
                </div>
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