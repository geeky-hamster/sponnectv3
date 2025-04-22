/**
 * Form validation utility functions
 */

/**
 * Validates if a value is not empty
 * @param {string} value - The value to check
 * @param {string} fieldName - Name of the field for error message
 * @returns {string|null} Error message or null if valid
 */
export const required = (value, fieldName = 'This field') => {
  if (!value && value !== 0) return `${fieldName} is required`;
  if (typeof value === 'string' && !value.trim()) return `${fieldName} is required`;
  return null;
};

/**
 * Validates if a value is a valid email
 * @param {string} value - The email to validate
 * @returns {string|null} Error message or null if valid
 */
export const email = (value) => {
  if (!value) return null; // Use required validator separately
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) return 'Please enter a valid email address';
  
  return null;
};

/**
 * Validates if a value is a number within specified range
 * @param {number} value - The number to validate
 * @param {number} min - Minimum allowed value
 * @param {number} max - Maximum allowed value
 * @returns {string|null} Error message or null if valid
 */
export const numeric = (value, min = null, max = null) => {
  if (!value && value !== 0) return null; // Use required validator separately
  
  const numValue = Number(value);
  
  if (isNaN(numValue)) return 'Please enter a valid number';
  if (min !== null && numValue < min) return `Value must be at least ${min}`;
  if (max !== null && numValue > max) return `Value must be at most ${max}`;
  
  return null;
};

/**
 * Validates minimum length of a string
 * @param {string} value - The string to check
 * @param {number} length - Minimum required length
 * @returns {string|null} Error message or null if valid
 */
export const minLength = (value, length) => {
  if (!value) return null; // Use required validator separately
  
  if (value.length < length) return `Must be at least ${length} characters`;
  
  return null;
};

/**
 * Validates if two values match
 * @param {any} value - The value to check
 * @param {any} matchValue - The value to match against
 * @param {string} fieldName - Name of the field for error message
 * @returns {string|null} Error message or null if valid
 */
export const matches = (value, matchValue, fieldName = 'Passwords') => {
  if (value !== matchValue) return `${fieldName} do not match`;
  
  return null;
};

/**
 * Validates a form object with provided rules
 * @param {Object} formData - The form data object
 * @param {Object} rules - Validation rules
 * @returns {Object} Validation errors object
 */
export const validateForm = (formData, rules) => {
  const errors = {};
  
  Object.keys(rules).forEach(field => {
    const fieldRules = rules[field];
    const value = formData[field];
    
    for (const rule of fieldRules) {
      const error = rule(value);
      if (error) {
        errors[field] = error;
        break;
      }
    }
  });
  
  return errors;
};

/**
 * Check if a form has any validation errors
 * @param {Object} errors - Validation errors object 
 * @returns {boolean} True if there are no errors
 */
export const isFormValid = (errors) => {
  return Object.keys(errors).length === 0;
}; 