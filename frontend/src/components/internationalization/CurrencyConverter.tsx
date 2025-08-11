'use client';

import React, { useState, useEffect } from 'react';
import { ArrowsRightLeftIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';

interface Currency {
  code: string;
  name: string;
  symbol: string;
}

interface CurrencyConverterProps {
  className?: string;
  defaultFromCurrency?: string;
  defaultToCurrency?: string;
  defaultAmount?: number;
}

export default function CurrencyConverter({
  className = '',
  defaultFromCurrency = 'USD',
  defaultToCurrency = 'EUR',
  defaultAmount = 100
}: CurrencyConverterProps) {
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [fromCurrency, setFromCurrency] = useState(defaultFromCurrency);
  const [toCurrency, setToCurrency] = useState(defaultToCurrency);
  const [amount, setAmount] = useState(defaultAmount);
  const [convertedAmount, setConvertedAmount] = useState<number | null>(null);
  const [exchangeRate, setExchangeRate] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrencies();
  }, []);

  useEffect(() => {
    if (amount > 0 && fromCurrency && toCurrency) {
      convertCurrency();
    }
  }, [amount, fromCurrency, toCurrency]);

  const fetchCurrencies = async () => {
    try {
      const response = await fetch('/api/internationalization/currencies/active/');
      if (response.ok) {
        const data = await response.json();
        setCurrencies(data);
      }
    } catch (error) {
      console.error('Error fetching currencies:', error);
    }
  };

  const convertCurrency = async () => {
    if (!amount || amount <= 0) {
      setConvertedAmount(null);
      setExchangeRate(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/internationalization/currencies/convert/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: amount.toString(),
          from_currency: fromCurrency,
          to_currency: toCurrency,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setConvertedAmount(parseFloat(data.converted_amount));
        setExchangeRate(parseFloat(data.exchange_rate));
      } else {
        setError('Failed to convert currency');
      }
    } catch (error) {
      setError('Error converting currency');
      console.error('Error converting currency:', error);
    } finally {
      setLoading(false);
    }
  };

  const swapCurrencies = () => {
    const temp = fromCurrency;
    setFromCurrency(toCurrency);
    setToCurrency(temp);
  };

  const formatCurrency = (amount: number, currencyCode: string) => {
    const currency = currencies.find(c => c.code === currencyCode);
    return `${currency?.symbol || currencyCode} ${amount.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-6">
        <CurrencyDollarIcon className="h-6 w-6 text-indigo-600" />
        <h3 className="text-lg font-semibold text-gray-900">Currency Converter</h3>
      </div>

      <div className="space-y-4">
        {/* Amount Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Amount
          </label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Enter amount"
            min="0"
            step="0.01"
          />
        </div>

        {/* From Currency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            From
          </label>
          <select
            value={fromCurrency}
            onChange={(e) => setFromCurrency(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {currencies.map((currency) => (
              <option key={currency.code} value={currency.code}>
                {currency.code} - {currency.name}
              </option>
            ))}
          </select>
        </div>

        {/* Swap Button */}
        <div className="flex justify-center">
          <button
            onClick={swapCurrencies}
            className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-colors"
            title="Swap currencies"
          >
            <ArrowsRightLeftIcon className="h-5 w-5" />
          </button>
        </div>

        {/* To Currency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            To
          </label>
          <select
            value={toCurrency}
            onChange={(e) => setToCurrency(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {currencies.map((currency) => (
              <option key={currency.code} value={currency.code}>
                {currency.code} - {currency.name}
              </option>
            ))}
          </select>
        </div>

        {/* Result */}
        <div className="bg-gray-50 rounded-md p-4">
          <div className="text-sm text-gray-600 mb-2">Converted Amount</div>
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded"></div>
            </div>
          ) : error ? (
            <div className="text-red-600 text-sm">{error}</div>
          ) : convertedAmount !== null ? (
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {formatCurrency(convertedAmount, toCurrency)}
              </div>
              {exchangeRate && (
                <div className="text-sm text-gray-500 mt-1">
                  1 {fromCurrency} = {exchangeRate.toFixed(6)} {toCurrency}
                </div>
              )}
            </div>
          ) : (
            <div className="text-gray-500">Enter amount to convert</div>
          )}
        </div>

        {/* Exchange Rate Info */}
        {exchangeRate && !loading && (
          <div className="text-xs text-gray-500 text-center">
            Exchange rates are updated regularly and may vary from actual market rates.
          </div>
        )}
      </div>
    </div>
  );
}