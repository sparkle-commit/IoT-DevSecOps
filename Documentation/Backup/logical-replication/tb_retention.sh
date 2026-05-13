#!/bin/bash
RETENTION_MONTHS=3
BACKUP_HOST="192.168.35.10"
BACKUP_USER="postgres"
BACKUP_DB="thingsboard"

ARCHIVE_MONTH=$(date -d "-${RETENTION_MONTHS} months" +"%Y_%m")
TABLE_NAME="ts_kv_${ARCHIVE_MONTH}"

echo "$(date) - Checking archive table: ${TABLE_NAME}"

# Cek tabel ada di main
EXISTS_MAIN=$(docker exec tb-postgres psql -U postgres -d thingsboard -tAc \
  "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '${TABLE_NAME}');")

if [ "$EXISTS_MAIN" = "f" ]; then
  echo "$(date) - Table ${TABLE_NAME} not found in main, skipping."
  exit 0
fi

# Verifikasi ada di backup
EXISTS_BACKUP=$(psql -h $BACKUP_HOST -U $BACKUP_USER -d $BACKUP_DB -tAc \
  "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '${TABLE_NAME}');" 2>/dev/null)

if [ "$EXISTS_BACKUP" != "t" ]; then
  echo "$(date) - WARNING: Table ${TABLE_NAME} not found in backup! Skipping drop."
  exit 1
fi

# Bandingkan row count
COUNT_MAIN=$(docker exec tb-postgres psql -U postgres -d thingsboard -tAc \
  "SELECT COUNT(*) FROM ${TABLE_NAME};")
COUNT_BACKUP=$(psql -h $BACKUP_HOST -U $BACKUP_USER -d $BACKUP_DB -tAc \
  "SELECT COUNT(*) FROM ${TABLE_NAME};" 2>/dev/null)

echo "$(date) - Main: ${COUNT_MAIN} rows | Backup: ${COUNT_BACKUP} rows"

if [ "$COUNT_MAIN" = "$COUNT_BACKUP" ]; then
  echo "$(date) - Data verified! Dropping ${TABLE_NAME} from main..."
  docker exec tb-postgres psql -U postgres -d thingsboard -c \
    "DROP TABLE IF EXISTS ${TABLE_NAME};"
  echo "$(date) - Done! ${TABLE_NAME} removed from main DB."
else
  echo "$(date) - WARNING: Row count mismatch! Skipping drop."
  exit 1
fi
