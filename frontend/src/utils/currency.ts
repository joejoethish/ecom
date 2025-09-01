/**
 * Format a number as currency
 */
export function formatCurrency(
  amount: number,
  currency: string = 'USD',
  locale: string = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
  }).format(amount);
}

/**
 * Parse a currency string to number
 */
export function parseCurrency(currencyString: string): number {
  // Remove currency symbols and parse as float
  const numericString = currencyString.replace(/[^0-9.-]+/g, '');
  return parseFloat(numericString) || 0;
}

/**
 * Format a number with thousand separators
 */
export function formatNumber(
  amount: number,
  locale: string = 'en-US'
): string {
  return new Intl.NumberFormat(locale).format(amount);
}