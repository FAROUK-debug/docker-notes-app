#!/usr/bin/env bash
# Adds a note, removes the containers, starts them again and checks the note is still there.
set -euo pipefail

URL=http://localhost:8000/api/notes
MARK="survives-$(date +%s)"

docker compose up -d --build --wait
curl -fsS -X POST "$URL" -H "Content-Type: application/json" -d "{\"text\": \"$MARK\"}" > /dev/null
echo "Added note: $MARK"

docker compose down
docker compose up -d --wait

curl -fsS "$URL" | grep -q "$MARK"
echo "PASS: the note survived docker compose down / up"
