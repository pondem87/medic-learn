#!/bin/sh
set -eu
backup_file=$(mktemp /tmp/meded-staging-XXXXXX.dump)
trap 'rm -f "$backup_file"' EXIT HUP INT TERM
pg_dump --format=custom --no-owner --no-acl --file="$backup_file"
backup_key="postgres/$(date -u +%Y/%m/%d)/$(date -u +%Y%m%dT%H%M%SZ).dump"
aws s3 cp "$backup_file" "s3://${BACKUP_BUCKET}/${backup_key}" --sse AES256
echo "Staging PostgreSQL backup uploaded: ${backup_key}"
