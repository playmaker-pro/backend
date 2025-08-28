# Use Python 3.8 base image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
        netcat-traditional \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry
RUN poetry config virtualenvs.create false

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install Python dependencies (including dev for better development experience)
RUN poetry install

# Create directories for logs and media
RUN mkdir -p _logs media

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Wait for postgres\n\
echo "Waiting for postgres..."\n\
while ! nc -z $POSTGRES__HOST $POSTGRES__PORT; do\n\
  sleep 0.1\n\
done\n\
echo "PostgreSQL started"\n\
\n\
# Wait for redis\n\
echo "Waiting for redis..."\n\
while ! nc -z $REDIS__HOST $REDIS__PORT; do\n\
  sleep 0.1\n\
done\n\
echo "Redis started"\n\
\n\
# Run migrations\n\
python manage.py migrate\n\
\n\
# Collect static files\n\
python manage.py collectstatic --noinput\n\
\n\
# Execute command\n\
exec "$@"' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
