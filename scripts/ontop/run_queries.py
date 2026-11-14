"""Run the reference queries against the Ontop SPARQL endpoint and compare the row counts
with the published ones.

Usage: python3 scripts/ontop/run_queries.py [--state seeds|sample|full] [--report FILE] [--dump DIR]

  seeds   what `docker compose up -d` loads on a fresh volume (the default)
  sample  the seeds plus one CTDC victim in forty and the UNODC figures of the Americas, the
          state of the offline validation
  full    the seeds plus the 257,969 victim records of CTDC and the 65,398 figures of UNODC

The endpoint is read from the ENDPOINT environment variable and defaults to
http://localhost:8080/sparql. With --dump, the answers of every query are also written to DIR,
one tab-separated file per query and without the final LIMIT. The published counts are read from
docs/validation/ONTOP_EXECUTION_REPORT.md. Exits with status 1 on any difference.
"""
import argparse, csv, glob, io, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENDPOINT = os.environ.get("ENDPOINT", "http://localhost:8080/sparql")
STATES = ["seeds", "sample", "full"]
LABEL = {"seeds": "seeds", "sample": "seeds plus the CTDC and UNODC sample", "full": "seeds plus CTDC and UNODC"}


def published(state):
    col = STATES.index(state) + 2
    out = {}
    with open(os.path.join(ROOT, "docs/validation/ONTOP_EXECUTION_REPORT.md")) as f:
        for line in f:
            m = re.match(r"\| `(Q\d+_[^`]+)` \| (\d+) \| (\d+) \| (\d+) \|", line)
            if m:
                out[m.group(1)] = int(m.group(col))
    return out


def run(path, strip_limit=False):
    query = open(path).read()
    if strip_limit:
        query = re.sub(r"\bLIMIT\s+\d+\s*$", "", query)
    req = urllib.request.Request(
        ENDPOINT,
        data=urllib.parse.urlencode({"query": query}).encode(),
        headers={"Accept": "text/csv"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        body = r.read().decode("utf-8")
    rows = list(csv.reader(io.StringIO(body)))
    if strip_limit:
        return rows[1:]
    return max(len(rows) - 1, 0), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", choices=STATES, default="seeds")
    ap.add_argument("--report")
    ap.add_argument("--dump")
    a = ap.parse_args()
    expected = published(a.state)
    files = sorted(glob.glob(os.path.join(ROOT, "queries", "Q*.rq")),
                   key=lambda p: int(re.match(r"Q(\d+)", os.path.basename(p)).group(1)))
    results, differ, failed = [], [], []
    for p in files:
        name = os.path.basename(p)[:-3]
        try:
            n, secs = run(p)
            if a.dump:
                os.makedirs(a.dump, exist_ok=True)
                with open(os.path.join(a.dump, name + ".tsv"), "w", encoding="utf-8") as f:
                    for row in run(p, strip_limit=True):
                        f.write("\t".join(v.replace("\t", " ").replace("\n", " ").replace("\r", " ") for v in row) + "\n")
        except Exception as e:
            failed.append(name)
            print(f"{name:45s} FAILED  {e}")
            continue
        results.append((name, n, expected.get(name), secs))
        mark = "" if n == expected.get(name) else f"   published: {expected.get(name)}"
        if mark:
            differ.append(name)
        print(f"{name:45s} {n:6d}  {secs:6.2f}s{mark}")
    with_rows = sum(1 for _, n, _, _ in results if n)
    print(f"executed: {len(results)} of {len(files)}  with rows: {with_rows}")
    if a.report:
        with open(a.report, "w") as f:
            for name, n, e, secs in results:
                f.write(f"{name}\t{n}\t{secs:.2f}\n")
    if failed or differ:
        print("differences:", ", ".join(failed + differ))
        sys.exit(1)
    print("row counts equal the published ones (%s)" % LABEL[a.state])


if __name__ == "__main__":
    main()
