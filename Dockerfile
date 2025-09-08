# Dockerfile for Sanctions Screening Platform
# Author: Eon (Himanshu Shekhar)
# Email: eonhimanshu@gmail.com
# GitHub: https://github.com/eonn/sanctions-screening
# Created: 2024

# Multi-stage build optimized for Fedora 42
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies with Fedora-compatible packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with optimizations

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --user --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for Fedora 42 optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONHASHSEED=random
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache

# Install runtime dependencies optimized for Fedora
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p app/static data logs cache && \
    chmod -R 755 /app

# Create non-root user for security (Fedora 42 compatible)
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser && \
    mkdir -p /home/appuser/.local && \
    cp -r /root/.local/* /home/appuser/.local/ && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /home/appuser/.local

# Switch to non-root user
USER appuser

# Set PATH for the appuser
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check optimized for Fedora 42
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with optimized settings
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 