FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for PDF generation with Calibre
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    xz-utils \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Calibre for ebook-convert
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | \
    sh /dev/stdin

# Copy requirements first for better layer caching
COPY frontend/requirements.txt /app/frontend/requirements.txt

# Install Python requirements
RUN pip install --no-cache-dir -r /app/frontend/requirements.txt

# Install additional required packages for the backend
RUN pip install --no-cache-dir scrapy beautifulsoup4 ebooklib tqdm

# Copy the entire application
COPY . /app/

# Set the working directory to the frontend folder
WORKDIR /app/frontend

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose the Streamlit port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
