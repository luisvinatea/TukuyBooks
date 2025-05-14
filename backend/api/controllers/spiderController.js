/**
 * Spider controller handling spider-related API endpoints
 */

const path = require("path");
const fs = require("fs");
const sanitizeFilename = require("sanitize-filename");
const spiderService = require("../services/spiderService");
const { createResponse, asyncHandler, APIError } = require("../utils");
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
  if (!/^[a-zA-Z0-9_-]+$/.test(spiderId)) {
    throw new APIError(
      "Invalid spider ID format",
      400,
      "INVALID_PARAMETER",
      { parameter: "id" }
    );
  }

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
  const spiderId = req.params.id;

  if (!runId) {
    throw new APIError(
      "Missing required parameter: runId",
      400,
      "MISSING_PARAMETER",
      { parameter: "runId" }
    );
  }

  const status = spiderService.getSpiderRunStatus(runId);

  if (!status) {
    throw new APIError(`Run ID ${runId} not found`, 404, "RUN_NOT_FOUND", {
      runId,
      spiderId,
    });
  }

  // Verify that the status belongs to the requested spider
  if (status.spiderId !== spiderId) {
    throw new APIError(
      `Run ID ${runId} does not belong to spider ${spiderId}`,
      400,
      "INVALID_RUN_ID",
      { runId, requestedSpiderId: spiderId, actualSpiderId: status.spiderId }
    );
  }

  res.json(createResponse(true, "Spider status retrieved", { status }));
});

/**
 * Generate an ebook from spider data
 */
const generateEbook = asyncHandler(async (req, res) => {
  const spiderId = req.params.id;
  const { format = "epub", title, runId } = req.body;

  // Validate format parameter
  const validFormats = ["epub", "pdf", "mobi"];
  if (!validFormats.includes(format)) {
    throw new APIError(
      `Invalid format: ${format}. Supported formats are: ${validFormats.join(
        ", "
      )}`,
      400,
      "INVALID_FORMAT",
      { requestedFormat: format, validFormats }
    );
  }

  // If runId is provided, verify that the run exists and is completed
  if (runId) {
    const runStatus = spiderService.getSpiderRunStatus(runId);
    if (!runStatus) {
      throw new APIError(`Run ID ${runId} not found`, 404, "RUN_NOT_FOUND", {
        runId,
        spiderId,
      });
    }

    if (runStatus.spiderId !== spiderId) {
      throw new APIError(
        `Run ID ${runId} does not belong to spider ${spiderId}`,
        400,
        "INVALID_RUN_ID",
        {
          runId,
          requestedSpiderId: spiderId,
          actualSpiderId: runStatus.spiderId,
        }
      );
    }

    if (runStatus.status !== "completed") {
      throw new APIError(
        `Cannot generate ebook: spider run is not completed (status: ${runStatus.status})`,
        400,
        "INCOMPLETE_RUN",
        { runId, status: runStatus.status }
      );
    }
  }

  try {
    const result = await spiderService.generateEbook(spiderId, format, title);
    res.json(createResponse(true, "E-book generated successfully", result));
  } catch (error) {
    // APIErrors will be caught by the errorHandler middleware
    throw error;
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
  const filename = sanitizeFilename(req.params.filename);
  const filePath = path.resolve(paths.outputs, filename);

  // Ensure the filePath is within the outputs directory
  if (!filePath.startsWith(path.resolve(paths.outputs))) {
    throw new APIError(
      "Access to the requested file is forbidden",
      403,
      "FORBIDDEN_ACCESS",
      { requestedPath: filename }
    );
  }

  // Check if file exists
  if (!fs.existsSync(filePath)) {
    throw new APIError(`File ${filename} not found`, 404, "FILE_NOT_FOUND", {
      requestedFile: filename,
    });
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
