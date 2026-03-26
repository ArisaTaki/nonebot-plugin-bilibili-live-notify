#!/usr/bin/env bash

set -euo pipefail

ROOM_ID="${1:-711308}"
PROXY_URL="${BILIBILI_LIVE_NOTIFY_PROXY_URL:-http://127.0.0.1:8000/bilibili/live?room_id={room_id}}"
URL="${PROXY_URL//\{room_id\}/$ROOM_ID}"

echo "GET $URL"
RESPONSE="$(curl --fail --silent --show-error "$URL")"
echo "$RESPONSE"

python3 -c '
import json
import sys

payload = json.loads(sys.argv[1])
required = {"ok", "is_live", "title", "cover"}
missing = sorted(required - payload.keys())
if missing:
    raise SystemExit(f"missing keys: {missing}")
print("payload ok")
' "$RESPONSE"
