# ScreenSort AI - Docker Container
# Build: docker build -t screensort-ai .
# Run:   docker run -v /path/to/screenshots:/screenshots screensort-ai

FROM python:3.11-slim

LABEL maintainer="beherebhagyesh"
LABEL description="AI-powered screenshot organizer with OCR, translation, and video analysis"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sort_screenshots.py .
COPY download_model.py .

# Create directories
RUN mkdir -p /screenshots /app/models /app/knowledge_base

# Environment variables (can be overridden at runtime)
ENV SCREENSORT_AI=0
ENV SCREENSORT_AI_OCR=0
ENV SCREENSORT_VIDEO=0
ENV SCREENSORT_TRANSLATE=0
ENV SOURCE_DIR=/screenshots
ENV DB_FILE=/app/screenshots.db

# Volume for screenshots (mount your folder here)
VOLUME ["/screenshots", "/app/models", "/app/screenshots.db"]

# Default command
CMD ["python", "sort_screenshots.py", "--interval", "60"]
