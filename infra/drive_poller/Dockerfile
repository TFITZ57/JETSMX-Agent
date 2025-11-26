FROM python:3.11-slim

WORKDIR /app

# Copy root requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy drive poller requirements
COPY infra/drive_poller/requirements.txt infra/drive_poller/requirements.txt
RUN pip install --no-cache-dir -r infra/drive_poller/requirements.txt

# Copy application code
COPY shared/ shared/
COPY tools/ tools/
COPY infra/drive_poller/ infra/drive_poller/

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

CMD exec python infra/drive_poller/main.py

