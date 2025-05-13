// Node.js backend for TukuyBooks API
const express = require("express");
const cors = require("cors");
const morgan = require("morgan");
const path = require("path");
const fs = require("fs");
const { PythonShell } = require("python-shell");
const { exec } = require("child_process");
const { v4: uuidv4 } = require("uuid");

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cors());
app.use(morgan("dev"));
app.use(express.urlencoded({ extended: true }));

// Store spider run statuses
const spiderRunStatus = {};

// Health check endpoint for Vercel
app.get("/_vercel/health", (req, res) => {
  res.status(200).json({ status: "ok", timestamp: new Date().toISOString() });
});

// Get available spiders
app.get("/api/spiders", (req, res) => {
  try {
    const configPath = path.join(__dirname, "../spiders/config.json");
    const configData = JSON.parse(fs.readFileSync(configPath, "utf8"));

    res.json({
      success: true,
      spiders: configData.spiders,
    });
  } catch (error) {
    console.error("Error loading spiders:", error);
    res.status(500).json({
      success: false,
      message: "Failed to load available spiders",
      error: error.message,
    });
  }
});

// Run a specific spider
app.post("/api/spiders/:id/run", (req, res) => {
  const spiderId = req.params.id;
  const runId = uuidv4();

  try {
    // Set up the path to the spider
    const spiderPath = path.join(
      __dirname,
      "../spiders",
      `${spiderId}_spider.py`
    );

    // Check if spider exists
    if (!fs.existsSync(spiderPath)) {
      return res.status(404).json({
        success: false,
        message: `Spider ${spiderId} not found`,
      });
    }

    // Store the run status
    spiderRunStatus[runId] = {
      spiderId,
      status: "running",
      startTime: new Date().toISOString(),
      progress: 0,
    };

    // PythonShell to run the spider
    const options = {
      mode: "text",
      pythonPath: "python3",
      scriptPath: path.join(__dirname, "../spiders"),
      args: [spiderId],
    };

    // Execute spider in background
    PythonShell.run(`${spiderId}_spider.py`, options)
      .then(() => {
        spiderRunStatus[runId].status = "completed";
        spiderRunStatus[runId].progress = 100;
        spiderRunStatus[runId].endTime = new Date().toISOString();
        console.log(`Spider ${spiderId} completed successfully`);
      })
      .catch((err) => {
        spiderRunStatus[runId].status = "failed";
        spiderRunStatus[runId].error = err.message;
        console.error(`Spider ${spiderId} failed:`, err);
      });

    // Return immediately with runId
    res.json({
      success: true,
      message: `Spider ${spiderId} started successfully`,
      runId,
    });
  } catch (error) {
    console.error(`Error starting spider ${spiderId}:`, error);
    res.status(500).json({
      success: false,
      message: `Failed to start spider ${spiderId}`,
      error: error.message,
    });
  }
});

// Get spider run status
app.get("/api/spiders/:id/status", (req, res) => {
  const runId = req.query.runId;

  if (!runId || !spiderRunStatus[runId]) {
    return res.status(404).json({
      success: false,
      message: "Run ID not found",
    });
  }

  res.json({
    success: true,
    status: spiderRunStatus[runId],
  });
});

// Generate ebook from scraped data
app.post("/api/spiders/:id/ebook", (req, res) => {
  const spiderId = req.params.id;
  const { format = "epub", title } = req.body;

  try {
    // Generate a unique filename
    const filename = `${spiderId}_${Date.now()}.${format}`;
    const outputPath = path.join(__dirname, "../outputs", filename);

    // Execute the ebook generation script
    const scriptPath = path.join(__dirname, "../scripts/make_ebook.py");

    const options = {
      mode: "text",
      pythonPath: "python3",
      scriptPath: path.join(__dirname, "../scripts"),
      args: [spiderId, format, outputPath, title || spiderId],
    };

    PythonShell.run("make_ebook.py", options)
      .then(() => {
        res.json({
          success: true,
          message: `E-book generated successfully`,
          filename,
        });
      })
      .catch((err) => {
        console.error(`Error generating ebook for ${spiderId}:`, err);
        res.status(500).json({
          success: false,
          message: `Failed to generate ebook for ${spiderId}`,
          error: err.message,
        });
      });
  } catch (error) {
    console.error(`Error generating ebook for ${spiderId}:`, error);
    res.status(500).json({
      success: false,
      message: `Failed to generate ebook for ${spiderId}`,
      error: error.message,
    });
  }
});

// Get list of available ebooks
app.get("/api/ebooks", (req, res) => {
  try {
    const outputsDir = path.join(__dirname, "../outputs");

    // Create outputs directory if it doesn't exist
    if (!fs.existsSync(outputsDir)) {
      fs.mkdirSync(outputsDir, { recursive: true });
    }

    const files = fs
      .readdirSync(outputsDir)
      .filter(
        (file) =>
          file.endsWith(".epub") ||
          file.endsWith(".pdf") ||
          file.endsWith(".mobi")
      )
      .map((file) => {
        const stats = fs.statSync(path.join(outputsDir, file));
        return {
          filename: file,
          size: stats.size,
          created: stats.birthtime.toISOString(),
        };
      });

    res.json({
      success: true,
      ebooks: files,
    });
  } catch (error) {
    console.error("Error listing ebooks:", error);
    res.status(500).json({
      success: false,
      message: "Failed to list available ebooks",
      error: error.message,
    });
  }
});

// Download a specific file
app.get("/api/download/:filename", (req, res) => {
  const filename = req.params.filename;
  const filePath = path.join(__dirname, "../outputs", filename);

  if (!fs.existsSync(filePath)) {
    return res.status(404).json({
      success: false,
      message: `File ${filename} not found`,
    });
  }

  res.download(filePath);
});

// Start the server if not on Vercel
if (process.env.NODE_ENV !== "production") {
  app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

// Export the Express API for Vercel
module.exports = app;
