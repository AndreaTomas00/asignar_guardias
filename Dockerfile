FROM python:3.11-slim-bullseye

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY *.py /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create directories for data persistence
RUN mkdir -p /app/data