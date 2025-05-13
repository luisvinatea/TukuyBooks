/**
 * Download routes configuration
 */

const express = require("express");
const router = express.Router();
const RateLimit = require("express-rate-limit");
const spiderController = require("../controllers/spiderController");

// Configure rate limiter: maximum of 100 requests per 15 minutes
const downloadLimiter = RateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
});

// Download a specific file
router.get("/:filename", downloadLimiter, spiderController.downloadFile);

module.exports = router;
