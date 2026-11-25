#!/usr/bin/env python3
"""Clingo -> Popper -> Clingo, case by case.

1. Clingo derives the signals of every example from the facts and the expert's definitions
   (verified employer, high pay, relocation, personal channel).
2. Popper learns rules from the examples. Negation is given to Popper as the complement of each
   signal (not_x), so it can learn rules of the form "a and not b", up to eight conditions long.
3. The learned rules are written in ASP with real negation as failure and Clingo evaluates them,
   next to the expert's rules, on the training examples and on the blind-test offers.

Positives: the press cases captured note by note (captura_casos_verificada.csv) and the expert's
own cases labelled fraude or peligro. Negatives: offers with a verified employer.

Usage: run_pipeline.py [persona|todos] [base|canal|completo|comparar]
  base      the 22 signals about what the offer says
  canal     + where the offer reached the person (social network, formal job board, direct message)
  completo  + whether the offer ever names the employer
  comparar  the three, side by side
"""
import csv, re, subprocess, sys, importlib.util, collections, io, contextlib
from pathlib import Path
import clingo

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data/operational/private"
D = ROOT / "data/processed/rule_learning"
ASP = ROOT / "scripts/rule_learning/asp"
OUT = P / "popper"
POPPER = Path.home() / "Downloads/_tools/Popper"
spec = importlib.util.spec_from_file_location("g", ASP / "build_posting_facts.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

# signal seen by Popper -> how Clingo derives it
BRIDGE = {"high_pay": "pay_high(O)", "relocation": "moves_person(O)", "personal_contact": "personal_channel(O)",
          "urgent": "has(O, contratacion_urgente), not portal_badge_only(O)", "no_experience": "has(O, sin_experiencia)",
          "verified": "verified_employer(O)"}
PLAIN = ["requires_experience", "sales", "seasonal", "internship", "entry_level", "security", "operational_role",
         "specialised_role", "unsolicited_contact", "asks_for_money", "no_job_described", "borrowed_name",
         "trafficking_risk_role", "appearance_required", "asks_for_documents", "asks_to_download", "intermediary"]
CHANNEL = ["social_network", "formal_portal", "direct_message"]      # their negation only counts when the channel is known
V1 = [b for b in BRIDGE if b != "verified"]
NEW = ["asks_for_photo", "coded_language", "recruitment_role"]
VARIANTS = {"base": (sorted(PLAIN + V1), "las 22 senales sobre lo que dice la oferta"),
            "canal": (sorted(PLAIN + V1 + CHANNEL), "las 22 + por donde llego la oferta (red social, portal formal, mensaje directo)"),
            "completo": (sorted(PLAIN + V1 + CHANNEL + ["employer_never_named", "bus_terminal", "transport_sent"]),
                         "las 22 + canal + empresa nunca nombrada + terminal de autobuses + le mandan transporte"),
            "v2": (sorted(PLAIN + V1 + CHANNEL + ["employer_never_named", "bus_terminal", "transport_sent"] + NEW + ["verified"]),
                   "completo + pide foto + codigos + puesto usado como gancho + empresa verificada (solo como excepcion de canal)")}
# Version 3 (24-nov-2026): Popper could not see two signals the expert uses (place of the appointment, addressed to
# women or an age range), so it missed the field cases "cited at the bus terminal". They are added here.
VARIANTS["v3"] = (sorted(VARIANTS["v2"][0] + ["unestablished_meeting_place", "women_or_age_targeted"]),
                  "v2 + cita en lugar no establecido + solo mujeres o rango de edad")
ALL = VARIANTS["v3"][0]
# Version 2 (24-nov-2026): a rule that uses the channel must carry the exception "employer verified" (expert),
# and "employer verified" may only appear as that exception.
CHANNEL_LITS = CHANNEL + ["not_" + c for c in CHANNEL]
BIAS_V2 = "\n".join(["chan(R) :- body_literal(R,%s,_,_)." % c for c in CHANNEL_LITS] +
                     [":- chan(R), not body_literal(R,not_verified,_,_).",
                      ":- body_literal(R,not_verified,_,_), not chan(R).", ":- body_literal(_,verified,_,_)."]) + "\n"
ES = {"unsolicited_contact": "llega sin haberla buscado", "borrowed_name": "usa un nombre ajeno", "asks_for_documents": "pide documentos antes",
      "asks_for_money": "pide dinero", "no_job_described": "no dice el puesto", "security": "puesto de seguridad",
      "operational_role": "puesto operativo", "personal_contact": "solo canal personal", "high_pay": "sueldo alto",
      "relocation": "otro estado o traslado", "no_experience": "sin experiencia", "seasonal": "de temporada", "urgent": "urgente",
      "sales": "ventas", "trafficking_risk_role": "puesto de riesgo de trata", "requires_experience": "pide experiencia",
      "appearance_required": "pide buena presentacion", "asks_to_download": "pide descargar algo", "intermediary": "intermediaria",
      "entry_level": "puesto de entrada", "internship": "becario", "specialised_role": "puesto especializado",
      "social_network": "llega por red social", "formal_portal": "esta en un portal formal", "direct_message": "llega por mensaje directo",
      "employer_never_named": "nunca nombra a la empresa",
      "bus_terminal": "terminal de autobuses", "transport_sent": "le mandan o pagan el transporte",
      "asks_for_photo": "pide foto", "coded_language": "usa codigos o emojis", "recruitment_role": "puesto usado como gancho",
      "verified": "empresa verificada", "unestablished_meeting_place": "cita en lugar no establecido",
      "women_or_age_targeted": "solo mujeres o rango de edad"}
CASE = {"pide_experiencia": "requires_experience", "no_solicitado": "unsolicited_contact", "pide_dinero": "asks_for_money",
        "usa_nombre_ajeno": "borrowed_name", "otro_estado_o_traslado": "relocation", "pagan_o_dan_el_boleto": "relocation",
        "pide_documentos": "asks_for_documents", "pide_datos_bancarios": "asks_for_documents", "pide_descargar": "asks_to_download",
        "buena_presentacion": "appearance_required", "no_dice_puesto": "no_job_described", "puesto_real_distinto": "different_job",
        "solo_mujeres_o_rango_edad": "women_or_age_targeted", "cita_en_lugar_no_establecido": "unestablished_meeting_place",
        "sigue_por_mensaje_privado": "personal_contact", "empresa_nunca_nombrada": "employer_never_named",
        "pide_fotos": "asks_for_photo"}
PERIOD = {"dia": 22, "semana": 4.33, "quincena": 2, "mes": 1}
RATE = {"MXN": 1, "USD": 19}
EXTRA = "formal_portal(O) :- verified_posting(O).  channel_known(O) :- verified_posting(O).\n"      # the verified postings come from a job board


def case_facts(which):
    """Facts of the press cases after the fourth reading (casos_finales.csv): one offer per distinct case,
    labelled by the expert. Cases she labelled "no es oferta" and the hooks that were not a job are left out."""
    case = dict(CASE)
    case.update({"cita_en_terminal_de_autobuses": "unestablished_meeting_place", "transporte_enviado_por_la_persona": "relocation",
                 "sueldo_alto_para_el_puesto": "high_pay"})
    extra = {"cita_en_terminal_de_autobuses": "bus_terminal", "transporte_enviado_por_la_persona": "transport_sent",
             "pagan_o_dan_el_boleto": "transport_sent"}
    lines, ids = [], {}
    for r in csv.DictReader(open(P / "prensa/casos_finales.csv", encoding="utf-8")):
        if r["etiqueta_daniela"] not in ("peligro", "fraude") or r["trata_del_tema"] == "0" or r["tipo_de_fila"] == "gancho_no_laboral": continue
        if which == "persona" and r["tipo_de_fila"] != "caso_individual": continue
        o = "c_" + r["caso"].lower().replace("-", "_"); ids[o] = r
        lines.append(f"offer({o}).")
        lines += [f"{pred}({o})." for col, pred in case.items() if r.get(col) == "1"]
        if r["sin_experiencia"] == "1": lines.append(f"has({o}, sin_experiencia).")
        if r["urgente"] == "1": lines.append(f"has({o}, contratacion_urgente).")
        if r["contacto"] in g.PERSONAL_CONTACT: lines.append(f"personal_contact({o}).")
        try:
            if float(r["pago_maximo"]) * RATE[r["pago_moneda"]] * PERIOD.get(r["pago_periodo"], 1) >= g.HIGH_PAY_MONTHLY: lines.append(f"high_pay({o}).")
        except (ValueError, KeyError): pass
        if g.CODES.search(r.get("codigos_o_emojis") or ""): lines.append(f"coded_language({o}).")
        for rx, pred in ((g.RECRUIT_ROLE, "recruitment_role"), (g.SECURITY, "security"), (g.TRAFFICKING_RISK, "trafficking_risk_role"), (g.PROMOTION, "sales"), (g.OPERATIONAL, "operational_role")):
            if rx.search(r["puesto"]): lines.append(f"{pred}({o}).")
        lines += sorted({f"{pred}({o})." for col, pred in extra.items() if r.get(col) == "1"})
        kinds, known = g.channel(r["plataformas"])
        if "social_network" in kinds or "direct_message" in kinds:      # a note that names a job board next to a social network
            kinds = [k for k in kinds if k != "formal_portal"]          # describes offers that circulate on the network
        lines += [f"{k}({o})." for k in kinds]
        if known: lines.append(f"channel_known({o}).")
    (P / "prensa/prensa_casos.lp").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ids


def solve(files, extra=""):
    """Run Clingo. Returns signals per offer, expert rules that hold per offer, offers the learned rules alert."""
    ctl = clingo.Control(["--warn=none"])
    for f in files: ctl.load(str(f))
    bridge = "\n".join("sig(O, %s) :- %s." % (s, BRIDGE.get(s, s + "(O)")) for s in ALL)
    ctl.add("base", [], bridge + "\nsig(O, verified) :- verified_employer(O).\nsig(O, channel_known) :- channel_known(O).\n" + EXTRA + extra)
    ctl.ground([("base", [])])
    sig, holds, alert = collections.defaultdict(set), collections.defaultdict(set), set()
    def on(m):
        for a in m.symbols(atoms=True):
            if a.name == "sig": sig[str(a.arguments[0])].add(str(a.arguments[1]))
            elif a.name == "holds": holds[str(a.arguments[0])].add(a.arguments[1].number)
            elif a.name == "alert": alert.add(str(a.arguments[0]))
    ctl.solve(on_model=on)
    return sig, holds, alert


def view(sig_o, signals):
    """What Popper sees of one example: each signal, true or false; the channel ones only when the channel is known."""
    out = []
    for s in signals:
        if s in sig_o: out.append(s)
        elif s not in CHANNEL or "channel_known" in sig_o: out.append("not_" + s)
    return out


def lit(b):
    if not b.startswith("not_"): return BRIDGE.get(b, b + "(O)")
    s = b[4:]; body = BRIDGE.get(s, s + "(O)")
    if ", not" in body: body = "sig_%s(O)" % s        # a derived signal with its own negation: negate it through a helper
    return ("channel_known(O), " if s in CHANNEL else "") + "not " + body


def prepare(which):
    cases = case_facts(which)
    files = [D / "offers.lp", D / "expert_facts.lp", ASP / "expert_rules.lp", P / "prensa/prensa_casos.lp"] + sorted(P.glob("anuncios_*.lp"))
    sig, holds, _ = solve(files)
    pos, neg = set(cases), set()
    for f in sorted(P.glob("anuncios_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            o = r["id"].lower().replace("-", "_")
            if r["id"].startswith("D-"):
                if r.get("clasificacion") in ("fraude", "peligro", "reclutamiento_criminal"): pos.add(o)
            elif "verified" in sig[o]: neg.add(o)
    neg |= set(re.findall(r"verified_posting\((\w+)\)", (D / "offers.lp").read_text(encoding="utf-8")))
    # Version 2: the 60 offers of the second blind test, already used as a test, join the training with the expert's
    # labels. E-11 is left out: after the test the expert said her label (legitima) was a mistake.
    ex = P / "prueba_ciega2"; exfacts = OUT / "_examen2"; exfacts.mkdir(parents=True, exist_ok=True)
    (exfacts / "anuncios_examen2.csv").write_text((ex / "ofertas_examen.csv").read_text(encoding="utf-8"), encoding="utf-8")
    g.PRIVATE = exfacts
    with contextlib.redirect_stdout(io.StringIO()): g.main()
    files.append(exfacts / "anuncios_examen2.lp")
    sig, holds, _ = solve(files)
    for r in csv.DictReader(open(ex / "etiquetas_daniela.csv", encoding="utf-8")):
        o = r["clave"].lower().replace("-", "_")
        if not o.startswith(("e_", "m_")) or o == "e_11": continue
        if r["etiqueta"] in ("fraude", "peligro"): pos.add(o)
        elif r["etiqueta"] == "legitima": neg.add(o)
    # Version 3: the 17 field cases (interviews and user cases), already scored with v1 and v2, join the training.
    (exfacts / "anuncios_campo.csv").write_text((ex / "campo/campo_ofertas.csv").read_text(encoding="utf-8"), encoding="utf-8")
    with contextlib.redirect_stdout(io.StringIO()): g.main()
    files.append(exfacts / "anuncios_campo.lp")
    sig, holds, _ = solve(files)
    for r in csv.DictReader(open(ex / "etiquetas_daniela.csv", encoding="utf-8")):
        o = r["clave"].lower().replace("-", "_")
        if o.startswith("k_") and r["etiqueta"] in ("fraude", "peligro"): pos.add(o)
    tmp = OUT / "_prueba"; tmp.mkdir(parents=True, exist_ok=True)      # facts of the blind-test offers, with the current generator
    (tmp / "anuncios_prueba.csv").write_text((P / "prueba_ciega/ofertas_prueba.csv").read_text(encoding="utf-8-sig"), encoding="utf-8")
    g.PRIVATE = tmp
    with contextlib.redirect_stdout(io.StringIO()): g.main()
    lab = {r["id"].lower().replace("-", "_"): r["etiqueta"] for r in csv.DictReader(open(P / "prueba_ciega/etiquetas_daniela.csv", encoding="utf-8"))}
    return dict(which=which, cases=cases, files=files, sig=sig, holds=holds, pos=pos, neg=neg, test=tmp / "anuncios_prueba.lp", lab=lab)


def learn(ctx, variant):
    signals = VARIANTS[variant][0]; sig, pos, neg = ctx["sig"], ctx["pos"], ctx["neg"]
    task = OUT / ("casos_%s_%s" % (ctx["which"], variant)); task.mkdir(parents=True, exist_ok=True)
    preds = signals + ["not_" + s for s in signals]
    decl = ", ".join(p + "/1" for p in preds)
    bk = [":- discontiguous " + decl + ".", ":- dynamic " + decl + "."]
    for o in sorted(pos | neg): bk += ["%s(%s)." % (v, o) for v in view(sig[o], signals)]
    (task / "bk.pl").write_text("\n".join(bk) + "\n")
    (task / "exs.pl").write_text("\n".join(["pos(alert(%s))." % o for o in sorted(pos)] + ["neg(alert(%s))." % o for o in sorted(neg)]) + "\n")
    (task / "bias.pl").write_text("head_pred(alert,1).\n" + "\n".join("body_pred(%s,1)." % p for p in preds) + "\n" + (BIAS_V2 if variant in ("v2", "v3") else ""))
    saved = task / "salida_popper.txt"
    if "guardado" in sys.argv and saved.exists():      # show the last run of Popper instead of learning again (several minutes)
        out = saved.read_text()
    else:
        out = subprocess.run(["uv", "run", "popper.py", str(task), "--max-vars", "1", "--max-body", "8", "--timeout", "900"],
                             cwd=POPPER, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
        saved.write_text(out)
    sol = out.split("SOLUTION")[-1]
    rules = [re.findall(r"(\w+)\(V0\)", l.split(":-")[1]) for l in sol.splitlines() if ":-" in l]
    helpers = ["sig_%s(O) :- %s." % (s, BRIDGE[s]) for s in BRIDGE if ", not" in BRIDGE[s]]
    asp = ["% Rules learned by Popper (" + variant + "), written with negation as failure. Generated by run_pipeline.py."] + helpers
    asp += ["alert(O) :- offer(O), %s." % ", ".join(dict.fromkeys(x for b in body for x in lit(b).split(", ") if x)) for body in rules]
    learned = task / "reglas_aprendidas.lp"; learned.write_text("\n".join(asp) + "\n")
    _, holds, alert = solve(ctx["files"] + [learned])
    _, th, ta = solve([ASP / "expert_rules.lp", ctx["test"], learned])
    lab = ctx["lab"]
    fr = [o for o, e in lab.items() if e == "fraude"]; le = [o for o, e in lab.items() if e == "legitima"]; du = [o for o, e in lab.items() if e == "dudosa"]
    same = collections.Counter(frozenset(view(sig[o], signals)) for o in neg)
    missed = sorted(pos - alert)
    return dict(variant=variant, rules=rules, asp=[a for a in asp if a.startswith("alert")], learned=learned, holds=holds, th=th,
                tp=len(pos & alert), fp=len(neg & alert), missed=len(missed), ident=sum(1 for o in missed if same[frozenset(view(sig[o], signals))]),
                t_fr=(sum(o in ta for o in fr), len(fr)), t_le=(sum(o not in ta for o in le), len(le)), t_du=(sum(o in ta for o in du), len(du)),
                fr=fr, le=le, du=du, n_neg=sum(b.startswith("not_") for r in rules for b in r), longest=max((len(r) for r in rules), default=0))


def show(ctx, res):
    pos, neg = ctx["pos"], ctx["neg"]
    print("\n   REGLAS APRENDIDAS: %d   (con negacion: %d condiciones negadas; la mas larga tiene %d condiciones)\n" % (len(res["rules"]), res["n_neg"], res["longest"]))
    for i, body in enumerate(res["rules"], 1):
        es = " Y ".join(("NO " + ES.get(b[4:], b[4:])) if b.startswith("not_") else ES.get(b, b) for b in body)
        print("   %2d. Alerta si: %s" % (i, es)); print("       " + res["asp"][i - 1])
    print("\n3. CLINGO evalua las reglas aprendidas y las de la experta\n")
    h = res["holds"]
    def row(name, a, b): print("   %-46s %4d de %-4d %10d de %d" % (name, a, len(pos), b, len(neg)))
    print("   %-46s %-12s %s" % ("EJEMPLOS DE ENTRENAMIENTO", "malas con", "legitimas con"))
    print("   %-46s %-12s %s" % ("", "alerta", "alerta (error)"))
    row("Popper", res["tp"], res["fp"])
    row("Experta, 22 reglas (v2), cualquier regla", sum(bool(h[o]) for o in pos), sum(bool(h[o]) for o in neg))
    row("Experta v2, sin la regla 10 (se sabe despues)", sum(bool(h[o] - {10}) for o in pos), sum(bool(h[o] - {10}) for o in neg))
    th, fr, le, du = res["th"], res["fr"], res["le"], res["du"]
    print("\n   %-46s %-12s %-14s %s" % ("PRUEBA (43 ofertas; ya no es ciega)", "fraudes", "legitimas", "dudosas"))
    print("   %-46s %-12s %-14s %s" % ("", "con alerta", "sin alerta", "con alerta"))
    print("   %-46s %2d de %-6d %2d de %-8d %2d de %d" % ("Popper", *res["t_fr"], *res["t_le"], *res["t_du"]))
    print("   %-46s %2d de %-6d %2d de %-8d %2d de %d" % ("Experta, 22 reglas (v2)", sum(bool(th[o]) for o in fr), len(fr), sum(not th[o] for o in le), len(le), sum(bool(th[o]) for o in du), len(du)))
    print("   %-46s  7 de 7      16 de 23        7 de 13" % "Experta, 10 reglas congeladas el 18-nov")
    print("\n   Positivos que Popper no cubre: %d   (identicos en senales a alguna legitima: %d)" % (res["missed"], res["ident"]))
    print("   Reglas aprendidas en ASP: %s\n" % res["learned"].relative_to(ROOT))


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "persona"
    variant = sys.argv[2] if len(sys.argv) > 2 else "v3"
    ctx = prepare(which)
    print("\n1. CLINGO prepara los ejemplos")
    print("   Positivos: %d (%d casos de prensa %s + %d casos de la experta)" % (len(ctx["pos"]), len(ctx["cases"]), "de persona o grupo, sin repetir" if which == "persona" else "de todo tipo, sin repetir", len(ctx["pos"]) - len(ctx["cases"])))
    print("   Negativos: %d ofertas legitimas con empresa validada" % len(ctx["neg"]))
    if variant == "comparar":
        print("\n2. POPPER aprende con tres juegos de senales (reglas de hasta 8 condiciones, con negacion)...\n")
        print("   %-10s %-9s %-10s %-9s %-16s %-16s %-14s %s" % ("Senales", "Reglas", "Negadas", "Mas", "Malas con", "Legitimas con", "Prueba:", "Prueba: legit."))
        print("   %-10s %-9s %-10s %-9s %-16s %-16s %-14s %s" % ("", "", "", "larga", "alerta", "alerta (error)", "fraudes", "sin alerta"))
        for v in ("base", "canal", "completo"):
            r = learn(ctx, v)
            print("   %-10s %-9d %-10d %-9d %3d de %-9d %3d de %-9d %2d de %-8d %2d de %d" % (v, len(r["rules"]), r["n_neg"], r["longest"], r["tp"], len(ctx["pos"]), r["fp"], len(ctx["neg"]), *r["t_fr"], *r["t_le"]))
        h = ctx["holds"]
        print("   %-10s %-9s %-10s %-9s %3d de %-9d %3d de %-9d" % ("experta", "17", "", "", sum(bool(h[o] - {10}) for o in ctx["pos"]), len(ctx["pos"]), sum(bool(h[o] - {10}) for o in ctx["neg"]), len(ctx["neg"])))
        for v in ("base", "canal", "completo"): print("\n   %s: %s" % (v, VARIANTS[v][1]))
        print()
        return
    print("   Senales: %s" % VARIANTS[variant][1])
    print("\n2. POPPER aprende reglas (con negacion, hasta 8 condiciones)...")
    res = learn(ctx, variant)
    if not res["rules"]: print("   Popper no devolvio reglas."); return
    show(ctx, res)


if __name__ == "__main__":
    main()
