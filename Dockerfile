# Dockerfile for Railway to run both backend and frontend (for simplicity in Monorepo without multiple services)
# In a real scenario, you might want two separate services.
# Here we will use a multi-stage build or just a python image that also installs node.

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for frontend build)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Backend Setup
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend/

# Frontend Setup
COPY frontend/package.json frontend/
WORKDIR /app/frontend
RUN npm install

COPY frontend .
RUN npm run build

# Back to backend root for running the app
WORKDIR /app/backend

# Expose ports
EXPOSE 8000

# Start script
# Running as 'app.main:app' assuming we are in /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
