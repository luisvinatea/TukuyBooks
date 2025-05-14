/**
 * Rate limiting middleware for TukuyBooks API
 * Helps prevent abuse and improves API stability
 */

const rateLimit = require("express-rate-limit");
const { APIError } = require("../utils");

/**
 * Create rate limiters with different configurations
 */

// Health check rate limiter - much more lenient
const healthCheckLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 30, // limit each IP to 30 requests per minute for health checks
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: true, // Return success even when rate limited for health check endpoints
    message: "Rate limit reached, but API is operational",
    warning: "You are sending too many health check requests",
    timestamp: new Date().toISOString(),
  },
  // Simple handler for health check rate limiting
  handler: (req, res) => {
    res.status(200).json({
      success: true,
      message: "TukuyBooks API is operational, but rate limit reached",
      timestamp: new Date().toISOString(),
      warning:
        "Health check rate limit exceeded, please reduce request frequency",
    });
  },
  // Skip if not a health check endpoint
  skip: (req) => {
    return !(
      req.path.includes("health") ||
      (req.query && req.query.path === "health")
    );
  },
});

// Standard API rate limiter
const standardLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 150, // increased limit from 100 to 150 requests per windowMs
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
  message: {
    success: false,
    message: "Too many requests, please try again later.",
    error: {
      code: "RATE_LIMIT_EXCEEDED",
      details: "You have exceeded the rate limit for this endpoint.",
    },
    timestamp: new Date().toISOString(),
  },
  handler: (req, res, next, options) => {
    next(
      new APIError(
        "Too many requests, please try again later.",
        429,
        "RATE_LIMIT_EXCEEDED",
        {
          retryAfter: res.getHeader("Retry-After"),
          limit: res.getHeader("X-RateLimit-Limit"),
        }
      )
    );
  },
  // Skip rate limiting for health endpoints (they use their own limiter)
  skip: (req) => {
    return (
      req.path.includes("health") || (req.query && req.query.path === "health")
    );
  },
});

// Heavy operations limiter (e.g., spider runs, ebook creation)
const heavyOperationsLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // limit each IP to 10 requests per windowMs
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: false,
    message: "Too many heavy operations, please try again later.",
    error: {
      code: "HEAVY_OPERATION_LIMIT_EXCEEDED",
      details: "You have exceeded the limit for resource-intensive operations.",
    },
    timestamp: new Date().toISOString(),
  },
  handler: (req, res, next, options) => {
    next(
      new APIError(
        "Too many resource-intensive operations, please try again later.",
        429,
        "HEAVY_OPERATION_LIMIT_EXCEEDED",
        {
          retryAfter: res.getHeader("Retry-After"),
          limit: res.getHeader("X-RateLimit-Limit"),
        }
      )
    );
  },
});

// Download limiter
const downloadLimiter = rateLimit({
  windowMs: 30 * 60 * 1000, // 30 minutes
  max: 20, // limit each IP to 20 downloads per windowMs
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: false,
    message: "Too many download requests, please try again later.",
    error: {
      code: "DOWNLOAD_LIMIT_EXCEEDED",
      details: "You have exceeded the download rate limit.",
    },
    timestamp: new Date().toISOString(),
  },
  handler: (req, res, next, options) => {
    next(
      new APIError(
        "Too many download requests, please try again later.",
        429,
        "DOWNLOAD_LIMIT_EXCEEDED",
        {
          retryAfter: res.getHeader("Retry-After"),
        }
      )
    );
  },
});

module.exports = {
  standardLimiter,
  healthCheckLimiter,
  heavyOperationsLimiter,
  downloadLimiter,
};
