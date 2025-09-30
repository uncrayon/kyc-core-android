FROM python:3.11-slim

WORKDIR /app

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY worker/ .

# Copy config file
COPY config.yaml /app/config.yaml

CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info", "--queues=kyc_processing"]
