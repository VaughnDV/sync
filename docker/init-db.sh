#!/bin/bash
set -e

# Create the rdb user and database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'rdb') THEN
            CREATE USER rdb WITH SUPERUSER PASSWORD 'postgres';
        END IF;
    END
    \$\$;
    GRANT ALL PRIVILEGES ON DATABASE vaughndv TO rdb;
    ALTER USER rdb WITH LOGIN;
EOSQL 
