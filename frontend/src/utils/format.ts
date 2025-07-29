/**
 * Format a number as currency
 * @param value - The number to format
 * @param locale - The locale to use for formatting (default: 'en-US')
 * @param currency - The currency code to use (default: 'USD')
 * @returns Formatted currency string
 */
export function formatCurrency(
  value: number,
  locale = 'en-US',
  currency = 'USD'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format a date string
 * @param dateString - The date string to format
 * @param locale - The locale to use for formatting (default: 'en-US')
 * @returns Formatted date string
 */
export function formatDate(
  dateString: string,
  locale = 'en-US'
): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

/**
 * Format a date with time
 * @param dateString - The date string to format
 * @param locale - The locale to use for formatting (default: 'en-US')
 * @returns Formatted date and time string
 */
export function formatDateTime(
  dateString: string,
  locale = 'en-US'
): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

/**
 * Truncate a string to a specified length
 * @param text - The text to truncate
 * @param maxLength - Maximum length before truncation
 * @param suffix - Suffix to add after truncation (default: '...')
 * @returns Truncated string
 */
export function truncateText(
  text: string,
  maxLength: number,
  suffix = '...'
): string {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength) + suffix;
}