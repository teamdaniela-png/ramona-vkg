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
CONTENT = sorted((set(UNARY) | set(DERIVED.values()) | set(HAS.values())) - {"different_job"})   # known only after contact
POS = {"fraude", "peligro", "reclutamiento_criminal"}
MONEY = re.compile(r"cuota|inscripci[oó]n|anticipo|dep[oó]sit|transferenc|cobr(a|o|an|aron|aban)\b|pag(ar|o|aron|aban) (por|para|de) (el |la |un |una )?(tr[aá]mite|visa|examen|curso|uniforme|gesti[oó]n)|pid(en|ieron|i[oó]|e) dinero|invertir|recarga", re.I)
BORROWED = re.compile(r"suplant|usurp|se hac[ií]a[n]? pasar|haci[eé]ndose pasar|a nombre de|nombre de (la|una) empresa|falsa[s]? (p[aá]gina|cuenta|empresa|agencia)|logotipo", re.I)
DOCS = re.compile(r"datos personales|datos bancarios|documentos|pasaporte|\bINE\b|identificaci[oó]n", re.I)
GENERIC_JOB = re.compile(r"^\s*$|^(empleo|trabajo|oferta de (empleo|trabajo)|vacante)s?\s*$", re.I)


def press_signals():
    """Signals of the press offers, captured note by note and case by case (captura_notas_por_caso.csv).

    An offer gets a signal when any case of any of its notes has it. Offers whose notes could not be
    opened fall back to the first capture (captura_167_notas.csv).
    """
    period = {"dia": 22, "semana": 4.33, "quincena": 2, "mes": 1}
    rate = {"MXN": 1, "USD": 19}
    flags = {"pide_experiencia": "requires_experience", "no_solicitado": "unsolicited_contact", "pide_dinero": "asks_for_money",
             "usa_nombre_ajeno": "borrowed_name", "otro_estado_o_traslado": "relocation", "pagan_o_dan_el_boleto": "relocation",
             "pide_documentos": "asks_for_documents", "pide_datos_bancarios": "asks_for_documents",
             "pide_descargar": "asks_to_download", "buena_presentacion": "appearance_required", "no_dice_puesto": "no_job_described",
             "puesto_real_distinto": "different_job", "solo_mujeres_o_rango_edad": "women_or_age_targeted",
             "cita_en_lugar_no_establecido": "unestablished_meeting_place", "sigue_por_mensaje_privado": "personal_contact",
             "empresa_nunca_nombrada": "employer_never_named", "incomunicado_o_retiran_celular": "held_incommunicado",
             "adiestramiento_o_capacitacion_fuera": "training_elsewhere"}
    facts = {}
    def add(o, r, pay_col):
        s = facts.setdefault(o, set()); job = r["puesto"]
        s.update(f"{pred}({o})." for col, pred in flags.items() if r.get(col) == "1")
        if r["sin_experiencia"] == "1": s.add(f"has({o}, sin_experiencia).")
        if r["urgente"] == "1": s.add(f"has({o}, contratacion_urgente).")
        if r["contacto"] in g.PERSONAL_CONTACT: s.add(f"personal_contact({o}).")
        try:
            if float(r[pay_col]) * rate[r["pago_moneda"]] * period.get(r["pago_periodo"], 1) >= g.HIGH_PAY_MONTHLY: s.add(f"high_pay({o}).")
        except (ValueError, KeyError): pass
        if g.SECURITY.search(job): s.add(f"security({o}).")
        if g.TRAFFICKING_RISK.search(job): s.add(f"trafficking_risk_role({o}).")
        if g.PROMOTION.search(job): s.add(f"sales({o}).")
        if g.OPERATIONAL.search(job): s.add(f"operational_role({o}).")
    for r in csv.DictReader(open(P / "prensa/captura_notas_por_caso.csv", encoding="utf-8")):
        if r["nota_disponible"] == "1" and r["trata_del_tema"] != "0" and r["describe_enganche"] == "1":
            add(r["id"].lower().replace("-", "_"), r, "pago_maximo")
    for r in csv.DictReader(open(P / "prensa/captura_167_notas.csv", encoding="utf-8")):
        o = r["id"].lower().replace("-", "_")
        if o not in facts: add(o, r, "pago_tope")
    (P / "prensa/prensa_senales.lp").write_text("\n".join(sorted(x for s in facts.values() for x in s)) + "\n", encoding="utf-8")


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
