FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ghostscript \
    calibre \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend files
COPY backend/ ./backend/

# Create output directory
RUN mkdir -p backend/outputs

# Copy entrypoint script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh
RUN chmod +x backend/scripts/book_optimizer.sh

# Set the entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
