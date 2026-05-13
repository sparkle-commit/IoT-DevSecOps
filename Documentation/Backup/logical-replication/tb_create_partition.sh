#!/bin/bash
TABLE_NAME="ts_kv_$(date -d '+1 month' +%Y_%m)"
START_TS=$(date -d "$(date -d '+1 month' +%Y-%m-01)" +%s)000
END_TS=$(date -d "$(date -d '+2 month' +%Y-%m-01)" +%s)000

echo "$(date) - Checking partition: ${TABLE_NAME}"
echo "$(date) - Range: ${START_TS} to ${END_TS}"

EXISTS=$(sudo -u postgres psql -d thingsboard -tAc \
  "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = '${TABLE_NAME}');")

if [ "$EXISTS" = "f" ]; then
  echo "$(date) - Creating partition: ${TABLE_NAME}"
  sudo -u postgres psql -d thingsboard -c \
    "CREATE TABLE ${TABLE_NAME} PARTITION OF ts_kv \
     FOR VALUES FROM (${START_TS}) TO (${END_TS});"
  echo "$(date) - Partition ${TABLE_NAME} created!"
else
  echo "$(date) - Partition ${TABLE_NAME} already exists, skipping."
fi
