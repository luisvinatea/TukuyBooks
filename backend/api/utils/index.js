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
 * @param {Error} error - An error object, if applicable
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
    response.error =
      process.env.NODE_ENV === "production"
        ? error.message
        : {
            message: error.message,
            stack: error.stack,
          };
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

module.exports = {
  ensureDirectoryExists,
  createResponse,
  asyncHandler,
  fileExists,
  APIError,
};
