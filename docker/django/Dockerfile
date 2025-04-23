FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .

# Install the project in development mode
RUN poetry install --no-interaction --no-ansi

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Create a script to run migrations and start the server
RUN echo '#!/bin/bash\n\
poetry run python src/manage.py migrate\n\
poetry run python src/manage.py runserver 0.0.0.0:8000' > /app/start.sh && \
chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"] 