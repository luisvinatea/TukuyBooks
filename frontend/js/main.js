/**
 * main.js
 * Main JavaScript file for the TukuyBooks web interface
 */

import TukuyBooksAPI from "./api.js";

// Create API client instance
const api = new TukuyBooksAPI();

// DOM elements
const spiderSelect = document.getElementById("spider-select");
const runSpiderBtn = document.getElementById("run-spider-btn");
const spiderStatus = document.getElementById("spider-status");
const statusText = document.getElementById("status-text");
const statusDetails = document.getElementById("status-details");
const progressBar = document.getElementById("progress-bar");
const createEbookBtn = document.getElementById("create-ebook-btn");
const formatRadios = document.querySelectorAll('input[name="format"]');
const ebooksContainer = document.querySelector(".ebooks");
const ebookSearch = document.getElementById("ebook-search");
const searchClearBtn = document.getElementById("search-clear-btn");

// Modal elements
const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modal-title");
const modalMessage = document.getElementById("modal-message");
const modalOkBtn = document.getElementById("modal-ok-btn");
const closeBtn = document.querySelector(".close-btn");

// Add theme toggle button
const themeToggle = document.getElementById("theme-toggle");

// DOM elements for activity panel
const activityPanel = document.getElementById("activity-panel");
const activityToggle = document.getElementById("activity-toggle");
const closeActivityPanelBtn = document.getElementById(
  "close-activity-panel-btn"
);
const clearActivitiesBtn = document.getElementById("clear-activities-btn");
const activityList = document.getElementById("activity-list");

// User activity tracking
class ActivityTracker {
  constructor() {
    this.activities = JSON.parse(localStorage.getItem("userActivities")) || [];
    this.maxItems = 20; // Maximum number of activities to store
  }

  // Add a new activity
  addActivity(type, details) {
    const activity = {
      type,
      details,
      timestamp: new Date().toISOString(),
    };

    // Add to the beginning of the array
    this.activities.unshift(activity);

    // Limit the number of items
    if (this.activities.length > this.maxItems) {
      this.activities = this.activities.slice(0, this.maxItems);
    }

    // Save to localStorage
    this.saveActivities();

    return activity;
  }

  // Get all activities
  getActivities() {
    return this.activities;
  }

  // Get activities by type
  getActivitiesByType(type) {
    return this.activities.filter((activity) => activity.type === type);
  }

  // Save activities to localStorage
  saveActivities() {
    localStorage.setItem("userActivities", JSON.stringify(this.activities));
  }

  // Clear all activities
  clearActivities() {
    this.activities = [];
    this.saveActivities();
  }
}

// Create activity tracker instance
const activityTracker = new ActivityTracker();

// State variables
let selectedSpider = null;
let statusCheckInterval = null;
let isProcessing = false;
let notificationTimeout = null;
let currentTheme = localStorage.getItem("theme") || "light";

// Check browser compatibility
function checkBrowserCompatibility() {
  // Check for necessary browser features
  const requiredFeatures = {
    fetch: typeof fetch !== "undefined",
    localStorage: typeof localStorage !== "undefined",
    promise: typeof Promise !== "undefined",
    asyncAwait: (function () {
      try {
        new Function("async () => {}");
        return true;
      } catch (e) {
        return false;
      }
    })(),
  };

  // Check if any features are missing
  const missingFeatures = Object.entries(requiredFeatures)
    .filter(([_, supported]) => !supported)
    .map(([feature]) => feature);

  if (missingFeatures.length > 0) {
    const message = `Your browser is missing some required features: ${missingFeatures.join(
      ", "
    )}. Please update your browser for the best experience.`;
    showNotification(message, "warning");
    console.warn("Browser compatibility issue:", message);
    return false;
  }

  return true;
}

// Initialize the application
async function init() {
  // Check browser compatibility
  checkBrowserCompatibility();

  // Initialize theme
  initTheme();

  // Set up keyboard navigation
  setupKeyboardNavigation();

  // Set up image loading handlers
  setupImageLoadHandlers();

  // Set up search functionality
  setupSearch();

  // Set up event listeners
  setupEventListeners();

  // Validate backend connection
  if (!(await validateBackendConnection())) {
    showNotification(
      "Could not connect to the backend server. Some features may not work.",
      "warning"
    );
    return;
  }

  try {
    // Load available spiders
    const spiders = await api.getSpiders();
    populateSpiderSelect(spiders);

    // Load available ebooks
    await loadAvailableEbooks();
  } catch (error) {
    console.error("Initialization error:", error);
    showNotification(
      "Failed to initialize the application: " + error.message,
      "error"
    );
  }
}

