# Use Python 3.8 slim image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_CACHE_DIR=/opt/poetry_cache
ENV POSTGRES__HOST=postgres
ENV REDIS__HOST=redis

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        supervisor 
        
# Install Poetry
RUN pip install poetry==1.8.2

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false && poetry install 

# Copy project
COPY . .

# Create directories for logs and media
RUN mkdir -p _logs media/uploads static

# Copy supervisor config
COPY tools/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

# Expose port
EXPOSE 8000

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
