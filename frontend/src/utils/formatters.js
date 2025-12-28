/**
 * Number Formatting Utilities
 * 数字格式化工具函数
 */

/**
 * Format a number as currency with fixed decimal places
 * @param {number} value - The value to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} - Formatted string
 */
export const formatCurrency = (value, decimals = 2) => {
  if (value == null || isNaN(value)) return '0.00';
  return value.toFixed(decimals);
};

/**
 * Format a large number with commas and decimals
 * @param {number} value - The value to format
 * @returns {string} - Formatted string with commas (e.g., "1,234.56")
 */
export const formatLargeNumber = (value) => {
  if (value == null || isNaN(value)) return '0.00';
  return value.toLocaleString('en-US', { 
    minimumFractionDigits: 2,
    maximumFractionDigits: 2 
  });
};

/**
 * Format a number as percentage
 * @param {number} value - The value to format (0.15 = 15%)
 * @returns {string} - Formatted percentage string (e.g., "15.00%")
 */
export const formatPercent = (value) => {
  if (value == null || isNaN(value)) return '0.00%';
  return `${(value * 100).toFixed(2)}%`;
};

/**
 * Format relative time (e.g., "2 hours ago")
 * @param {Date|string} timestamp - The timestamp to format
 * @returns {string} - Relative time string
 */
export const formatRelativeTime = (timestamp) => {
  if (!timestamp) return 'Unknown';
  
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  
  return date.toLocaleDateString();
};

