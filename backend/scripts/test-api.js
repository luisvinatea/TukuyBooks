/**
 * API Tester script
 *
 * This script is used to test API connectivity from the backend directly.
 * Run with: node scripts/test-api.js
 */

const https = require("https");
const http = require("http");

// Use the Vercel API URL by default
const API_URL = process.env.API_URL || "https://tukuybooks.vercel.app/api";

/**
 * Make a GET request to the API
 *
 * @param {string} path - The API path to fetch
 * @returns {Promise<object>} - The response data
 */
function makeRequest(path) {
  return new Promise((resolve, reject) => {
    // Determine if we're using http or https
    const client = API_URL.startsWith("https") ? https : http;
    const url = `${API_URL}${path}`;

    console.log(`Testing endpoint: ${url}`);

    const req = client.get(url, (res) => {
      let data = "";

      // Log the status code
      console.log(`Status Code: ${res.statusCode}`);
      console.log(`Headers: ${JSON.stringify(res.headers, null, 2)}`);

      // Accumulate data
      res.on("data", (chunk) => {
        data += chunk;
      });

      // Handle end of response
      res.on("end", () => {
        try {
          // Try to parse JSON response
          const jsonData = JSON.parse(data);
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: jsonData,
          });
        } catch (error) {
          console.log("Response is not JSON:", data);
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: data,
          });
        }
      });
    });

    // Handle request errors
    req.on("error", (error) => {
      console.error(`Request error: ${error.message}`);
      reject(error);
    });

    // Set a timeout
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error("Request timed out after 10s"));
    });
  });
}

/**
 * Main function to run API tests
 */
async function runTests() {
  console.log(`Testing API at: ${API_URL}`);
  console.log("=".repeat(50));

  try {
    // Test health endpoint
    console.log("\n1. Testing /health endpoint");
    const healthResult = await makeRequest("/health");
    console.log(
      "Health check result:",
      JSON.stringify(healthResult.data, null, 2)
    );

    // Test spiders endpoint
    console.log("\n2. Testing /spiders endpoint");
    const spidersResult = await makeRequest("/spiders");
    console.log("Spiders result:", JSON.stringify(spidersResult.data, null, 2));

    // Test ebooks endpoint
    console.log("\n3. Testing /ebooks endpoint");
    const ebooksResult = await makeRequest("/ebooks");
    console.log("Ebooks result:", JSON.stringify(ebooksResult.data, null, 2));

    // Test non-existent endpoint
    console.log("\n4. Testing non-existent endpoint");
    const notFoundResult = await makeRequest("/nonexistent");
    console.log(
      "Not found result:",
      JSON.stringify(notFoundResult.data, null, 2)
    );

    console.log("\nAll tests completed!");
  } catch (error) {
    console.error("Test failed:", error);
  }
}

// Run the tests
runTests();
