#!/usr/bin/env node

/**
 * API Validator script
 * Ensures API endpoints are consistent with API documentation
 */

const fs = require("fs");
const path = require("path");
const apiDoc = require("../api/config/api-doc");

console.log("Validating API structure against API documentation...");

// Load route files
const routesDir = path.join(__dirname, "../api/routes");
const controllerDir = path.join(__dirname, "../api/controllers");

// Get all defined routes in the API doc
const apiPaths = Object.keys(apiDoc.paths);
console.log(`Found ${apiPaths.length} paths defined in API documentation`);

// Check controller files for implemented methods
let implementedEndpoints = [];
let issues = [];

// Read controller files
const controllerFiles = fs
  .readdirSync(controllerDir)
  .filter((file) => file.endsWith(".js"));
controllerFiles.forEach((file) => {
  const controllerPath = path.join(controllerDir, file);
  const controller = require(controllerPath);

  console.log(`Checking controller: ${file}`);

  // Check each method in the controller
  Object.keys(controller).forEach((method) => {
    const func = controller[method];
    if (typeof func === "function") {
      // Extract information from the function name
      let endpoint = null;

      // Match common patterns like getSpiders, runSpider, getEbooks, etc.
      if (method.startsWith("get")) {
        const resource = method.replace("get", "").toLowerCase();
        endpoint = `/${resource.endsWith("s") ? resource : resource + "s"}`;
      } else if (method.match(/^(create|add)/)) {
        const resource = method.replace(/^(create|add)/, "").toLowerCase();
        endpoint = `/${resource.endsWith("s") ? resource : resource + "s"}`;
      } else if (method.match(/^(update|edit)/)) {
        const resource = method.replace(/^(update|edit)/, "").toLowerCase();
        endpoint = `/${
          resource.endsWith("s") ? resource : resource + "s"
        }/{id}`;
      } else if (method.match(/^(delete|remove)/)) {
        const resource = method.replace(/^(delete|remove)/, "").toLowerCase();
        endpoint = `/${
          resource.endsWith("s") ? resource : resource + "s"
        }/{id}`;
      }

      if (endpoint) {
        implementedEndpoints.push(endpoint);

        // Check if this endpoint is documented
        if (!apiPaths.some((path) => path.startsWith(endpoint))) {
          issues.push(
            `Warning: Implemented endpoint ${endpoint} (${method}) not found in API documentation`
          );
        }
      }
    }
  });
});

// Check for documented endpoints that are not implemented
apiPaths.forEach((path) => {
  if (!implementedEndpoints.some((impl) => path.startsWith(impl))) {
    issues.push(
      `Warning: Documented endpoint ${path} not implemented in controllers`
    );
  }
});

// Show issues
if (issues.length > 0) {
  console.log("\nIssues found:");
  issues.forEach((issue) => console.log(`- ${issue}`));
} else {
  console.log("\nAll good! API documentation matches implementation.");
}

console.log("\nValidation complete!");
