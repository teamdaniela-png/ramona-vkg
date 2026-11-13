#!/usr/bin/env python3
"""Rule learning over the documented offers (exploratory).

Learns conjunctive rules of the form  f1 AND f2 [AND f3] -> class  from two tables that are
already in the repository, and writes the example table, the rules and a results page.

  Task 1 (trap vs verified):  press-documented offers in Mexico (audit status "verificada")
                              against postings of verified employers.
  Task 2 (within press):      criminal-recruitment offers against the other documented offers.
                              Both sides come from the same source and the same coding pass.

Three learners, standard library only, fixed seed:
  * exhaustive search of conjunctions up to three conditions (support, confidence, lift,
    one-sided Fisher exact test, Benjamini-Hochberg correction),
  * a greedy sequential-covering rule list, scored by repeated stratified cross-validation,
  * a depth-3 decision tree (Gini) as baseline, scored the same way.

Usage:  python3 scripts/rule_learning/learn_rules.py
"""
import csv
import itertools
import math
import random
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRESS = ROOT / "data/real/press_offers_verified.csv"
LEGIT = ROOT / "data/real/legit_offers.csv"
OUT = ROOT / "data/processed/rule_learning"
DOC = ROOT / "docs/results/RULE_LEARNING_RESULTS.md"

SEED = 2026
MIN_SUPPORT = 5
FOLDS, REPEATS = 5, 20
WEEKS_PER_MONTH = 4.33

TYPE_A = ["sueldo_alto", "empleo_fuera_estado", "pago_adelantado", "horario_flexible",
          "traslado_pagado", "sin_experiencia", "contratacion_urgente"]
TYPE_B = ["rol_plausible_gancho", "pidio_datos_personales", "cita_edificio_multiusos",
          "empresa_sin_nombre", "pidio_ir_sola", "pidio_sin_identificacion", "whatsapp_sin_logo",
          "messenger_a_whatsapp", "cambio_ubicacion_ultimo_momento"]

JOB_PATTERNS = [
    ("job_security", r"guardia|seguridad|vigilan|escolta|custodi"),
    ("job_driver", r"chofer|conductor|taxi|repartidor|operador de (cami|trans|unidad)"),
    ("job_service", r"meser|hostess|edec|modelo|bar\b|bares|dama de compa|restaurant|cocin"),
    ("job_care_cleaning", r"limpieza|niñer|cuidador|cuidar|dom[eé]stic"),
    ("job_field_construction", r"agr[ií]col|jornal|alba[ñn]il|construc|f[aá]brica|almac[eé]n|granja|invernadero|agave|campo"),
    ("job_remote_tasks", r"likes|medio tiempo|desde casa|virtual|pedidos|en l[ií]nea|remoto"),
]
LEGIT_CATEGORY = {"guardia": "job_security", "chofer": "job_driver", "hostess": "job_service",
                  "mesero": "job_service"}
SOCIAL = {"facebook", "whatsapp", "tiktok", "telegram", "instagram"}


def flags(cell):
    return {f.strip() for f in re.split(r"[;|]", cell or "") if f.strip()}


def legit_verified(note):
    n = note.strip().lower()
    return n.startswith("marca_conocida") or n.startswith("existe")


def weekly_mxn(amount, currency, period):
    if not amount or currency != "MXN":
        return None
    if period == "semanal":
        return float(amount)
    if period == "mensual":
        return float(amount) / WEEKS_PER_MONTH
    return None


