#!/usr/bin/env python3
"""
Extract survivor-testimony patterns from the classified press observatory.

Reads data/processed/press_cases.jsonl and aggregates every Type A flag, Type B
pattern, communication tool, recruitment method and exploitation type detected.
Writes db/07_press_patterns.sql with additional survivor_patterns rows and a
docs/patterns_summary.json with full frequency tables.

Rows added cover patterns NOT already in db/02_seed_reference.sql and tag each
with:
  - pattern_name (canonical code)
  - pattern_description (human-readable explanation)
  - pattern_kind ('classic_a' / 'credible_b' / 'communication' / 'recruitment' / 'exploitation')
  - observed_count (how often it was detected in the 1,332 classified articles)
  - dominance_bucket ('hot' >= 5%, 'warm' 1-5%, 'cold' < 1%)
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


DESCRIPTIONS = {
    # Type A — Ramona's 7 classic red flags
    "sueldo_alto":              "Oferta con sueldo explícitamente descrito como alto o fuera de mercado.",
    "horarios_flexibles":       "Oferta describe horarios flexibles o 'tú pones tu horario'.",
    "sin_experiencia":          "Oferta anuncia que no se requiere experiencia.",
    "pago_adelantado":          "Oferta menciona pago adelantado o bono inicial en efectivo.",
    "aceptacion_urgente":       "Oferta exige contratación inmediata o presión de decisión rápida.",
    "entrevista_lejana_traslado": "Oferta pide entrevista fuera de la ciudad con traslado pagado.",
    "empleo_fuera_estado":      "Oferta implica mudarse fuera del estado o del país.",
    # Type B — credible-lethal
    "empresa_sin_nombre":       "El reclutador no dice ni reconoce el nombre de la empresa.",
    "sin_logo_whatsapp":        "El número de WhatsApp no tiene logo ni foto de perfil.",
    "cita_edificio_multiusos":  "La cita se programa en un edificio multiusos, bodega, sótano o departamento particular.",
    "solicita_ir_sola":         "El reclutador insiste en que la candidata acuda sola.",
    "solicita_sin_identificacion": "El reclutador pide que la candidata no lleve identificación oficial.",
    "messenger_to_whatsapp":    "Primer contacto en Facebook Messenger migrado rápidamente a WhatsApp.",
    "filtro_datos_personales":  "Se solicitan datos personales sensibles (CURP, INE, estado civil, lazos familiares) antes del contrato.",
    "horario_atipico":          "La cita se programa en horario no laboral: noche, domingo, madrugada.",
    "cambio_ubicacion_ultimo_momento": "La dirección de la cita cambia poco antes, a veces mientras la candidata está en camino.",
    "rol_plausible_limpieza_hosteleria": "Rol ofrecido es plausible (limpieza, mesera, recepción, cocina) pero acompañado de patrones Type B.",
    # Communication tools
    "comm_whatsapp":            "Primer contacto o reclutamiento a través de WhatsApp.",
    "comm_messenger":           "Primer contacto a través de Facebook Messenger.",
    "comm_telegram":            "Primer contacto o reclutamiento a través de Telegram.",
    "comm_sms":                 "Contacto inicial por mensaje de texto.",
    "comm_voice_call":          "Contacto inicial por llamada telefónica directa.",
    "comm_in_person":           "Contacto inicial en persona.",
    "comm_email":               "Contacto inicial por correo electrónico.",
    # Recruitment methods
    "recr_social_media":        "Reclutamiento a través de redes sociales (Facebook, Instagram, TikTok, Marketplace).",
    "recr_family":              "Reclutamiento a través de un miembro de la familia de la víctima.",
    "recr_friend":              "Reclutamiento a través de un amigo cercano.",
    "recr_intimate_partner":    "Reclutamiento a través de la pareja sentimental de la víctima.",
    "recr_abduction":           "Secuestro directo o reclutamiento forzado sin pretexto laboral.",
    "recr_false_job_offer":     "Oferta de trabajo falsa anunciada explícitamente (aparece en título o cuerpo del artículo).",
    "recr_labour_broker":       "Reclutador tipo enganchador o 'labour broker'.",
    "recr_classifieds":         "Oferta publicada en avisos clasificados o sitios tipo Marketplace.",
    "recr_in_person_street":    "Abordaje en la calle sin intermediación digital.",
    # Exploitation types
    "exp_labour_hospitality":   "Explotación laboral en hospitalidad: meseros, cocina, hotelería.",
    "exp_labour_construction":  "Explotación laboral en construcción u obra.",
    "exp_labour_agriculture":   "Explotación laboral agrícola, jornaleros, corte de caña u hortalizas.",
    "exp_labour_domestic":      "Explotación en trabajo doméstico, incluyendo niñeras y cuidadoras.",
    "exp_labour_other":         "Explotación laboral de tipo no especificado.",
    "exp_sex_prostitution":     "Explotación sexual forzada, prostitución.",
    "exp_sex_pornography":      "Explotación sexual en producción de material pornográfico.",
    "exp_forced_criminality":   "Trabajo forzado en estructuras criminales: halcones, sicariato, 'seguridad privada'.",
    "exp_forced_marriage":      "Matrimonio forzado.",
    "exp_organ_removal":        "Extracción forzada de órganos o pretexto médico como lure.",
}


def sql_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def dominance(pct: float) -> str:
    if pct >= 5.0:
        return "hot"
    if pct >= 1.0:
        return "warm"
    return "cold"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/processed/press_cases.jsonl")
    ap.add_argument("--out", dest="out", default="db/07_press_patterns.sql")
    ap.add_argument("--summary", default="docs/patterns_summary.json")
    args = ap.parse_args()

    flags_a = Counter()
    flags_b = Counter()
    comm = Counter()
    recr = Counter()
    exp = Counter()
    total = 0

    with Path(args.inp).open() as f:
        for line in f:
            rec = json.loads(line)
            total += 1
            for k in rec["flags_classic"]:       flags_a[k] += 1
            for k in rec["flags_credible_lethal"]: flags_b[k] += 1
            for k in rec["communication_tools"]: comm[f"comm_{k}"] += 1
            for k in rec["recruitment_methods"]: recr[f"recr_{k}"] += 1
            for k in rec["exploitation_types"]:  exp[f"exp_{k}"] += 1

    rows = []
    def add(name, kind, count):
        pct = (count / total * 100) if total else 0.0
        rows.append({
            "pattern_name": name,
            "pattern_kind": kind,
            "pattern_description": DESCRIPTIONS.get(name, "(sin descripción)"),
            "observed_count": count,
            "pct_of_cases": round(pct, 2),
            "dominance_bucket": dominance(pct),
        })

    for k, v in flags_a.items():
        add(k, "classic_a", v)
    for k, v in flags_b.items():
        add(k, "credible_b", v)
    for k, v in comm.items():
        add(k, "communication", v)
    for k, v in recr.items():
        add(k, "recruitment", v)
    for k, v in exp.items():
        add(k, "exploitation", v)

    # SQL output
    out = Path(args.out)
    lines = []
    lines.append("-- Press-derived survivor-testimony patterns")
    lines.append(f"-- Extracted from {total:,} case-relevant articles classified by rules")
    lines.append(f"-- {len(rows):,} distinct patterns across 5 kinds (classic_a, credible_b, communication, recruitment, exploitation)")
    lines.append("")
    lines.append("SET search_path TO ramona, public;")
    lines.append("")
    lines.append("-- Extend the survivor_patterns table with two optional columns if they")
    lines.append("-- do not already exist. Required for v1.3 observatory stats.")
    lines.append("ALTER TABLE ramona.survivor_patterns ADD COLUMN IF NOT EXISTS pattern_kind TEXT;")
    lines.append("ALTER TABLE ramona.survivor_patterns ADD COLUMN IF NOT EXISTS observed_count INTEGER;")
    lines.append("ALTER TABLE ramona.survivor_patterns ADD COLUMN IF NOT EXISTS dominance_bucket TEXT;")
    lines.append("")
    lines.append("INSERT INTO survivor_patterns (pattern_name, pattern_description, pattern_kind, observed_count, dominance_bucket, evidence_source) VALUES")
    value_rows = []
    for r in rows:
        value_rows.append(
            f"  ({sql_str(r['pattern_name'])}, {sql_str(r['pattern_description'])}, "
            f"{sql_str(r['pattern_kind'])}, {r['observed_count']}, "
            f"{sql_str(r['dominance_bucket'])}, NULL)"
        )
    lines.append(",\n".join(value_rows))
    lines.append("ON CONFLICT (pattern_name) DO UPDATE SET")
    lines.append("  pattern_description = EXCLUDED.pattern_description,")
    lines.append("  pattern_kind = EXCLUDED.pattern_kind,")
    lines.append("  observed_count = EXCLUDED.observed_count,")
    lines.append("  dominance_bucket = EXCLUDED.dominance_bucket;")
    lines.append("")

    out.write_text("\n".join(lines))
    print(f"wrote {out}: {len(rows):,} patterns")

    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(json.dumps(
        {"total_articles": total, "patterns": rows},
        indent=2, ensure_ascii=False
    ))
    print(f"wrote {args.summary}")


if __name__ == "__main__":
    main()
