# Dockerfile for webhook receiver
FROM python:3.11-slim

WORKDIR /app

# Copy root requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy webhook requirements
COPY infra/webhooks/requirements.txt infra/webhooks/requirements.txt
RUN pip install --no-cache-dir -r infra/webhooks/requirements.txt

# Copy application code (from project root)
COPY shared/ shared/
COPY tools/ tools/
COPY infra/ infra/

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

# Run the application
CMD exec uvicorn infra.webhooks.main:app --host 0.0.0.0 --port ${PORT}

