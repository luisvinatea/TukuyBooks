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

// Modal elements
const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modal-title");
const modalMessage = document.getElementById("modal-message");
const modalOkBtn = document.getElementById("modal-ok-btn");
const closeBtn = document.querySelector(".close-btn");

// State variables
let selectedSpider = null;
let statusCheckInterval = null;
let isProcessing = false;

// Initialize the application
async function init() {
  // Load available spiders
  await loadSpiders();

  // Set up event listeners
  setupEventListeners();
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

// Handle run spider button click
async function handleRunSpider() {
  if (!selectedSpider || isProcessing) return;

  try {
    isProcessing = true;
    runSpiderBtn.disabled = true;

    showStatus("starting", "Starting the spider...");

    const result = await api.runSpider(selectedSpider);
    console.log("Spider started:", result);

    // Start checking status
    startStatusCheck();
  } catch (error) {
    console.error("Error running spider:", error);
    showStatus("error", "Failed to start the spider. Please try again.");
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
      showModal(
        "Success",
        "EPUB created successfully! You can now download it.",
        () => {
          window.location.href = api.getDownloadUrl(
            result.epub_path.split("/").pop()
          );
        }
      );
    } else if (format === "pdf" && result.pdf_path) {
      showModal(
        "Success",
        "PDF created successfully! You can now download it.",
        () => {
          window.location.href = api.getDownloadUrl(
            result.pdf_path.split("/").pop()
          );
        }
      );
    } else {
      showModal("Success", `${format.toUpperCase()} created successfully!`);
    }

    isProcessing = false;
    createEbookBtn.disabled = false;
  } catch (error) {
    console.error("Error creating ebook:", error);
    closeModal();
    showModal(
      "Error",
      `Failed to create ${format.toUpperCase()}. Please try again.`
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

// Initialize the app when DOM is fully loaded
document.addEventListener("DOMContentLoaded", init);
