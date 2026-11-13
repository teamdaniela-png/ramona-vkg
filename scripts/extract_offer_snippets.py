#!/usr/bin/env python3
"""
Step 1 of the press-offer corpus: from the press articles that describe a case, extracts the
passages that describe the offer (job, pay, platform, requirements, verbatim quotes of the ad).
Output: data/processed/offers/snippets.jsonl (git-ignored: it contains press text).
Step 2 is the reading and structuring of these passages.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OFFER = re.compile(r"(se solicita|se busca|solicitamos|buscamos|vacante|ofrec[ií]a[n]?|ofrecieron|ofert[ao]s? (de|laboral)|promet[ií]a[n]?|prometieron|sueldo|salario|pago de|pagaban|pagar[ií]an|\$\s?\d|\d[\d,\.]*\s?(mil )?(pesos|d[oó]lares|soles)|semanal|quincenal|sin experiencia|anuncio|publicaci[oó]n|convocatoria|reclutador)", re.I)
JOB = re.compile(r"(trabaj|empleo|chamba|jale|vacante|puesto|oferta|guardia|seguridad|mesera|edecan|modelo|call center|almac[eé]n|limpieza|ventas|cocina|repartidor|chofer)", re.I)
SENT = re.compile(r"(?<=[\.\!\?])\s+")


def main():
    cases = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "data/processed/press_cases.jsonl")}
    out, n_art = [], 0
    for line in open(ROOT / "data/raw/press.jsonl"):
        a = json.loads(line)
        c = cases.get(a["id"])
        if not c or not c["case_present"] or not a.get("text"):
            continue
        sents = SENT.split(re.sub(r"\s+", " ", a["text"]))
        keep = sorted({j for i, s in enumerate(sents) if OFFER.search(s) and JOB.search(s)
                       for j in (i - 1, i, i + 1) if 0 <= j < len(sents)})
        if not keep:
            continue
        hits = sum(1 for i, s in enumerate(sents) if OFFER.search(s) and JOB.search(s))
        if hits < 2 and not re.search(r"[“\"«][^”\"»]{25,}[”\"»]", " ".join(sents[i] for i in keep)):
            continue
        n_art += 1
        out.append({"id": a["id"], "url": a.get("final_url") or a["url"], "outlet": a["outlet"],
                    "published": a["published"], "title": a["title"], "countries": c["countries"],
                    "snippet": " ".join(sents[i] for i in keep)[:2500]})
    p = ROOT / "data/processed/offers/snippets.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(n_art, "notas con fragmentos de oferta;", sum(len(o["snippet"]) for o in out), "caracteres ->", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
