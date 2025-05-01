/**
 * Preprocesses date input to handle various formats and edge cases
 * @param {string|Date|Object} dateInput - The date input to process
 * @returns {string|Date|null} - A normalized date input
 */
const preprocessDateInput = (dateInput) => {
  if (!dateInput) return null;
  
  try {
    // Log input for debugging
    console.log(`Processing date input: ${JSON.stringify(dateInput)}`);
    
    // Handle date objects with special properties
    if (typeof dateInput === 'object' && !Array.isArray(dateInput)) {
      // If it's a Date object already, return it
      if (dateInput instanceof Date) {
        return dateInput;
      }
      
      // Check for ISO or raw date string in object
      if (dateInput.iso) return dateInput.iso;
      if (dateInput.raw) return dateInput.raw;
      if (dateInput._iso) return dateInput._iso;
      if (dateInput._raw) return dateInput._raw;
      
      // Look for any property that might contain a date string
      for (const key of ['date', 'timestamp', 'time']) {
        if (dateInput[key] && typeof dateInput[key] === 'string') {
          return dateInput[key];
        }
      }
    }
    
    // Handle string inputs
    if (typeof dateInput === 'string') {
      // Check if it contains "NaN" and return null
      if (dateInput.includes('NaN')) {
        console.warn(`Date string contains NaN: ${dateInput}`);
        return null;
      }
      
      // Special handling for DD-MM-YYYY with time format (e.g., "22-04-2025 13:02:13")
      const timeFormatRegex = /^(\d{1,2})-(\d{1,2})-(\d{4})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})$/;
      const timeMatch = dateInput.match(timeFormatRegex);
      
      if (timeMatch) {
        const [_, day, month, year, hours, minutes, seconds] = timeMatch;
        return new Date(
          parseInt(year), 
          parseInt(month) - 1, // JS months are 0-indexed
          parseInt(day),
          parseInt(hours),
          parseInt(minutes),
          parseInt(seconds)
        );
      }
      
      // Try to handle DD-MM-YYYY format which JavaScript can't parse natively
      if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(dateInput)) {
        const parts = dateInput.split('-');
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1; // JS months are 0-indexed
        const year = parseInt(parts[2], 10);
        return new Date(year, month, day);
      }
      
      // Return the string for standard parsing
      return dateInput;
    }
    
    return dateInput;
  } catch (e) {
    console.error(`Error preprocessing date input: ${e.message}`, dateInput);
    return null;
  }
};

/**
 * Format a date string to DD-MM-YYYY format, with error handling
 * @param {string|Date} dateString - The date string to format
 * @returns {string} The formatted date
 */
export const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  
  try {
    // Preprocess the date input
    const processedInput = preprocessDateInput(dateString);
    if (!processedInput) return "N/A";
    
    console.log(`Formatting date: ${processedInput}, type: ${typeof processedInput}`);
    
    // If we already have a Date object from preprocessing
    if (processedInput instanceof Date) {
      // Check if valid
      if (isNaN(processedInput.getTime())) {
        console.error(`Invalid date object from preprocessing: ${dateString}`);
        return "N/A";
      }
      
      // Format as DD-MM-YYYY
      const day = processedInput.getDate().toString().padStart(2, "0");
      const month = (processedInput.getMonth() + 1).toString().padStart(2, "0"); // Months are 0-indexed
      const year = processedInput.getFullYear();
      
      return `${day}-${month}-${year}`;
    }
    
    // Try parsing as ISO format or standard date string
    const date = new Date(processedInput);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.error(`Invalid date after preprocessing: ${processedInput}`);
      return "N/A";
    }
    
    // Format as DD-MM-YYYY
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0"); // Months are 0-indexed
    const year = date.getFullYear();
    
    return `${day}-${month}-${year}`;
  } catch (e) {
    console.error("Error formatting date:", e, dateString);
    return "N/A";
  }
};

/**
 * Format a date string to DD-MM-YYYY HH:MM format, with error handling
 * @param {string|Date} dateString - The date string to format
 * @returns {string} The formatted date with time
 */
export const formatDateWithTime = (dateString) => {
  if (!dateString) return "N/A";
  
  try {
    // Preprocess the date input
    const processedInput = preprocessDateInput(dateString);
    if (!processedInput) return "N/A";
    
    // Try parsing as ISO format or standard date string
    const date = processedInput instanceof Date ? processedInput : new Date(processedInput);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.warn("Invalid date format for time formatting:", processedInput);
      return "N/A";
    }
    
    // Format as DD-MM-YYYY HH:MM
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0"); // Months are 0-indexed
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    const seconds = date.getSeconds().toString().padStart(2, "0");
    
    // Return format with seconds if seconds are non-zero
    if (parseInt(seconds) > 0) {
      return `${day}-${month}-${year} ${hours}:${minutes}:${seconds}`;
    }
    
    return `${day}-${month}-${year} ${hours}:${minutes}`;
  } catch (e) {
    console.error("Error formatting date with time:", e, dateString);
    return "N/A";
  }
}; 