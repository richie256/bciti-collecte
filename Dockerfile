# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final stage
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=America/Toronto \
    CACHE_FILE=/data/collections_cache.json

# Install minimal runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Set timezone correctly
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Use a non-root user for security
RUN mkdir /data && \
    useradd --create-home --shell /bin/bash scraperuser && \
    chown -R scraperuser:scraperuser /app /data

USER scraperuser
VOLUME /data

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD find /tmp/heartbeat -mmin -5 || exit 1

CMD ["python", "main.py"]
