/**
 * Spider controller handling spider-related API endpoints
 */

const path = require("path");
const fs = require("fs");
const sanitizeFilename = require("sanitize-filename");
const spiderService = require("../services/spiderService");
const { createResponse, asyncHandler } = require("../utils");
const { paths } = require("../config");

/**
 * Get list of available spiders
 */
const getSpiders = asyncHandler(async (req, res) => {
  const spiders = await spiderService.getAvailableSpiders();
  res.json(createResponse(true, "Spiders retrieved successfully", { spiders }));
});

/**
 * Get a specific spider by ID
 */
const getSpiderById = asyncHandler(async (req, res) => {
  const spiderId = req.params.id;
  const spider = await spiderService.getSpiderById(spiderId);

  if (!spider) {
    return res
      .status(404)
      .json(createResponse(false, `Spider ${spiderId} not found`));
  }

  res.json(createResponse(true, "Spider retrieved successfully", { spider }));
});

/**
 * Run a spider
 */
const runSpider = asyncHandler(async (req, res) => {
  const spiderId = req.params.id;

  try {
    const result = await spiderService.runSpider(spiderId);
    res.json(
      createResponse(true, `Spider ${spiderId} started successfully`, result)
    );
  } catch (error) {
    res
      .status(error.message.includes("not found") ? 404 : 500)
      .json(createResponse(false, error.message, null, error));
  }
});

/**
 * Get status of a spider run
 */
const getSpiderStatus = asyncHandler(async (req, res) => {
  const runId = req.query.runId;

  if (!runId) {
    return res
      .status(400)
      .json(createResponse(false, "Missing required parameter: runId"));
  }

  const status = spiderService.getSpiderRunStatus(runId);

  if (!status) {
    return res
      .status(404)
      .json(createResponse(false, `Run ID ${runId} not found`));
  }

  res.json(createResponse(true, "Spider status retrieved", { status }));
});

/**
 * Generate an ebook from spider data
 */
const generateEbook = asyncHandler(async (req, res) => {
  const spiderId = req.params.id;
  const { format = "epub", title } = req.body;

  try {
    const result = await spiderService.generateEbook(spiderId, format, title);
    res.json(createResponse(true, "E-book generated successfully", result));
  } catch (error) {
    const statusCode = error.message.includes("not found")
      ? 404
      : error.message.includes("Run the spider first")
      ? 400
      : 500;

    res
      .status(statusCode)
      .json(createResponse(false, error.message, null, error));
  }
});

/**
 * Get list of available ebooks
 */
const getEbooks = asyncHandler(async (req, res) => {
  try {
    const ebooks = await spiderService.listEbooks();
    res.json(createResponse(true, "Ebooks retrieved successfully", { ebooks }));
  } catch (error) {
    res
      .status(500)
      .json(createResponse(false, "Failed to retrieve ebooks", null, error));
  }
});

/**
 * Download a specific ebook
 */
const downloadFile = asyncHandler(async (req, res) => {
  const sanitizeFilename = require("sanitize-filename");
  const filename = sanitizeFilename(req.params.filename);
  const filePath = path.resolve(paths.outputs, filename);

  // Ensure the filePath is within the outputs directory
  if (!filePath.startsWith(path.resolve(paths.outputs))) {
    return res
      .status(403)
      .json(createResponse(false, "Access to the requested file is forbidden"));
  }

  // Check if file exists
  if (!fs.existsSync(filePath)) {
    return res
      .status(404)
      .json(createResponse(false, `File ${filename} not found`));
  }

  // Send the file for download
  res.download(filePath, filename, (err) => {
    if (err) {
      console.error(`Error downloading file ${filename}:`, err);
      // If headers are already sent, we can't respond with JSON
      if (!res.headersSent) {
        res
          .status(500)
          .json(createResponse(false, "Error during file download", null, err));
      }
    }
  });
});

module.exports = {
  getSpiders,
  getSpiderById,
  runSpider,
  getSpiderStatus,
  generateEbook,
  getEbooks,
  downloadFile,
};
