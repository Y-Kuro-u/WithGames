# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

# Copy dependency files and README (required for package build)
COPY pyproject.toml uv.lock .python-version README.md ./

# Install Python dependencies using uv
RUN uv sync --no-dev

# Copy application code
COPY src/ ./src/
COPY .env.example .env.example

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

USER botuser

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the bot directly using Python from the virtual environment
CMD [".venv/bin/python", "-m", "src.main"]
