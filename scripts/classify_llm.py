#!/usr/bin/env python3
"""
LLM-based classifier for offer-bearing records (Ramona operational reports or any
text that actually contains the terms of a job offer).

Why this exists: the rule-based classifier in classify_press.py cannot separate
Type-A (classic red flags) from Type-B (credible-lethal) reliably, because press
articles describe outcomes, not offers (see docs/CLASSIFIER_VALIDATION.md, where an
LLM read found only ~8% of articles contain the offer terms). This script is meant
for inputs where the offer IS present: the reports users submit to Ramona.

Input  JSONL: one record per line, must contain at least {"id", "text"} (a "title"
              field is used if present).
Output JSONL: one record per line with the structured classification.
Summary JSON: aggregate counts including the Type-A vs Type-B breakdown.

Requires:  pip install anthropic   and   ANTHROPIC_API_KEY in the environment.

Usage:
    python scripts/classify_llm.py --in data/operational/offers.jsonl \
        --out data/processed/offers_llm.jsonl \
        --summary data/processed/offers_llm_summary.json \
        --model claude-haiku-4-5-20251001 --concurrency 8
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SYSTEM = (
    "Eres un anotador experto en trata de personas y fraude de reclutamiento laboral. "
    "Clasificas el TEXTO DE UNA OFERTA o de un reporte que describe una oferta. "
    "Sé estricto y honesto: si el texto no permite determinar algo, responde con el "
    "valor 'no_determinable' o false. Nunca inventes."
)

# Tool schema forces structured, validated output from the model.
TOOL = {
    "name": "registrar_clasificacion",
    "description": "Registra la clasificación estructurada de una oferta laboral.",
    "input_schema": {
        "type": "object",
        "properties": {
            "describe_oferta": {
                "type": "boolean",
                "description": "¿El texto describe los TÉRMINOS de una oferta concreta (sueldo, horario, requisitos, canal de contacto, lugar de cita)?",
            },
            "type_a": {
                "type": "boolean",
                "description": "Red flags clásicas EXPLÍCITAS en la oferta: sueldo desproporcionado, sin experiencia, contratación urgente, pago adelantado, traslado pagado.",
            },
            "type_b": {
                "type": "boolean",
                "description": "Oferta plausible pero con riesgo en la logística del primer contacto: empresa sin nombre, WhatsApp sin logo, cita en edificio multiusos/bodega, ir sola, no llevar identificación, salto Messenger a WhatsApp, rol gancho (limpieza/mesera/recepción).",
            },
            "metodo_reclutamiento": {
                "type": "string",
                "enum": ["redes_sociales", "conocido_cercano", "oferta_laboral_falsa",
                         "secuestro_directo", "enganchador", "en_persona_calle", "no_determinable"],
            },
            "tipo_explotacion": {
                "type": "string",
                "enum": ["sexual", "laboral", "criminalidad_forzada", "organos",
                         "mendicidad", "no_determinable"],
            },
            "justificacion": {"type": "string", "description": "Una frase breve."},
        },
        "required": ["describe_oferta", "type_a", "type_b",
                     "metodo_reclutamiento", "tipo_explotacion"],
    },
}


def classify_one(client, model, rec: dict) -> dict:
    text = ((rec.get("title") or "") + "\n" + (rec.get("text") or "")).strip()[:4000]
    msg = client.messages.create(
        model=model,
        max_tokens=400,
        system=SYSTEM,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": "registrar_clasificacion"},
        messages=[{"role": "user", "content": f"Clasifica esta oferta/reporte:\n\n{text}"}],
    )
    data = {}
    for block in msg.content:
        if getattr(block, "type", None) == "tool_use":
            data = block.input
            break
    data["id"] = rec.get("id")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", default="data/processed/offers_llm.jsonl")
    ap.add_argument("--summary", default="data/processed/offers_llm_summary.json")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: set ANTHROPIC_API_KEY in the environment.")
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: pip install anthropic")

    client = anthropic.Anthropic()
    records = [json.loads(l) for l in Path(args.inp).open() if l.strip()]
    if args.limit:
        records = records[: args.limit]

    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(classify_one, client, args.model, r): r for r in records}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({"id": futs[fut].get("id"), "error": str(e)})
            if i % 50 == 0:
                print(f"[llm] {i}/{len(records)}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as g:
        for r in results:
            g.write(json.dumps(r, ensure_ascii=False) + "\n")

    ok = [r for r in results if "error" not in r]
    describe = [r for r in ok if r.get("describe_oferta")]
    a_only = sum(1 for r in describe if r.get("type_a") and not r.get("type_b"))
    b_only = sum(1 for r in describe if r.get("type_b") and not r.get("type_a"))
    both = sum(1 for r in describe if r.get("type_a") and r.get("type_b"))
    summary = {
        "total": len(results),
        "classified_ok": len(ok),
        "describe_oferta": len(describe),
        "type_a_only": a_only,
        "type_b_only": b_only,
        "type_a_and_b": both,
        "ratio_b_a": round(b_only / a_only, 2) if a_only else None,
        "metodo": dict(Counter(r.get("metodo_reclutamiento") for r in ok)),
        "explotacion": dict(Counter(r.get("tipo_explotacion") for r in ok)),
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
