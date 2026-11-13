"""Compare the answers of the reference queries from two runs, row by row.

Usage: python3 scripts/ontop/compare_answers.py <dir-ontop> <dir-offline>

Each directory holds one tab-separated file per query, written by
scripts/ontop/run_queries.py --dump and scripts/offline_vkg/run_queries.py --dump.
Rows are compared as multisets, numbers by value to six decimal places.
Exits with status 1 if any query differs.
"""
import glob, os, re, sys
from collections import Counter
from decimal import Decimal, InvalidOperation


def cell(v):
    v = v.strip()
    if v in ("true", "false"):
        return v
    try:
        return "%.6f" % Decimal(v)
    except InvalidOperation:
        return v


def load(path):
    with open(path, encoding="utf-8") as f:
        return Counter(tuple(cell(v) for v in line.rstrip("\n").split("\t")) for line in f if line.strip("\n"))


def main():
    a, b = sys.argv[1:3]
    names = sorted({os.path.basename(p) for d in (a, b) for p in glob.glob(os.path.join(d, "Q*.tsv"))},
                   key=lambda n: int(re.match(r"Q(\d+)", n).group(1)))
    differ = []
    for n in names:
        pa, pb = os.path.join(a, n), os.path.join(b, n)
        if not (os.path.exists(pa) and os.path.exists(pb)):
            differ.append(n[:-4]); print("%-44s missing in one run" % n[:-4]); continue
        ra, rb = load(pa), load(pb)
        if ra != rb:
            differ.append(n[:-4])
            print("%-44s %d rows against %d; only in the first: %d, only in the second: %d"
                  % (n[:-4], sum(ra.values()), sum(rb.values()), sum((ra - rb).values()), sum((rb - ra).values())))
            for label, d in (("first ", ra - rb), ("second", rb - ra)):
                for row in list(d)[:3]:
                    print("    %s: %s" % (label, " | ".join(row)[:200]))
    print("queries compared: %d   with the same answers: %d" % (len(names), len(names) - len(differ)))
    if differ:
        sys.exit(1)


if __name__ == "__main__":
    main()
