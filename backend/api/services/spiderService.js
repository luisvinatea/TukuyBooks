/**
 * Spider service module for managing spider operations
 */

const path = require("path");
const fs = require("fs").promises;
const { PythonShell } = require("python-shell");
const { v4: uuidv4 } = require("uuid");
const { spider: spiderConfig, paths } = require("../config");
const { ensureDirectoryExists, fileExists } = require("../utils");

// Store for tracking spider runs
const spiderRunStore = new Map();

/**
 * Get a list of all available spiders
 *
 * @returns {Promise<Array>} - List of spider objects
 */
async function getAvailableSpiders() {
  try {
    const configData = await fs.readFile(spiderConfig.spiderConfigPath, "utf8");
    return JSON.parse(configData).spiders;
  } catch (error) {
    console.error("Error loading spider configuration:", error);
    throw new Error(`Failed to load spider configuration: ${error.message}`);
  }
}

/**
 * Get a specific spider by ID
 *
 * @param {string} spiderId - The ID of the spider to find
 * @returns {Promise<Object|null>} - The spider object or null if not found
 */
async function getSpiderById(spiderId) {
  const spiders = await getAvailableSpiders();
  return spiders.find((spider) => spider.id === spiderId) || null;
}

/**
 * Run a spider by ID
 *
 * @param {string} spiderId - ID of the spider to run
 * @returns {Promise<Object>} - Run information including the runId
 */
async function runSpider(spiderId) {
  // Check if the spider exists
  const spider = await getSpiderById(spiderId);
  if (!spider) {
    throw new Error(`Spider ${spiderId} not found`);
  }

  // Generate a unique ID for this run
  const runId = uuidv4();

  // Set initial status
  const runStatus = {
    id: runId,
    spiderId,
    status: "starting",
    startTime: new Date().toISOString(),
    progress: 0,
  };

  // Store the run status
  spiderRunStore.set(runId, runStatus);

  // Set up options for the Python script
  const options = {
    mode: "text",
    pythonPath: spiderConfig.pythonPath,
    scriptPath: paths.scripts,
    args: [spiderId],
  };

  // Run the spider in a background process
  runStatus.status = "running";

  // Create a promise that will resolve when the spider finishes
  const spiderPromise = PythonShell.run("spider_runner.py", options)
    .then((results) => {
      // Update status on completion
      runStatus.status = "completed";
      runStatus.progress = 100;
      runStatus.endTime = new Date().toISOString();
      runStatus.results = results;
      return { runId, status: "completed" };
    })
    .catch((err) => {
      // Update status on error
      runStatus.status = "failed";
      runStatus.error = err.message;
      runStatus.endTime = new Date().toISOString();
      console.error(`Spider ${spiderId} run failed:`, err);
      throw new Error(`Spider run failed: ${err.message}`);
    });

  // Return the run ID immediately, don't wait for completion
  return { runId, status: runStatus.status };
}

/**
 * Get the status of a spider run
 *
 * @param {string} runId - The ID of the run to check
 * @returns {Object|null} - The run status or null if not found
 */
function getSpiderRunStatus(runId) {
  return spiderRunStore.get(runId) || null;
}

/**
 * Generate an ebook from spider data
 *
 * @param {string} spiderId - ID of the spider whose data to use
 * @param {string} format - Format of the ebook (epub, pdf, mobi)
 * @param {string} title - Optional title for the ebook
 * @returns {Promise<Object>} - Information about the generated ebook
 */
async function generateEbook(spiderId, format = "epub", title = null) {
  // Check if the spider exists
  const spider = await getSpiderById(spiderId);
  if (!spider) {
    throw new Error(`Spider ${spiderId} not found`);
  }

  // Check if the spider data file exists
  const dataFilePath = path.join(paths.outputs, `${spiderId}.jl`);
  if (!(await fileExists(dataFilePath))) {
    throw new Error(
      `No data found for spider ${spiderId}. Run the spider first.`
    );
  }

  // Ensure the outputs directory exists
  ensureDirectoryExists(paths.outputs);

  // Generate a filename for the ebook
  const filename = `${spiderId}_${Date.now()}.${format}`;
  const outputPath = path.join(paths.outputs, filename);

  // Set up options for the Python script
  const options = {
    mode: "text",
    pythonPath: spiderConfig.pythonPath,
    scriptPath: paths.scripts,
    args: [
      spiderId,
      format,
      outputPath,
      title || spider.output_prefix || spiderId,
    ],
  };

  // Run the ebook generation script
  try {
    await PythonShell.run("make_ebook.py", options);

    return {
      filename,
      format,
      path: outputPath,
      title: title || spider.output_prefix || spiderId,
    };
  } catch (error) {
    throw new Error(`Failed to generate ebook: ${error.message}`);
  }
}

/**
 * List all available ebooks
 *
 * @returns {Promise<Array>} - List of ebook objects
 */
async function listEbooks() {
  try {
    // Ensure the outputs directory exists
    ensureDirectoryExists(paths.outputs);

    const files = await fs.readdir(paths.outputs);

    // Filter for ebook files
    const ebookFiles = files.filter((file) => /\.(epub|pdf|mobi)$/i.test(file));

    // Get stats for each file
    const ebookPromises = ebookFiles.map(async (file) => {
      const filePath = path.join(paths.outputs, file);
      const stats = await fs.stat(filePath);

      // Extract spider ID from filename pattern
      const spiderIdMatch = file.match(/^([a-z0-9_]+)_\d+\.[a-z]+$/);
      const spiderId = spiderIdMatch ? spiderIdMatch[1] : "unknown";

      return {
        filename: file,
        spiderId,
        format: path.extname(file).substring(1),
        size: stats.size,
        created: stats.birthtime.toISOString(),
      };
    });

    return Promise.all(ebookPromises);
  } catch (error) {
    console.error("Error listing ebooks:", error);
    throw new Error(`Failed to list ebooks: ${error.message}`);
  }
}

module.exports = {
  getAvailableSpiders,
  getSpiderById,
  runSpider,
  getSpiderRunStatus,
  generateEbook,
  listEbooks,
};
