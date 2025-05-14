/**
 * Error handling middleware for the API
 */

const { createResponse } = require("../utils");

/**
 * Global error handler middleware
 */
function errorHandler(err, req, res, next) {
  console.error("API Error:", err);

  // Determine status code based on error type
  let statusCode = 500;

  if (err.statusCode) {
    // Use the statusCode from APIError or other custom error types
    statusCode = err.statusCode;
  } else if (err.name === "ValidationError") {
    statusCode = 400;
  } else if (err.name === "UnauthorizedError") {
    statusCode = 401;
  } else if (err.name === "ForbiddenError") {
    statusCode = 403;
  } else if (err.name === "NotFoundError") {
    statusCode = 404;
  } else if (err.name === "SyntaxError" && err.type === "entity.parse.failed") {
    // Handle JSON parse errors
    statusCode = 400;
    err.message = "Invalid JSON in request body";
    err.code = "INVALID_JSON";
  }

  // Add request ID for tracking (if configured)
  const requestId = req.id || req.headers["x-request-id"] || "unknown";

  // Log the error with request details
  console.error(
    `[${requestId}] [${req.method}] ${req.path} - Status ${statusCode}:`,
    {
      error: err.message,
      stack: process.env.NODE_ENV !== "production" ? err.stack : undefined,
      body: req.body ? JSON.stringify(req.body).substring(0, 200) : undefined,
      params: req.params,
      query: req.query,
    }
  );

  // Create standardized error response
  const response = createResponse(
    false,
    err.message || "Internal server error",
    null,
    err
  );

  // Send response
  res.status(statusCode).json(response);
}

/**
 * 404 Not Found middleware for handling undefined routes
 */
function notFoundHandler(req, res, next) {
  res
    .status(404)
    .json(createResponse(false, `Route not found: ${req.originalUrl}`));
}

module.exports = {
  errorHandler,
  notFoundHandler,
};
