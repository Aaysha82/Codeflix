# ProofSAR AI — Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Compile C++ Detection Engine
RUN g++ -o DETECTION/detector DETECTION/structuring.cpp -std=c++17 -IDETECTION/include || echo "C++ Compilation failed, using Python fallback"

# Expose ports
EXPOSE 8000 8501

# Default environment variables
ENV BACKEND_URL=http://localhost:8000
ENV REDIS_URL=redis://redis:6379/0

# Command to run (overridden by docker-compose for specific services)
CMD ["python", "run_app.py"]
