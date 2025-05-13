/**
 * Models and TypeScript-like interfaces for the API
 * This file provides documentation and structure for the API responses
 */

/**
 * @typedef {Object} ApiResponse
 * @property {boolean} success - Whether the request was successful
 * @property {string} message - A message describing the result
 * @property {Object} [data] - The response data (optional)
 * @property {string} [error] - Error message if success is false (optional)
 * @property {string} timestamp - ISO timestamp of when the response was generated
 */

/**
 * @typedef {Object} Spider
 * @property {string} id - Unique identifier for the spider
 * @property {string} name - Display name of the spider
 * @property {string} description - Description of what the spider does
 * @property {string} [module] - Python module containing the spider
 * @property {string} [class] - Python class name of the spider
 * @property {string} [output_prefix] - Prefix for output files
 */

/**
 * @typedef {Object} RunStatus
 * @property {string} id - Unique run identifier
 * @property {string} spiderId - ID of the spider being run
 * @property {string} status - Current status: "starting", "running", "completed", "failed"
 * @property {string} startTime - ISO timestamp when the run started
 * @property {string} [endTime] - ISO timestamp when the run completed (if applicable)
 * @property {number} progress - Progress percentage (0-100)
 * @property {Object} [results] - Any results from the spider run
 * @property {string} [error] - Error message if status is "failed"
 */

/**
 * @typedef {Object} Ebook
 * @property {string} filename - Filename of the ebook
 * @property {string} spiderId - ID of the spider that generated the data
 * @property {string} format - Format of the ebook: "epub", "pdf", "mobi"
 * @property {number} size - File size in bytes
 * @property {string} created - ISO timestamp when the ebook was created
 */

module.exports = {
  // This file is just for documentation purposes
};
