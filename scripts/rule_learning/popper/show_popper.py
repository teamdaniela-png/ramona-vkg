#!/usr/bin/env python3
"""Run Popper on the task and show, in Spanish, the rules it learns and how they do on the held-out offers."""
import csv, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/operational/private/popper"
POPPER = Path.home() / "Downloads/_tools/Popper"
ES = {"unsolicited_contact": "llega sin haberla buscado", "borrowed_name": "usa un nombre ajeno", "asks_for_documents": "pide documentos antes",
      "asks_for_money": "pide dinero", "no_job_described": "no dice el puesto", "security": "puesto de seguridad",
      "operational_role": "puesto operativo", "personal_contact": "solo canal personal", "high_pay": "sueldo alto",
      "relocation": "otro estado o traslado", "no_experience": "sin experiencia", "seasonal": "de temporada", "urgent": "urgente",
      "sales": "ventas", "trafficking_risk_role": "puesto de riesgo de trata", "not_verified": "empresa sin validar",
      "requires_experience": "pide experiencia", "appearance_required": "pide buena presentacion", "different_job": "el trabajo real es otro",
      "asks_to_download": "pide descargar algo", "intermediary": "intermediaria", "entry_level": "puesto de entrada",
      "internship": "becario", "specialised_role": "puesto especializado"}
task = sys.argv[1] if len(sys.argv) > 1 else "todo"
noisy = ["--noisy"] if len(sys.argv) > 2 else []
pos = sum(1 for l in open(OUT / task / "exs.pl") if l.startswith("pos"))
neg = sum(1 for l in open(OUT / task / "exs.pl") if l.startswith("neg"))
print("\nPOPPER: aprende reglas solo a partir de ejemplos\n")
print("Le doy %d ofertas que la experta marco como fraude o peligro" % pos)
print("y %d ofertas legitimas con empresa validada.\n" % neg)
print("Corriendo Popper...\n")
r = subprocess.run(["uv", "run", "popper.py", str(OUT / task), "--max-vars", "1", "--max-body", "4", "--timeout", "200"] + noisy,
                   cwd=POPPER, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
sol = r.split("SOLUTION")[-1]
m = re.search(r"TP:(\d+) FN:(\d+) TN:(\d+) FP:(\d+)", sol)
rules = [re.findall(r"(\w+)\(V0\)", l.split(":-")[1]) for l in sol.splitlines() if ":-" in l]
print("REGLAS QUE APRENDIO (%d):\n" % len(rules))
for i, body in enumerate(rules, 1):
    print("  %2d. Alerta si: %s" % (i, " Y ".join(ES.get(b, b) for b in body)))
    print("      alert(O) :- %s." % ", ".join("%s(O)" % b for b in body))
tp, fn, tn, fp = map(int, m.groups())
print("\nCON LOS EJEMPLOS QUE VIO:")
print("  Fraude o peligro que atrapa:        %d de %d" % (tp, tp + fn))
print("  Legitimas que alerta por error:     %d de %d" % (fp, fp + tn))
t = {}
for row in csv.DictReader(open(OUT / "prueba_hechos.csv")):
    h = set(row["hechos"].split()); a = any(all(b in h for b in body) for body in rules)
    t.setdefault(row["etiqueta"], [0, 0])[a] += 1
print("\nCON 43 OFERTAS QUE NUNCA VIO (prueba ciega):")
print("  Fraudes que atrapa:                 %d de %d" % (t["fraude"][1], sum(t["fraude"])))
print("  Legitimas que deja sin alerta:      %d de %d" % (t["legitima"][0], sum(t["legitima"])))
print("  Dudosas que alerta:                 %d de %d" % (t["dudosa"][1], sum(t["dudosa"])))
print("\nLAS REGLAS DE LA EXPERTA EN ESA MISMA PRUEBA (10 reglas congeladas):")
print("  Fraudes que atrapa:                 7 de 7")
print("  Legitimas que deja sin alerta:      16 de 23\n")
