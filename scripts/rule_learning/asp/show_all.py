#!/usr/bin/env python3
"""Print every expert rule as written in expert_rules.lp."""
import re
from pathlib import Path
T = (Path(__file__).resolve().parent / "expert_rules.lp").read_text(encoding="utf-8")
ES = {1: "SUELDO ALTO", 2: "URGENCIA", 3: "URGENCIA Y SIN EXPERIENCIA", 4: "LLEGA SIN HABER BUSCADO",
      5: "SOLO CANAL PERSONAL", 6: "TE PIDEN DINERO", 7: "NO DICE EL PUESTO", 8: "USA NOMBRE AJENO",
      9: "OTRO ESTADO O TRASLADO PAGADO", 10: "EL TRABAJO REAL ES OTRO",
      11: "PUESTO DE RIESGO DE TRATA (CONSEJO CIUDADANO)", 12: "SEGURIDAD O ESCOLTA DE EMPRESA ANONIMA", 13: "BUENA PRESENTACION SIN DECIR EL PUESTO",
      14: "PIDEN DOCUMENTOS ANTES DE LA ENTREVISTA", 15: "PIDEN DESCARGAR ALGO O HACER UNA EVALUACION"}
m = re.search(r"% ---- An employer that advertises.*?(?=\n\n)", T, re.S)
print("\n=== CUANDO UNA EMPRESA CUENTA COMO VALIDADA ===\n")
print("\n".join(l for l in T.splitlines() if l.startswith("verified_employer(")))
if m:
    print(m.group(0).replace("% ---- ", "").replace("%      ", "  ").replace("#show validated_on_social/1.", ""))
for c in range(1, 16):
    b = re.search(r"% ---- Component " + str(c) + r"\..*?(?=\n\n)", T, re.S)
    if b:
        print("\n=== REGLA %d. %s ===\n" % (c, ES[c]))
        print(b.group(0).replace("% ---- ", "").replace("%      ", "  "))
print()
