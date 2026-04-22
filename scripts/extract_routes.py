#!/usr/bin/env python3
"""
Extract trafficking routes from the CTDC Global Synthetic Dataset.

Reads the CTDC CSV (27 variables, 257k rows) and produces SQL INSERT statements
for db/06_ctdc_routes.sql: one row per unique (citizenship, CountryOfExploitation)
pair observed with at least N victims. Also outputs a summary JSON with
route-level statistics.

Each route records:
  - iso3 origin and destination
  - victim count
  - earliest yearOfRegistration observed
  - latest yearOfRegistration observed
  - dominant exploitation type (from the majority of victims on that route)
  - dominant gender
  - dominant age group

Usage:
    python scripts/extract_routes.py \
        --csv /Users/danielacamberos/Downloads/CTDC_global_synthetic_data_v2025.csv \
        --out db/06_ctdc_routes.sql \
        --summary docs/routes_summary.json \
        --min-victims 5
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


EXPLOITATION_COLUMNS = [
    ("typeOfLabourAgriculture",  "labour_agriculture"),
    ("typeOfLabourConstruction", "labour_construction"),
    ("typeOfLabourDomesticWork", "labour_domestic"),
    ("typeOfLabourHospitality",  "labour_hospitality"),
    ("typeOfSexProstitution",    "sex_prostitution"),
    ("typeOfSexPornography",     "sex_pornography"),
    ("isForcedLabour",           "labour_other"),
    ("isSexualExploit",          "sex_generic"),
    ("isOtherExploit",           "other_exploit"),
]


def clean(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v if v and v.upper() != "NULL" else None


def is_one(v: str | None) -> bool:
    return v is not None and v.strip() == "1"


def sql_str(s: str | None) -> str:
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default="db/06_ctdc_routes.sql")
    ap.add_argument("--summary", default="docs/routes_summary.json")
    ap.add_argument("--min-victims", type=int, default=5)
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    # route_key -> dict of aggregates
    routes = defaultdict(lambda: {
        "count": 0,
        "years": [],
        "exploitation_types": Counter(),
        "genders": Counter(),
        "age_groups": Counter(),
    })

    total = 0
    with csv_path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            origin = clean(row.get("citizenship"))
            dest = clean(row.get("CountryOfExploitation"))
            if not origin or not dest:
                continue
            key = (origin, dest)
            r = routes[key]
            r["count"] += 1
            yr = clean(row.get("yearOfRegistration"))
            if yr and yr.isdigit():
                r["years"].append(int(yr))
            for col, exp in EXPLOITATION_COLUMNS:
                if is_one(row.get(col)):
                    r["exploitation_types"][exp] += 1
            g = clean(row.get("gender"))
            if g:
                r["genders"][g] += 1
            ag = clean(row.get("ageBroad"))
            if ag:
                r["age_groups"][ag] += 1

    # filter and prepare rows
    filtered = [((o, d), agg) for (o, d), agg in routes.items() if agg["count"] >= args.min_victims]
    filtered.sort(key=lambda kv: -kv[1]["count"])

    # write SQL
    out = Path(args.out)
    lines = []
    lines.append("-- CTDC-derived trafficking routes")
    lines.append(f"-- Extracted from {total:,} victim records in the CTDC Global Synthetic Dataset v2025")
    lines.append(f"-- {len(filtered):,} routes with >= {args.min_victims} victims")
    lines.append("")
    lines.append("SET search_path TO ramona, public;")
    lines.append("")
    lines.append("-- One row per unique (citizenship, country_of_exploitation) pair.")
    lines.append("-- route_name format: 'ORIGIN_ISO3 -> DEST_ISO3'. known_since = earliest yearOfRegistration.")
    lines.append("")
    lines.append("INSERT INTO trafficking_routes (route_name, origin_country, destination_country, known_since, evidence_source) VALUES")
    value_rows = []
    for (o, d), agg in filtered:
        # origin and destination in the routes table use 2-letter country codes
        # but CTDC gives ISO3. we keep ISO3 as the code for now. The countries
        # table in the schema can be extended to hold ISO3.
        name = f"{o} -> {d}"
        year = min(agg["years"]) if agg["years"] else None
        sql_year = f"DATE '{year}-01-01'" if year else "NULL"
        # evidence_source: we reference the CTDC dataset (inserted by ingest_ctdc)
        # Not every install has that row yet, so we leave NULL and rely on the
        # OBDA mapping to recover provenance through source_kind='ctdc'.
        value_rows.append(f"  ({sql_str(name)}, {sql_str(o)}, {sql_str(d)}, {sql_year}, NULL)")
    lines.append(",\n".join(value_rows))
    lines.append("ON CONFLICT DO NOTHING;")
    lines.append("")

    out.write_text("\n".join(lines))
    print(f"wrote {out}: {len(filtered):,} routes from {total:,} victims")

    # write summary JSON
    summary = {
        "total_records": total,
        "total_routes": len(filtered),
        "min_victims_threshold": args.min_victims,
        "top_20_routes_by_victims": [
            {
                "origin": o,
                "destination": d,
                "victims": agg["count"],
                "year_range": [min(agg["years"]) if agg["years"] else None,
                               max(agg["years"]) if agg["years"] else None],
                "top_exploitation": agg["exploitation_types"].most_common(3),
                "top_gender": agg["genders"].most_common(1),
                "top_age_group": agg["age_groups"].most_common(1),
            }
            for (o, d), agg in filtered[:20]
        ],
    }
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"wrote {args.summary}")


if __name__ == "__main__":
    main()
