FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for your packages
RUN apt-get update && apt-get install -y \
    pkg-config \
    libcairo2-dev \
    gcc \
    g++ \
    python3-dev \
    libssl-dev \
    libffi-dev \
    portaudio19-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories that your app needs at runtime
RUN mkdir -p /app/data /app/reports /app/.cache

# Expose port (Render will override this with PORT env var)
EXPOSE 8000

# Health check for monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
# Use $PORT env var from Render, fallback to 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}