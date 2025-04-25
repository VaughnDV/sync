#!/bin/bash
set -e

# Create the postgres user and database
psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
            CREATE USER postgres WITH SUPERUSER PASSWORD 'postgres';
        END IF;
    END
    \$\$;
    CREATE DATABASE vaughndv;
    GRANT ALL PRIVILEGES ON DATABASE vaughndv TO postgres;
    ALTER USER postgres WITH LOGIN;
EOSQL 
