import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import {
  fetchCurrencies,
  setSelectedCurrency,
  convertCurrency
} from '@/store/slices/paymentSlice';

interface CurrencySelectorProps {
  amount: number;
  onCurrencyChange?: (currency: string, convertedAmount: number) => void;
}

  amount,
  onCurrencyChange
}) => {
  const dispatch = useAppDispatch();
  const {
    currencies,
    selectedCurrency,
    loading,
    error,
    currencyConversion
  } = useSelector((state: RootState) => state.payments);

  useEffect(() => {
    dispatch(fetchCurrencies());
  }, [dispatch]);

  useEffect(() => {
    if (selectedCurrency && amount > 0) {
      dispatch(convertCurrency({
        from_currency: &apos;USD&apos;, // Assuming base currency is USD
        to_currency: selectedCurrency,
        amount
      }));
    }
  }, [dispatch, selectedCurrency, amount]);

  useEffect(() => {
    if (currencyConversion && onCurrencyChange) {
      onCurrencyChange(
        currencyConversion.to_currency,
        currencyConversion.converted_amount
      );
    }
  }, [currencyConversion, onCurrencyChange]);

  const handleCurrencyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newCurrency = e.target.value;
    dispatch(setSelectedCurrency(newCurrency));
  };

  if (loading && currencies.length === 0) {
    return (
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 rounded w-32"></div>
      </div>
    );
  }

  if (error && currencies.length === 0) {
    return (
      <div className="text-red-500 text-sm">
        Error loading currencies
      </div>
    );
  }

  const selectedCurrencyObj = currencies.find(c => c.code === selectedCurrency);

  return (
    <div className="currency-selector">
      <div className="flex items-center space-x-2">
        <select
          value={selectedCurrency}
          onChange={handleCurrencyChange}
          className="form-select rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          disabled={loading}
        >
          {currencies.map((currency) => (
            <option key={currency.code} value={currency.code}>
              {currency.code} ({currency.symbol})
            </option>
          ))}
        </select>

        {currencyConversion ? (
          <div className="text-sm text-gray-500">
            <span>Exchange rate: 1 USD = {selectedCurrencyObj?.exchange_rate?.toFixed(4)} {selectedCurrency}</span>
          </div>
        ) : null}
      </div>

      {currencyConversion ? (
        <div className="mt-2 text-sm">
          <span className="font-medium">
            {currencyConversion.amount?.toFixed(2)} USD =
            {&apos; &apos;}{selectedCurrencyObj?.symbol}{currencyConversion.converted_amount?.toFixed(2)} {selectedCurrency}
          </span>
        </div>
      ) : null}
    </div>
  );
};

export default CurrencySelector;