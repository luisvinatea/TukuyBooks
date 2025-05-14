/**
 * Main entry point for the TukuyBooks API
 * This file initializes the Express app and configures middleware and routes
 */

const express = require("express");
const cors = require("cors");
const path = require("path");
const fs = require("fs");

// Import configurations
const config = require("./config");
const {
  errorHandler,
  notFoundHandler,
} = require("./middleware/errorMiddleware");
const { standardLimiter } = require("./middleware/rateLimitMiddleware");
const { createRequestLogger } = require("./middleware/loggerMiddleware");
const routes = require("./routes");
const { ensureDirectoryExists } = require("./utils");

// Initialize Express app
const app = express();
const PORT = config.server.port;

// Configure middleware
app.use(express.json());
app.use(cors(config.cors));
app.use(createRequestLogger()); // Use our custom request logger
app.use(express.urlencoded({ extended: true }));

// Apply rate limiting to all requests
app.use(standardLimiter);

// Ensure necessary directories exist
ensureDirectoryExists(config.paths.outputs);

// Mount API routes
app.use("/", routes); // Don't prefix with "/api" since Vercel already does that

// Global error handling middleware
app.use(errorHandler);

// Start the server if not on Vercel
if (!config.isVercel) {
  app.listen(PORT, () => {
    console.log(`TukuyBooks API server running on http://localhost:${PORT}`);
    console.log(`Environment: ${config.server.environment}`);
  });
}

// Export the Express API for Vercel
module.exports = app;