// Initialize theme based on user preference
function initTheme() {
  // Check if user has a saved preference
  if (currentTheme === "dark") {
    document.body.classList.add("dark-theme");
  } else {
    document.body.classList.remove("dark-theme");
  }
}

// Toggle between light and dark theme
function toggleTheme() {
  if (document.body.classList.contains("dark-theme")) {
    document.body.classList.remove("dark-theme");
    currentTheme = "light";
  } else {
    document.body.classList.add("dark-theme");
    currentTheme = "dark";
  }

  // Save preference to local storage
  localStorage.setItem("theme", currentTheme);

  // Show notification
  showNotification(`Switched to ${currentTheme} theme`, "info");
}

// Set up keyboard navigation for accessibility
function setupKeyboardNavigation() {
  // Modal keyboard control
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      // Close modal with Escape key
      if (modal.style.display === "block") {
        closeModal();
      }

      // Close activity panel with Escape key
      if (activityPanel.classList.contains("active")) {
        toggleActivityPanel();
      }
    }
  });

  // Add keyboard support for buttons and interactive elements
  const interactiveElements = [
    runSpiderBtn,
    createEbookBtn,
    document.getElementById("refresh-ebooks-btn"),
    themeToggle,
    activityToggle,
    searchClearBtn,
  ].filter(Boolean); // Filter out any null elements

  interactiveElements.forEach((element) => {
    if (!element) return;

    // Make sure it's focusable
    if (
      !element.getAttribute("tabindex") &&
      element.tagName !== "BUTTON" &&
      element.tagName !== "A" &&
      element.tagName !== "INPUT" &&
      element.tagName !== "SELECT"
    ) {
      element.setAttribute("tabindex", "0");
    }

    element.addEventListener("keydown", (e) => {
      // Activate on Enter or Space
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        element.click();
      }
    });
  });

  // Add keyboard support for format radio options
  const formatOptions = document.querySelectorAll(".format-option label");
  formatOptions.forEach((label) => {
    label.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        const input = document.getElementById(label.getAttribute("for"));
        if (input) {
          input.checked = true;
        }
      }
    });
  });

  // Add focus trap for modal
  if (modal) {
    modal.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        const focusableElements = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          // If shift + tab and on first element, focus the last element
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          // If tab and on last element, focus the first element
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    });
  }

  // Make download and share buttons accessible via keyboard
  const makeEbookActionsAccessible = () => {
    document
      .querySelectorAll(".download-link, .share-btn")
      .forEach((element) => {
        if (!element.getAttribute("tabindex")) {
          element.setAttribute("tabindex", "0");
        }

        element.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            element.click();
          }
        });
      });
  };

  // Apply after ebooks are loaded
  const originalLoadAvailableEbooks = loadAvailableEbooks;
  loadAvailableEbooks = async function () {
    await originalLoadAvailableEbooks();
    makeEbookActionsAccessible();
  };
}

// Set up image loading handlers
function setupImageLoadHandlers() {
  // Get all images
  const images = document.querySelectorAll("img");

  // Add loading and error handling
  images.forEach((img) => {
    // Skip if already has event listeners
    if (img.dataset.eventsAdded) return;

    // Add loading attribute for better UX
    img.setAttribute("loading", "lazy");

    // Add error handler
    img.addEventListener("error", () => {
      img.src = "img/placeholder.png"; // Fall back to placeholder
      img.alt = "Image failed to load";
    });

    // Mark as processed
    img.dataset.eventsAdded = "true";
  });
}

// Load available spiders from API
async function loadSpiders() {
  try {
    const spiders = await api.getSpiders();

    // Clear existing options
    spiderSelect.innerHTML = '<option value="">Please select a source</option>';

    // Add options for each spider
    spiders.forEach((spider) => {
      const option = document.createElement("option");
      option.value = spider.id;
      option.textContent = spider.name;
      spiderSelect.appendChild(option);
    });

    console.log("Loaded spiders:", spiders);
  } catch (error) {
    console.error("Error loading spiders:", error);
    showModal(
      "Error",
      "Failed to load documentation sources. Please try again later."
    );
  }
}