def load():
    press = [r for r in csv.DictReader(open(PRESS, encoding="utf-8")) if r["audit_status"] == "verificada"]
    legit = list(csv.DictReader(open(LEGIT, encoding="utf-8")))
    legit_pay = [float(r["sueldo_semanal_mxn_equiv"]) for r in legit
                 if r["sueldo_semanal_mxn_equiv"] and legit_verified(r["verificacion_empresa"])]
    pay_median = statistics.median(legit_pay)
    pay_max = max(legit_pay)
    rows = []
    for r in press:
        fl = flags(r["type_a_flags"]) | flags(r["type_b_flags"])
        title = r["job_title"].lower()
        w = weekly_mxn(r["pay_amount"], r["pay_currency"], r["pay_period"])
        target = r["target_profile"].lower()
        f = {k: int(k in fl) for k in TYPE_A + TYPE_B}
        for name, pat in JOB_PATTERNS:
            f[name] = int(bool(re.search(pat, title)))
        f["job_unspecified"] = int(not title or "no especificad" in title or "sin detalle" in title
                                   or "sin especificar" in title)
        f["pay_stated"] = int(bool(r["pay_amount"]))
        f["pay_weekly_over_1_5x_verified_median"] = int(w is not None and w > 1.5 * pay_median)
        f["pay_weekly_over_verified_max"] = int(w is not None and w > pay_max)
        f["requirements_stated"] = int(bool(r["requirements"].strip()))
        f["no_requirements_stated"] = 1 - f["requirements_stated"]
        f["via_social_or_messaging"] = int(r["platform"] in SOCIAL)
        f["target_women"] = int(bool(re.search(r"mujer|chica|jovencita|femenin|niñas", target)))
        f["target_minors"] = int(bool(re.search(r"menor|adolescen|niñ|estudiante|1[0-7] años", target)))
        f["target_young"] = int(bool(re.search(r"j[oó]ven", target)))
        rows.append({"id": r["offer_uid"], "source": "press", "mexico": int("MEX" in r["countries"]),
                     "criminal_recruitment": int(r["criminal_recruitment"] == "True"),
                     "verified_employer": 0, "weekly_mxn": w, **f})
    for r in legit:
        fl = flags(r["type_a_flags"]) | flags(r["type_b_flags"])
        w = float(r["sueldo_semanal_mxn_equiv"]) if r["sueldo_semanal_mxn_equiv"] else None
        f = {k: int(k in fl) for k in TYPE_A + TYPE_B}
        for name, _ in JOB_PATTERNS:
            f[name] = int(LEGIT_CATEGORY.get(r["categoria"].strip()) == name)
        f["job_unspecified"] = 0
        f["pay_stated"] = int(w is not None)
        f["pay_weekly_over_1_5x_verified_median"] = int(w is not None and w > 1.5 * pay_median)
        f["pay_weekly_over_verified_max"] = int(w is not None and w > pay_max)
        f["requirements_stated"] = int(bool(r["requisitos"].strip()))
        f["no_requirements_stated"] = 1 - f["requirements_stated"]
        f["via_social_or_messaging"] = 0
        f["target_women"] = f["target_minors"] = f["target_young"] = 0
        rows.append({"id": r["legit_id"], "source": "legit", "mexico": 1, "criminal_recruitment": 0,
                     "verified_employer": int(legit_verified(r["verificacion_empresa"])),
                     "weekly_mxn": w, **f})
    return rows, pay_median, pay_max


# ---------------------------------------------------------------- statistics
def fisher_greater(a, b, c, d):
    """P(X >= a) for the 2x2 table [[a, b], [c, d]] (rule fires / not, positive / negative)."""
    n1, n2, k = a + b, c + d, a + c
    total = math.comb(n1 + n2, k)
    return sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / total


def bh(pvalues):
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    q, prev = [0.0] * len(pvalues), 1.0
    for rank in range(len(order), 0, -1):
        i = order[rank - 1]
        prev = min(prev, pvalues[i] * len(pvalues) / rank)
        q[i] = prev
    return q


def covers(rule, x):
    return all(x[f] for f in rule)


def stats(rule, X, y):
    tp = sum(1 for x, t in zip(X, y) if t and covers(rule, x))
    fp = sum(1 for x, t in zip(X, y) if not t and covers(rule, x))
    return tp, fp


# ---------------------------------------------------------------- learners
def exhaustive(X, y, feats, target=1, max_len=3):
    P = sum(1 for t in y if t == target)
    N = len(y) - P
    yy = [int(t == target) for t in y]
    out = []
    for k in range(1, max_len + 1):
        for rule in itertools.combinations(feats, k):
            tp, fp = stats(rule, X, yy)
            if tp + fp < MIN_SUPPORT:
                continue
            conf = tp / (tp + fp)
            out.append({"rule": rule, "tp": tp, "fp": fp, "confidence": conf,
                        "coverage_of_class": tp / P, "lift": conf / (P / (P + N)),
                        "p": fisher_greater(tp, fp, P - tp, N - fp)})
    for r, q in zip(out, bh([r["p"] for r in out])):
        r["q"] = q
    return out


def minimal(rules):
    """Drop a rule when a strictly shorter rule over a subset of its conditions is at least as confident."""
    keep = []
    by = {r["rule"]: r for r in rules}
    for r in rules:
        dominated = False
        for k in range(1, len(r["rule"])):
            for sub in itertools.combinations(r["rule"], k):
                s = by.get(sub)
                if s and s["confidence"] >= r["confidence"]:
                    dominated = True
        if not dominated:
            keep.append(r)
    return keep


