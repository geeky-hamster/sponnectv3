/**
 * Utility functions for formatting currency and dates
 */

/**
 * Format a currency value
 * @param {number} amount - Amount to format
 * @param {string} [currency='INR'] - Currency code
 * @param {string} [locale='en-IN'] - Locale for formatting
 * @param {number} [minimumFractionDigits=0] - Minimum number of fraction digits
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, currency = 'INR', locale = 'en-IN', minimumFractionDigits = 0) => {
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
  
  try {
    // Handle date strings with time components
    if (typeof dateString === 'string' && dateString.includes(' ')) {
      // Extract just the date part if there's a space (indicating time component)
      const datePart = dateString.split(' ')[0];
      
      // Check if it's in DD-MM-YYYY format
      if (datePart.includes('-')) {
        const parts = datePart.split('-');
        if (parts.length === 3) {
          // If the first part is likely a day (1-31), assume DD-MM-YYYY
          if (parseInt(parts[0], 10) >= 1 && parseInt(parts[0], 10) <= 31) {
            return datePart; // Return the extracted date part as is
          }
        }
      }
    }
    
    // Parse date value
    let date;
    
    if (dateString instanceof Date) {
      date = dateString;
    } else {
      date = new Date(dateString);
    }
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      // Try to handle common date formats before giving up
      if (typeof dateString === 'string') {
        // Try DD-MM-YYYY format
        const dashParts = dateString.split('-');
        if (dashParts.length === 3) {
          const day = parseInt(dashParts[0], 10);
          const month = parseInt(dashParts[1], 10) - 1;
          const year = parseInt(dashParts[2], 10);
          date = new Date(year, month, day);
          
          if (!isNaN(date.getTime())) {
            return `${dashParts[0]}-${dashParts[1]}-${dashParts[2]}`;
          }
        }
        
        // Try YYYY-MM-DD format (ISO format variation)
        if (dashParts.length === 3) {
          const year = parseInt(dashParts[0], 10);
          const month = parseInt(dashParts[1], 10) - 1;
          const day = parseInt(dashParts[2], 10);
          
          // Check if it looks like YYYY-MM-DD (year usually > 1000)
          if (year > 1000) {
            date = new Date(year, month, day);
            if (!isNaN(date.getTime())) {
              // Format as DD-MM-YYYY for output
              return `${day.toString().padStart(2, "0")}-${(month + 1).toString().padStart(2, "0")}-${year}`;
            }
          }
        }
      }
      
      console.warn("Invalid date encountered:", dateString);
      return 'N/A';
    }
    
    // Use explicit formatting to avoid locale differences
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0"); // Months are 0-indexed
    const year = date.getFullYear();
    
    // Format as DD-MM-YYYY
    return `${day}-${month}-${year}`;
  } catch (e) {
    console.error("Error formatting date:", e, dateString);
    return 'N/A';
  }
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
  
  try {
    // Special handling for datetime strings with specific formats
    if (typeof dateString === 'string') {
      // For "DD-MM-YYYY HH:MM:SS" format
      if (dateString.includes(' ') && dateString.includes('-')) {
        const [datePart, timePart] = dateString.split(' ');
        const dateParts = datePart.split('-');
        
        if (dateParts.length === 3) {
          const day = parseInt(dateParts[0], 10);
          // Check if it looks like DD-MM-YYYY (day usually <= 31)
          if (day <= 31) {
            const month = parseInt(dateParts[1], 10) - 1;
            const year = parseInt(dateParts[2], 10);
            
            // If there's a time part with colons (like HH:MM:SS)
            if (timePart && timePart.includes(':')) {
              const timeParts = timePart.split(':');
              if (timeParts.length >= 2) {
                const hour = parseInt(timeParts[0], 10);
                const minute = parseInt(timeParts[1], 10);
                const second = timeParts.length > 2 ? parseInt(timeParts[2], 10) : 0;
                
                const date = new Date(year, month, day, hour, minute, second);
                if (!isNaN(date.getTime())) {
                  // Format using the provided options
                  return date.toLocaleString('en-IN', options);
                }
              }
            }
          }
        }
      }
    }
    
    // Standard date parsing for other formats
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.warn("Invalid datetime encountered:", dateString);
      return 'N/A';
    }
    
    return date.toLocaleString('en-IN', options);
  } catch (e) {
    console.error("Error formatting datetime:", e, dateString);
    return 'N/A';
  }
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