#!/usr/bin/env python3
"""Show the expert rules written out with explicit negation and check, with Clingo, that they give
exactly the same alerts as expert_rules.lp on every offer collected so far."""
import collections, re, sys
from pathlib import Path
import clingo
ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data/operational/private"
D = ROOT / "data/processed/rule_learning"
ASP = ROOT / "scripts/rule_learning/asp"
NAMES = {1: "SUELDO ALTO", 2: "URGENCIA", 3: "URGENCIA Y SIN EXPERIENCIA", 4: "LLEGA SIN HABERLA BUSCADO", 5: "SOLO CANAL PERSONAL",
         6: "PIDEN DINERO", 7: "NO DICE EL PUESTO", 8: "USA NOMBRE AJENO", 9: "OTRO ESTADO O TRASLADO", 10: "EL TRABAJO REAL ES OTRO",
         11: "PUESTO DE RIESGO DE TRATA", 12: "PUESTO DE SEGURIDAD", 13: "BUENA PRESENTACION SIN PUESTO", 14: "PIDEN DOCUMENTOS ANTES",
         15: "PIDEN DESCARGAR O EVALUACION", 16: "CITA EN LUGAR NO ESTABLECIDO", 17: "SOLO MUJERES O RANGO DE EDAD",
         18: "PIDE FOTO SIN EMPRESA VERIFICADA", 19: "USA CODIGOS O EMOJIS", 20: "EMPRESA NUNCA NOMBRADA EN RED O CANAL PERSONAL",
         21: "SUELDO ALTO SIN EMPRESA, SIN EXPERIENCIA O SIN PUESTO", 22: "PUESTO USADO COMO GANCHO (VERIFICA)"}
text = (ASP / "expert_rules_long.lp").read_text(encoding="utf-8")
if "-q" not in sys.argv:
    print("\nLAS 22 REGLAS, ESCRITAS LARGAS Y CON LA NEGACION A LA VISTA\n")
    for n in range(1, 23):
        body = re.findall(r"^l\(O, %d\) :-.*?\.$" % n, text, re.M | re.S)
        print("%d. %s   (%d regla%s)" % (n, NAMES[n], len(body), "" if len(body) == 1 else "s"))
        for b in body: print("   " + re.sub(r"\s+", " ", b))
        print()
files = [D / "offers.lp", D / "expert_facts.lp", ASP / "expert_rules.lp", ASP / "expert_rules_long.lp"] + sorted(P.glob("anuncios_*.lp"))
for extra in ("prensa/prensa_casos.lp", "popper/_prueba/anuncios_prueba.lp"):
    if (P / extra).exists(): files.append(P / extra)
ctl = clingo.Control(["--warn=none"])
for f in files: ctl.load(str(f))
ctl.add("base", [], "#show. #show holds/2. #show l/2. #show offer/1. #show alerta/1. #show verifica/1. #show escalar/1. #show l_alerta/1. #show l_verifica/1. #show l_escalar/1.")
ctl.ground([("base", [])])
short, long_, offers = collections.defaultdict(set), collections.defaultdict(set), set()
def on(m):
    for a in m.symbols(shown=True):
        if a.name == "offer": offers.add(str(a.arguments[0]))
        elif a.name == "holds": short[str(a.arguments[0])].add(a.arguments[1].number)
        elif a.name == "l": long_[str(a.arguments[0])].add(a.arguments[1].number)
        elif a.name in ("alerta", "verifica", "escalar"): short[str(a.arguments[0])].add(a.name)
        elif a.name.startswith("l_"): long_[str(a.arguments[0])].add(a.name[2:])
ctl.solve(on_model=on)
diff = [(o, sorted(short[o] ^ long_[o])) for o in offers if short[o] != long_[o]]
lits = re.findall(r"^l\(O, \d+\) :-(.*?)\.$", text, re.M | re.S)
n_rules = len(lits); n_neg = sum(b.count("not ") for b in lits); longest = max(len(re.findall(r"\w+\(", b)) for b in lits)
print("COMPROBACION CON CLINGO")
print("   Reglas largas: %d   Negaciones en total: %d   La mas larga tiene %d condiciones" % (n_rules, n_neg, longest))
print("   Ofertas y casos evaluados: %d" % len(offers))
print("   Alertas con las reglas originales: %d   con las reglas largas: %d" % (sum(len(v) for v in short.values()), sum(len(v) for v in long_.values())))
print("   Ofertas donde difieren: %d%s\n" % (len(diff), "  -> SON EQUIVALENTES" if not diff else "  -> REVISAR: " + str(diff[:5])))
