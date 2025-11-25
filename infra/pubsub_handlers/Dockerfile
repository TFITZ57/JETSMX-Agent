# Dockerfile for Pub/Sub handler
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8081

# Run the application
CMD exec uvicorn infra.pubsub_handlers.main:app --host 0.0.0.0 --port ${PORT}

