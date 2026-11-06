#!/usr/bin/env bash
# Adds a note, removes the containers, starts them again and checks the note is still there.
# Then checks that the API refuses bad requests.
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

status() { curl -s -o /dev/null -w '%{http_code}' "$@"; }
[ "$(status -X POST "$URL" -H "Content-Type: application/json" -d '{"text": "   "}')" = 422 ]
[ "$(status -X DELETE "$URL/999999999")" = 404 ]
echo "PASS: the API refuses an empty note and a missing id"
