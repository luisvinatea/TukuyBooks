/**
 * Custom request logging middleware for debugging
 * Extends Morgan logger with additional context
 */

const morgan = require("morgan");
const chalk = require("chalk");

/**
 * Create a formatted logger for API requests
 */
function createRequestLogger() {
  // Create a custom token for response time in a more readable format
  morgan.token("response-time-formatted", (req, res) => {
    const time = res["_responseTime"];
    if (!time) return "unknown";

    // Format based on response time
    if (time < 100) return chalk.green(`${time.toFixed(2)}ms`);
    if (time < 500) return chalk.yellow(`${time.toFixed(2)}ms`);
    return chalk.red(`${time.toFixed(2)}ms`);
  });

  // Custom token for remote host with sanitization
  morgan.token("remote-addr", (req) => {
    const addr =
      req.headers["x-forwarded-for"] ||
      req.connection.remoteAddress ||
      req.socket.remoteAddress;

    // Basic logging for production environments to maintain privacy
    if (process.env.NODE_ENV === "production") {
      // Only keep first part of the IP address for privacy
      const parts = String(addr).split(".");
      if (parts.length === 4) {
        return `${parts[0]}.${parts[1]}.*.*`;
      }
      return "unknown";
    }

    return addr;
  });

  // Custom token for HTTP method with color
  morgan.token("method-colored", (req) => {
    const method = req.method.toUpperCase();
    switch (method) {
      case "GET":
        return chalk.cyan(method);
      case "POST":
        return chalk.green(method);
      case "PUT":
        return chalk.yellow(method);
      case "DELETE":
        return chalk.red(method);
      case "OPTIONS":
        return chalk.gray(method);
      default:
        return chalk.white(method);
    }
  });

  // Custom token for response status with color
  morgan.token("status-colored", (req, res) => {
    const status = res.statusCode;
    if (status >= 500) return chalk.red(status);
    if (status >= 400) return chalk.yellow(status);
    if (status >= 300) return chalk.cyan(status);
    return chalk.green(status);
  });

  // Custom token for API version
  morgan.token("api-version", (req) => {
    return req.headers["x-api-version"] || "v1";
  });

  // Custom logging format for development
  const developmentFormat = (tokens, req, res) => {
    // Capture response time
    res["_responseTime"] = parseFloat(tokens["response-time"](req, res));

    return [
      chalk.blue(`[API]`),
      tokens["remote-addr"](req, res),
      tokens.date(req, res, "iso"),
      tokens["method-colored"](req, res),
      tokens.url(req, res),
      tokens["status-colored"](req, res),
      tokens["response-time-formatted"](req, res),
      tokens.referrer(req, res) ? `Referrer: ${tokens.referrer(req, res)}` : "",
      tokens["user-agent"](req, res)
        ? `UA: ${tokens["user-agent"](req, res)}`
        : "",
    ]
      .filter(Boolean)
      .join(" ");
  };

  // Production format is more compact
  const productionFormat =
    ':remote-addr - [:date[iso]] ":method :url HTTP/:http-version" :status :res[content-length] :response-time ms';

  // Return the appropriate middleware based on environment
  return morgan(
    process.env.NODE_ENV === "production" ? productionFormat : developmentFormat
  );
}

/**
 * Request debugging middleware that logs detailed information about each request
 * This is particularly useful for diagnosing routing and parameter issues
 *
 * @returns {Function} Express middleware
 */
function createRequestDebugger() {
  return (req, res, next) => {
    // Create a unique ID for this request
    const requestId =
      req.id ||
      `req_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
    req.id = requestId;

    // Log basic request information
    console.log(`[${requestId}] ${req.method} ${req.originalUrl}`);

    // Log detailed request information
    console.log({
      path: req.path,
      baseUrl: req.baseUrl,
      params: req.params,
      query: req.query,
      hostname: req.hostname,
      ip: req.ip,
      protocol: req.protocol,
      headers: {
        origin: req.headers.origin,
        host: req.headers.host,
        referer: req.headers.referer,
        "user-agent": req.headers["user-agent"],
      },
    });

    // Continue with request handling
    next();
  };
}

module.exports = { createRequestLogger, createRequestDebugger };
