#!/usr/bin/env python3
"""
Ingest the CTDC Global Synthetic Dataset (IOM, 2025) into the Ramona VKG Postgres.

Expects a CSV with the 27 variables documented in
Codebook_CTDC_global_synthetic_data_v2025.pdf.

Mapping (CTDC column -> Ramona table/column):

  yearOfRegistration          -> victim.year_of_registration
  gender                      -> victim.gender_code          (Woman/Man/Trans... -> female/male/trans_nc)
  ageBroad                    -> victim.age_group_code
  citizenship                 -> victim.citizenship_iso3
  CountryOfExploitation       -> victim.country_of_exploitation_iso3
  traffickMonths              -> victim.traffick_duration_band
  meansDebtBondageEarnings    -> victim_means_of_control('debt_bondage_earnings')
  meansThreats                -> victim_means_of_control('threats')
  meansAbusePsyPhySex         -> victim_means_of_control('abuse_psy_phy_sex')
  meansFalsePromises          -> victim_means_of_control('false_promises')
  meansDrugsAlcohol           -> victim_means_of_control('drugs_alcohol')
  meansDenyBasicNeeds         -> victim_means_of_control('deny_basic_needs')
  meansExcessiveWorkHours     -> victim_means_of_control('excessive_work_hours')
  meansWithholdDocs           -> victim_means_of_control('withhold_docs')
  isForcedLabour              -> victim_exploitation('labour_other')  [broad bucket]
  isSexualExploit             -> victim_exploitation('sex_prostitution' or 'sex_pornography' if given)
  isOtherExploit              -> victim_exploitation('other')
  typeOfLabourAgriculture     -> victim_exploitation('labour_agriculture')
  typeOfLabourConstruction    -> victim_exploitation('labour_construction')
  typeOfLabourDomesticWork    -> victim_exploitation('labour_domestic')
  typeOfLabourHospitality     -> victim_exploitation('labour_hospitality')
  typeOfSexProstitution       -> victim_exploitation('sex_prostitution')
  typeOfSexPornography        -> victim_exploitation('sex_pornography')
  recruiterRelationIntimatePartner -> recruitment_method='intimate_partner'
  recruiterRelationFriend     -> recruitment_method='friend'
  recruiterRelationFamily     -> recruitment_method='family'
  recruiterRelationOther      -> recruitment_method='other'

Usage:
    DSN="postgresql://ramona:ramona@localhost:5432/ramona" \
      python scripts/ingest_ctdc.py --csv /path/to/ctdc_global_synthetic_v2025.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

try:
    import psycopg
except ImportError:
    print("[ctdc] psycopg is required. pip install 'psycopg[binary]'", file=sys.stderr)
    sys.exit(1)


GENDER_MAP = {
    "Woman": "female",
    "Man": "male",
    "Trans/Transgender/NonConforming": "trans_nc",
    "Trans": "trans_nc",
    "": None,
    None: None,
}

EXPLOITATION_TYPE_FROM_ROW = [
    ("typeOfLabourAgriculture",  "labour_agriculture"),
    ("typeOfLabourConstruction", "labour_construction"),
    ("typeOfLabourDomesticWork", "labour_domestic"),
    ("typeOfLabourHospitality",  "labour_hospitality"),
    ("typeOfSexProstitution",    "sex_prostitution"),
    ("typeOfSexPornography",     "sex_pornography"),
]

MEANS_FROM_ROW = [
    ("meansDebtBondageEarnings", "debt_bondage_earnings"),
    ("meansThreats",             "threats"),
    ("meansAbusePsyPhySex",      "abuse_psy_phy_sex"),
    ("meansFalsePromises",       "false_promises"),
    ("meansDrugsAlcohol",        "drugs_alcohol"),
    ("meansDenyBasicNeeds",      "deny_basic_needs"),
    ("meansExcessiveWorkHours",  "excessive_work_hours"),
    ("meansWithholdDocs",        "withhold_docs"),
]

RECRUITER_RELATION_FROM_ROW = [
    ("recruiterRelationIntimatePartner", "intimate_partner"),
    ("recruiterRelationFriend",          "friend"),
    ("recruiterRelationFamily",          "family"),
    ("recruiterRelationOther",           "other"),
]

AGE_CANON = {
    "0--8": "0-8", "0-8": "0-8", "0—8": "0-8",
    "9--17": "9-17", "9-17": "9-17", "9—17": "9-17",
    "18--20": "18-20", "18-20": "18-20", "18—20": "18-20",
    "21--23": "21-23", "21-23": "21-23", "21—23": "21-23",
    "24--26": "24-26", "24-26": "24-26", "24—26": "24-26",
    "27--29": "27-29", "27-29": "27-29", "27—29": "27-29",
    "30--38": "30-38", "30-38": "30-38", "30—38": "30-38",
    "39--47": "39-47", "39-47": "39-47", "39—47": "39-47",
    "48+":   "48+",
}


def _one_or_none(v: str | None) -> bool:
    return v is not None and str(v).strip() == "1"


def _clean(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v if v and v.upper() != "NULL" else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--dsn", default=os.environ.get("DSN", "postgresql://ramona:ramona@localhost:5432/ramona"))
    ap.add_argument("--batch", type=int, default=1000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[ctdc] CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    with psycopg.connect(args.dsn) as conn, conn.cursor() as cur:
        # create an evidence_source row for the dataset
        cur.execute(
            """
            INSERT INTO evidence_source_extended (source_kind, dataset_name, title, url, published_at)
            VALUES ('ctdc', 'CTDC Global Synthetic Dataset v2025', 'The Global Synthetic Dataset',
                    'https://www.ctdatacollaborative.org/page/global-synthetic-dataset', '2025-02-01')
            ON CONFLICT DO NOTHING
            RETURNING source_id
            """
        )
        r = cur.fetchone()
        if r is None:
            cur.execute(
                "SELECT source_id FROM evidence_source_extended WHERE source_kind='ctdc' AND dataset_name='CTDC Global Synthetic Dataset v2025'"
            )
            r = cur.fetchone()
        ctdc_source_id = r[0]
        print(f"[ctdc] evidence_source_id = {ctdc_source_id}")

        inserted = 0
        with csv_path.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            batch_victims: list[tuple] = []
            batch_exp: list[tuple] = []
            batch_means: list[tuple] = []

            for row_no, row in enumerate(reader, start=1):
                external_id = f"ctdc_{row_no:08d}"
                year = _clean(row.get("yearOfRegistration"))
                try:
                    year_val = int(year) if year else None
                except ValueError:
                    year_val = None
                gender_raw = _clean(row.get("gender"))
                gender_code = GENDER_MAP.get(gender_raw, None)

                age_raw = _clean(row.get("ageBroad"))
                age_code = AGE_CANON.get(age_raw, age_raw)

                citizenship = _clean(row.get("citizenship"))
                coe = _clean(row.get("CountryOfExploitation"))
                dur = _clean(row.get("traffickMonths"))

                # recruitment method from relation fields
                rec_code = None
                for col, code in RECRUITER_RELATION_FROM_ROW:
                    if _one_or_none(row.get(col)):
                        rec_code = code
                        break

                batch_victims.append(
                    (external_id, "ctdc", ctdc_source_id, year_val, age_code, gender_code,
                     citizenship, coe, dur, rec_code)
                )

                for col, exp_code in EXPLOITATION_TYPE_FROM_ROW:
                    if _one_or_none(row.get(col)):
                        batch_exp.append((external_id, exp_code))
                # broad buckets
                if _one_or_none(row.get("isForcedLabour")) and not any(
                    _one_or_none(row.get(c)) for c, _ in EXPLOITATION_TYPE_FROM_ROW if c.startswith("typeOfLabour")
                ):
                    batch_exp.append((external_id, "labour_other"))
                if _one_or_none(row.get("isOtherExploit")):
                    batch_exp.append((external_id, "other"))

                for col, moc_code in MEANS_FROM_ROW:
                    if _one_or_none(row.get(col)):
                        batch_means.append((external_id, moc_code))

                if row_no % args.batch == 0:
                    _flush(cur, batch_victims, batch_exp, batch_means, args.dry_run)
                    inserted += len(batch_victims)
                    print(f"[ctdc] ingested {inserted} victims")
                    batch_victims.clear(); batch_exp.clear(); batch_means.clear()

            if batch_victims:
                _flush(cur, batch_victims, batch_exp, batch_means, args.dry_run)
                inserted += len(batch_victims)

        if not args.dry_run:
            conn.commit()
        print(f"[ctdc] done. victims ingested: {inserted}")


def _flush(cur, victims, exps, means, dry_run):
    if dry_run:
        print(f"[ctdc] DRY RUN. would insert {len(victims)} victims, {len(exps)} exp rows, {len(means)} moc rows")
        return
    # insert victims and capture ids
    cur.executemany(
        """
        INSERT INTO victim (external_id, source_kind, source_id, year_of_registration,
                            age_group_code, gender_code, citizenship_iso3,
                            country_of_exploitation_iso3, traffick_duration_band,
                            recruitment_method_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_kind, external_id) DO NOTHING
        """,
        victims,
    )
    if exps:
        cur.executemany(
            """
            INSERT INTO victim_exploitation (victim_id, exploitation_type_code)
            SELECT v.victim_id, %s
            FROM victim v
            WHERE v.source_kind='ctdc' AND v.external_id=%s
            ON CONFLICT DO NOTHING
            """,
            [(e[1], e[0]) for e in exps],
        )
    if means:
        cur.executemany(
            """
            INSERT INTO victim_means_of_control (victim_id, means_code)
            SELECT v.victim_id, %s
            FROM victim v
            WHERE v.source_kind='ctdc' AND v.external_id=%s
            ON CONFLICT DO NOTHING
            """,
            [(m[1], m[0]) for m in means],
        )


if __name__ == "__main__":
    main()
