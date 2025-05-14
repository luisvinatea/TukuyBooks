/**
 * Main routes file that aggregates all API routes
 */

const express = require("express");
const router = express.Router();
const spiderRoutes = require("./spiderRoutes");
const ebookRoutes = require("./ebookRoutes");
const { notFoundHandler } = require("../middleware/errorMiddleware");
const { serveApiDoc } = require("../middleware/apiDocMiddleware");

// Health check endpoint for Vercel
router.get("/_vercel/health", (req, res) => {
  res.status(200).json({
    status: "ok",
    timestamp: new Date().toISOString(),
  });
});

// Public health check endpoint for client applications
router.get("/health", (req, res) => {
  // Ensure CORS headers are set for health endpoint specifically
  const allowedOrigins = [
    "https://luisvinatea.github.io",
    "https://localhost:3000",
    "http://localhost:3000",
    "http://localhost:8080",
  ];
  const origin = req.headers.origin;

  // Either set the specific origin if it's in our allowed list, or use * for development
  if (origin && allowedOrigins.includes(origin)) {
    res.set("Access-Control-Allow-Origin", origin);
  } else {
    res.set("Access-Control-Allow-Origin", "*");
  }

  // Set remaining CORS headers
  res.set("Access-Control-Allow-Credentials", "true");
  res.set("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.set(
    "Access-Control-Allow-Headers",
    "Content-Type, Authorization, X-Requested-With, Accept, Cache-Control"
  );

  res.status(200).json({
    success: true,
    message: "TukuyBooks API is operational",
    timestamp: new Date().toISOString(),
    version: "1.0.0",
    environment: process.env.NODE_ENV || "development",
  });
});

// Additional health endpoint that handles query params for frontend testing
router.get("*", (req, res, next) => {
  // Handle requests with health in the path (frontend sometimes adds ?path=health)
  if (
    req.path.includes("health") ||
    (req.query && req.query.path === "health")
  ) {
    // Ensure CORS headers are set for query-based health endpoint
    const allowedOrigins = [
      "https://luisvinatea.github.io",
      "https://localhost:3000",
      "http://localhost:3000",
      "http://localhost:8080",
    ];
    const origin = req.headers.origin;

    // Either set the specific origin if it's in our allowed list, or use * for development
    if (origin && allowedOrigins.includes(origin)) {
      res.set("Access-Control-Allow-Origin", origin);
    } else {
      res.set("Access-Control-Allow-Origin", "*");
    }

    // Set remaining CORS headers
    res.set("Access-Control-Allow-Credentials", "true");
    res.set("Access-Control-Allow-Methods", "GET, OPTIONS");
    res.set(
      "Access-Control-Allow-Headers",
      "Content-Type, Authorization, X-Requested-With, Accept, Cache-Control"
    );

    return res.status(200).json({
      success: true,
      message: "TukuyBooks API is operational (query param handler)",
      timestamp: new Date().toISOString(),
      version: "1.0.0",
      environment: process.env.NODE_ENV || "development",
    });
  }
  // Not a health check, continue with normal routing
  next();
});

// API documentation endpoint
router.get("/docs", serveApiDoc);

// API routes
router.use("/spiders", spiderRoutes);
router.use("/ebooks", ebookRoutes);
router.use("/download", require("./downloadRoutes"));

// Handle 404 for undefined routes
router.use(notFoundHandler);

module.exports = router;
