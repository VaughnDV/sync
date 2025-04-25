#!/bin/bash
set -e

echo "Starting database initialization..."

# Create the postgres user if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
            CREATE USER postgres WITH SUPERUSER PASSWORD 'postgres';
            RAISE NOTICE 'Created postgres user';
        ELSE
            RAISE NOTICE 'postgres user already exists';
        END IF;
    END
    \$\$;
EOSQL

echo "Checking if database exists..."
# Create the database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    SELECT 'CREATE DATABASE vaughndv'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vaughndv')\gexec
EOSQL

echo "Setting up database permissions..."
# Grant privileges and set up the user
psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE vaughndv TO postgres;
    ALTER USER postgres WITH LOGIN;
    ALTER USER postgres WITH PASSWORD 'postgres';
EOSQL

echo "Database initialization complete!" 
