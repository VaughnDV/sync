#!/bin/bash
set -e

echo "Starting database initialization..."

# Create the database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE vaughndv' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vaughndv')\gexec
    GRANT ALL PRIVILEGES ON DATABASE vaughndv TO postgres;
EOSQL

echo "Database initialization completed." 