// Load available ebooks and populate the download section
async function loadAvailableEbooks() {
  const ebooksContainer = document.querySelector(".ebooks");

  // Add loading state
  ebooksContainer.innerHTML =
    '<div class="loading-container"><div class="loading-spinner"></div><p>Loading available ebooks...</p></div>';

  try {
    const ebooks = await api.getAvailableEbooks();

    if (Array.isArray(ebooks) && ebooks.length > 0) {
      // Clear the container
      ebooksContainer.innerHTML = "";

      // Sort ebooks by date (newest first)
      ebooks.sort(
        (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
      );

      // Create and append ebook cards
      ebooks.forEach((ebook) => {
        // Create ebook card
        const ebookCard = document.createElement("div");
        ebookCard.className = "ebook-card";

        // Get the spider name from the filename if available
        let spiderName = ebook.spider_id || "Unknown";

        // Try to get a more readable name
        try {
          if (ebook.filename) {
            const filenameParts = ebook.filename.split("-");
            if (filenameParts.length > 1) {
              spiderName =
                filenameParts[0].charAt(0).toUpperCase() +
                filenameParts[0].slice(1);
            }
          }
        } catch (e) {
          console.error("Error parsing spider name:", e);
        }

        // Format the creation date
        let createdAt = "Unknown date";
        if (ebook.created_at) {
          const date = new Date(ebook.created_at);
          createdAt = date.toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          });
        }

        // Determine the file type and icon
        const isEpub = ebook.filename && ebook.filename.endsWith(".epub");
        const isPdf = ebook.filename && ebook.filename.endsWith(".pdf");

        let formatIcon = '<i class="fas fa-file"></i>';
        let formatName = "Unknown";

        if (isEpub) {
          formatIcon = '<i class="fas fa-book"></i>';
          formatName = "EPUB";
        } else if (isPdf) {
          formatIcon = '<i class="fas fa-file-pdf"></i>';
          formatName = "PDF";
        }

        // Build the card HTML
        ebookCard.innerHTML = `
          <div class="ebook-format">${formatIcon}</div>
          <div class="ebook-info">
            <h3 class="ebook-title">${spiderName}</h3>
            <p class="ebook-details">
              <span class="format-badge">${formatName}</span>
              <span class="created-date">${createdAt}</span>
            </p>
          </div>
          <div class="ebook-actions">
            <a href="#" class="download-link" data-filename="${ebook.filename}" title="Download this ebook">
              <i class="fas fa-download"></i>
            </a>
            <button class="share-btn" data-title="${spiderName}" data-filename="${ebook.filename}" title="Share this ebook">
              <i class="fas fa-share-alt"></i>
            </button>
          </div>
        `;

        // Append to container
        ebooksContainer.appendChild(ebookCard);
      });

      // Add event listeners to the buttons
      document.querySelectorAll(".download-link").forEach((link) => {
        link.addEventListener("click", handleDownload);
      });

      document.querySelectorAll(".share-btn").forEach((btn) => {
        btn.addEventListener("click", handleShare);
      });
    } else {
      // No ebooks found
      ebooksContainer.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-book-open"></i>
          <p>No ebooks available yet. Generate one using the form above!</p>
        </div>
      `;
    }
  } catch (error) {
    console.error("Error loading ebooks:", error);
    ebooksContainer.innerHTML = `
      <div class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <p>Failed to load available ebooks. Please try again.</p>
        <button class="btn secondary-btn" onclick="loadAvailableEbooks()">Retry</button>
      </div>
    `;
  }
}

// Handle refresh ebooks button click
function handleRefreshEbooks() {
  loadAvailableEbooks();
  showNotification("Refreshing ebook list...", "info");
}

// Create an ebook card element
function createEbookCard(ebook) {
  const card = document.createElement("div");
  card.className = "ebook-card";

  // Determine the icon based on the title
  let icon = "book";
  if (ebook.title.toLowerCase().includes("python")) {
    icon = "python fab";
  } else if (ebook.title.toLowerCase().includes("javascript")) {
    icon = "js fab";
  } else if (ebook.title.toLowerCase().includes("java")) {
    icon = "java fab";
  } else if (ebook.title.toLowerCase().includes("react")) {
    icon = "react fab";
  }

  // Format file size if available
  const fileSize = ebook.file_size_human || "";
  const fileSizeText = fileSize
    ? `<span class="file-size">${fileSize}</span>`
    : "";

  // Format date if available
  let dateText = "";
  if (ebook.created_date) {
    const date = new Date(ebook.created_date);
    dateText = `<span class="created-date">Created: ${date.toLocaleDateString()}</span>`;
  }

  card.innerHTML = `
    <div class="ebook-icon">
      <i class="fas fa-${icon}"></i>
    </div>
    <div class="ebook-content">
      <h3>${ebook.title}</h3>
      <p class="ebook-info">${ebook.description || ""}</p>
      <div class="ebook-meta">
        ${dateText}
        ${fileSizeText}
      </div>
      <div class="ebook-formats">
        ${
          ebook.epub_path
            ? `<a href="#" class="download-link" data-filename="${getFilenameFromPath(
                ebook.epub_path
              )}">
          <i class="fas fa-book"></i> EPUB
        </a>`
            : ""
        }
        ${
          ebook.pdf_path
            ? `<a href="#" class="download-link" data-filename="${getFilenameFromPath(
                ebook.pdf_path
              )}">
          <i class="fas fa-file-pdf"></i> PDF
        </a>`
            : ""
        }
      </div>
    </div>
  `;

  // Add event listeners to the download links
  card.querySelectorAll(".download-link").forEach((link) => {
    link.addEventListener("click", handleDownload);
  });

  return card;
}

// Get filename from a path
function getFilenameFromPath(path) {
  return path.split("/").pop();
}

// Show loading state in a container
function showLoadingState(container, message) {
  container.innerHTML = `
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <p>${message}</p>
    </div>
  `;
}

// Show error state in a container
function showErrorState(container, message) {
  container.innerHTML = `
    <div class="error-state">
      <div class="error-icon"><i class="fas fa-exclamation-circle"></i></div>
      <p>${message}</p>
    </div>
  `;
}

// Format date for display
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString();
}

// Display activities in the activity panel
function displayActivities() {
  const activities = activityTracker.getActivities();

  // Clear current list
  activityList.innerHTML = "";

  if (activities.length === 0) {
    activityList.innerHTML = '<p class="empty-state">No activities yet</p>';
    return;
  }

  // Add each activity to the list
  activities.forEach((activity) => {
    const activityItem = document.createElement("div");
    activityItem.className = "activity-item";

    // Format based on activity type
    let title = "";
    let details = "";

    switch (activity.type) {
      case "spider_run":
        title = "Started Spider";
        details = `Spider ID: ${activity.details.spiderId}`;
        break;
      case "ebook_creation":
        title = "Created Ebook";
        details = `Spider ID: ${
          activity.details.spiderId
        }, Format: ${activity.details.format.toUpperCase()}`;
        break;
      case "download":
        title = "Downloaded File";
        details = `Filename: ${activity.details.filename}`;
        break;
      case "search":
        title = "Searched Ebooks";
        details = `Search Term: ${activity.details.term}`;
        break;
      case "share":
        title = "Shared Ebook";
        details = `Title: ${activity.details.title}, Filename: ${activity.details.filename}`;
        break;
      case "share_platform":
        title = "Shared on Platform";
        details = `Platform: ${activity.details.platform}`;
        break;
      default:
        title = activity.type;
        details = JSON.stringify(activity.details);
    }

    activityItem.innerHTML = `
      <div class="activity-type">${title}</div>
      <div class="activity-details">${details}</div>
      <div class="activity-time">${formatDate(activity.timestamp)}</div>
    `;

    activityList.appendChild(activityItem);
  });
}

// Toggle activity panel
function toggleActivityPanel() {
  activityPanel.classList.toggle("active");

  if (activityPanel.classList.contains("active")) {
    displayActivities();
  }
}

// Set up additional event listeners for the activity panel
function setupActivityPanel() {
  if (activityToggle) {
    activityToggle.addEventListener("click", toggleActivityPanel);
  }

  if (closeActivityPanelBtn) {
    closeActivityPanelBtn.addEventListener("click", toggleActivityPanel);
  }

  if (clearActivitiesBtn) {
    clearActivitiesBtn.addEventListener("click", () => {
      activityTracker.clearActivities();
      displayActivities();
      showNotification("Activity history cleared", "info");
    });
  }
}

// Set up event listeners
function setupEventListeners() {
  // Spider selection
  spiderSelect.addEventListener("change", handleSpiderSelection);

  // Run spider button
  runSpiderBtn.addEventListener("click", handleRunSpider);

  // Create ebook button
  createEbookBtn.addEventListener("click", handleCreateEbook);

  // Download links
  document.querySelectorAll(".download-link").forEach((link) => {
    link.addEventListener("click", handleDownload);
  });

  // Modal close events
  closeBtn.addEventListener("click", closeModal);
  modalOkBtn.addEventListener("click", closeModal);
  window.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });

  // Add refresh button event listener
  const refreshBtn = document.getElementById("refresh-ebooks-btn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", handleRefreshEbooks);
  }

  // Theme toggle button
  if (themeToggle) {
    themeToggle.addEventListener("click", toggleTheme);
  }

  // Set up activity panel listeners
  setupActivityPanel();
}

// Handle spider selection change
function handleSpiderSelection() {
  selectedSpider = spiderSelect.value;

  if (selectedSpider) {
    runSpiderBtn.disabled = false;

    // Check if this spider has already been run
    checkSpiderStatus();
  } else {
    runSpiderBtn.disabled = true;
    resetStatus();
  }
}

// Validate spider selection
function validateSpiderSelection() {
  if (!selectedSpider) {
    showNotification("Please select a documentation source first.", "warning");
    return false;
  }
  return true;
}

// Validate connection to backend
async function validateBackendConnection() {
  try {
    // Try to connect to the backend API
    await api.getSpiders();
    console.log("Backend connection successful");
    return true;
  } catch (error) {
    console.error("Backend connection failed:", error);
    return false;
  }
}

// Handle run spider button click
async function handleRunSpider() {
  if (!selectedSpider || isProcessing) return;

  if (!validateSpiderSelection()) return;

  if (!(await validateBackendConnection())) return;

  try {
    isProcessing = true;
    runSpiderBtn.disabled = true;

    showStatus("starting", "Starting the spider...");
    showNotification("Starting spider process...", "info");

    // Track activity
    activityTracker.addActivity("spider_run", {
      spiderId: selectedSpider,
      timestamp: new Date().toISOString(),
    });

    const result = await api.runSpider(selectedSpider);
    console.log("Spider started:", result);

    // Start checking status
    startStatusCheck();
  } catch (error) {
    console.error("Error running spider:", error);
    showStatus("error", "Failed to start the spider. Please try again.");
    showNotification("Failed to start the spider: " + error.message, "error");
    isProcessing = false;
    runSpiderBtn.disabled = false;
  }
}

// Start checking spider status periodically
function startStatusCheck() {
  // Clear any existing interval
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
  }

  // Check status immediately
  checkSpiderStatus();

  // Then check every 5 seconds
  statusCheckInterval = setInterval(checkSpiderStatus, 5000);
}

// Check the current status of the selected spider
async function checkSpiderStatus() {
  if (!selectedSpider) return;

  try {
    const status = await api.getSpiderStatus(selectedSpider);
    console.log("Spider status:", status);

    if (status.status === "not_started") {
      showStatus("waiting", "Spider has not been started yet.");
      updateProgress(0);
      createEbookBtn.disabled = true;
    } else if (status.status === "running") {
      showStatus(
        "running",
        `Spider is running. Scraped ${status.items_scraped} items so far (${status.file_size_human}).`
      );
      updateProgress(50); // We don't know the total, so show indeterminate progress
      createEbookBtn.disabled = true;
    } else if (status.status === "completed") {
      showStatus(
        "completed",
        `Spider completed. Scraped ${status.items_scraped} items (${status.file_size_human}).`
      );
      updateProgress(100);
      createEbookBtn.disabled = false;

      // Show notification when completed
      showNotification(
        "Spider completed successfully! You can now generate an ebook.",
        "success"
      );

      // Stop checking status
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
      }

      isProcessing = false;
    }
  } catch (error) {
    console.error("Error checking spider status:", error);
    showStatus("error", "Failed to check spider status.");
    showNotification("Error checking spider status", "error");
  }
}

// Show status in the UI
function showStatus(state, message) {
  spiderStatus.classList.remove("hidden");

  let statusClassName = "";
  let progressValue = 0;

  switch (state) {
    case "starting":
      statusClassName = "starting";
      statusText.textContent = "Starting";
      progressValue = 5;
      break;
    case "crawling":
      statusClassName = "crawling";
      statusText.textContent = "Crawling";
      progressValue = 30;
      break;
    case "processing":
      statusClassName = "processing";
      statusText.textContent = "Processing";
      progressValue = 70;
      break;
    case "complete":
      statusClassName = "complete";
      statusText.textContent = "Complete";
      progressValue = 100;
      break;
    case "error":
      statusClassName = "error";
      statusText.textContent = "Error";
      progressValue = 0;
      break;
  }

  // Remove all status classes
  spiderStatus.className = "status-box";

  // Add current status class
  spiderStatus.classList.add(statusClassName);

  // Update progress bar
  progressBar.style.width = `${progressValue}%`;

  // Update ARIA attributes for accessibility
  const progressContainer = document.querySelector(".progress-container");
  if (progressContainer) {
    progressContainer.setAttribute("aria-valuenow", progressValue);
  }

  // Update details text
  statusDetails.textContent = message;
}

// Update progress bar
function updateProgress(percent) {
  progressBar.style.width = percent + "%";
}

// Reset status display
function resetStatus() {
  spiderStatus.classList.add("hidden");
  statusText.textContent = "Waiting";
  statusDetails.textContent = "";
  updateProgress(0);
  createEbookBtn.disabled = true;

  // Clear status check interval
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
    statusCheckInterval = null;
  }
}

// Handle create ebook button click
async function handleCreateEbook() {
  if (!selectedSpider || isProcessing) return;

  if (!validateSpiderSelection()) return;

  if (!(await validateBackendConnection())) return;

  // Get selected format
  const format =
    Array.from(formatRadios).find((radio) => radio.checked)?.value || "epub";

  try {
    isProcessing = true;
    createEbookBtn.disabled = true;

    showModal(
      "Creating Ebook",
      `Creating ${format.toUpperCase()} file. This may take a few minutes...`
    );

    // Track activity
    activityTracker.addActivity("ebook_creation", {
      spiderId: selectedSpider,
      format: format,
      timestamp: new Date().toISOString(),
    });

    const result = await api.createEbook(selectedSpider, format);
    console.log("Ebook created:", result);

    closeModal();

    if (format === "epub" && result.epub_path) {
      showNotification(`EPUB created successfully!`, "success");

      // Start download automatically
      setTimeout(() => {
        window.location.href = api.getDownloadUrl(
          result.epub_path.split("/").pop()
        );
      }, 1000);

      // Refresh the ebooks list after creation
      loadAvailableEbooks();
    } else if (format === "pdf" && result.pdf_path) {
      showNotification(`PDF created successfully!`, "success");

      // Start download automatically
      setTimeout(() => {
        window.location.href = api.getDownloadUrl(
          result.pdf_path.split("/").pop()
        );
      }, 1000);

      // Refresh the ebooks list after creation
      loadAvailableEbooks();
    } else {
      showNotification(
        `${format.toUpperCase()} created successfully!`,
        "success"
      );

      // Refresh the ebooks list after creation
      loadAvailableEbooks();
    }

    isProcessing = false;
    createEbookBtn.disabled = false;
  } catch (error) {
    console.error("Error creating ebook:", error);
    closeModal();
    showNotification(
      `Failed to create ${format.toUpperCase()}: ${error.message}`,
      "error"
    );
    isProcessing = false;
    createEbookBtn.disabled = false;
  }
}

// Handle download link click
function handleDownload(event) {
  event.preventDefault();
  const filename = event.currentTarget.dataset.filename;
  if (filename) {
    showNotification(`Downloading ${filename}...`, "info");

    // Track activity
    activityTracker.addActivity("download", {
      filename: filename,
      timestamp: new Date().toISOString(),
    });

    window.location.href = api.getDownloadUrl(filename);
  }
}

// Handle share button click
async function handleShare(event) {
  const btn = event.currentTarget;
  const title = btn.dataset.title || "TukuyBooks Ebook";
  const filename = btn.dataset.filename || "";

  if (!filename) {
    showNotification("Cannot share ebook: missing filename", "error");
    return;
  }

  // Track activity
  activityTracker.addActivity("share", {
    title: title,
    filename: filename,
    timestamp: new Date().toISOString(),
  });

  // Generate share URL (absolute URL)
  const downloadUrl = new URL(
    api.getDownloadUrl(filename),
    window.location.origin
  ).toString();

  // Check if Web Share API is available
  if (navigator.share) {
    try {
      await navigator.share({
        title: `${title} - TukuyBooks`,
        text: `Check out this ebook: ${title}`,
        url: downloadUrl,
      });

      showNotification("Shared successfully!", "success");
    } catch (error) {
      console.error("Error sharing:", error);

      if (error.name !== "AbortError") {
        // Only show error if user didn't cancel
        showNotification(
          "Could not share directly. Showing share options instead.",
          "info"
        );
        showShareModal(title, downloadUrl);
      }
    }
  } else {
    // Fallback for browsers that don't support Web Share API
    showShareModal(title, downloadUrl);
  }
}

// Show modal with share options
function showShareModal(title, url) {
  modalTitle.textContent = "Share Ebook";

  // Create share options
  const shareContent = document.createElement("div");
  shareContent.innerHTML = `
    <p>Share "${title}" with others:</p>
    
    <div class="share-options">
      <div class="share-option" data-platform="email">
        <i class="fas fa-envelope"></i>
        <span>Email</span>
      </div>
      
      <div class="share-option" data-platform="twitter">
        <i class="fab fa-twitter"></i>
        <span>Twitter</span>
      </div>
      
      <div class="share-option" data-platform="facebook">
        <i class="fab fa-facebook"></i>
        <span>Facebook</span>
      </div>
      
      <div class="share-option" data-platform="linkedin">
        <i class="fab fa-linkedin"></i>
        <span>LinkedIn</span>
      </div>
    </div>
    
    <p>Or copy this link:</p>
    <div class="share-link-container">
      <input type="text" class="share-link-input" value="${url}" readonly>
      <button class="btn secondary-btn copy-link-btn">
        <i class="fas fa-copy"></i> Copy
      </button>
    </div>
  `;

  // Replace modal content
  modalMessage.innerHTML = "";
  modalMessage.appendChild(shareContent);

  // Add event listeners to share options
  shareContent.querySelectorAll(".share-option").forEach((option) => {
    option.addEventListener("click", () => {
      const platform = option.dataset.platform;
      shareToSocialMedia(platform, title, url);
    });
  });

  // Add event listener to copy button
  const copyBtn = shareContent.querySelector(".copy-link-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const input = shareContent.querySelector(".share-link-input");
      input.select();
      document.execCommand("copy");
      showNotification("Link copied to clipboard!", "success");
    });
  }

  // Show the modal
  showModal("Share Ebook", shareContent);
}

// Share to social media platforms
function shareToSocialMedia(platform, title, url) {
  let shareUrl = "";
  const encodedUrl = encodeURIComponent(url);
  const encodedTitle = encodeURIComponent(`${title} - TukuyBooks Ebook`);
  const encodedText = encodeURIComponent(`Check out this free ebook: ${title}`);

  switch (platform) {
    case "email":
      shareUrl = `mailto:?subject=${encodedTitle}&body=${encodedText}%0A%0A${encodedUrl}`;
      break;
    case "twitter":
      shareUrl = `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`;
      break;
    case "facebook":
      shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
      break;
    case "linkedin":
      shareUrl = `https://www.linkedin.com/shareArticle?mini=true&url=${encodedUrl}&title=${encodedTitle}`;
      break;
  }

  if (shareUrl) {
    window.open(shareUrl, "_blank");

    // Track sharing activity
    activityTracker.addActivity("share_platform", {
      platform: platform,
      timestamp: new Date().toISOString(),
    });

    // Close the modal after sharing
    setTimeout(() => {
      closeModal();
    }, 500);
  }
}

