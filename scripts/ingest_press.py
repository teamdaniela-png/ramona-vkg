#!/usr/bin/env python3
"""
Ingest classified press cases into the Ramona VKG Postgres.

Reads data/processed/press_cases.jsonl (output of classify_press.py) and writes
rows into:
  * evidence_source_extended  (one per article)
  * victim                    (one per article, source_kind='press')
  * victim_exploitation       (from article-level exploitation hits)
  * offer_detection_track     (flags A/B counts for the associated offer-like record)

NOTE: a press article does not correspond to exactly one victim. We create one
anonymised "case" row per article to preserve the 1:1 ingestion mapping. The
dashboard treats press cases as aggregated indicators, not individual victims.

Usage:
    DSN="postgresql://ramona:ramona@localhost:5432/ramona" python scripts/ingest_press.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import psycopg
except ImportError:
    print("[press] psycopg is required. pip install 'psycopg[binary]'", file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/processed/press_cases.jsonl")
    ap.add_argument("--dsn", default=os.environ.get("DSN", "postgresql://ramona:ramona@localhost:5432/ramona"))
    args = ap.parse_args()
    inp = Path(args.inp)

    with psycopg.connect(args.dsn) as conn, conn.cursor() as cur:
        inserted = 0
        with inp.open() as f:
            for line in f:
                rec = json.loads(line)
                src_url = rec.get("url")
                cur.execute(
                    """
                    INSERT INTO evidence_source_extended (source_kind, outlet, title, url, published_at)
                    VALUES ('press', %s, %s, %s, NULL)
                    ON CONFLICT DO NOTHING
                    RETURNING source_id
                    """,
                    (rec.get("outlet"), rec.get("title"), src_url),
                )
                r = cur.fetchone()
                if r is None:
                    cur.execute(
                        "SELECT source_id FROM evidence_source_extended WHERE source_kind='press' AND url=%s",
                        (src_url,),
                    )
                    r = cur.fetchone()
                if r is None:
                    continue
                source_id = r[0]

                external_id = f"press_{rec['id']}"
                coe = rec["countries"][0] if rec["countries"] else None
                comm_tool = rec["communication_tools"][0] if rec["communication_tools"] else None
                rec_meth = rec["recruitment_methods"][0] if rec["recruitment_methods"] else None

                cur.execute(
                    """
                    INSERT INTO victim (external_id, source_kind, source_id,
                                        country_of_exploitation_iso3,
                                        recruitment_method_code,
                                        communication_tool_code)
                    VALUES (%s, 'press', %s, %s, %s, %s)
                    ON CONFLICT (source_kind, external_id) DO NOTHING
                    RETURNING victim_id
                    """,
                    (external_id, source_id, coe, rec_meth, comm_tool),
                )
                r = cur.fetchone()
                if r is None:
                    cur.execute(
                        "SELECT victim_id FROM victim WHERE source_kind='press' AND external_id=%s",
                        (external_id,),
                    )
                    r = cur.fetchone()
                if r is None:
                    continue
                victim_id = r[0]

                for e in rec["exploitation_types"]:
                    cur.execute(
                        "INSERT INTO victim_exploitation (victim_id, exploitation_type_code) "
                        "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (victim_id, e),
                    )
                # detection track, using victim_id as the "offer_id" proxy for press cases
                cur.execute(
                    """
                    INSERT INTO offer_detection_track
                        (offer_id, has_classic_red_flags, classic_flag_count,
                         has_credible_lethal_pattern, credible_pattern_count, comment)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (offer_id) DO UPDATE SET
                        has_classic_red_flags = EXCLUDED.has_classic_red_flags,
                        classic_flag_count = EXCLUDED.classic_flag_count,
                        has_credible_lethal_pattern = EXCLUDED.has_credible_lethal_pattern,
                        credible_pattern_count = EXCLUDED.credible_pattern_count
                    """,
                    (victim_id, rec["type_a"], len(rec["flags_classic"]),
                     rec["type_b"], len(rec["flags_credible_lethal"]),
                     f"{','.join(rec['flags_classic'])}|{','.join(rec['flags_credible_lethal'])}"),
                )
                inserted += 1
        conn.commit()
    print(f"[press] ingested: {inserted}")


if __name__ == "__main__":
    main()
