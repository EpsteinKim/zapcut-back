#!/usr/bin/env sh
set -e

export ENV=production

[ -d "/zapcut-back/app/assets/fonts" ] || echo "warn: fonts missing"
[ -d "/zapcut-back/app/assets/sounds" ] || echo "warn: sounds missing"

exec uvicorn app.worker_main:app --host 0.0.0.0 --port 80 --workers 2 --access-log 