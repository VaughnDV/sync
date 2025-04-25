FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Copy and set up entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set proper permissions
RUN chown -R appuser:appuser /app && \
    chown -R appuser:appuser /usr/local/lib/python3.11/site-packages && \
    chown -R appuser:appuser /usr/local/bin/poetry

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app/src
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Switch to non-root user
USER appuser

# Use the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Run the application
CMD ["poetry", "run", "uvicorn", "src.sync.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
