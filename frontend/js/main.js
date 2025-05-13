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

// Modal elements
const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modal-title");
const modalMessage = document.getElementById("modal-message");
const modalOkBtn = document.getElementById("modal-ok-btn");
const closeBtn = document.querySelector(".close-btn");

// Add theme toggle button
const themeToggle = document.getElementById("theme-toggle");

// State variables
let selectedSpider = null;
let statusCheckInterval = null;
let isProcessing = false;
let notificationTimeout = null;
let currentTheme = localStorage.getItem("theme") || "light";

// Initialize the application
async function init() {
  // Initialize theme
  initTheme();

  // Set up keyboard navigation
  setupKeyboardNavigation();

  // Set up image loading handlers
  setupImageLoadHandlers();

  // Validate backend connection
  if (!(await validateBackendConnection())) {
    showNotification(
      "Could not connect to the backend server. Some features may not work.",
      "warning"
    );
  }

  // Load available spiders
  await loadSpiders();

  // Load available ebooks
  await loadAvailableEbooks();

  // Set up event listeners
  setupEventListeners();
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

// Set up keyboard navigation
function setupKeyboardNavigation() {
  document.addEventListener("keydown", (e) => {
    // ESC to close modals
    if (e.key === "Escape") {
      if (modal.style.display === "block") {
        closeModal();
      }
    }

    // Ctrl+D or Cmd+D to toggle dark mode
    if ((e.ctrlKey || e.metaKey) && e.key === "d") {
      e.preventDefault();
      toggleTheme();
    }

    // Alt+R to refresh ebook list
    if (e.altKey && e.key === "r") {
      e.preventDefault();
      handleRefreshEbooks();
    }
  });
}

// Set up image loading handlers
function setupImageLoadHandlers() {
  // Add load event to all images
  const images = document.querySelectorAll("img");
  images.forEach((img) => {
    img.addEventListener("load", function () {
      this.classList.add("loaded");
    });

    // If already loaded (e.g., from cache), add loaded class
    if (img.complete) {
      img.classList.add("loaded");
    }
  });

  // Monitor for dynamically added images using MutationObserver
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes) {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) {
            // Element node
            const images = node.querySelectorAll("img");
            images.forEach((img) => {
              img.addEventListener("load", function () {
                this.classList.add("loaded");
              });

              if (img.complete) {
                img.classList.add("loaded");
              }
            });
          }
        });
      }
    });
  });

  // Start observing
  observer.observe(document.body, { childList: true, subtree: true });
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

// Load available ebooks from API
async function loadAvailableEbooks() {
  try {
    showLoadingState(ebooksContainer, "Loading available ebooks...");

    const ebooks = await api.getAvailableEbooks();

    // Clear existing content (except the placeholder)
    const placeholder = document.querySelector(".ebook-placeholder");
    ebooksContainer.innerHTML = "";

    if (ebooks && ebooks.length > 0) {
      // Add each ebook to the container
      ebooks.forEach((ebook) => {
        const ebookCard = createEbookCard(ebook);
        ebooksContainer.appendChild(ebookCard);
      });

      // Add the placeholder back
      if (placeholder) {
        ebooksContainer.appendChild(placeholder);
      }

      console.log("Loaded ebooks:", ebooks);
    } else {
      // No ebooks available
      const noEbooksMessage = document.createElement("div");
      noEbooksMessage.className = "no-ebooks-message";
      noEbooksMessage.innerHTML = `
        <div class="ebook-icon">
          <i class="fas fa-book-open"></i>
        </div>
        <h3>No Ebooks Available Yet</h3>
        <p>Generate your first ebook by selecting a documentation source above.</p>
      `;
      ebooksContainer.appendChild(noEbooksMessage);

      // Add the placeholder back
      if (placeholder) {
        ebooksContainer.appendChild(placeholder);
      }
    }
  } catch (error) {
    console.error("Error loading available ebooks:", error);
    showErrorState(
      ebooksContainer,
      "Failed to load available ebooks. Please refresh the page to try again."
    );
  }
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

  // Listen for system theme changes
  if (window.matchMedia) {
    const colorSchemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
    colorSchemeQuery.addEventListener("change", (e) => {
      // Only change if user has no preference set
      if (!localStorage.getItem("theme")) {
        if (e.matches) {
          document.body.classList.add("dark-theme");
          currentTheme = "dark";
        } else {
          document.body.classList.remove("dark-theme");
          currentTheme = "light";
        }
      }
    });

    // Initialize based on system preference if user has no preference
    if (!localStorage.getItem("theme")) {
      if (colorSchemeQuery.matches) {
        document.body.classList.add("dark-theme");
        currentTheme = "dark";
      }
    }
  }
}

// Handle refresh ebooks button click
async function handleRefreshEbooks() {
  const refreshBtn = document.getElementById("refresh-ebooks-btn");

  // Add rotating animation class
  if (refreshBtn) {
    refreshBtn.classList.add("refresh-rotating");
    refreshBtn.disabled = true;
  }

  // Show notification
  showNotification("Refreshing available ebooks...", "info");

  // Refresh ebooks
  await loadAvailableEbooks();

  // Remove rotating animation class after refresh
  if (refreshBtn) {
    setTimeout(() => {
      refreshBtn.classList.remove("refresh-rotating");
      refreshBtn.disabled = false;
    }, 500);
  }
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
    showNotification("Please select a documentation source", "warning");
    return false;
  }
  return true;
}

// Validate connection to backend
async function validateBackendConnection() {
  try {
    // Try to fetch spiders as a simple check
    await api.getSpiders();
    return true;
  } catch (error) {
    console.error("Backend connection error:", error);
    showModal(
      "Connection Error",
      "Could not connect to the backend server. Please make sure the server is running and try again."
    );
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
  statusText.textContent = state.charAt(0).toUpperCase() + state.slice(1);
  statusDetails.textContent = message;

  // Add appropriate status color
  spiderStatus.className = "status-box";
  spiderStatus.classList.add("status-" + state);
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
    window.location.href = api.getDownloadUrl(filename);
  }
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

// Show notification
function showNotification(message, type = "info") {
  // Clear any existing notification
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
    notificationTimeout = null;
  }

  // Check if notification container exists, create if not
  let notificationContainer = document.getElementById("notification-container");
  if (!notificationContainer) {
    notificationContainer = document.createElement("div");
    notificationContainer.id = "notification-container";
    document.body.appendChild(notificationContainer);
  }

  // Create notification element
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;

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

  notification.innerHTML = `
    <i class="fas fa-${icon}"></i>
    <span>${message}</span>
    <button class="notification-close"><i class="fas fa-times"></i></button>
  `;

  // Add close event
  notification
    .querySelector(".notification-close")
    .addEventListener("click", () => {
      notification.classList.add("notification-closing");
      setTimeout(() => {
        notification.remove();
      }, 300);
    });

  // Add to container
  notificationContainer.appendChild(notification);

  // Show with animation
  setTimeout(() => {
    notification.classList.add("notification-visible");
  }, 10);

  // Auto-remove after 5 seconds
  notificationTimeout = setTimeout(() => {
    notification.classList.add("notification-closing");
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 5000);

  return notification;
}

// Initialize the app when DOM is fully loaded
document.addEventListener("DOMContentLoaded", init);
