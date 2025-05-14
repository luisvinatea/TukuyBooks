/**
 * Spider routes configuration
 */

const express = require("express");
const router = express.Router();
const spiderController = require("../controllers/spiderController");
const { heavyOperationsLimiter } = require("../middleware/rateLimitMiddleware");

// Get all spiders
router.get("/", spiderController.getSpiders);

// Get a specific spider
router.get("/:id", spiderController.getSpiderById);

// Run a spider (resource-intensive operation)
router.post("/:id/run", heavyOperationsLimiter, spiderController.runSpider);

// Get spider run status
router.get("/:id/status", spiderController.getSpiderStatus);

// Generate an ebook from spider data (resource-intensive operation)
router.post(
  "/:id/ebook",
  heavyOperationsLimiter,
  spiderController.generateEbook
);

module.exports = router;
