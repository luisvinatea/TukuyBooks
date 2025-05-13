/**
 * Configuration module for TukuyBooks API
 * Centralizes all configuration variables and constants
 */

const path = require("path");

// Environment detection
const isProduction = process.env.NODE_ENV === "production";
const isVercel = process.env.VERCEL_DEPLOYMENT === "true";

// Server configuration
const serverConfig = {
  port: process.env.PORT || 3000,
  environment: process.env.NODE_ENV || "development",
};

// Path configuration
const pathConfig = {
  root: path.resolve(__dirname, "../.."),
  spiders: path.resolve(__dirname, "../../spiders"),
  outputs: path.resolve(__dirname, "../../outputs"),
  scripts: path.resolve(__dirname, "../../scripts"),
  static: path.resolve(__dirname, "../../static"),
};

// Spider configuration
const spiderConfig = {
  spiderConfigPath: path.join(pathConfig.spiders, "config.json"),
  pythonPath: process.env.PYTHON_PATH || "python3",
  maxRunTime: 300000, // 5 minutes in milliseconds
};

// CORS configuration
const corsConfig = {
  origin: isProduction ? [/tukuybooks\.vercel\.app$/] : "*",
  methods: ["GET", "POST", "PUT", "DELETE"],
  allowedHeaders: ["Content-Type", "Authorization"],
  credentials: true,
};

// Export all configurations
module.exports = {
  isProduction,
  isVercel,
  server: serverConfig,
  paths: pathConfig,
  spider: spiderConfig,
  cors: corsConfig,
};
