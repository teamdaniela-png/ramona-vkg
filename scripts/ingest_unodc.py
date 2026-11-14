#!/usr/bin/env python3
"""
Ingest the UNODC data on trafficking in persons into the Ramona VKG Postgres.

Expects the workbook `data_glotip.xlsx` of the UNODC data portal
(https://dataunodc.un.org/dp-trafficking-persons), with the columns Iso3_code, Country, Region,
Subregion, Indicator, Dimension, Category, Sex, Age, Year, Unit of measurement, txtVALUE, Source.

Each row becomes one row of ramona.unodc_statistics, keyed by its position in the workbook.
A suppressed figure such as '<5' is kept as published and has no numeric value; a figure
written with one thousands separator, such as '2,015', is read as the number. Any other form is
kept as published without a numeric value. Rows whose
country code is not in ramona.countries are skipped and counted.

Usage:
    DSN="postgresql://ramona:ramona_demo@localhost:5432/ramona" \
      python scripts/ingest_unodc.py --xlsx /path/to/data_glotip.xlsx [--region Americas]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import psycopg
except ImportError:
    print("[unodc] psycopg is required. pip install 'psycopg[binary]'", file=sys.stderr)
    sys.exit(1)

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
COLUMNS = ["Iso3_code", "Country", "Region", "Subregion", "Indicator", "Dimension", "Category",
           "Sex", "Age", "Year", "Unit of measurement", "txtVALUE", "Source"]


def read_rows(path):
    """Rows of the first sheet as lists of strings. Reads the workbook's XML directly."""
    z = zipfile.ZipFile(path)
    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.parse(z.open("xl/sharedStrings.xml")).getroot().findall(NS + "si"):
            strings.append("".join(t.text or "" for t in si.iter(NS + "t")))

    def column(ref):
        n = 0
        for ch in re.match(r"[A-Z]+", ref).group(0):
            n = n * 26 + ord(ch) - 64
        return n - 1

    for row in ET.parse(z.open("xl/worksheets/sheet1.xml")).getroot().iter(NS + "row"):
        cells = {}
        for c in row.findall(NS + "c"):
            v = c.find(NS + "v")
            if c.get("t") == "inlineStr":
                value = "".join(t.text or "" for t in c.iter(NS + "t"))
            elif v is None:
                value = None
            elif c.get("t") == "s":
                value = strings[int(v.text)]
            else:
                value = v.text
            cells[column(c.get("r"))] = value
        yield [cells.get(i) for i in range(max(cells) + 1)] if cells else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--dsn", default=os.environ.get("DSN", "postgresql://ramona:ramona_demo@localhost:5432/ramona"))
    ap.add_argument("--region", help="load only the rows of this region, for example Americas")
    args = ap.parse_args()

    path = Path(args.xlsx)
    if not path.exists():
        print(f"[unodc] workbook not found: {path}", file=sys.stderr)
        sys.exit(2)

    rows = list(read_rows(path))
    header = next(i for i, r in enumerate(rows) if r and r[0] == "Iso3_code")
    if rows[header][:len(COLUMNS)] != COLUMNS:
        print(f"[unodc] unexpected columns: {rows[header]}", file=sys.stderr)
        sys.exit(2)
    release = next((r[0] for r in rows[:header] if r and r[0] and re.fullmatch(r"\d{2}/\d{2}/\d{4}", r[0])), None)
    day, month, year = release.split("/") if release else (None, None, None)
    dataset = "UNODC data portal, Trafficking in Persons" + (f", release of {year}-{month}-{day}" if release else "")

    with psycopg.connect(args.dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT source_id FROM evidence_source_extended WHERE source_kind='unodc' AND dataset_name=%s", (dataset,))
        r = cur.fetchone()
        if r is None:
            cur.execute(
                """
                INSERT INTO evidence_source_extended (source_kind, dataset_name, title, url, published_at)
                VALUES ('unodc', %s, 'UNODC Research - Data Portal - Trafficking in Persons',
                        'https://dataunodc.un.org/dp-trafficking-persons', %s)
                RETURNING source_id
                """,
                (dataset, f"{year}-{month}-{day}" if release else None),
            )
            source_id = cur.fetchone()[0]
        else:
            source_id = r[0]
        print(f"[unodc] evidence_source_id = {source_id}")

        cur.execute("SELECT country_iso3 FROM countries WHERE country_iso3 IS NOT NULL")
        known = set()
        while True:
            c = cur.fetchone()
            if c is None:
                break
            known.add(c[0])

        batch, loaded, skipped = [], 0, 0
        for stat_id, row in enumerate(rows[header + 1:], start=1):
            row = row + [None] * (len(COLUMNS) - len(row))
            iso3, region, indicator, dimension, category, sex, age, yr, published = (
                row[0], row[2], row[4], row[5], row[6], row[7], row[8], row[9], row[11])
            if not iso3 or published is None:
                continue
            if args.region and region != args.region:
                continue
            if iso3 not in known:
                skipped += 1
                continue
            published = str(published).strip()
            digits = published.replace(",", "") if re.fullmatch(r"\d{1,3},\d{3}", published) else published
            value = int(digits) if re.fullmatch(r"\d+", digits) else None
            batch.append((stat_id, source_id, iso3, indicator, dimension, category, sex, age, int(yr), value, published))
            if len(batch) == 5000:
                loaded += flush(cur, batch)
        loaded += flush(cur, batch)
        conn.commit()
        print(f"[unodc] done. figures ingested: {loaded}; skipped, country code not in the catalogue: {skipped}")


def flush(cur, batch):
    n = len(batch)
    if n:
        cur.executemany(
            """
            INSERT INTO unodc_statistics (stat_id, source_id, country_iso3, indicator, dimension, category,
                                          sex, age, year, value, value_as_published)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (stat_id) DO NOTHING
            """,
            batch,
        )
        batch.clear()
    return n


if __name__ == "__main__":
    main()
