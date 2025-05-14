/**
 * api.js
 * This module provides an API wrapper for interacting with the TukuyBooks backend.
 */

class TukuyBooksAPI {
  /**
   * Create a new TukuyBooks API client
   *
   * @param {string} baseUrl - Base URL for the API
   */
  constructor(baseUrl = null) {
    // Check for user-provided configuration
    const config = window.TukuyBooksConfig || {};

    // Use config URL, provided URL, or auto-detect
    if (config.apiUrl) {
      baseUrl = config.apiUrl;
      if (config.debug) console.log(`Using configured API URL: ${baseUrl}`);
    } else if (baseUrl) {
      if (config.debug) console.log(`Using provided API URL: ${baseUrl}`);
    } else {
      // Auto-detect environment and set the appropriate API URL
      const hostname = window.location.hostname;
      if (hostname === "localhost" || hostname === "127.0.0.1") {
        baseUrl = "http://localhost:3000/api"; // Development
        if (config.debug) console.log(`Detected localhost, using: ${baseUrl}`);
      } else if (hostname === "luisvinatea.github.io") {
        baseUrl = "https://tukuybooks.vercel.app/api"; // Production from GitHub Pages
        if (config.debug)
          console.log(`Detected GitHub Pages, using: ${baseUrl}`);
      } else {
        baseUrl = "/api"; // Same-origin fallback
        if (config.debug) console.log(`Using same-origin API URL: ${baseUrl}`);
      }
    }

    this.baseUrl = baseUrl;
    this.activeRequests = 0;
    this.loadingIndicator = document.getElementById("global-loading");
    this.maxRetries = 3; // Maximum number of retries for failed requests
  }

  /**
   * Show the loading indicator
   */
  showLoading() {
    this.activeRequests++;
    if (this.loadingIndicator) {
      this.loadingIndicator.classList.add("active");
    }
  }

  /**
   * Hide the loading indicator if all requests are complete
   */
  hideLoading() {
    this.activeRequests--;
    if (this.activeRequests <= 0) {
      this.activeRequests = 0;
      if (this.loadingIndicator) {
        this.loadingIndicator.classList.remove("active");
      }
    }
  }

  /**
   * Make a fetch request with automatic retry
   *
   * @param {string} url - URL to fetch
   * @param {Object} options - Fetch options
   * @param {number} retries - Number of retries left
   * @returns {Promise<Object>} - Response data
   */
  async fetchWithRetry(url, options = {}, retries = this.maxRetries) {
    this.showLoading();

    try {
      const response = await fetch(url, options);
      const data = await response.json();

      if (!data.success && retries > 0 && response.status >= 500) {
        // Server error, retry after a delay
        console.log(`Retrying request to ${url}, ${retries} retries left`);
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return this.fetchWithRetry(url, options, retries - 1);
      }

      if (!data.success) {
        throw new Error(data.message || "API request failed");
      }

      return data;
    } catch (error) {
      if (
        retries > 0 &&
        (error.message.includes("network") ||
          error.message.includes("failed to fetch"))
      ) {
        // Network error, retry after a delay
        console.log(
          `Retrying request to ${url} due to network error, ${retries} retries left`
        );
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return this.fetchWithRetry(url, options, retries - 1);
      }
      throw error;
    } finally {
      this.hideLoading();
    }
  }

  /**
   * Test the API connection and return API status
   *
   * @returns {Promise<Object>} - API connection status
   */
  async testConnection() {
    try {
      // First try the direct health endpoint
      try {
        const response = await fetch(`${this.baseUrl}/health`, {
          method: "GET",
          headers: {
            Accept: "application/json",
            "Cache-Control": "no-cache",
          },
          mode: "cors",
          cache: "no-store",
        });

        if (response.ok) {
          const data = await response.json();
          return {
            connected: true,
            url: this.baseUrl,
            status: response.status,
            statusText: response.statusText,
            details: data,
          };
        }
      } catch (primaryError) {
        console.warn(
          "Primary health check failed, trying fallback",
          primaryError
        );
      }

      // If direct health check fails, try with query parameter (workaround for query param issue)
      try {
        const response = await fetch(`${this.baseUrl}?path=health`, {
          method: "GET",
          headers: {
            Accept: "application/json",
            "Cache-Control": "no-cache",
          },
          mode: "cors",
          cache: "no-store",
        });

        if (response.ok) {
          const data = await response.json();
          return {
            connected: true,
            url: this.baseUrl,
            status: response.status,
            statusText: response.statusText,
            details: data,
          };
        }

        return {
          connected: false,
          url: this.baseUrl,
          status: response.status,
          statusText: response.statusText,
          error: `API returned ${response.status}: ${response.statusText}`,
        };
      } catch (fallbackError) {
        return {
          connected: false,
          url: this.baseUrl,
          error: fallbackError.message || "Unknown connection error",
        };
      }
    } catch (error) {
      return {
        connected: false,
        url: this.baseUrl,
        error: error.message || "Unknown connection error",
      };
    }
  }

  /**
   * Get a list of available spiders
   *
   * @returns {Promise<Array>} - List of available spiders
   */
  async getSpiders() {
    try {
      // Use clean URL without query parameters
      const url = `${this.baseUrl}/spiders`;
      const data = await this.fetchWithRetry(url);
      return data.data.spiders;
    } catch (error) {
      console.error("Error getting spiders:", error);
      throw error;
    }
  }

  /**
   * Run a spider
   *
   * @param {string} spiderId - ID of the spider to run
   * @returns {Promise<Object>} - Status of the spider run
   */
  async runSpider(spiderId) {
    return this.fetchWithRetry(`${this.baseUrl}/spiders/${spiderId}/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  /**
   * Get the status of a spider run
   *
   * @param {string} spiderId - ID of the spider
   * @param {string} runId - ID of the spider run
   * @returns {Promise<Object>} - Status information
   */
  async getSpiderStatus(spiderId, runId) {
    return this.fetchWithRetry(
      `${this.baseUrl}/spiders/${spiderId}/status?runId=${runId}`
    );
  }

  /**
   * Create an ebook from scraped data
   *
   * @param {string} spiderId - ID of the spider that generated the data
   * @param {string} format - Format of the ebook ('epub' or 'pdf')
   * @returns {Promise<Object>} - Status of the ebook creation
   */
  async createEbook(spiderId, format = "epub") {
    try {
      const data = await this.fetchWithRetry(
        `${this.baseUrl}/spiders/${spiderId}/ebook`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ format }),
        }
      );
      return data;
    } catch (error) {
      console.error(`Error creating ${format} for spider ${spiderId}:`, error);
      throw error;
    }
  }

  /**
   * Get a list of available ebooks
   *
   * @returns {Promise<Array>} - List of available ebooks
   */
  async getAvailableEbooks() {
    try {
      const data = await this.fetchWithRetry(`${this.baseUrl}/ebooks`);
      return data.data.ebooks;
    } catch (error) {
      console.error("Error getting available ebooks:", error);
      throw error;
    }
  }

  /**
   * Get the download URL for a file
   *
   * @param {string} filename - Name of the file to download
   * @returns {string} - URL to download the file
   */
  getDownloadUrl(filename) {
    return `${this.baseUrl}/download/${encodeURIComponent(filename)}`;
  }
}

// Export the API client
export default TukuyBooksAPI;
