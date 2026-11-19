#!/usr/bin/env python3
"""Build Popper tasks (bk.pl, exs.pl, bias.pl) from the expert's private offers.

Positives: offers the expert classified as fraude, peligro or reclutamiento_criminal.
Negatives: offers whose employer is verified (portal check, known brand or social validation).
Offers labelled dudosa, por_confirmar or with an unverified employer are left out: no firm label.
Two tasks are written: "con_validacion" (Popper may use verified/not_verified) and
"sin_validacion" (only what the offer itself says).
Also writes the blind-test offers (P-001..) as a held-out set.
"""
import csv, sys, importlib.util
from pathlib import Path
import clingo
ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data/operational/private"
OUT = P / "popper"
ASP = ROOT / "scripts/rule_learning/asp"
UNARY = ["high_pay", "requires_experience", "sales", "seasonal", "internship", "entry_level", "security",
         "operational_role", "specialised_role", "personal_contact", "unsolicited_contact", "asks_for_money",
         "no_job_described", "borrowed_name", "relocation", "different_job", "trafficking_risk_role",
         "anonymous_employer", "appearance_required", "asks_for_documents", "asks_to_download", "intermediary"]
HAS = {"contratacion_urgente": "urgent", "sin_experiencia": "no_experience"}
POS = {"fraude", "peligro", "reclutamiento_criminal"}

def atoms(lp_files):
    ctl = clingo.Control(["--warn=none"])
    for f in lp_files: ctl.load(str(f))
    ctl.add("base", [], "#show. #show verified_employer/1. #show offer/1. #show has/2. " + " ".join("#show %s/1." % u for u in UNARY))
    ctl.ground([("base", [])])
    feats = {}
    def on(m):
        for a in m.symbols(shown=True):
            o = str(a.arguments[0]); feats.setdefault(o, set())
            if a.name == "has":
                k = HAS.get(str(a.arguments[1]));  k and feats[o].add(k)
            elif a.name == "verified_employer": feats[o].add("verified")
            elif a.name != "offer": feats[o].add(a.name)
    ctl.solve(on_model=on)
    for o in feats:
        if "verified" not in feats[o]: feats[o].add("not_verified")
    return feats

def write(name, feats, pos, neg, preds):
    d = OUT / name; d.mkdir(parents=True, exist_ok=True)
    bk = [":- discontiguous " + ", ".join(p + "/1" for p in preds) + ".", ":- dynamic " + ", ".join(p + "/1" for p in preds) + "."]
    for o in sorted(pos | neg): bk += ["%s(%s)." % (f, o) for f in sorted(feats[o]) if f in preds]
    (d / "bk.pl").write_text("\n".join(bk) + "\n")
    (d / "exs.pl").write_text("\n".join(["pos(alert(%s))." % o for o in sorted(pos)] + ["neg(alert(%s))." % o for o in sorted(neg)]) + "\n")
    (d / "bias.pl").write_text("head_pred(alert,1).\n" + "\n".join("body_pred(%s,1)." % p for p in preds) + "\n")
    print(name, "pos", len(pos), "neg", len(neg))

def main():
    feats = atoms([ASP / "expert_rules.lp"] + sorted(P.glob("anuncios_*.lp")))
    pos, neg = set(), set()
    for f in sorted(P.glob("anuncios_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            o = r["id"].lower().replace("-", "_")
            if r["id"].startswith("D-"):
                if r.get("clasificacion") in POS: pos.add(o)
            elif "verified" in feats[o]: neg.add(o)
    content = UNARY + list(HAS.values())
    write("con_validacion", feats, pos, neg, content + ["verified", "not_verified"])
    write("sin_validacion", feats, pos, neg, content)
    # held-out: blind-test offers with the expert's labels
    spec = importlib.util.spec_from_file_location("g", ASP / "build_posting_facts.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    tmp = OUT / "_prueba"; tmp.mkdir(exist_ok=True)
    (tmp / "anuncios_prueba.csv").write_text((P / "prueba_ciega/ofertas_prueba.csv").read_text(encoding="utf-8-sig"), encoding="utf-8")
    g.PRIVATE = tmp; g.main()
    tf = atoms([ASP / "expert_rules.lp", tmp / "anuncios_prueba.lp"])
    lab = {r["id"].lower().replace("-", "_"): r["etiqueta"] for r in csv.DictReader(open(P / "prueba_ciega/etiquetas_daniela.csv", encoding="utf-8"))}
    with open(OUT / "prueba_hechos.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["id", "etiqueta", "hechos"])
        for o in sorted(tf): w.writerow([o, lab.get(o, ""), " ".join(sorted(tf[o]))])

if __name__ == "__main__":
    main()
