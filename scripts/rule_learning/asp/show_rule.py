#!/usr/bin/env python3
"""Show what one expert rule does, offer by offer.

Usage: python scripts/rule_learning/asp/show_rule.py <1|2|3|4|5>

Prints the rule as written in expert_rules.lp, how many documented traps and verified postings
it fires on with and without its exceptions, and the offers the exceptions block.
Needs the clingo Python package. Run build_facts.py and build_expert_facts.py first.
"""
import csv
import re
import sys
from pathlib import Path

import clingo

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/processed/rule_learning"
RULES = ROOT / "scripts/rule_learning/asp/expert_rules.lp"


def main():
    c = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    text = RULES.read_text(encoding="utf-8")
    block = re.search(r"% ---- Component " + str(c) + r"\..*?(?=\n\n)", text, re.S).group(0)
    print(block.replace("% ---- ", "").replace("%      ", "  "))
    print()

    ctl = clingo.Control(["--warn=none"])
    extra = sorted((ROOT / "data/operational/private").glob("*.lp")) + sorted((ROOT / "data/operational/private").glob("prensa/prensa_senales.lp"))
    for f in [D / "offers.lp", D / "expert_facts.lp", RULES] + extra:
        ctl.load(str(f))
    ctl.ground([("base", [])])
    fires, default = set(), set()

    def on_model(m):
        for a in m.symbols(shown=True):
            if a.name in ("holds", "holds_default") and a.arguments[1].number == c:
                (fires if a.name == "holds" else default).add(str(a.arguments[0]))
    ctl.solve(on_model=on_model)

    facts = (D / "offers.lp").read_text(encoding="utf-8")
    traps = set(re.findall(r"documented_trap\((\w+)\)", facts))
    postings = set(re.findall(r"verified_posting\((\w+)\)", facts))
    new, doubtful = set(), set()
    name = {}
    for f in extra:
        new |= set(re.findall(r"job_board_posting\((\w+)\)", f.read_text(encoding="utf-8")))
        doubtful |= set(re.findall(r"expert_doubtful\((\w+)\)", f.read_text(encoding="utf-8")))
    new -= doubtful
    for f in sorted((ROOT / "data/operational/private").glob("anuncios_*.csv")):
        if "crudo" in f.name:
            continue
        for r in csv.DictReader(open(f, encoding="utf-8")):
            name[r["id"].lower().replace("-", "_")] = "%s. %s, %s. Experiencia: %s. %s" % (
                r["id"], r["puesto"], r["empresa"], r["experiencia"], r["nota"])
    for r in csv.DictReader(open(ROOT / "data/real/press_offers_verified.csv", encoding="utf-8")):
        name[r["offer_uid"].lower().replace("-", "_")] = "%s. %s" % (r["offer_uid"], r["job_title"])
    for r in csv.DictReader(open(ROOT / "data/real/legit_offers.csv", encoding="utf-8")):
        name[r["legit_id"].lower().replace("-", "_")] = "%s. %s, %s. Asks: %s" % (
            r["legit_id"], r["puesto"], r["empresa"], r["requisitos"])

    def kind(o):
        return ("verified posting" if o in postings else "new posting" if o in new
                else "expert: doubtful" if o in doubtful else "documented trap")
    head = ("documented traps (%d)" % len(traps), "verified postings (%d)" % len(postings),
            "new postings (%d)" % len(new), "expert: doubtful (%d)" % len(doubtful))
    print("%-20s %22s %24s %19s %22s" % (("",) + head))
    for label, s in (("general rule alone", default), ("with the exceptions", fires)):
        print("%-20s %22d %24d %19d %22d" % (label, len(s & traps), len(s & postings), len(s & new), len(s & doubtful)))
    blocked = sorted(default - fires)
    print("\noffers the exceptions take out: %d" % len(blocked))
    for o in blocked:
        print("  [%s] %s" % (kind(o), name.get(o, o)))
    still = sorted(fires & (postings | new | doubtful))
    if still:
        print("\npostings the rule still fires on: %d" % len(still))
        for o in still:
            print("  [%s] %s" % (kind(o), name.get(o, o)))


if __name__ == "__main__":
    main()
