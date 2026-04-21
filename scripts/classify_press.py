#!/usr/bin/env python3
"""
Classify scraped press articles into Ramona offer/victim records.

Input:  data/raw/press.jsonl           (output of scrape_press.py)
Output: data/processed/press_cases.jsonl   (one record per article that looks case-relevant)

For each article, this extracts:
  * whether it describes at least one real case (case_present: bool)
  * Type A red flags (the 7 canonical Ramona flags) via keyword patterns
  * Type B credible-lethal patterns (Edith Guadalupe family) via keyword patterns
  * mentions of communication tools, recruitment method, exploitation type
  * country and outlet
  * candidate victim age/gender if mentioned

This is a rule-based first pass. A later LLM pass can refine, but rules already
give us a classified JSONL that we can load directly into Postgres.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

# ========== Type A: classic red flags (Ramona 7-flag taxonomy) ==========
FLAGS_A = {
    "sueldo_alto": [
        r"sueldo\s+(muy\s+)?alto", r"sueldo.+arriba del promedio",
        r"salario.+exhorbit", r"pagan\s+muy\s+bien", r"ingreso\s+mensual.+(\$|peso|mxn)",
        r"hasta\s+\$?\d{2,3}[.,]?\d{0,3}\s*mxn.*semana", r"15[.,]?000.+semanal",
    ],
    "horarios_flexibles": [
        r"horario\s+flexible", r"sin\s+horarios", r"tú\s+pones\s+tu\s+horario",
    ],
    "sin_experiencia": [
        r"sin\s+experiencia", r"no\s+se\s+requiere\s+experiencia",
        r"no\s+necesita\s+experiencia",
    ],
    "pago_adelantado": [
        r"pago\s+adelantado", r"anticipo\s+en\s+efectivo", r"reciben?\s+bono.+antes",
    ],
    "aceptacion_urgente": [
        r"urge(nte)?", r"empieza\s+hoy", r"arranca\s+hoy\s+mismo",
        r"contratación\s+inmediata",
    ],
    "entrevista_lejana_traslado": [
        r"entrevista.+en\s+otra\s+ciudad", r"entrevista.+fuera\s+(de|del)\s+estado",
        r"traslado\s+pagado", r"te\s+pagan\s+el\s+traslado", r"viaje\s+pagado",
    ],
    "empleo_fuera_estado": [
        r"empleo\s+fuera\s+del\s+estado", r"trabajo\s+en\s+otro\s+estado",
        r"reubicación", r"mudarse",
    ],
}

# ========== Type B: credible-lethal patterns (Edith Guadalupe family) ==========
FLAGS_B = {
    "empresa_sin_nombre": [
        r"empresa\s+sin\s+nombre", r"no\s+(dan|dicen)\s+(el\s+)?nombre\s+de\s+la\s+empresa",
        r"no\s+hay\s+razón\s+social", r"no\s+quisieron\s+decir\s+el\s+nombre",
    ],
    "sin_logo_whatsapp": [
        r"no\s+hay\s+(logo|logotipo)\s+en\s+whatsapp",
        r"sin\s+foto\s+de\s+perfil", r"whatsapp\s+sin\s+logo",
    ],
    "cita_edificio_multiusos": [
        r"edificio\s+multiusos", r"edificio.+sin\s+oficinas", r"bodega",
        r"sótano", r"departamento.+entrevista",
    ],
    "solicita_ir_sola": [
        r"pid(ió|en|ieron).+ir\s+sola", r"sola\s+(vas|debes)\s+ir",
        r"ven\s+sola", r"sin\s+acompañante",
    ],
    "solicita_sin_identificacion": [
        r"sin\s+identificación", r"no\s+llevar\s+(identificación|ine|pasaporte)",
        r"pid(ió|en|ieron)\s+(no\s+llevar|dejar)\s+(la\s+)?ine",
    ],
    "messenger_to_whatsapp": [
        r"messenger.+whatsapp", r"(facebook|fb).{0,20}messenger.{0,80}whatsapp",
    ],
    "filtro_datos_personales": [
        r"pidieron.+datos\s+personales", r"filtro\s+de\s+datos",
        r"curp|ine|acta\s+de\s+nacimiento", r"estado\s+civil",
        r"con\s+quién\s+vives",
    ],
    "horario_atipico": [
        r"(cita|entrevista).+(noche|domingo|madrugada|20:|21:|22:|23:)",
    ],
    "cambio_ubicacion_ultimo_momento": [
        r"cambi(ó|aron).+ubicación.+último\s+momento",
        r"me\s+mandaron\s+una\s+nueva\s+dirección",
    ],
    "rol_plausible_limpieza_hosteleria": [
        r"oferta.+(limpieza|mesera|recepcion|cajera|ayudante\s+general)",
        r"puesto\s+de\s+limpieza", r"trabajo\s+de\s+limpieza",
    ],
}

COMM_TOOL_PATTERNS = {
    "whatsapp":  r"\bwhats?app\b",
    "messenger": r"\bmessenger\b|\bfacebook\s+messenger\b",
    "telegram":  r"\btelegram\b",
    "sms":       r"\bsms\b|mensaje\s+de\s+texto",
    "voice_call": r"llamada\s+telefónica|llamada\s+de\s+voz",
    "in_person": r"en\s+persona|cara\s+a\s+cara",
    "email":     r"correo\s+electrónico|\bemail\b",
}

EXPLOITATION_PATTERNS = {
    "labour_domestic":     r"trabajo\s+doméstico|empleada\s+doméstica",
    "labour_agriculture":  r"jornalero|campo\s+agrícola|cosecha",
    "labour_construction": r"construcción|obra",
    "labour_hospitality":  r"mesera|mesero|bar|hotel|cocinera",
    "labour_other":        r"trabajo\s+forzad|explotación\s+laboral",
    "sex_prostitution":    r"explotación\s+sexual|prostitución|lenocinio",
    "sex_pornography":     r"pornograf",
    "forced_marriage":     r"matrimonio\s+forzado",
    "forced_criminality":  r"sicari|seguridad\s+privada\s+cjng|forzad.+delinquir",
    "organ_removal":       r"tráfico\s+de\s+órganos|extracción\s+de\s+órganos",
}

RECRUIT_METHOD_PATTERNS = {
    "false_job_offer":   r"oferta\s+de\s+trabajo\s+falsa|falsa\s+oferta\s+de\s+trabajo|oferta\s+laboral\s+falsa",
    "social_media":      r"redes\s+sociales|facebook|instagram|tiktok",
    "classifieds":       r"marketplace|clasificad|avisos\s+de\s+ocasión",
    "intimate_partner":  r"novio|pareja",
    "friend":            r"amig[oa]",
    "family":            r"familiar|prim[oa]",
    "labour_broker":     r"engancha(dor)?|enganche\s+laboral",
    "in_person_street":  r"en\s+la\s+calle|aborda(do|ron)\s+en\s+la\s+calle",
    "abduction":         r"secuestr",
}

COUNTRY_PATTERNS = {
    "MEX": r"México|CDMX|Jalisco|Guadalajara|Monterrey|Puebla|Estado\s+de\s+México|Guerrero|Oaxaca|Chiapas",
    "GTM": r"Guatemala",
    "HND": r"Honduras",
    "SLV": r"El\s+Salvador",
    "USA": r"Estados\s+Unidos|EEUU|\bUSA\b",
    "COL": r"Colombia",
    "ARG": r"Argentina",
    "PER": r"Perú",
    "CHL": r"Chile",
    "VEN": r"Venezuela",
}

CASE_MARKERS = [
    r"víctim[ao]s?\b", r"desaparec", r"rescate(?:\w{0,4})?",
    r"detenidos?\b", r"liberad[oa]s?\b", r"fue\s+encontrad",
    r"denunci(a|ó|aron)", r"asesinad[oa]", r"hallaron", r"secuestr",
    r"encontrada\s+muerta", r"explotación\b",
]

CASE_MARKER_RE = re.compile("|".join(CASE_MARKERS), re.IGNORECASE)


def compile_dict(d: dict[str, list[str] | str]) -> dict[str, re.Pattern]:
    out = {}
    for k, v in d.items():
        if isinstance(v, str):
            out[k] = re.compile(v, re.IGNORECASE)
        else:
            out[k] = re.compile("|".join(v), re.IGNORECASE)
    return out


FLAGS_A_RE = compile_dict(FLAGS_A)
FLAGS_B_RE = compile_dict(FLAGS_B)
COMM_TOOL_RE = compile_dict(COMM_TOOL_PATTERNS)
EXPLOIT_RE = compile_dict(EXPLOITATION_PATTERNS)
RECRUIT_RE = compile_dict(RECRUIT_METHOD_PATTERNS)
COUNTRY_RE = compile_dict(COUNTRY_PATTERNS)


def matched(text: str, compiled: dict[str, re.Pattern]) -> list[str]:
    hits = []
    for k, r in compiled.items():
        if r.search(text):
            hits.append(k)
    return hits


def classify(rec: dict) -> dict | None:
    text = (rec.get("text") or "") + " " + (rec.get("title") or "")
    if not text.strip():
        return None
    text_lc = text.lower()
    case_present = bool(CASE_MARKER_RE.search(text))
    flags_a = matched(text, FLAGS_A_RE)
    flags_b = matched(text, FLAGS_B_RE)
    tools = matched(text, COMM_TOOL_RE)
    exps = matched(text, EXPLOIT_RE)
    recs = matched(text, RECRUIT_RE)
    countries = matched(text, COUNTRY_RE)
    # At least one substantive signal or an explicit case marker
    if not (case_present or flags_a or flags_b or exps or recs):
        return None
    out = {
        "id": rec.get("id"),
        "url": rec.get("final_url") or rec.get("url"),
        "domain": rec.get("domain") or (urlparse(rec.get("final_url") or rec.get("url") or "").netloc or None),
        "outlet": rec.get("outlet"),
        "published": rec.get("published"),
        "title": rec.get("title"),
        "case_present": case_present,
        "flags_classic": flags_a,
        "flags_credible_lethal": flags_b,
        "type_a": bool(flags_a),
        "type_b": bool(flags_b),
        "type_b_only": bool(flags_b) and not bool(flags_a),
        "communication_tools": tools,
        "exploitation_types": exps,
        "recruitment_methods": recs,
        "countries": countries,
        "chars": rec.get("chars", 0),
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/raw/press.jsonl")
    ap.add_argument("--out", default="data/processed/press_cases.jsonl")
    ap.add_argument("--summary", default="data/processed/press_summary.json")
    args = ap.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    kept = 0
    type_a_only = 0
    type_b_only = 0
    both = 0
    by_outlet: dict[str, int] = {}
    by_country: dict[str, int] = {}
    by_exp: dict[str, int] = {}

    with inp.open() as f, out.open("w") as g:
        for line in f:
            total += 1
            try:
                rec = json.loads(line)
            except Exception:
                continue
            c = classify(rec)
            if c is None:
                continue
            g.write(json.dumps(c, ensure_ascii=False) + "\n")
            kept += 1
            if c["type_a"] and c["type_b"]:
                both += 1
            elif c["type_a"]:
                type_a_only += 1
            elif c["type_b"]:
                type_b_only += 1
            outlet = c.get("outlet") or c.get("domain") or "unknown"
            by_outlet[outlet] = by_outlet.get(outlet, 0) + 1
            for iso in c["countries"]:
                by_country[iso] = by_country.get(iso, 0) + 1
            for e in c["exploitation_types"]:
                by_exp[e] = by_exp.get(e, 0) + 1

    summary = {
        "total_articles": total,
        "case_relevant": kept,
        "type_a_only": type_a_only,
        "type_b_only": type_b_only,
        "type_a_and_b": both,
        "top_outlets": sorted(by_outlet.items(), key=lambda kv: -kv[1])[:20],
        "countries": sorted(by_country.items(), key=lambda kv: -kv[1]),
        "exploitation_types": sorted(by_exp.items(), key=lambda kv: -kv[1]),
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
