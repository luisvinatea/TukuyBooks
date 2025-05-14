# TukuyBooks: Transforming Open-Source Internet into Free Access Knowledge

Welcome to **TukuyBooks**, an open-source initiative to scrape, process, and convert freely available online documentation into high-quality, offline-accessible EPUBs and PDFs. Our mission is to preserve and democratize knowledge from the open-source internet, making it available to anyone, anywhere, without barriers.

## Docker Usage

TukuyBooks now provides Docker containers for easy local deployment of spider pipelines. Run our spiders without worrying about dependencies or complex setup:

```bash
# Build the Docker image
./run_docker.sh

# Run the Python documentation spider
docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest crawl python_docs

# Generate an ebook from the scraped data
docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest make-ebook python_docs

# Run the full pipeline (crawl -> make-ebook -> optimize)
docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest all python_docs
```

The generated ebooks will be available in your local `./outputs` directory.

## Online Interface

The TukuyBooks web interface allows you to:

- View available documentation sources
- Start scraping processes
- Generate EPUB/PDF files from scraped content
- Download pre-generated ebooks

**Visit the online interface:** [https://luisvinatea.github.io/TukuyBooks/](https://luisvinatea.github.io/TukuyBooks/)

**API Debug Tool:** [https://luisvinatea.github.io/TukuyBooks/api-debug.html](https://luisvinatea.github.io/TukuyBooks/api-debug.html)

## Features

- **Web Scraping**: Capture documentation from open-source websites with custom spiders
- **Ebook Generation**: Transform web content into EPUB and PDF formats with proper formatting
- **Responsive UI**: Mobile-friendly interface that works across devices
- **Real-time Status Updates**: Monitor scraping progress with real-time notifications
- **Offline Reading**: Download ebooks for offline reading on e-readers or other devices
- **Dark Mode**: Comfortable reading experience in low-light environments
- **User Activity Tracking**: Keep track of your scraping and ebook generation history
- **Advanced Error Handling**: Automatic retry functionality for more reliable operation
- **Accessibility**: Full keyboard navigation support and screen reader compatibility
- **Cross-Browser Support**: Works across all modern browsers with fallbacks

## Vision

TukuyBooks aims to:

- Capture valuable documentation from open-source websites.
- Transform it into portable, optimized formats (EPUB, PDF).
- Distribute these resources freely via GitHub Releases.
- Foster a collaborative community to maintain and expand this knowledge library.

Each website we target gets its own dedicated spider pipeline within this repository, ensuring modularity and scalability.

## Current Pipelines

Below are the active spider pipelines transforming specific websites into free knowledge assets:

- **PythonDocs**: Scrapes Python 3 documentation from `docs.python.org/3/`.
  - Status: Active
  - Outputs: `Python3Docs.epub`, `Python3Docs.pdf`

*More pipelines coming soon! Suggest new websites via [Issues](https://github.com/luisvinatea/TukuyBooks/issues).*

## General Prerequisites

To contribute or run any pipeline, you’ll need:

- Python 3.12+
- Scrapy (`pip install scrapy`)
- Calibre (`sudo pacman -S calibre` or equivalent)
- Ghostscript (`sudo pacman -S ghostscript`)
- Sigil (optional, for EPUB tweaks)

## Project Structure

The project is organized into the following structure:

```plaintext
TukuyBooks/
├── backend/              # Backend API and server
│   ├── api/             # Flask API for the web interface
│   ├── outputs/         # Generated ebooks and intermediate files
│   ├── scripts/         # Utilities for ebook generation
│   ├── spiders/         # Scrapy spiders for different documentation sites
│   └── utils/           # Shared utility functions
├── frontend/            # Web interface
│   ├── css/             # Stylesheets
│   ├── js/              # Client-side JavaScript
│   └── index.html       # Main HTML file
└── scrapy.cfg           # Scrapy configuration file
```

## Frontend Architecture

The TukuyBooks frontend is built with modern vanilla JavaScript and follows best practices for maintainable web applications:

### Core Components

- **API Client (`api.js`)**: Handles all communication with the backend, including automatic retries and loading indicators
- **User Interface (`main.js`)**: Manages the UI state, event handling, and application logic
- **Theme System**: Supports both light and dark modes with persistent user preferences
- **Notification System**: Provides user feedback with different status types and auto-dismissal
- **Activity Tracking**: Records user actions and displays them in an activity panel
- **Search System**: Allows filtering of available ebooks
- **Share Functionality**: Enables users to share ebooks across various platforms

### Technical Features

#### Progressive Enhancement

The frontend implements progressive enhancement principles:

- Core functionality works with basic JavaScript
- Enhanced features gracefully degrade in older browsers
- Browser compatibility checks provide feedback to users

#### Error Handling

Robust error handling strategy:

- Automatic retry for network failures with exponential backoff
- Detailed error messages with recovery suggestions
- Fallback content when API requests fail
- Offline capabilities for viewing previously loaded content

#### Performance Optimization

- Lazy loading images and non-critical resources
- Minimal DOM manipulation for better performance
- Optimized CSS with minimal dependencies
- Efficient event delegation patterns

#### Mobile First Design

- Responsive design works on all screen sizes
- Touch-friendly controls for mobile devices
- Adaptive layout that reflows for different viewports
- Optimized for both portrait and landscape orientations

#### Accessibility

- ARIA attributes for screen reader compatibility
- Full keyboard navigation support
- Sufficient color contrast in both light and dark modes
- Focus management for modals and interactive elements
- Status announcements for loading states and events

## Architecture

TukuyBooks uses a modern architecture:

- **Frontend**: HTML/CSS/JS hosted on GitHub Pages
- **Backend**: Node.js API deployed on Vercel (handles API requests and runs Python spiders)
- **Spiders**: Python-based web scrapers using the Scrapy framework
- **Ebook Generation**: Custom Python scripts for EPUB and PDF creation
