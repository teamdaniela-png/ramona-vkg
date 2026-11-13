#!/usr/bin/env python3
"""Learn default rules with exceptions from offers.lp with clingo (see learn_exceptions.lp).

Two tasks, each learned on all examples and scored by repeated stratified 5-fold cross-validation:
  A. criminal recruitment against the other documented offers (Mexico),
  B. documented offers against verified postings.

Needs the clingo Python package (pip install clingo).
"""
import collections
import random
import re
import statistics
from pathlib import Path

import clingo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FACTS = ROOT / "data/processed/rule_learning/offers.lp"
SEED, FOLDS, REPEATS = 2026, 5, 10

JOBS = ["security", "driver", "service", "care_cleaning", "field_construction", "remote_tasks"]
# Fixed by how each side was sampled or coded; never used to tell documented offers from verified postings.
SAMPLING = {"social_channel", "women", "minors", "young", "rol_plausible_gancho", "requirements"}


def load():
    feats, label = collections.defaultdict(set), {}
    for line in FACTS.read_text(encoding="utf-8").splitlines():
        for name, args in re.findall(r"(\w+)\(([^)]*)\)\.", line):
            a = [x.strip() for x in args.split(",")]
            o = a[0]
            if name in ("has", "target"):
                feats[o].add(a[1])
            elif name in JOBS + ["high_pay", "requirements", "social_channel"]:
                feats[o].add(name)
            elif name == "kind":
                label[o] = ("trap", a[1])
            elif name == "verified_posting":
                label[o] = ("verified", None)
            elif name == "offer":
                feats[o]
    return feats, label


def learn(examples, positives, feats, defaults, exceptions):
    ctl = clingo.Control(["--opt-mode=optN", "0"])
    ctl.load(str(HERE / "learn_exceptions.lp"))
    prog = [f"example({o})." for o in examples] + [f"pos({o})." for o in positives]
    prog += [f"feat({o},{f})." for o in examples for f in feats[o]]
    prog += [f"default_candidate({f})." for f in defaults] + [f"exception_candidate({f})." for f in exceptions]
    ctl.add("base", [], "\n".join(prog))
    ctl.ground([("base", [])])
    best = []

    def on_model(m):
        if m.optimality_proven:
            ins = sorted(str(a.arguments[0]) for a in m.symbols(shown=True) if a.name == "in")
            exs = sorted((str(a.arguments[0]), str(a.arguments[1])) for a in m.symbols(shown=True) if a.name == "ex")
            best.append((tuple(ins), tuple(exs), m.cost[0]))

    ctl.solve(on_model=on_model)
    return sorted(set(best))


def predict(h, f):
    ins, exs, _ = h
    return any(d in f and not any(e in f for dd, e in exs if dd == d) for d in ins)


def show(h):
    ins, exs, cost = h
    out = []
    for d in ins:
        e = [x for dd, x in exs if dd == d]
        out.append(f"positive(O) :- {d}(O)" + (", not ab(O)." if e else ".") +
                   "".join(f"   ab(O) :- {x}(O)." for x in e))
    return out or ["(empty hypothesis: nothing predicted positive)"]


def score(pred, truth):
    tp = sum(1 for p, t in zip(pred, truth) if p and t)
    fp = sum(1 for p, t in zip(pred, truth) if p and not t)
    fn = sum(1 for p, t in zip(pred, truth) if not p and t)
    tn = sum(1 for p, t in zip(pred, truth) if not p and not t)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    return prec, rec, (rec + spec) / 2, tp, fp, fn, tn


def task(title, examples, positives, feats, defaults, exceptions):
    print(f"== {title}")
    print(f"   {len(positives)} positive, {len(examples) - len(positives)} negative; "
          f"{len(defaults)} candidate defaults, {len(exceptions)} candidate exceptions")
    for label, exc in (("defaults only", []), ("defaults with exceptions", exceptions)):
        hyps = learn(examples, positives, feats, defaults, exc)
        h = hyps[0]
        p, r, b, tp, fp, fn, tn = score([predict(h, feats[o]) for o in examples], [o in positives for o in examples])
        print(f"\n   {label}: {len(hyps)} optimal hypothesis(es), cost {h[2]}")
        for line in show(h):
            print(f"      {line}")
        print(f"      on all examples: {tp} right, {fp} false alarms, {fn} missed; precision {p:.2f}, recall {r:.2f}")
        rng = random.Random(SEED)
        runs = []
        for _ in range(REPEATS):
            pos = [o for o in examples if o in positives]
            neg = [o for o in examples if o not in positives]
            rng.shuffle(pos)
            rng.shuffle(neg)
            pred, truth = [], []
            for k in range(FOLDS):
                test = pos[k::FOLDS] + neg[k::FOLDS]
                held = set(test)
                train = [o for o in examples if o not in held]
                hk = learn(train, positives & set(train), feats, defaults, exc)[0]
                pred += [predict(hk, feats[o]) for o in test]
                truth += [o in positives for o in test]
            runs.append(score(pred, truth)[:3])
        m = [statistics.mean(x) for x in zip(*runs)]
        s = [statistics.pstdev(x) for x in zip(*runs)]
        print(f"      cross-validated: precision {m[0]:.2f} ± {s[0]:.2f}, recall {m[1]:.2f} ± {s[1]:.2f}, "
              f"balanced accuracy {m[2]:.2f} ± {s[2]:.2f}")
    print()


def main():
    feats, label = load()
    allf = sorted({f for fs in feats.values() for f in fs})
    traps = [o for o in feats if label[o][0] == "trap"]
    verified = [o for o in feats if label[o][0] == "verified"]

    cand = [f for f in allf if f != "requirements"]
    task("A. criminal recruitment against the other documented offers (Mexico)",
         traps, {o for o in traps if label[o][1] == "criminal"}, feats, cand, cand)

    defaults = [f for f in allf if f not in SAMPLING and f not in JOBS]
    exceptions = [f for f in allf if f not in SAMPLING or f == "requirements"]
    task("B. documented offers against verified postings", traps + verified, set(traps), feats, defaults, exceptions)


if __name__ == "__main__":
    main()
