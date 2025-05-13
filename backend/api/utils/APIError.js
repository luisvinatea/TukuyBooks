/**
 * Custom API Error class for standardized API error handling
 */
class APIError extends Error {
  /**
   * Create a new API Error
   *
   * @param {string} message - Error message
   * @param {number} statusCode - HTTP status code
   * @param {string} code - Error code
   * @param {any} details - Additional error details
   */
  constructor(
    message,
    statusCode = 500,
    code = "UNKNOWN_ERROR",
    details = null
  ) {
    super(message);
    this.name = "APIError";
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
    this.timestamp = new Date().toISOString();
  }

  /**
   * Create an error from an API response
   *
   * @param {Object} response - API response object
   * @returns {APIError} - A new APIError instance
   */
  static fromResponse(response) {
    const { message, error } = response;
    const code = error?.code || "API_ERROR";
    const details = error?.details || null;

    return new APIError(
      message || "Unknown API error",
      response.status || 500,
      code,
      details
    );
  }

  /**
   * Create an error from a network error
   *
   * @param {Error} error - Original error
   * @returns {APIError} - A new APIError instance
   */
  static fromNetworkError(error) {
    return new APIError(error.message || "Network error", 0, "NETWORK_ERROR", {
      originalError: error.toString(),
    });
  }

  /**
   * Create an error for validation issues
   *
   * @param {string} message - Error message
   * @param {Object} validationErrors - Validation error details
   * @returns {APIError} - A new APIError instance
   */
  static validationError(message, validationErrors) {
    return new APIError(
      message || "Validation failed",
      400,
      "VALIDATION_ERROR",
      validationErrors
    );
  }

  /**
   * Create an error for authentication issues
   *
   * @param {string} message - Error message
   * @returns {APIError} - A new APIError instance
   */
  static authenticationError(message) {
    return new APIError(
      message || "Authentication failed",
      401,
      "AUTHENTICATION_ERROR"
    );
  }

  /**
   * Create an error for not found resources
   *
   * @param {string} message - Error message
   * @param {string} resource - Resource that wasn't found
   * @returns {APIError} - A new APIError instance
   */
  static notFoundError(message, resource) {
    return new APIError(
      message || `Resource not found: ${resource}`,
      404,
      "NOT_FOUND",
      { resource }
    );
  }

  /**
   * Convert the error to a JSON object
   *
   * @returns {Object} - JSON representation of the error
   */
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      statusCode: this.statusCode,
      code: this.code,
      details: this.details,
      timestamp: this.timestamp,
    };
  }
}

module.exports = APIError;
