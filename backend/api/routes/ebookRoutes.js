/**
 * Ebook routes configuration
 */

const express = require("express");
const router = express.Router();
const spiderController = require("../controllers/spiderController");

// Get all ebooks
router.get("/", spiderController.getEbooks);

module.exports = router;
