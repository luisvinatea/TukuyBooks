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
  res.status(200).json({
    success: true,
    message: "TukuyBooks API is operational",
    timestamp: new Date().toISOString(),
    version: "1.0.0",
    environment: process.env.NODE_ENV || "development",
  });
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
