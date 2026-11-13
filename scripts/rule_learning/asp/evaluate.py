#!/usr/bin/env python3
"""Run rules_with_exceptions.lp over offers.lp with clingo and compare each rule with what is documented.

Needs the clingo Python package (pip install clingo).
"""
import collections
from pathlib import Path

import clingo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FACTS = ROOT / "data/processed/rule_learning/offers.lp"


def solve():
    ctl = clingo.Control(["0"])
    ctl.load(str(FACTS))
    ctl.load(str(HERE / "rules_with_exceptions.lp"))
    ctl.add("base", [], "#show documented_trap/1. #show verified_posting/1. #show kind/2.")
    ctl.ground([("base", [])])
    models = []
    ctl.solve(on_model=lambda m: models.append([str(a) for a in m.symbols(shown=True)]))
    assert len(models) == 1, f"expected one answer set, got {len(models)}"
    out = collections.defaultdict(set)
    for a in models[0]:
        name, args = a.split("(", 1)
        out[name].add(tuple(args.rstrip(")").split(",")))
    return out


def main():
    m = solve()
    trap = {a[0] for a in m["documented_trap"]}
    verified = {a[0] for a in m["verified_posting"]}
    kind = dict(m["kind"])
    print(f"{len(trap)} documented offers (Mexico), {len(verified)} verified postings, one answer set\n")

    print("Example 1. alert on pay")
    for name in ("alert_pay_default", "alert_pay"):
        fired = {a[0] for a in m[name]}
        print(f"  {name:20s} fires on {len(fired):3d}: {len(fired & trap)} documented, {len(fired & verified)} verified"
              f"   {sorted(fired & verified)}")
    blocked = {a[0] for a in m["alert_pay_default"]} - {a[0] for a in m["alert_pay"]}
    print(f"  blocked by the exception: {sorted(blocked)}\n")

    for title, default, full in (("Example 2. kind of trap from a promise of high pay", "kind_pay_default", "kind_pay"),
                                 ("Example 3. kind of trap from an ordinary-sounding job", "kind_role_default", "kind_role")):
        print(title)
        for name in (default, full):
            pred = m[name]
            ok = sum(1 for o, k in pred if kind.get(o) == k)
            by = collections.Counter(k for _, k in pred)
            hit = collections.Counter(k for o, k in pred if kind.get(o) == k)
            detail = ", ".join(f"{k}: {hit[k]}/{by[k]}" for k in sorted(by))
            print(f"  {name:20s} concludes on {len(pred):3d}, correct {ok} ({100 * ok / len(pred):.0f}%)   [{detail}]")
        silent = {o for o, _ in m[default]} - {o for o, _ in m[full]}
        print(f"  no conclusion after the exceptions: {len(silent)} offers, documented as "
              f"{dict(collections.Counter(kind[o] for o in silent))}\n")


if __name__ == "__main__":
    main()
