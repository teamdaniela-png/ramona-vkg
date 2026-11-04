#!/usr/bin/env python3
"""
Aplica la auditoria independiente (data/processed/offers/audit/out_*.jsonl) al corpus de prensa.

Reglas (verificadas por codigo, no por la palabra del revisor):
- `evidencia` y cada `evidencia_correcciones` deben ser subcadenas literales del texto de las fuentes;
  si no lo son, se ignoran.
- verificada  = revisor dice "si" Y la evidencia es literal.
- dudosa      = revisor dice "dudoso", o dice "si" sin evidencia literal.
- descartada  = revisor dice "no".
- Campo `incorrecto` con correccion respaldada -> se corrige; sin respaldo -> se vacia.
- Campo `no_en_texto` -> se vacia.  Cita `incorrecto` -> se vacia.
- criminal_recruitment `incorrecto` -> se invierte.
Salida: data/real/press_offers_verified.csv (+ columnas audit_status, audit_evidence, audit_changes)
"""
import csv, glob, json, re, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["job_title", "pay_amount", "pay_currency", "pay_period", "platform", "offer_location", "target_profile"]

def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()

def main():
    srcs = {}
    for l in open(ROOT / "data/processed/offers/audit/in_1.jsonl").readlines() + sum((open(f).readlines() for f in sorted(glob.glob(str(ROOT / "data/processed/offers/audit/in_*.jsonl")))[1:]), []):
        it = json.loads(l)
        srcs[it["offer_uid"]] = norm(" ".join(s["title"] + " " + s["lede"] + " " + s["snippet"] for s in it["sources"]))
    audit = {}
    for f in sorted(glob.glob(str(ROOT / "data/processed/offers/audit/out_*.jsonl"))):
        for l in open(f):
            if l.strip():
                a = json.loads(l); audit[a["offer_uid"]] = a
    offers = list(csv.DictReader(open(ROOT / "data/real/press_offers.csv", encoding="utf-8")))
    stats = collections.Counter(); out = []
    for o in offers:
        a = audit.get(o["offer_uid"]); T = srcs.get(o["offer_uid"], "")
        changes = []
        if not a:
            o["audit_status"] = "sin_auditar"; o["audit_evidence"] = ""; o["audit_changes"] = ""; out.append(o); stats["sin_auditar"] += 1; continue
        ev = norm(a.get("evidencia")); ev_ok = bool(ev) and ev in T
        verdict = a.get("es_engano_o_reclutamiento")
        status = "descartada" if verdict == "no" else ("verificada" if verdict == "si" and ev_ok else "dudosa")
        corr = a.get("correcciones") or {}; evc = a.get("evidencia_correcciones") or {}
        for f, v in (a.get("campos") or {}).items():
            if f not in FIELDS or not o.get(f):
                continue
            if v == "incorrecto":
                if f in corr and norm(evc.get(f)) and norm(evc.get(f)) in T:
                    changes.append(f"{f}: {o[f]!r} -> {corr[f]!r}"); o[f] = "" if corr[f] is None else str(corr[f])
                else:
                    changes.append(f"{f}: {o[f]!r} -> '' (sin respaldo)"); o[f] = ""
            elif v == "no_en_texto":
                changes.append(f"{f}: {o[f]!r} -> '' (no esta en el texto)"); o[f] = ""
        if o["verbatim_quote"] and a.get("verbatim_quote_check") == "incorrecto":
            changes.append("verbatim_quote eliminada (no es texto del anuncio/reclutador)"); o["verbatim_quote"] = ""
        if a.get("criminal_recruitment_check") == "incorrecto":
            new = "False" if o["criminal_recruitment"] == "True" else "True"
            changes.append(f"criminal_recruitment: {o['criminal_recruitment']} -> {new}"); o["criminal_recruitment"] = new
        o["audit_status"] = status; o["audit_evidence"] = ev if ev_ok else ""; o["audit_changes"] = " | ".join(changes)
        stats[status] += 1; stats["campos_cambiados"] += len(changes); stats["ofertas_con_cambios"] += bool(changes)
        out.append(o)
    cols = list(offers[0].keys())
    with open(ROOT / "data/real/press_offers_verified.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
    print(dict(stats))
    mx = [o for o in out if o["audit_status"] == "verificada" and "MEX" in o["countries"]]
    print("verificadas en Mexico:", len(mx), "| con cita textual:", sum(1 for o in out if o["audit_status"] == "verificada" and o["verbatim_quote"]))

if __name__ == "__main__":
    main()
