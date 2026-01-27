# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Create requirements.txt and install CPU-only PyTorch (MUCH smaller)
RUN pip install --no-cache-dir pip-tools && \
    pip-compile pyproject.toml -o requirements.txt && \
    # Remove CUDA PyTorch and install CPU-only version
    grep -v "nvidia" requirements.txt | grep -v "triton" > requirements-cpu.txt && \
    pip install --no-cache-dir --target=/app/deps \
        torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --target=/app/deps -r requirements-cpu.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder
COPY --from=builder /app/deps /usr/local/lib/python3.11/site-packages/

# Copy application code
COPY app/ ./app/
COPY pyproject.toml ./

# Create data directory
RUN mkdir -p /app/data /app/logs

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
