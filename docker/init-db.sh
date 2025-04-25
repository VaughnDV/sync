#!/bin/bash
set -e

# Create the postgres user and database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER postgres WITH SUPERUSER PASSWORD 'postgres';
    GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
    ALTER USER postgres WITH LOGIN;
EOSQL 