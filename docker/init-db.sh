#!/bin/bash
set -e

# Create the postgres user if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
            CREATE USER postgres WITH SUPERUSER PASSWORD 'postgres';
        END IF;
    END
    \$\$;
    GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
    ALTER USER postgres WITH LOGIN;
EOSQL 
