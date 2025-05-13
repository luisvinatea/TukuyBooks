/**
 * Download routes configuration
 */

const express = require("express");
const router = express.Router();
const spiderController = require("../controllers/spiderController");

// Download a specific file
router.get("/:filename", spiderController.downloadFile);

module.exports = router;
