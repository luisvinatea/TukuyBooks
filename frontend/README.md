# TukuyBooks Streamlit Frontend

This directory contains the Streamlit web application for TukuyBooks, providing a user-friendly interface to:

- Run documentation spiders
- Create ebooks from scraped data
- Convert EPUB files to PDF
- Browse and download generated files

## Requirements

- Python 3.8+
- Streamlit
- Other dependencies listed in `requirements.txt`

## Installation

```bash
# Install required packages
pip install -r requirements.txt
```

## Usage

### Running Locally

```bash
# Start the Streamlit app
streamlit run app.py
```

This will start the web application and open it in your default browser.

### Using the Convenience Script

```bash
# Run with automatic dependency installation
./run_streamlit.sh --install
```

Or if you already have dependencies installed:

```bash
./run_streamlit.sh
```

### Using Docker

We provide Docker support for easy deployment:

```bash
# Build and run the Docker container
./run_docker.sh
```

This will build the Docker image and start the container with the Streamlit application accessible at <http://localhost:8501>.

## Features

### Home

- Overview of the application
- List of available documentation spiders

### Run Spider

- Select and run a documentation spider
- View real-time progress and output

### Create Ebook

- Convert spider output to EPUB format
- Customize output filename

### Convert to PDF

- Convert EPUB files to PDF format using calibre
- Download the generated PDF files

### View Files

- Browse available EPUB and PDF files
- Download files directly from the interface

## Integration with Backend

This frontend integrates with the backend `tukuy_ebook_maker.py` script to provide a graphical interface for all functionality previously available only via command line.
