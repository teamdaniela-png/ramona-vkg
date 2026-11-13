#!/usr/bin/env bash
# Validate the running demonstrator against the offline validation.
#
#   scripts/ontop/run_all.sh [work-directory]
#
# Expects `docker compose up -d` on a fresh volume, that is, the seeds without the CTDC load.
# Runs the reference queries through the Ontop endpoint and compares the row counts with the
# published ones, materialises the graph with Ontop, compares it with the graph that
# scripts/offline_vkg/run_all.sh produces from the same files, and compares the answers of
# the two runs row by row.
# Needs Docker Compose v2 and Python 3 with rdflib. Nothing is written inside the repository.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${1:-$(mktemp -d)}"
H="$ROOT/scripts/ontop"
ENDPOINT="${ENDPOINT:-http://localhost:8080/sparql}"
IN=/opt/ontop/input
mkdir -p "$WORK"
cd "$ROOT"
echo "== 1. the endpoint"
for _ in $(seq 1 90); do
  code="$(curl -s -o /dev/null -w '%{http_code}' -G "$ENDPOINT" --data-urlencode 'query=ASK { ?s ?p ?o }' || true)"
  [ "$code" = 200 ] && break
  python3 -c "import time; time.sleep(2)"
done
[ "$code" = 200 ] || { echo "no answer from $ENDPOINT"; exit 1; }
echo "$ENDPOINT answers"
echo "== 2. the reference queries through Ontop"
python3 "$H/run_queries.py" --dump "$WORK/answers_ontop"
echo "== 3. the graph Ontop materialises"
docker compose exec -T ontop /opt/ontop/ontop materialize \
  -m "$IN/ramona.obda" -t "$IN/ratr-o.ttl" -p "$IN/ontop.properties" \
  -f ntriples -o /tmp/ontop.nt 2>&1 | grep "NR of TRIPLES"
docker compose cp ontop:/tmp/ontop.nt "$WORK/ontop.nt" >/dev/null 2>&1
echo "== 4. the graph of the offline validation"
"$ROOT/scripts/offline_vkg/run_all.sh" "$WORK/offline" | grep -E "^mappings:|^executed|^row counts"
echo "== 5. the two graphs"
python3 "$H/compare_with_offline.py" "$WORK/ontop.nt" "$WORK/offline/abox_obda.ttl"
echo "== 6. the answers of the two runs"
python3 "$ROOT/scripts/offline_vkg/run_queries.py" "$WORK/offline/abox_obda.ttl" --dump "$WORK/answers_offline" >/dev/null
python3 "$H/compare_answers.py" "$WORK/answers_ontop" "$WORK/answers_offline"
echo "work directory: $WORK"