// Handle search functionality
function setupSearch() {
  if (!ebookSearch || !searchClearBtn) return;

  // Original list of ebooks for filtering
  let allEbooks = [];

  // Function to save all ebook elements when they're loaded
  function saveAllEbooks() {
    const ebookCards = ebooksContainer.querySelectorAll(".ebook-card");
    allEbooks = Array.from(ebookCards);
  }

  // Function to filter ebooks based on search term
  function filterEbooks(searchTerm) {
    if (searchTerm === "") {
      // If search is empty, show all ebooks
      allEbooks.forEach((card) => {
        card.style.display = "";
      });

      // Hide clear button when search is empty
      searchClearBtn.classList.remove("visible");
      return;
    }

    // Show clear button when search has content
    searchClearBtn.classList.add("visible");

    // Convert search term to lowercase for case-insensitive comparison
    searchTerm = searchTerm.toLowerCase();

    // Filter the ebooks
    let visibleCount = 0;

    allEbooks.forEach((card) => {
      const title =
        card.querySelector(".ebook-title")?.textContent?.toLowerCase() || "";
      const format =
        card.querySelector(".format-badge")?.textContent?.toLowerCase() || "";
      const details =
        card.querySelector(".ebook-details")?.textContent?.toLowerCase() || "";

      // Check if the card contains the search term
      if (
        title.includes(searchTerm) ||
        format.includes(searchTerm) ||
        details.includes(searchTerm)
      ) {
        card.style.display = "";
        visibleCount++;
      } else {
        card.style.display = "none";
      }
    });

    // Show a message if no results found
    if (
      visibleCount === 0 &&
      ebooksContainer.querySelector(".no-results") === null
    ) {
      const noResults = document.createElement("div");
      noResults.className = "no-results";
      noResults.innerHTML = `
        <i class="fas fa-search"></i>
        <p>No ebooks found matching "${searchTerm}"</p>
      `;
      ebooksContainer.appendChild(noResults);
    } else {
      // Remove no results message if there are matches
      const noResults = ebooksContainer.querySelector(".no-results");
      if (noResults && visibleCount > 0) {
        noResults.remove();
      }
    }
  }

  // Search input event handler
  ebookSearch.addEventListener("input", (e) => {
    const searchTerm = e.target.value.trim();
    filterEbooks(searchTerm);

    // Record activity if search term is meaningful
    if (searchTerm.length > 2) {
      activityTracker.addActivity("search", {
        term: searchTerm,
        timestamp: new Date().toISOString(),
      });
    }
  });

  // Clear search button event handler
  searchClearBtn.addEventListener("click", () => {
    ebookSearch.value = "";
    filterEbooks("");
    ebookSearch.focus();
  });

  // Override the loadAvailableEbooks function to save all ebooks after loading
  const originalLoadAvailableEbooks = loadAvailableEbooks;
  loadAvailableEbooks = async function () {
    await originalLoadAvailableEbooks();
    saveAllEbooks();

    // Apply any existing search filter
    if (ebookSearch.value.trim() !== "") {
      filterEbooks(ebookSearch.value.trim());
    }
  };
}

