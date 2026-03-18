# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download BART model to reduce first-request latency
RUN python -c "from transformers import BartForConditionalGeneration, BartTokenizer; \
    BartTokenizer.from_pretrained('facebook/bart-large-cnn'); \
    BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')"

# Final stage
FROM python:3.11-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy model cache from builder
COPY --from=builder --chown=appuser:appuser /root/.cache /home/appuser/.cache

# Copy application code
COPY --chown=appuser:appuser . .

# Create transcripts directory
RUN mkdir -p transcripts && chown -R appuser:appuser transcripts

# Switch to non-root user
USER appuser

# Set environment variables for BART configuration
ENV BART_DEVICE=cpu
ENV BART_ENABLE_FALLBACK=true
ENV BART_WARMUP=true
ENV PYTHONUNBUFFERED=1

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/bart')" || exit 1

# Run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
