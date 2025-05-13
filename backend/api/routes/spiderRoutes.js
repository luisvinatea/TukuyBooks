/**
 * Spider routes configuration
 */

const express = require("express");
const router = express.Router();
const spiderController = require("../controllers/spiderController");

// Get all spiders
router.get("/", spiderController.getSpiders);

// Get a specific spider
router.get("/:id", spiderController.getSpiderById);

// Run a spider
router.post("/:id/run", spiderController.runSpider);

// Get spider run status
router.get("/:id/status", spiderController.getSpiderStatus);

// Generate an ebook from spider data
router.post("/:id/ebook", spiderController.generateEbook);

module.exports = router;
