FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY backend/pyproject.toml backend/.python-version ./

# Create src directory structure
RUN mkdir -p src/finagent

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy source code
COPY backend/src/ ./src/

# Create data directories
RUN mkdir -p data/documents data/vector_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "finagent.main:app", "--host", "0.0.0.0", "--port", "8000"]
