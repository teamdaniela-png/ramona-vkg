#!/usr/bin/env python3
"""Build Popper tasks (bk.pl, exs.pl, bias.pl) from the offers labelled by the domain expert.

Positives: offers the expert labelled fraude or peligro (her own cases and the press offers).
Negatives: offers whose employer is verified (portal check, known brand, social validation,
or the verified-employer postings of offers.lp).
Offers labelled dudosa or with an unverified employer are left out: no firm label.
Tasks: "todo" (every positive), "mexico" (press offers of Mexico only) and
"con_validacion" (Popper may also use verified/not_verified).
The blind-test offers (P-001..) are written as a held-out set.
"""
import csv, re, importlib.util
from pathlib import Path
import clingo
ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data/operational/private"
D = ROOT / "data/processed/rule_learning"
OUT = P / "popper"
ASP = ROOT / "scripts/rule_learning/asp"
spec = importlib.util.spec_from_file_location("g", ASP / "build_posting_facts.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

UNARY = ["requires_experience", "sales", "seasonal", "internship", "entry_level", "security", "operational_role",
         "specialised_role", "unsolicited_contact", "asks_for_money", "no_job_described", "borrowed_name",
         "different_job", "trafficking_risk_role", "appearance_required", "asks_for_documents", "asks_to_download",
         "intermediary"]
DERIVED = {"pay_high": "high_pay", "moves_person": "relocation", "personal_channel": "personal_contact"}
HAS = {"contratacion_urgente": "urgent", "sin_experiencia": "no_experience", "pago_adelantado": "asks_for_money",
       "pidio_datos_personales": "asks_for_documents"}
CONTENT = sorted(set(UNARY) | set(DERIVED.values()) | set(HAS.values()))
POS = {"fraude", "peligro", "reclutamiento_criminal"}
MONEY = re.compile(r"cuota|inscripci[oó]n|anticipo|dep[oó]sit|transferenc|cobr(a|o|an|aron|aban)\b|pag(ar|o|aron|aban) (por|para|de) (el |la |un |una )?(tr[aá]mite|visa|examen|curso|uniforme|gesti[oó]n)|pid(en|ieron|i[oó]|e) dinero|invertir|recarga", re.I)
BORROWED = re.compile(r"suplant|usurp|se hac[ií]a[n]? pasar|haci[eé]ndose pasar|a nombre de|nombre de (la|una) empresa|falsa[s]? (p[aá]gina|cuenta|empresa|agencia)|logotipo", re.I)
DOCS = re.compile(r"datos personales|datos bancarios|documentos|pasaporte|\bINE\b|identificaci[oó]n", re.I)
GENERIC_JOB = re.compile(r"^\s*$|^(empleo|trabajo|oferta de (empleo|trabajo)|vacante)s?\s*$", re.I)


def press_signals():
    """Signals of the press offers read from their text with the same patterns used for the postings."""
    lines = []
    for r in csv.DictReader(open(ROOT / "data/real/press_offers_verified.csv", encoding="utf-8-sig")):
        o = r["offer_uid"].lower().replace("-", "_")
        job = r["job_title"]; text = " ".join(r[k] for k in ("job_title", "requirements", "contact_method", "paraphrase", "verbatim_quote"))
        if g.SECURITY.search(job): lines.append(f"security({o}).")
        if g.TRAFFICKING_RISK.search(job): lines.append(f"trafficking_risk_role({o}).")
        if g.APPEARANCE.search(text): lines.append(f"appearance_required({o}).")
        if GENERIC_JOB.search(job): lines.append(f"no_job_described({o}).")
        if MONEY.search(text): lines.append(f"asks_for_money({o}).")
        if BORROWED.search(text): lines.append(f"borrowed_name({o}).")
        if DOCS.search(r["requirements"]): lines.append(f"asks_for_documents({o}).")
    (P / "prensa").mkdir(exist_ok=True)
    (P / "prensa/prensa_senales.lp").write_text("\n".join(lines) + "\n", encoding="utf-8")


def atoms(lp_files):
    ctl = clingo.Control(["--warn=none"])
    for f in lp_files: ctl.load(str(f))
    ctl.add("base", [], "#show. #show verified_employer/1. #show offer/1. #show has/2. "
            + " ".join("#show %s/1." % u for u in UNARY + list(DERIVED)))
    ctl.ground([("base", [])])
    feats = {}
    def on(m):
        for a in m.symbols(shown=True):
            o = str(a.arguments[0]); feats.setdefault(o, set())
            if a.name == "has":
                k = HAS.get(str(a.arguments[1]));  k and feats[o].add(k)
            elif a.name == "verified_employer": feats[o].add("verified")
            elif a.name in DERIVED: feats[o].add(DERIVED[a.name])
            elif a.name != "offer": feats[o].add(a.name)
    ctl.solve(on_model=on)
    for o in feats:
        if "verified" not in feats[o]: feats[o].add("not_verified")
    return feats


def write(name, feats, pos, neg, preds):
    d = OUT / name; d.mkdir(parents=True, exist_ok=True)
    decl = ", ".join(p + "/1" for p in preds)
    bk = [":- discontiguous " + decl + ".", ":- dynamic " + decl + "."]
    for o in sorted(pos | neg): bk += ["%s(%s)." % (f, o) for f in sorted(feats[o]) if f in preds]
    (d / "bk.pl").write_text("\n".join(bk) + "\n")
    (d / "exs.pl").write_text("\n".join(["pos(alert(%s))." % o for o in sorted(pos)] + ["neg(alert(%s))." % o for o in sorted(neg)]) + "\n")
    (d / "bias.pl").write_text("head_pred(alert,1).\n" + "\n".join("body_pred(%s,1)." % p for p in preds) + "\n")
    print(name, "pos", len(pos), "neg", len(neg))


def main():
    press_signals()
    feats = atoms([D / "offers.lp", D / "expert_facts.lp", P / "prensa/prensa_senales.lp", ASP / "expert_rules.lp"] + sorted(P.glob("anuncios_*.lp")))
    pos, pos_mx, neg = set(), set(), set()
    for f in sorted(P.glob("anuncios_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            o = r["id"].lower().replace("-", "_")
            if r["id"].startswith("D-"):
                if r.get("clasificacion") in POS: pos.add(o); pos_mx.add(o)
            elif "verified" in feats[o]: neg.add(o)
    country = {r["offer_uid"]: r["countries"] for r in csv.DictReader(open(ROOT / "data/real/press_offers_verified.csv", encoding="utf-8-sig"))}
    for r in csv.DictReader(open(P / "prensa/etiquetas_daniela_prensa.csv", encoding="utf-8")):
        o = r["id"].lower().replace("-", "_")
        if r["etiqueta"] in POS and o in feats:
            pos.add(o)
            if "MEX" in country.get(r["id"], ""): pos_mx.add(o)
    t = (D / "offers.lp").read_text(encoding="utf-8")
    neg |= {o for o in re.findall(r"verified_posting\((\w+)\)", t) if o in feats}
    write("todo", feats, pos, neg, CONTENT)
    write("mexico", feats, pos_mx, neg, CONTENT)
    write("con_validacion", feats, pos, neg, CONTENT + ["verified", "not_verified"])
    with open(OUT / "entrenamiento_hechos.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["id", "clase", "mexico", "hechos"])
        for o in sorted(pos | neg): w.writerow([o, "pos" if o in pos else "neg", int(o in pos_mx or o in neg), " ".join(sorted(feats[o]))])
    # held-out: the blind-test offers with the expert's labels
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