def covering(X, y, feats, max_len=3, min_precision=0.8):
    """Greedy rule list for class 1: grow a conjunction by Laplace precision, remove covered examples."""
    rest = list(zip(X, y))
    rules = []
    while sum(t for _, t in rest) >= MIN_SUPPORT:
        rule, best = (), -1.0
        while len(rule) < max_len:
            cand = None
            for f in feats:
                if f in rule:
                    continue
                r = rule + (f,)
                tp = sum(1 for x, t in rest if t and covers(r, x))
                fp = sum(1 for x, t in rest if not t and covers(r, x))
                if tp < MIN_SUPPORT:
                    continue
                score = (tp + 1) / (tp + fp + 2)
                if score > best + 1e-12:
                    best, cand = score, r
            if cand is None:
                break
            rule = cand
        if not rule:
            break
        tp = sum(1 for x, t in rest if t and covers(rule, x))
        fp = sum(1 for x, t in rest if not t and covers(rule, x))
        if tp / (tp + fp) < min_precision:
            break
        rules.append(rule)
        rest = [(x, t) for x, t in rest if not covers(rule, x)]
    return rules


def gini(pos, n):
    if n == 0:
        return 0.0
    p = pos / n
    return 2 * p * (1 - p)


def tree(X, y, feats, depth=3, min_leaf=5):
    n, pos = len(y), sum(y)
    if depth == 0 or pos in (0, n):
        return int(pos * 2 >= n)
    best, split = gini(pos, n) - 1e-9, None
    for f in feats:
        l = [i for i in range(n) if X[i][f]]
        if len(l) < min_leaf or n - len(l) < min_leaf:
            continue
        lp = sum(y[i] for i in l)
        g = (len(l) * gini(lp, len(l)) + (n - len(l)) * gini(pos - lp, n - len(l))) / n
        if g < best:
            best, split = g, f
    if split is None:
        return int(pos * 2 >= n)
    li = [i for i in range(n) if X[i][split]]
    ri = [i for i in range(n) if not X[i][split]]
    return (split, tree([X[i] for i in li], [y[i] for i in li], feats, depth - 1, min_leaf),
            tree([X[i] for i in ri], [y[i] for i in ri], feats, depth - 1, min_leaf))


def tree_predict(t, x):
    while isinstance(t, tuple):
        t = t[1] if x[t[0]] else t[2]
    return t


def cross_validate(X, y, fit, predict):
    rng = random.Random(SEED)
    acc = {"precision": [], "recall": [], "f1": [], "accuracy": [], "balanced_accuracy": []}
    for _ in range(REPEATS):
        pos = [i for i, t in enumerate(y) if t]
        neg = [i for i, t in enumerate(y) if not t]
        rng.shuffle(pos)
        rng.shuffle(neg)
        folds = [pos[k::FOLDS] + neg[k::FOLDS] for k in range(FOLDS)]
        tp = fp = fn = tn = 0
        for test in folds:
            held = set(test)
            tr = [i for i in range(len(y)) if i not in held]
            model = fit([X[i] for i in tr], [y[i] for i in tr])
            for i in test:
                p = predict(model, X[i])
                tp += p and y[i]
                fp += p and not y[i]
                fn += (not p) and y[i]
                tn += (not p) and not y[i]
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        spec = tn / (tn + fp) if tn + fp else 0.0
        acc["precision"].append(prec)
        acc["recall"].append(rec)
        acc["f1"].append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
        acc["accuracy"].append((tp + tn) / len(y))
        acc["balanced_accuracy"].append((rec + spec) / 2)
    return {k: (statistics.mean(v), statistics.pstdev(v)) for k, v in acc.items()}


# ---------------------------------------------------------------- reporting
def fmt_rule(rule):
    return " AND ".join(rule)


def pct(x):
    return f"{100 * x:.1f}%"


def rule_table(rules, pos_name, neg_name, limit):
    lines = [f"| Rule | {pos_name} covered | {neg_name} covered | Confidence | Lift | q (BH) |",
             "|---|---|---|---|---|---|"]
    for r in rules[:limit]:
        lines.append(f"| `{fmt_rule(r['rule'])}` | {r['tp']} ({pct(r['coverage_of_class'])}) | {r['fp']} | "
                     f"{pct(r['confidence'])} | {r['lift']:.2f} | {r['q']:.3g} |")
    return lines


