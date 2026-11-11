#!/usr/bin/env bash
# Validate the mappings and the queries without Docker.
#
#   scripts/offline_vkg/run_all.sh [work-directory]
#
# Loads db/*.sql into SQLite (dialect translation only), executes mappings/ramona.obda and
# mappings/ramona.r2rml.ttl over it, checks that the two give the same graph, types every
# individual by the domain and range axioms, checks that keys and foreign keys survive the
# mapping, and runs the reference queries.
# Needs Python 3 with rdflib. Nothing is written inside the repository.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${1:-$(mktemp -d)}"
H="$ROOT/scripts/offline_vkg"
mkdir -p "$WORK"
echo "== 1. seeds into SQLite"
python3 "$H/load_sqlite.py" "$ROOT" "$WORK/ramona.db" | grep -E "ok=|errors" || true
echo "== 2. ABox from the Ontop native mapping"
python3 "$H/materialize_obda.py" "$ROOT/mappings/ramona.obda" "$WORK/ramona.db" "$WORK/abox_obda.ttl" 2>/dev/null | head -1
echo "== 3. ABox from the R2RML mapping"
python3 "$H/materialize_r2rml.py" "$ROOT/mappings/ramona.r2rml.ttl" "$WORK/ramona.db" "$WORK/abox_r2rml.ttl" | head -1
echo "== 4. the two graphs"
python3 "$H/compare_graphs.py" "$WORK/abox_obda.ttl" "$WORK/abox_r2rml.ttl"
echo "== 5. domain and range typing"
python3 "$H/check_domain_range.py" "$WORK/abox_obda.ttl"
echo "== 6. keys, foreign keys and literals"
python3 "$H/check_integrity.py" "$WORK/ramona.db" "$WORK/abox_obda.ttl"
echo "== 7. the reference queries"
python3 "$H/run_queries.py" "$WORK/abox_obda.ttl" | sed -n '/^query/,$p'
echo "work directory: $WORK"
