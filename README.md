# TukuyBooks: Transforming Open-Source Internet into Free Access Knowledge

Welcome to **TukuyBooks**, an open-source initiative to scrape, process, and convert freely available online documentation into high-quality, offline-accessible EPUBs and PDFs. Our mission is to preserve and democratize knowledge from the open-source internet, making it available to anyone, anywhere, without barriers.

## Online Interface

The TukuyBooks web interface allows you to:

- View available documentation sources
- Start scraping processes
- Generate EPUB/PDF files from scraped content
- Download pre-generated ebooks

**Visit the online interface:** [https://luisvinatea.github.io/TukuyBooks/](https://luisvinatea.github.io/TukuyBooks/)

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

- **[PythonDocs](PythonDocs/)**: Scrapes Python 3 documentation from `docs.python.org/3/`.
  - Status: Active
  - Outputs: `Python3Docs.epub`, `Python3Docs.pdf`
  - See [PythonDocs README](PythonDocs/README.md) for details.

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

The TukuyBooks web interface is built with vanilla JavaScript and structured for simplicity:

- **API Client**: The `api.js` file provides a clean interface to communicate with the backend.
- **UI Components**: Modular components for different sections (ebook cards, notifications, etc.).
- **Responsive Design**: Fully responsive layout that works on mobile, tablet, and desktop.
- **Event-Driven**: Uses event listeners to handle user interactions and state changes.

Key features of the frontend:

- Real-time progress tracking for spider processes
- Notifications system for user feedback
- Automatic detection of available ebooks
- Client-side validation to prevent errors
- Mobile-first responsive design