def cv_table(results):
    lines = ["| Model | Precision | Recall | F1 | Balanced accuracy |", "|---|---|---|---|---|"]
    for name, m in results:
        lines.append(f"| {name} | " + " | ".join(f"{m[k][0]:.2f} ± {m[k][1]:.2f}"
                                                  for k in ("precision", "recall", "f1", "balanced_accuracy")) + " |")
    return lines


def tree_text(t, indent=0):
    pad = "    " * indent
    if not isinstance(t, tuple):
        return [f"{pad}-> {'positive' if t else 'negative'}"]
    return ([f"{pad}if {t[0]}:"] + tree_text(t[1], indent + 1) + [f"{pad}else:"] + tree_text(t[2], indent + 1))


def collapse(t):
    """Merge a split whose two branches predict the same class."""
    if not isinstance(t, tuple):
        return t
    a, b = collapse(t[1]), collapse(t[2])
    return a if (not isinstance(a, tuple) and a == b) else (t[0], a, b)


def run_task(X, y, feats, context=()):
    """`context` features describe the sample, not the offer: they may refine a rule but never stand alone,
    and the rule list and the tree do not use them."""
    rules = [r for r in exhaustive(X, y, feats) if not all(f in context for f in r["rule"])]
    for r, q in zip(rules, bh([r["p"] for r in rules])):
        r["q"] = q
    feats = [f for f in feats if f not in context]
    sig = sorted(minimal([r for r in rules if r["q"] < 0.05 and r["lift"] > 1]),
                 key=lambda r: (-r["confidence"], -r["tp"], len(r["rule"])))
    fit_list = lambda A, b: covering(A, b, feats)
    pred_list = lambda m, x: int(any(covers(r, x) for r in m))
    fit_tree = lambda A, b: tree(A, b, feats)
    majority = int(sum(y) * 2 >= len(y))
    cv = [("Rule list (sequential covering)", cross_validate(X, y, fit_list, pred_list)),
          ("Decision tree, depth 3", cross_validate(X, y, fit_tree, tree_predict)),
          ("Majority class", cross_validate(X, y, lambda A, b: majority, lambda m, x: m))]
    return {"tested": len(rules), "significant": sig, "list": covering(X, y, feats),
            "tree": collapse(tree(X, y, feats)), "cv": cv, "all": rules}


def flag_comparison(rows_pos, rows_neg):
    out = []
    for f in TYPE_A + TYPE_B:
        a = sum(r[f] for r in rows_pos)
        c = sum(r[f] for r in rows_neg)
        b, d = len(rows_pos) - a, len(rows_neg) - c
        p_more = fisher_greater(a, b, c, d)
        p_less = fisher_greater(c, d, a, b)
        if a + c < MIN_SUPPORT:
            verdict = "too rare to judge"
        elif p_more < 0.05:
            verdict = "separates (more frequent in documented cases)"
        elif p_less < 0.05:
            verdict = "reversed (more frequent in verified postings)"
        else:
            verdict = "does not separate in this sample"
        out.append({"flag": f, "type": "A" if f in TYPE_A else "B", "pos": a, "neg": c,
                    "pos_rate": a / len(rows_pos), "neg_rate": c / len(rows_neg),
                    "p_more": p_more, "p_less": p_less, "verdict": verdict})
    return out


