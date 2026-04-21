#!/usr/bin/env python3
"""
Generate RATR-O seed data by synthesising offer / recruiter / evidence_source
records from already-classified press articles.

Input:  data/processed/press_cases.jsonl  (output of classify_press.py)
Output: db/05_seed_cases_v1_2.sql          (idempotent INSERT statements)

The goal is: every seed row is anchored to a REAL press article as its
evidence source. We do not invent cases. We synthesise minimal offer rows
from the categorical signals already extracted by the rule-based classifier.

Privacy:
- No personal data is introduced. Recruiters are represented by deterministic
  SHA-256-style stubs ("HSH_" + 8-char hex).
- Employers are NULL unless the article names a public institution.
- Raw article text is not copied into the seed; only categorical fields and
  the article URL as :derivedFrom.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


# --------- Mapping from classifier tags to Ramona schema controlled vocabs ---------

COUNTRY_TO_CODE = {
    "MEX": "MX", "COL": "CO", "USA": "US", "PER": "PE", "ARG": "AR",
    "VEN": "VE", "CHL": "CL", "GTM": "GT", "HND": "HN", "SLV": "SV",
    "CAN": "CA", "FRA": "FR", "ESP": "ES", "BRA": "BR",
}

FLAG_TYPES_TYPEA = {
    "sueldo_alto", "horarios_flexibles", "sin_experiencia", "pago_adelantado",
    "aceptacion_urgente", "entrevista_lejana_traslado", "empleo_fuera_estado",
}

TYPE_B_PATTERNS = {
    "empresa_sin_nombre", "sin_logo_whatsapp", "cita_edificio_multiusos",
    "solicita_ir_sola", "solicita_sin_identificacion", "messenger_to_whatsapp",
    "filtro_datos_personales", "horario_atipico", "cambio_ubicacion_ultimo_momento",
    "rol_plausible_limpieza_hosteleria",
}

COMM_TOOL_TO_PLATFORM_TYPE = {
    "whatsapp":  "whatsapp",
    "messenger": "messenger",
    "telegram":  "telegram",
    "sms":       "sms",
    "voice_call": "other",
    "in_person": "other",
    "email":     "other",
}

EXPLOIT_TO_ROLE_HINT = {
    "labour_agriculture":  "jornalero / corte agrícola",
    "labour_construction": "albañil / ayudante de obra",
    "labour_domestic":     "trabajo doméstico",
    "labour_hospitality":  "mesera / cocina / hotel",
    "labour_other":        "empleo general",
    "sex_prostitution":    "supuesta modelo / dama de compañía",
    "sex_pornography":     "modelaje / videos",
    "forced_criminality":  "seguridad privada / vigilancia",
    "organ_removal":       "traslado médico (pretexto)",
    "forced_marriage":     "acompañante / ama de casa",
}

SCHEME_DETECTORS = [
    # (regex on full classification dict representation, scheme code)
]


def sha_stub(seed: str, prefix: str = "HSH_") -> str:
    return prefix + hashlib.sha256(seed.encode()).hexdigest()[:8].upper()


def sql_str(s: str | None) -> str:
    if s is None:
        return "NULL"
    # escape single quotes
    s = s.replace("'", "''")
    return f"'{s}'"


def detect_scheme(rec: dict) -> str | None:
    """Best-effort mapping from classifier tags to one FraudScheme code."""
    exps = set(rec.get("exploitation_types", []))
    recs = set(rec.get("recruitment_methods", []))
    flags_b = set(rec.get("flags_credible_lethal", []))
    title_lower = (rec.get("title") or "").lower()

    if "forced_criminality" in exps:
        return "ForcedCriminalityScheme"
    if "organ_removal" in exps:
        return "DebtBondageTraffickingScheme"
    if any(k in title_lower for k in ("maquila", "maquiladora")):
        return "FakeMaquilaScheme"
    if any(k in title_lower for k in ("call center", "callcenter", "call-center")):
        return "CallCenterScamScheme"
    if any(k in title_lower for k in ("modela", "modelaje", "actriz", "actuación")):
        return "ModelingAgencyScheme"
    if any(k in title_lower for k in ("crypto", "forex", "trader", "blockchain")):
        return "OnlineCryptoJobScheme"
    if any(k in title_lower for k in ("uber", "didi", "rappi", "beat ", "conductor", "chofer")):
        return "GigEconomyFakeDriverScheme"
    if any(k in title_lower for k in ("multinivel", "mlm", "piramidal", "pirámide")):
        return "MLMHealthBeautyScheme"
    if any(k in title_lower for k in ("influencer", "community manager", "embajad")):
        return "OnlineInfluencerSalesScheme"
    if any(k in title_lower for k in ("maestr", "profesor", "teacher", "idioma", "inglés", "español")):
        return "ForeignLanguageTeacherScheme"
    if any(k in title_lower for k in ("niñera", "au pair", "nanny", "cuidador")):
        return "VisaFraudScheme" if any(k in title_lower for k in ("canadá", "canada", "francia", "paris")) else "DomesticWorkerLockInScheme"
    if "solicita_ir_sola" in flags_b or "cita_edificio_multiusos" in flags_b:
        return "InPersonLureScheme"
    if "pago_adelantado" in rec.get("flags_classic", []):
        return "PayToWorkScheme"
    if "filtro_datos_personales" in flags_b:
        return "IdentityTheftScheme"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/processed/press_cases.jsonl")
    ap.add_argument("--out", dest="out", default="db/05_seed_cases_v1_2.sql")
    ap.add_argument("--limit", type=int, default=1500)
    args = ap.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)

    # Pre-scan: collect unique domains for platform rows
    records = []
    with inp.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            records.append(rec)
    records = records[: args.limit]

    # Build SQL
    lines = []
    lines.append("-- Ramona VKG seed v1.2 — generated from classified press cases")
    lines.append(f"-- Source records: {len(records)} classified articles from press scraper")
    lines.append("-- Each offer row is anchored to a REAL press article via evidence_sources.")
    lines.append("-- Recruiters represented by deterministic SHA-256 stubs. No PII introduced.")
    lines.append("")
    lines.append("SET search_path TO ramona, public;")
    lines.append("")

    # Evidence sources (press articles as sources)
    lines.append("-- ============================================================")
    lines.append("-- Evidence sources (one per article)")
    lines.append("-- ============================================================")
    lines.append("INSERT INTO evidence_sources (source_title, source_outlet, source_url, source_date, source_pattern) VALUES")
    es_values = []
    for i, rec in enumerate(records, start=1):
        title = (rec.get("title") or "")[:300]
        outlet = rec.get("outlet")
        url = rec.get("final_url") or rec.get("url")
        # date — use "published" heuristic; else NULL
        published = rec.get("published") or ""
        m = re.search(r"(20\d{2})[-/](\d{2})[-/](\d{2})", published) or re.search(r"(\d{2}) (\w{3}) (20\d{2})", published)
        date = m.group(0)[:10] if m else None
        sql_date = f"DATE '{date}'" if date and re.match(r"20\d{2}-\d{2}-\d{2}", date) else "NULL"
        schemes_code = detect_scheme(rec)
        pattern_tag = schemes_code or "general"
        es_values.append(f"  ({sql_str(title)}, {sql_str(outlet)}, {sql_str(url)}, {sql_date}, {sql_str(pattern_tag)})")
    lines.append(",\n".join(es_values) + "\nON CONFLICT DO NOTHING;")
    lines.append("")

    # Recruiters (one synthetic recruiter per article)
    lines.append("-- ============================================================")
    lines.append("-- Synthetic recruiters (one per article)")
    lines.append("-- ============================================================")
    lines.append("INSERT INTO recruiters (contact_hash, agent_name, recruiter_country, first_seen_at, historical_offer_count, historical_flag_count, associated_employer) VALUES")
    rec_rows = []
    for i, rec in enumerate(records, start=1):
        country_iso3 = rec.get("countries", [None])[0] if rec.get("countries") else None
        country_code = COUNTRY_TO_CODE.get(country_iso3, "MX")
        contact_hash = sha_stub(f"press_recruiter_{i}")
        name = f"Reclutador sintético #{i:04d}"
        classic_count = len(rec.get("flags_classic", []))
        b_count = len(rec.get("flags_credible_lethal", []))
        flag_count = classic_count + b_count
        offer_count = 1  # one article -> one synthetic offer
        rec_rows.append(
            f"  ('{contact_hash}', {sql_str(name)}, {sql_str(country_code)}, NULL, {offer_count}, {flag_count}, NULL)"
        )
    lines.append(",\n".join(rec_rows) + "\nON CONFLICT DO NOTHING;")
    lines.append("")

    # Offers
    lines.append("-- ============================================================")
    lines.append("-- Offers (synthetic; anchored to press evidence)")
    lines.append("-- ============================================================")
    lines.append("""INSERT INTO offers (raw_text, posted_at, source_platform, country_code, language_code,
    offered_role, offered_location, offered_salary_mxn, risk_score, recruiter_id, employer_id, classification_id) VALUES""")
    off_rows = []
    for i, rec in enumerate(records, start=1):
        # Synthesise raw_text from title only (copyright-safe) with a note that full source is linked
        title = (rec.get("title") or "")[:240]
        raw = f"[Sintetizado desde artículo de prensa: {title}]"
        tools = rec.get("communication_tools", [])
        plat_type = COMM_TOOL_TO_PLATFORM_TYPE.get(tools[0], "other") if tools else "other"
        plat_sub = f"(SELECT platform_id FROM platforms WHERE platform_type = '{plat_type}' LIMIT 1)"
        country_iso3 = rec.get("countries", [None])[0] if rec.get("countries") else "MEX"
        country_code = COUNTRY_TO_CODE.get(country_iso3, "MX")
        exps = rec.get("exploitation_types", [])
        role = EXPLOIT_TO_ROLE_HINT.get(exps[0], "empleo general") if exps else "empleo general"
        # risk score: B weighs more (Edith-like). Both weigh max.
        a = len(rec.get("flags_classic", []))
        b = len(rec.get("flags_credible_lethal", []))
        if a and b:
            risk = 0.95
        elif b:
            risk = 0.80
        elif a:
            risk = 0.55
        else:
            risk = 0.30
        # synthetic location: use country macro; no street addresses
        location = f"{country_iso3} (ubicación anonimizada)"
        # synthetic recruiter id — by CREATE order we set it to press_offer_i+100 to avoid collision
        recruiter_sub = f"(SELECT recruiter_id FROM recruiters WHERE contact_hash='{sha_stub(f'press_recruiter_{i}')}')"
        off_rows.append(
            f"  ({sql_str(raw)}, NULL, {plat_sub}, {sql_str(country_code)}, 'es', "
            f"{sql_str(role)}, {sql_str(location)}, NULL, {risk}, {recruiter_sub}, NULL, NULL)"
        )
    lines.append(",\n".join(off_rows) + "\nON CONFLICT DO NOTHING;")
    lines.append("")

    out.write_text("\n".join(lines))
    print(f"wrote {out}: {len(records)} offers, {len(records)} recruiters, {len(records)} evidence sources")


if __name__ == "__main__":
    main()
