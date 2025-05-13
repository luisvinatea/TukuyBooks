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
    statusCode = err.statusCode;
  } else if (err.name === "ValidationError") {
    statusCode = 400;
  } else if (err.name === "UnauthorizedError") {
    statusCode = 401;
  } else if (err.name === "ForbiddenError") {
    statusCode = 403;
  } else if (err.name === "NotFoundError") {
    statusCode = 404;
  }

  // Create standardized error response
  const response = createResponse(
    false,
    err.message || "Internal server error",
    null,
    err
  );

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
