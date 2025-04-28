FROM python:3.11-slim

WORKDIR /app


ENV PYTHONPATH=${PYTHONPATH}:${PWD} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.5.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    netcat-traditional \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*


# Install Poetry
RUN pip install --upgrade pip setuptools wheel && \
    pip install "poetry==$POETRY_VERSION" && \
    poetry --version

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Copy and set up entrypoint and init-db script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh 

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app/src
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Use the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
RUN chmod +x entrypoint.prod.sh

# Run the application
CMD ["poetry", "run", "uvicorn", "src.sync.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
