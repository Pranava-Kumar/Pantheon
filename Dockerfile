# Multi-stage Dockerfile for Project Pantheon
# Optimized for small image size and fast builds

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY pantheon/ ./pantheon/
COPY tests/ ./tests/
COPY pyproject.toml .
COPY .env.example .env

# Ensure scripts are executable
RUN chmod +x pantheon/jobs/*.py 2>/dev/null || true

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health', timeout=5)" || exit 1

# Default command (API server)
CMD ["uvicorn", "pantheon.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