def main():
    rows, pay_median, pay_max = load()
    OUT.mkdir(parents=True, exist_ok=True)
    feature_names = [k for k in rows[0] if k not in ("id", "source", "mexico", "criminal_recruitment",
                                                     "verified_employer", "weekly_mxn")]
    with open(OUT / "examples.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})

    # Task 1. Excluded: features fixed by how each side was sampled or coded (verified postings were captured
    # from job boards; press rarely reports requirements) and `rol_plausible_gancho`, which is defined by the
    # outcome (a plausible role *used as a hook*) and cannot hold of a verified posting.
    t1_excluded = {"via_social_or_messaging", "target_women", "target_minors", "target_young",
                   "requirements_stated", "no_requirements_stated", "job_unspecified", "pay_stated",
                   "rol_plausible_gancho"}
    jobs = tuple(name for name, _ in JOB_PATTERNS)
    t1_feats = [f for f in feature_names if f not in t1_excluded]
    pos1 = [r for r in rows if r["source"] == "press" and r["mexico"]]
    neg1 = [r for r in rows if r["source"] == "legit" and r["verified_employer"]]
    T1 = run_task(pos1 + neg1, [1] * len(pos1) + [0] * len(neg1), t1_feats, jobs)
    comp = flag_comparison(pos1, neg1)

    # Task 1b. Same comparison restricted to the job families that exist on both sides.
    shared = ("job_security", "job_driver", "job_service")
    pos1b = [r for r in pos1 if any(r[j] for j in shared)]
    neg1b = [r for r in neg1 if any(r[j] for j in shared)]
    T1b = run_task(pos1b + neg1b, [1] * len(pos1b) + [0] * len(neg1b), t1_feats, jobs)
    comp_b = flag_comparison(pos1b, neg1b)

    # Task 2. Within the press corpus (Mexico): criminal recruitment against the other documented offers.
    t2_feats = [f for f in feature_names if f not in ("requirements_stated", "no_requirements_stated")]
    press_mx = [r for r in rows if r["source"] == "press" and r["mexico"]]
    y2 = [r["criminal_recruitment"] for r in press_mx]
    T2 = run_task(press_mx, y2, t2_feats)
    T2neg = run_task(press_mx, [1 - t for t in y2], t2_feats)

    for name, T in (("task1_trap_vs_verified", T1), ("task1b_same_job_families", T1b),
                    ("task2_criminal_recruitment", T2), ("task2_other_offers", T2neg)):
        with open(OUT / f"rules_{name}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["rule", "n_conditions", "positives_covered", "negatives_covered", "confidence",
                        "coverage_of_class", "lift", "p_fisher", "q_bh"])
            for r in sorted(T["all"], key=lambda r: (r["q"], -r["confidence"])):
                w.writerow([fmt_rule(r["rule"]), len(r["rule"]), r["tp"], r["fp"], f"{r['confidence']:.4f}",
                            f"{r['coverage_of_class']:.4f}", f"{r['lift']:.4f}", f"{r['p']:.6g}", f"{r['q']:.6g}"])
    with open(OUT / "hand_flags_vs_data.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["scope", "flag", "type", "documented_cases", "verified_postings", "rate_cases",
                    "rate_verified", "p_more_in_cases", "p_more_in_verified", "verdict"])
        for scope, table in (("all_mexico", comp), ("same_job_families", comp_b)):
            for c in table:
                w.writerow([scope, c["flag"], c["type"], c["pos"], c["neg"], f"{c['pos_rate']:.4f}",
                            f"{c['neg_rate']:.4f}", f"{c['p_more']:.6g}", f"{c['p_less']:.6g}", c["verdict"]])

    pay_pos = [r["weekly_mxn"] for r in pos1 if r["weekly_mxn"] is not None]
    pay_neg = [r["weekly_mxn"] for r in neg1 if r["weekly_mxn"] is not None]

    L = []
    L += ["# Rule learning over the documented offers: first results", "",
          "Exploratory. Generated by `scripts/rule_learning/learn_rules.py` (standard library, seed 2026). "
          "Re-run the script to regenerate this page and the tables in `data/processed/rule_learning/`.", "",
          "## Question", "",
          "Which combinations of signals separate an offer documented as a trap from a posting of a verified "
          "employer, and do they agree with the hand-written red flags of RATR-O (Type A, classic; Type B, "
          "credible)?", "",
          "## Examples", "",
          f"- Documented offers: {sum(1 for r in rows if r['source'] == 'press')} press-documented offers with audit "
          f"status *verificada*; {len(pos1)} of them in Mexico, of which {sum(y2)} are criminal recruitment.",
          f"- Verified postings: {len(neg1)} postings of verified employers, all in Mexico "
          f"(of {sum(1 for r in rows if r['source'] == 'legit')} captured).",
          f"- {len(feature_names)} binary features: the 16 hand-written flags, job family, pay, requirements, "
          "channel and target (`data/processed/rule_learning/examples.csv`).",
          f"- Weekly pay in MXN is known for {len(pay_pos)} documented offers (median {statistics.median(pay_pos):,.0f}) "
          f"and {len(pay_neg)} verified postings (median {pay_median:,.0f}, maximum {pay_max:,.0f}). "
          f"Monthly amounts are divided by {WEEKS_PER_MONTH}.", "",
          "## Method", "",
          f"- Exhaustive search of conjunctions of up to three conditions, minimum {MIN_SUPPORT} offers covered. "
          "One-sided Fisher exact test per rule, Benjamini-Hochberg correction over all rules tested in the task; "
          "a rule is reported when q < 0.05 and no shorter rule over a subset of its conditions is at least as confident.",
          "- Greedy sequential-covering rule list (Laplace precision, at most three conditions, precision of at "
          "least 80% on the training fold).",
          "- Decision tree of depth 3 (Gini) and majority class as baselines.",
          f"- {FOLDS}-fold stratified cross-validation repeated {REPEATS} times; mean ± standard deviation over repetitions.", ""]

    L += ["## Task 1: documented offers against verified postings (Mexico)", "",
          f"{len(pos1)} documented offers, {len(neg1)} verified postings. {T1['tested']} rules tested, "
          f"{len(T1['significant'])} reported.", ""]
    L += rule_table(T1["significant"], "Documented", "Verified", 15) + [""]
    L += cv_table(T1["cv"]) + [""]
    L += ["The classes are unbalanced, so the majority baseline already has high precision; balanced accuracy is "
          "the figure to read.", "",
          "Job family is set by which postings were captured, so it never stands alone in a Task 1 rule and the "
          "rule list and the tree do not use it. `rol_plausible_gancho` is left out of the learning because it is "
          "defined by the outcome. `sueldo_alto` is the coder's reading of the source (high pay was promised); "
          "the `pay_weekly_*` features are its numeric counterpart, computed from the stated amount.", "",
          "Rule list learned on all examples:", ""]
    L += [f"{i}. `{fmt_rule(r)}`" for i, r in enumerate(T1["list"], 1)] or ["(no rule reached the thresholds)"]
    L += ["", "### Same job families on both sides", "",
          f"Security, driver and service jobs only: {len(pos1b)} documented offers, {len(neg1b)} verified postings. "
          f"{T1b['tested']} rules tested, {len(T1b['significant'])} reported.", ""]
    L += rule_table(T1b["significant"], "Documented", "Verified", 15) + [""]
    L += cv_table(T1b["cv"]) + [""]

    L += ["## The hand-written flags against the data", "",
          "Share of documented offers (Mexico) and of verified postings that carry each flag. "
          "Fisher exact test, uncorrected, one flag at a time.", "",
          "| Flag | Type | Documented | Verified | Reading |", "|---|---|---|---|---|"]
    for c in comp:
        L.append(f"| `{c['flag']}` | {c['type']} | {c['pos']} ({pct(c['pos_rate'])}) | {c['neg']} ({pct(c['neg_rate'])}) | {c['verdict']} |")
    L += ["", "Restricted to security, driver and service jobs:", "",
          "| Flag | Type | Documented | Verified | Reading |", "|---|---|---|---|---|"]
    for c in comp_b:
        L.append(f"| `{c['flag']}` | {c['type']} | {c['pos']} ({pct(c['pos_rate'])}) | {c['neg']} ({pct(c['neg_rate'])}) | {c['verdict']} |")

    L += ["", "## Task 2: criminal recruitment against the other documented offers (Mexico)", "",
          "Both classes come from the press corpus and from the same coding pass, so the comparison does not "
          "depend on how the verified postings were sampled.", "",
          f"{sum(y2)} criminal-recruitment offers, {len(y2) - sum(y2)} other documented offers. "
          f"{T2['tested']} rules tested.", "",
          f"Rules for criminal recruitment ({len(T2['significant'])} reported):", ""]
    L += rule_table(T2["significant"], "Criminal recruitment", "Other", 15) + [""]
    L += [f"Rules for the other documented offers ({len(T2neg['significant'])} reported):", ""]
    L += rule_table(T2neg["significant"], "Other", "Criminal recruitment", 15) + [""]
    L += cv_table(T2["cv"]) + ["", "Decision tree learned on all examples (positive = criminal recruitment):", "", "```"]
    L += tree_text(T2["tree"]) + ["```", ""]

    L += ["## Limits", "",
          "- The two sides of Task 1 were not observed the same way. A verified posting is read in full. A documented "
          "offer is known through what a journalist reported, so a missing flag means *not reported*, not *absent*. "
          "Flag rates on the documented side are lower bounds, and any rule built on the absence of a signal is unsafe.",
          "- The verified postings come from formal job boards and four job categories. Informal, word-of-mouth "
          "recruitment is not represented. Channel and target features are excluded from Task 1 for that reason.",
          f"- {len(neg1)} verified postings is a small negative class. Confidence values near 100% mean *no verified "
          "posting in this sample*, not *no legitimate posting*.",
          "- In Task 2, `pay_stated` means that the source reports an amount, not that the other offers had none.",
          "- Press coverage over-represents heavily reported cases; deduplication is conservative.",
          "- The rules are hypotheses about documented cases. They are not prevalence estimates and have not been "
          "tested on offers submitted by users.", ""]
    DOC.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {DOC.relative_to(ROOT)} and {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
