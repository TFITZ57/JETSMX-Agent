# Dockerfile for Pub/Sub handler
FROM python:3.11-slim

WORKDIR /app

# Copy root requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pubsub_handlers requirements
COPY infra/pubsub_handlers/requirements.txt infra/pubsub_handlers/requirements.txt
RUN pip install --no-cache-dir -r infra/pubsub_handlers/requirements.txt

# Copy application code (from project root)
COPY shared/ shared/
COPY tools/ tools/
COPY agents/ agents/
COPY infra/ infra/

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

# Run the application
CMD exec uvicorn infra.pubsub_handlers.main:app --host 0.0.0.0 --port ${PORT}

