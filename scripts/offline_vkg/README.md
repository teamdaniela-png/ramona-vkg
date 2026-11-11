# Validating the VKG without Docker

Ontop answers SPARQL by rewriting it into SQL over Postgres. These scripts check the same mappings
and the same queries without either: the seed files are loaded into SQLite, the mapping files are
executed row by row to produce the graph Ontop would expose, and the queries are run over that graph
together with the ontology.

```bash
scripts/offline_vkg/run_all.sh
```

| Script | What it does |
| --- | --- |
| `load_sqlite.py` | Loads `db/*.sql` into SQLite. Only the SQL dialect is translated; no datum is changed. |
| `materialize_obda.py` | Executes `mappings/ramona.obda` and writes the ABox. |
| `materialize_r2rml.py` | Executes `mappings/ramona.r2rml.ttl`, following the W3C R2RML recommendation, and writes the ABox. |
| `compare_graphs.py` | Compares the two ABoxes triple for triple. |
| `check_domain_range.py` | Types every individual by the domain and range axioms of the properties it takes part in and reports any class outside the hierarchy of its asserted one. |
| `check_integrity.py` | Checks that keys, foreign keys and datatypes survive the mapping, and writes `docs/MAPPING_SPEC.md`. |
| `run_queries.py` | Runs the reference queries over the ABox plus the TBox closure Ontop applies at rewrite time. |
| `shim/psycopg.py` | A sqlite-backed stand-in for psycopg, so `scripts/ingest_ctdc.py` can load the CTDC release into the same SQLite file. |

## With the CTDC victim records

The CTDC Global Synthetic Dataset is not redistributed here. With a downloaded copy:

```bash
WORK=$(mktemp -d)
python3 scripts/offline_vkg/load_sqlite.py . $WORK/ramona.db
SQLITE_PATH=$WORK/ramona.db PYTHONPATH=scripts/offline_vkg/shim \
  python3 scripts/ingest_ctdc.py --csv /path/to/CTDC_global_synthetic_data_v2025.csv
```

The full load is 257,969 victim records. The in-memory query runner is comfortable with a sample;
`docs/validation/QUERY_EXECUTION_REPORT.md` used one victim in forty.

## What this does not replace

Query answering by reformulation is Ontop's job and is exercised by the Docker stack described in the
top-level README. These scripts establish that the seeds load, that the mappings produce a graph
consistent with the ontology, and what each query returns over that graph.
