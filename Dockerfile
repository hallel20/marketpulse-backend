FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies required for your Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # PostgreSQL client and development headers
        postgresql-client \
        libpq-dev \
        # Build tools for compiling Python packages
        build-essential \
        gcc \
        g++ \
        # Required for cryptography and other packages
        libffi-dev \
        libssl-dev \
        # Required for lxml
        libxml2-dev \
        libxslt1-dev \
        # Required for Pillow (if used)
        libjpeg-dev \
        libpng-dev \
        # General utilities
        curl \
        pkg-config \
        # Required for some Python packages
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]