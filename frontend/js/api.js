/**
 * api.js
 * This module provides an API wrapper for interacting with the TukuyBooks backend.
 */

class TukuyBooksAPI {
  /**
   * Create a new TukuyBooks API client
   *
   * @param {string} baseUrl - Base URL for the API (default: /api)
   */
  constructor(baseUrl = "/api") {
    this.baseUrl = baseUrl;
  }

  /**
   * Get a list of available spiders
   *
   * @returns {Promise<Array>} - List of available spiders
   */
  async getSpiders() {
    try {
      const response = await fetch(`${this.baseUrl}/spiders`);
      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Failed to get spiders");
      }

      return data.spiders;
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
    try {
      const response = await fetch(`${this.baseUrl}/spiders/${spiderId}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Failed to run spider");
      }

      return data;
    } catch (error) {
      console.error(`Error running spider ${spiderId}:`, error);
      throw error;
    }
  }

  /**
   * Get the status of a spider
   *
   * @param {string} spiderId - ID of the spider
   * @returns {Promise<Object>} - Status information
   */
  async getSpiderStatus(spiderId) {
    try {
      const response = await fetch(
        `${this.baseUrl}/spiders/${spiderId}/status`
      );
      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Failed to get spider status");
      }

      return data;
    } catch (error) {
      console.error(`Error getting status for spider ${spiderId}:`, error);
      throw error;
    }
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
      const response = await fetch(
        `${this.baseUrl}/spiders/${spiderId}/ebook`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ format }),
        }
      );

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Failed to create ebook");
      }

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
      const response = await fetch(`${this.baseUrl}/ebooks`);
      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Failed to get available ebooks");
      }

      return data.ebooks;
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
