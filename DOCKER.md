# TukuyBooks Docker Guide

This directory contains Docker configurations to run TukuyBooks spiders locally without the need to set up a complex development environment.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier management)

## Quick Start

1. Clone the repository:

   ```bash
   git clone https://github.com/luisvinatea/TukuyBooks.git
   cd TukuyBooks
   ```

2. Build the Docker image:

   ```bash
   ./run_docker.sh
   ```

   Or using Docker Compose:

   ```bash
   docker-compose build
   ```

3. Run a spider:

   ```bash
   docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest crawl python_docs
   ```

4. Generate an ebook from the spider output:

   ```bash
   docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest make-ebook python_docs
   ```

5. Optimize the generated ebooks:

   ```bash
   docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest optimize
   ```

## Available Commands

- `help`: Display usage information
- `crawl [spider_name]`: Run a specific spider
- `make-ebook [spider_id]`: Create an ebook from scraped data
- `optimize`: Optimize generated ebooks
- `all [spider_name]`: Run the full pipeline with the unified tool
- `unified [options]`: Run the unified ebook maker directly
- `legacy-all [spider]`: Run full pipeline with original tools

## Using the Unified Ebook Maker

The Docker image now includes a unified ebook maker that combines all steps of the workflow. You can use it directly:

```bash
# Run the complete workflow for Python docs
docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest all python_docs

# Run the unified tool directly with custom options
docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest unified --list
docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest unified --spider python_docs --make-ebook python_docs --optimize
docker run -v $(pwd)/outputs:/app/backend/outputs tukuybooks:latest unified --all --output "complete_docs"
```

### Unified Tool Options

- `--list`: List available spiders
- `--spider SPIDER_ID`: Run the specified spider
- `--make-ebook SPIDER_ID`: Create an ebook from scraped data
- `--optimize`: Optimize generated ebooks
- `--all`: Run the complete workflow for all spiders
- `--output OUTPUT`: Specify custom output filename (without extension)
- `crawl [spider_name]`: Run a specific spider (default: python_docs)
- `make-ebook [spider_id]`: Convert spider output to an ebook
- `optimize`: Optimize the generated ebooks for size
- `all [spider_name]`: Run the full pipeline (crawl, make-ebook, optimize)

## Using Docker Compose

For a simpler workflow, you can use Docker Compose:

```bash
# Build the image
docker-compose build

# Run the Python docs spider
docker-compose run --rm tukuybooks crawl python_docs

# Generate an ebook
docker-compose run --rm tukuybooks make-ebook python_docs

# Run the full pipeline
docker-compose run --rm tukuybooks all python_docs
```

## Output Files

The generated files will be available in the `outputs` directory in your project root. These include:

- JSON Lines files with scraped content (e.g., `python_docs.jl`)
- EPUB files (e.g., `Python3Docs.epub`)
- PDF files (e.g., `Python3Docs.pdf`)
- Optimized versions in the `outputs/optimized` directory

## Customizing the Container

You can modify the following files to customize the Docker container:

- `Dockerfile`: The main Docker configuration
- `docker-entrypoint.sh`: The entry point script that handles commands
- `docker-compose.yml`: Docker Compose configuration for easier management

## Troubleshooting

- **Permission issues**: If you encounter permission issues with output files, run the Docker container with your user ID:

  ```bash
  docker run -v $(pwd)/outputs:/app/backend/outputs --user $(id -u):$(id -g) tukuybooks:latest crawl python_docs
  ```

- **Docker volume not working**: Ensure you're using absolute paths with the `-v` flag:

  ```bash
  docker run -v "$(pwd)/outputs":/app/backend/outputs tukuybooks:latest crawl python_docs
  ```
