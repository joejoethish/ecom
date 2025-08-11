/**
 * Utility functions for formatting data
 */

/**
 * Format a number as currency
 * @param amount - The amount to format
 * @param currencyCode - The currency code (default: USD)
 * @param locale - The locale to use for formatting (default: en-US)
 * @returns Formatted currency string
 */
export const formatCurrency = (
  amount: number,
  currencyCode: string = 'USD',
  locale: string = 'en-US'
): string => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currencyCode,
  }).format(amount);
};

/**
 * Format a credit card number with spaces after every 4 digits
 * @param cardNumber - The card number to format
 * @returns Formatted card number
 */
export const formatCardNumber = (cardNumber: string): string => {
  // Remove all non-digit characters
  const digits = cardNumber.replace(/\D/g, '');
  
  // Add space after every 4 digits
  let formatted = '';
  for (let i = 0; i < digits.length; i += 4) {
    formatted += digits.slice(i, i + 4) + ' ';
  }
  
  return formatted.trim();
};

/**
 * Mask a credit card number to show only the last 4 digits
 * @param cardNumber - The card number to mask
 * @returns Masked card number
 */
export const maskCardNumber = (cardNumber: string): string => {
  // Remove all non-digit characters
  const digits = cardNumber.replace(/\D/g, '');
  
  if (digits.length <= 4) {
    return digits;
  }
  
  const lastFour = digits.slice(-4);
  const maskedPart = '•'.repeat(digits.length - 4);
  
  // Format with spaces for readability
  let formatted = '';
  for (let i = 0; i < maskedPart.length; i += 4) {
    formatted += maskedPart.slice(i, i + 4) + ' ';
  }
  
  return (formatted + lastFour).trim();
};

/**
 * Format a date string to a readable format
 * @param dateString - The date string to format
 * @param locale - The locale to use for formatting (default: en-US)
 * @returns Formatted date string
 */
export const formatDate = (
  dateString: string,
  locale: string = 'en-US'
): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
};

/**
 * Format a date string to include time
 * @param dateString - The date string to format
 * @param locale - The locale to use for formatting (default: en-US)
 * @returns Formatted date and time string
 */
export const formatDateTime = (
  dateString: string,
  locale: string = 'en-US'
): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

/**
 * Format a payment status to a more readable form
 * @param status - The payment status
 * @returns Formatted payment status
 */
export const formatPaymentStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'PENDING': 'Pending',
    'PROCESSING': 'Processing',
    'COMPLETED': 'Completed',
    'FAILED': 'Failed',
    'REFUNDED': 'Refunded',
    'PARTIALLY_REFUNDED': 'Partially Refunded',
    'CANCELLED': 'Cancelled',
  };
  
  return statusMap[status] || status;
};

/**
 * Get a CSS class for a payment status
 * @param status - The payment status
 * @returns CSS class name
 */
export const getPaymentStatusClass = (status: string): string => {
  const statusClassMap: Record<string, string> = {
    'PENDING': 'bg-yellow-100 text-yellow-800',
    'PROCESSING': 'bg-blue-100 text-blue-800',
    'COMPLETED': 'bg-green-100 text-green-800',
    'FAILED': 'bg-red-100 text-red-800',
    'REFUNDED': 'bg-purple-100 text-purple-800',
    'PARTIALLY_REFUNDED': 'bg-indigo-100 text-indigo-800',
    'CANCELLED': 'bg-gray-100 text-gray-800',
  };
  
  return statusClassMap[status] || 'bg-gray-100 text-gray-800';
};