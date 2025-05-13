/**
 * TukuyBooks API Type Definitions
 *
 * This file contains TypeScript-like definitions for the API
 * to improve developer experience and code quality.
 */

/**
 * Spider object representing a web scraping spider
 * @typedef {Object} Spider
 * @property {string} id - Unique identifier
 * @property {string} name - Display name
 * @property {string} description - Detailed description
 * @property {string} [module] - Python module containing the spider
 * @property {string} [class] - Python class name
 * @property {string} [output_prefix] - Prefix for output files
 */

/**
 * Spider run status information
 * @typedef {Object} SpiderRunStatus
 * @property {string} id - Run identifier
 * @property {string} spiderId - Spider identifier
 * @property {'starting'|'running'|'completed'|'failed'} status - Current run status
 * @property {string} startTime - ISO timestamp of when the run began
 * @property {string} [endTime] - ISO timestamp of when the run ended (if complete)
 * @property {number} progress - Progress percentage (0-100)
 * @property {Object} [results] - Results data if available
 * @property {string} [error] - Error message if status is 'failed'
 */

/**
 * Ebook object representing a generated ebook
 * @typedef {Object} Ebook
 * @property {string} filename - Filename
 * @property {string} spiderId - ID of the spider that generated the content
 * @property {'epub'|'pdf'|'mobi'} format - Format of the ebook
 * @property {number} size - File size in bytes
 * @property {string} created - ISO timestamp of when it was created
 */

/**
 * API Response format for all endpoints
 * @typedef {Object} ApiResponse
 * @property {boolean} success - Whether the operation succeeded
 * @property {string} message - Human-readable message
 * @property {string} timestamp - ISO timestamp of the response
 * @property {Object} [data] - Response data if success is true
 * @property {Object} [error] - Error details if success is false
 */

/**
 * Response for the /spiders endpoint
 * @typedef {Object} SpidersResponse
 * @property {boolean} success
 * @property {string} message
 * @property {string} timestamp
 * @property {Object} data
 * @property {Spider[]} data.spiders - Array of available spiders
 */

/**
 * Response for the /spiders/{id}/run endpoint
 * @typedef {Object} SpiderRunResponse
 * @property {boolean} success
 * @property {string} message
 * @property {string} timestamp
 * @property {string} runId - ID to track the spider run
 * @property {'starting'|'running'} status - Initial status
 */

/**
 * Response for the /spiders/{id}/status endpoint
 * @typedef {Object} SpiderStatusResponse
 * @property {boolean} success
 * @property {string} message
 * @property {string} timestamp
 * @property {Object} data
 * @property {SpiderRunStatus} data.status - Current status details
 */

/**
 * Response for the /spiders/{id}/ebook endpoint
 * @typedef {Object} EbookGenerationResponse
 * @property {boolean} success
 * @property {string} message
 * @property {string} timestamp
 * @property {Object} data
 * @property {string} data.filename - Generated filename
 * @property {string} data.format - Format of the ebook
 * @property {string} data.path - Path to the generated file
 * @property {string} data.title - Title of the ebook
 */

/**
 * Response for the /ebooks endpoint
 * @typedef {Object} EbooksResponse
 * @property {boolean} success
 * @property {string} message
 * @property {string} timestamp
 * @property {Object} data
 * @property {Ebook[]} data.ebooks - Array of available ebooks
 */

/**
 * Error response format
 * @typedef {Object} ErrorResponse
 * @property {boolean} success - Always false for errors
 * @property {string} message - Human-readable error message
 * @property {string} timestamp - ISO timestamp of the error
 * @property {Object} error - Error details
 * @property {string} error.code - Error code
 * @property {Object} [error.details] - Additional error information
 */
