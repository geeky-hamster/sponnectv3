/**
 * Utility functions for formatting currency and dates
 */

/**
 * Format a currency value
 * @param {number} amount - Amount to format
 * @param {string} [currency='USD'] - Currency code
 * @param {string} [locale='en-US'] - Locale for formatting
 * @param {number} [minimumFractionDigits=0] - Minimum number of fraction digits
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, currency = 'USD', locale = 'en-US', minimumFractionDigits = 0) => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: minimumFractionDigits
  }).format(amount || 0);
};

/**
 * Format a date value
 * @param {string|Date} dateString - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export const formatDate = (dateString, options = { 
  year: 'numeric', 
  month: 'short', 
  day: 'numeric' 
}) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString(undefined, options);
};

/**
 * Format a datetime value
 * @param {string|Date} dateString - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted datetime string
 */
export const formatDateTime = (dateString, options = { 
  year: 'numeric', 
  month: 'short', 
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit'
}) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString(undefined, options);
};

/**
 * Format a number with commas
 * @param {number} num - Number to format
 * @param {string} [locale='en-IN'] - Locale for formatting
 * @returns {string} Formatted number string
 */
export const formatNumber = (num, locale = 'en-IN') => {
  return new Intl.NumberFormat(locale).format(num || 0);
};

/**
 * Format a percentage value
 * @param {number} value - Value to format as percentage
 * @param {number} [decimals=1] - Number of decimal places
 * @param {boolean} [addPlusSign=true] - Whether to add + sign for positive values
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, decimals = 1, addPlusSign = true) => {
  const numValue = Number(value) || 0;
  const prefix = addPlusSign && numValue > 0 ? '+' : '';
  return `${prefix}${numValue.toFixed(decimals)}%`;
};

/**
 * Format file size
 * @param {number} bytes - Size in bytes
 * @param {number} [decimals=2] - Number of decimal places
 * @returns {string} Formatted file size string
 */
export const formatFileSize = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
};

export default {
  formatCurrency,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPercentage,
  formatFileSize
}; 