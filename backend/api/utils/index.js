/**
 * Utility functions for the TukuyBooks API
 */

const fs = require("fs");
const path = require("path");
const APIError = require("./APIError");

/**
 * Ensures a directory exists, creating it if necessary
 *
 * @param {string} dirPath - The path to check/create
 * @returns {boolean} - True if the directory exists or was created
 */
function ensureDirectoryExists(dirPath) {
  try {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
    return true;
  } catch (error) {
    console.error(`Error ensuring directory exists: ${dirPath}`, error);
    return false;
  }
}

/**
 * Creates a standardized API response object
 *
 * @param {boolean} success - Whether the operation was successful
 * @param {string} message - A message describing the result
 * @param {object} data - Any data to include in the response
 * @param {Error|APIError} error - An error object, if applicable
 * @returns {object} - A standardized response object
 */
function createResponse(success, message, data = null, error = null) {
  const response = {
    success,
    message,
    timestamp: new Date().toISOString(),
  };

  if (data) {
    response.data = data;
  }

  if (error && !success) {
    // Handle APIError objects vs standard errors
    if (error instanceof APIError) {
      response.error = {
        code: error.code || "UNKNOWN_ERROR",
        message: error.message,
        ...(error.details && { details: error.details }),
      };
    } else {
      response.error =
        process.env.NODE_ENV === "production"
          ? {
              code: "INTERNAL_ERROR",
              message: "An internal server error occurred",
            }
          : {
              code: error.code || "UNKNOWN_ERROR",
              message: error.message || "Unknown error",
              stack: error.stack,
              ...(error.details && { details: error.details }),
            };
    }
  }

  return response;
}

/**
 * Handles asynchronous request processing with error handling
 *
 * @param {Function} handler - Async function to handle the request
 * @returns {Function} - Express middleware function
 */
function asyncHandler(handler) {
  return async (req, res, next) => {
    try {
      await handler(req, res, next);
    } catch (error) {
      console.error("Request error:", error);
      res.status(500).json(createResponse(false, "Server error", null, error));
    }
  };
}

/**
 * Checks if a file exists and is accessible
 *
 * @param {string} filePath - Path to the file
 * @returns {Promise<boolean>} - True if the file exists and is accessible
 */
async function fileExists(filePath) {
  try {
    await fs.promises.access(filePath, fs.constants.F_OK);
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Validates and sanitizes route parameters
 *
 * @param {string} paramValue - The parameter value from req.params
 * @param {object} options - Options for validation
 * @param {boolean} options.alphanumericOnly - If true, only allows alphanumeric characters, hyphens and underscores
 * @param {boolean} options.required - If true, throws error if parameter is missing
 * @returns {string} - The sanitized parameter value
 */
function validateRouteParam(
  paramValue,
  options = { alphanumericOnly: true, required: true }
) {
  // Check if parameter exists
  if (!paramValue && options.required) {
    throw new APIError("Missing required route parameter", 400);
  }

  // For non-required params that are missing, just return null
  if (!paramValue && !options.required) {
    return null;
  }

  // Remove any query string for path parameters that might get them
  if (paramValue.includes("?")) {
    paramValue = paramValue.split("?")[0];
  }

  // Validate alphanumeric characters if needed
  if (options.alphanumericOnly && !/^[a-zA-Z0-9_-]+$/.test(paramValue)) {
    throw new APIError(
      `Invalid parameter format: ${paramValue}. Must contain only letters, numbers, underscores or hyphens.`,
      400
    );
  }

  return paramValue;
}

module.exports = {
  ensureDirectoryExists,
  createResponse,
  asyncHandler,
  fileExists,
  validateRouteParam,
  APIError,
};
