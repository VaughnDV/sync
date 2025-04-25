FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*


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


# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app/src
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Use the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Run the application
CMD ["poetry", "run", "uvicorn", "src.sync.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
