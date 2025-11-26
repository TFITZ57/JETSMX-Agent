FROM python:3.11-slim

WORKDIR /app

# Copy root requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy uploader requirements
COPY infra/resume_uploader/requirements.txt infra/resume_uploader/requirements.txt
RUN pip install --no-cache-dir -r infra/resume_uploader/requirements.txt

# Copy application code
COPY shared/ shared/
COPY tools/ tools/
COPY infra/resume_uploader/ infra/resume_uploader/

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

WORKDIR /app/infra/resume_uploader

CMD exec python main.py

