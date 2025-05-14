/**
 * Download routes configuration
 */

const express = require("express");
const router = express.Router();
const { downloadLimiter } = require("../middleware/rateLimitMiddleware");
const spiderController = require("../controllers/spiderController");

// Download a specific file
router.get("/:filename", downloadLimiter, spiderController.downloadFile);

module.exports = router;