// Show modal
function showModal(title, message, onOk) {
  modalTitle.textContent = title;
  modalMessage.textContent = message;

  // Set OK button callback
  if (typeof onOk === "function") {
    modalOkBtn.onclick = () => {
      closeModal();
      onOk();
    };
  } else {
    modalOkBtn.onclick = closeModal;
  }

  modal.style.display = "block";
}

// Close modal
function closeModal() {
  modal.style.display = "none";
}

// Show notification to user
function showNotification(message, type = "info") {
  // Hide any existing notification to prevent overlap
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
  }

  // Create notification container if not exist
  let notificationsContainer = document.querySelector(".notifications");
  if (!notificationsContainer) {
    notificationsContainer = document.createElement("div");
    notificationsContainer.className = "notifications";
    document.body.appendChild(notificationsContainer);
  }

  // Create notification element
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;

  // Add ARIA attributes for screen readers
  notification.setAttribute("role", "alert");
  notification.setAttribute(
    "aria-live",
    type === "error" ? "assertive" : "polite"
  );

  // Add icon based on type
  let icon;
  switch (type) {
    case "success":
      icon = "check-circle";
      break;
    case "error":
      icon = "exclamation-circle";
      break;
    case "warning":
      icon = "exclamation-triangle";
      break;
    default:
      icon = "info-circle";
  }

  // Set notification content
  notification.innerHTML = `
    <div class="notification-icon">
      <i class="fas fa-${icon}" aria-hidden="true"></i>
    </div>
    <div class="notification-content">
      <p></p>
    </div>
    <button class="notification-close" aria-label="Close notification">
      <i class="fas fa-times" aria-hidden="true"></i>
    </button>
  `;

  // Safely set the message text
  const messageElement = notification.querySelector(".notification-content p");
  messageElement.textContent = message;

  // Add close functionality
  const closeBtn = notification.querySelector(".notification-close");
  closeBtn.addEventListener("click", () => {
    notification.classList.add("fade-out");
    setTimeout(() => {
      notification.remove();
    }, 300);
  });

  // Add to DOM
  notificationsContainer.appendChild(notification);

  // Show animation
  setTimeout(() => {
    notification.classList.add("show");
  }, 10);

  // Auto-dismiss after a delay
  notificationTimeout = setTimeout(() => {
    notification.classList.add("fade-out");
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 5000);

  return notification;
}

// Initialize the app when DOM is fully loaded
document.addEventListener("DOMContentLoaded", init);
