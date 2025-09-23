#!/bin/bash
set -e

# postgresql.conf를 직접 수정하거나 ALTER SYSTEM 사용
psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<-EOSQL
    ALTER SYSTEM SET shared_buffers = '1GB';
    ALTER SYSTEM SET work_mem = '64MB';
    ALTER SYSTEM SET maintenance_work_mem = '512MB';
EOSQL