// spiderRunner.js - A module to handle running Python spiders
const { PythonShell } = require("python-shell");
const path = require("path");
const fs = require("fs");

/**
 * Run a spider by its name
 * @param {string} spiderId - The ID of the spider to run
 * @returns {Promise<object>} - A promise that resolves when the spider completes
 */
function runSpider(spiderId) {
  return new Promise((resolve, reject) => {
    // Check if the spider exists
    const spiderPath = path.join(
      __dirname,
      "../spiders",
      `${spiderId}_spider.py`
    );
    if (!fs.existsSync(spiderPath)) {
      return reject(new Error(`Spider ${spiderId} not found`));
    }

    // Set up options for PythonShell
    const options = {
      mode: "text",
      pythonPath: "python3",
      scriptPath: path.join(__dirname, "../scripts"),
      args: [spiderId],
    };

    // Run the spider
    PythonShell.run("spider_runner.py", options)
      .then((results) => {
        resolve({
          success: true,
          message: `Spider ${spiderId} completed successfully`,
          results,
        });
      })
      .catch((err) => {
        reject(new Error(`Failed to run spider ${spiderId}: ${err.message}`));
      });
  });
}

/**
 * Get available spiders
 * @returns {Promise<array>} - A promise that resolves with an array of available spiders
 */
function getAvailableSpiders() {
  return new Promise((resolve, reject) => {
    try {
      const configPath = path.join(__dirname, "../spiders/config.json");
      const configData = JSON.parse(fs.readFileSync(configPath, "utf8"));
      resolve(configData.spiders);
    } catch (error) {
      reject(new Error(`Failed to load available spiders: ${error.message}`));
    }
  });
}

/**
 * Generate an ebook from spider output
 * @param {string} spiderId - The ID of the spider
 * @param {string} format - The ebook format (epub, pdf, mobi)
 * @param {string} title - The title of the ebook
 * @returns {Promise<object>} - A promise that resolves when the ebook is generated
 */
function generateEbook(spiderId, format = "epub", title) {
  return new Promise((resolve, reject) => {
    // Generate a unique filename
    const filename = `${spiderId}_${Date.now()}.${format}`;
    const outputPath = path.join(__dirname, "../outputs", filename);

    // Set up options for PythonShell
    const options = {
      mode: "text",
      pythonPath: "python3",
      scriptPath: path.join(__dirname, "../scripts"),
      args: [spiderId, format, outputPath, title || spiderId],
    };

    // Run the ebook generation script
    PythonShell.run("make_ebook.py", options)
      .then(() => {
        resolve({
          success: true,
          message: `E-book generated successfully`,
          filename,
        });
      })
      .catch((err) => {
        reject(
          new Error(`Failed to generate ebook for ${spiderId}: ${err.message}`)
        );
      });
  });
}

module.exports = {
  runSpider,
  getAvailableSpiders,
  generateEbook,
};
