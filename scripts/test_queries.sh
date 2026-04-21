#!/usr/bin/env bash
# Run the 8 reference SPARQL queries against the local Ontop endpoint.
# Expects: docker compose up -d has completed and Ontop is ready on :8080.

set -e

ENDPOINT="${ENDPOINT:-http://localhost:8080/sparql}"
QDIR="$(cd "$(dirname "$0")/.." && pwd)/queries"

echo "Ramona VKG demo test runner"
echo "Endpoint: $ENDPOINT"
echo "---------------------------------------------"

for q in "$QDIR"/Q*.rq; do
  name="$(basename "$q" .rq)"
  echo
  echo "### $name"
  echo
  curl -sS -G "$ENDPOINT" \
    --data-urlencode "query@$q" \
    -H "Accept: text/csv" | head -40
  echo
  echo "---------------------------------------------"
done
