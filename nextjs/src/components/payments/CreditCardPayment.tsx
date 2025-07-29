import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';

interface CreditCardPaymentProps {
  amount: number;
  onProceed: (cardData: CardFormData) => void;
}

export interface CardFormData {
  cardNumber: string;
  cardholderName: string;
  expiryMonth: string;
  expiryYear: string;
  cvv: string;
  saveCard?: boolean;
}

const CreditCardPayment: React.FC<CreditCardPaymentProps> = ({ amount, onProceed }) => {
  const { selectedCurrency, currencies } = useSelector((state: RootState) => state.payments);
  
  const [cardData, setCardData] = useState<CardFormData>({
    cardNumber: '',
    cardholderName: '',
    expiryMonth: '',
    expiryYear: '',
    cvv: '',
    saveCard: false
  });
  
  const [errors, setErrors] = useState<Partial<Record<keyof CardFormData, string>>>({});

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;
    
    setCardData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user types
    if (errors[name as keyof CardFormData]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined
      }));
    }
  };

  const formatCardNumber = (value: string) => {
    // Remove all non-digit characters
    const digits = value.replace(/\D/g, '');
    
    // Add space after every 4 digits
    let formatted = '';
    for (let i = 0; i < digits.length; i += 4) {
      formatted += digits.slice(i, i + 4) + ' ';
    }
    
    return formatted.trim();
  };

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formattedValue = formatCardNumber(e.target.value);
    setCardData(prev => ({
      ...prev,
      cardNumber: formattedValue
    }));
    
    if (errors.cardNumber) {
      setErrors(prev => ({
        ...prev,
        cardNumber: undefined
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof CardFormData, string>> = {};
    
    // Card number validation (simple length check)
    const cardNumberDigits = cardData.cardNumber.replace(/\D/g, '');
    if (!cardNumberDigits || cardNumberDigits.length < 13 || cardNumberDigits.length > 19) {
      newErrors.cardNumber = 'Please enter a valid card number';
    }
    
    // Cardholder name validation
    if (!cardData.cardholderName.trim()) {
      newErrors.cardholderName = 'Cardholder name is required';
    }
    
    // Expiry validation
    if (!cardData.expiryMonth) {
      newErrors.expiryMonth = 'Required';
    }
    
    if (!cardData.expiryYear) {
      newErrors.expiryYear = 'Required';
    }
    
    // CVV validation
    if (!cardData.cvv || cardData.cvv.length < 3 || cardData.cvv.length > 4) {
      newErrors.cvv = 'Invalid CVV';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onProceed(cardData);
    }
  };

  // Generate month options
  const monthOptions = Array.from({ length: 12 }, (_, i) => {
    const month = i + 1;
    const value = month.toString().padStart(2, '0');
    return (
      <option key={value} value={value}>
        {value}
      </option>
    );
  });

  // Generate year options (current year + 10 years)
  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 11 }, (_, i) => {
    const year = currentYear + i;
    return (
      <option key={year} value={year}>
        {year}
      </option>
    );
  });

  // Find the selected currency
  const currency = currencies.find(c => c.code === selectedCurrency) || {
    code: 'USD',
    symbol: '$'
  };

  return (
    <div className="credit-card-payment p-4 border rounded-lg">
      <h4 className="text-lg font-medium mb-4">Credit/Debit Card Payment</h4>
      
      <div className="mb-4 p-3 bg-gray-50 rounded-md">
        <div className="flex justify-between">
          <span>Payment Amount:</span>
          <span className="font-medium">{currency.symbol}{amount.toFixed(2)} {currency.code}</span>
        </div>
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="cardNumber" className="block text-sm font-medium text-gray-700 mb-1">
            Card Number
          </label>
          <input
            id="cardNumber"
            name="cardNumber"
            type="text"
            value={cardData.cardNumber}
            onChange={handleCardNumberChange}
            placeholder="1234 5678 9012 3456"
            maxLength={19}
            className={`w-full form-input rounded-md ${
              errors.cardNumber 
                ? 'border-red-300 focus:border-red-500 focus:ring-red-200' 
                : 'border-gray-300 focus:border-blue-300 focus:ring-blue-200'
            } focus:ring focus:ring-opacity-50`}
          />
          {errors.cardNumber && (
            <p className="mt-1 text-sm text-red-600">{errors.cardNumber}</p>
          )}
        </div>
        
        <div className="mb-4">
          <label htmlFor="cardholderName" className="block text-sm font-medium text-gray-700 mb-1">
            Cardholder Name
          </label>
          <input
            id="cardholderName"
            name="cardholderName"
            type="text"
            value={cardData.cardholderName}
            onChange={handleInputChange}
            placeholder="John Doe"
            className={`w-full form-input rounded-md ${
              errors.cardholderName 
                ? 'border-red-300 focus:border-red-500 focus:ring-red-200' 
                : 'border-gray-300 focus:border-blue-300 focus:ring-blue-200'
            } focus:ring focus:ring-opacity-50`}
          />
          {errors.cardholderName && (
            <p className="mt-1 text-sm text-red-600">{errors.cardholderName}</p>
          )}
        </div>
        
        <div className="flex mb-4 space-x-4">
          <div className="flex-1">
            <label htmlFor="expiryMonth" className="block text-sm font-medium text-gray-700 mb-1">
              Expiry Date
            </label>
            <div className="flex space-x-2">
              <select
                id="expiryMonth"
                name="expiryMonth"
                value={cardData.expiryMonth}
                onChange={handleInputChange}
                className={`w-full form-select rounded-md ${
                  errors.expiryMonth 
                    ? 'border-red-300 focus:border-red-500 focus:ring-red-200' 
                    : 'border-gray-300 focus:border-blue-300 focus:ring-blue-200'
                } focus:ring focus:ring-opacity-50`}
              >
                <option value="">Month</option>
                {monthOptions}
              </select>
              
              <select
                id="expiryYear"
                name="expiryYear"
                value={cardData.expiryYear}
                onChange={handleInputChange}
                className={`w-full form-select rounded-md ${
                  errors.expiryYear 
                    ? 'border-red-300 focus:border-red-500 focus:ring-red-200' 
                    : 'border-gray-300 focus:border-blue-300 focus:ring-blue-200'
                } focus:ring focus:ring-opacity-50`}
              >
                <option value="">Year</option>
                {yearOptions}
              </select>
            </div>
            {(errors.expiryMonth || errors.expiryYear) && (
              <p className="mt-1 text-sm text-red-600">Please select a valid expiry date</p>
            )}
          </div>
          
          <div className="w-1/3">
            <label htmlFor="cvv" className="block text-sm font-medium text-gray-700 mb-1">
              CVV
            </label>
            <input
              id="cvv"
              name="cvv"
              type="password"
              value={cardData.cvv}
              onChange={handleInputChange}
              placeholder="123"
              maxLength={4}
              className={`w-full form-input rounded-md ${
                errors.cvv 
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-200' 
                  : 'border-gray-300 focus:border-blue-300 focus:ring-blue-200'
              } focus:ring focus:ring-opacity-50`}
            />
            {errors.cvv && (
              <p className="mt-1 text-sm text-red-600">{errors.cvv}</p>
            )}
          </div>
        </div>
        
        <div className="mb-6">
          <div className="flex items-center">
            <input
              id="saveCard"
              name="saveCard"
              type="checkbox"
              checked={cardData.saveCard}
              onChange={handleInputChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="saveCard" className="ml-2 block text-sm text-gray-700">
              Save card for future payments
            </label>
          </div>
        </div>
        
        <button 
          type="submit"
          className="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Pay {currency.symbol}{amount.toFixed(2)}
        </button>
      </form>
    </div>
  );
};

export default CreditCardPayment;