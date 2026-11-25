#!/usr/bin/env python3
"""One-screen summary of the expert rules over every collected offer."""
import csv, glob, re, collections
from pathlib import Path
import clingo
ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/processed/rule_learning"
P = ROOT / "data/operational/private"
NAMES = {1: "Sueldo alto", 2: "Urgencia", 3: "Urgencia y sin experiencia", 4: "Llega sin haber buscado",
         5: "Solo canal personal", 6: "Te piden dinero", 7: "No dice el puesto", 8: "Usa nombre ajeno",
         9: "Otro estado o traslado", 10: "El trabajo real es otro",
         11: "Puesto de riesgo de trata", 12: "Puesto de seguridad", 13: "Buena presentacion sin puesto",
         14: "Piden documentos antes", 15: "Piden descargar o evaluacion",
         16: "Cita en lugar no establecido", 17: "Solo mujeres o rango de edad", 18: "Pide foto sin empresa verificada", 19: "Codigos o emojis (pollitos)", 20: "Empresa nunca nombrada en red", 21: "Sueldo alto sin empresa/exp/puesto", 22: "Puesto gancho (verifica)"}
ctl = clingo.Control(["--warn=none"])
for f in [D / "offers.lp", D / "expert_facts.lp", ROOT / "scripts/rule_learning/asp/expert_rules.lp"] + sorted(P.glob("*.lp")) + sorted(P.glob("prensa/prensa_senales.lp")):
    ctl.load(str(f))
ctl.ground([("base", [])])
fin, dft = collections.defaultdict(set), collections.defaultdict(set)
def on_model(m):
    for a in m.symbols(shown=True):
        if a.name in ("holds", "holds_default"):
            (fin if a.name == "holds" else dft)[str(a.arguments[0])].add(a.arguments[1].number)
ctl.solve(on_model=on_model)
group = {}
for f in sorted(glob.glob(str(P / "anuncios_*.csv"))):
    for r in csv.DictReader(open(f, encoding="utf-8")):
        o = r["id"].lower().replace("-", "_")
        if r["id"].startswith("D-"):
            group[o] = "Fraude, reclutamiento o dudosa (experta)"
        elif r["verificacion"] in ("existe", "marca_conocida"):
            group[o] = "Real, empresa validada"
        else:
            group[o] = "Empresa sin validar"
t = (D / "offers.lp").read_text(encoding="utf-8")
for o in re.findall(r"documented_trap\((\w+)\)", t): group[o] = "Trampa documentada en prensa"
for o in re.findall(r"verified_posting\((\w+)\)", t): group[o] = "Real, empresa validada"
order = ["Real, empresa validada", "Empresa sin validar", "Fraude, reclutamiento o dudosa (experta)", "Trampa documentada en prensa"]
n = collections.Counter(group.values())
print("\nOFERTAS: %d\n" % len(group))
print("%-44s %8s %14s %14s" % ("Grupo", "Ofertas", "Sin excepcion", "Con excepcion"))
for g in order:
    ids = [o for o in group if group[o] == g]
    print("%-44s %8d %14d %14d" % (g, len(ids), sum(1 for o in ids if dft[o]), sum(1 for o in ids if fin[o])))
print("\nPOR REGLA (ofertas que la disparan: sin excepcion -> con excepcion)\n")
print("%-30s %22s %22s %22s" % ("Regla", "Real validada", "Experta: fraude etc.", "Prensa"))
for c in range(1, 23):
    row = []
    for g in (order[0], order[2], order[3]):
        ids = [o for o in group if group[o] == g]
        row.append("%d -> %d" % (sum(1 for o in ids if c in dft[o]), sum(1 for o in ids if c in fin[o])))
    print("%-30s %22s %22s %22s" % ("%d. %s" % (c, NAMES[c]), *row))
print()
