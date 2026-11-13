"""Run the reference queries over a materialised ABox plus the TBox.

Usage: python scripts/offline_vkg/run_queries.py <abox.ttl> [--dump DIR]

With --dump, the answers of every query are also written to DIR, one tab-separated file per
query and without the final LIMIT, so that they can be compared with the answers of the Ontop
endpoint (scripts/ontop/compare_answers.py).

The TBox is applied as the subclass, subproperty and inverse closure, which is what Ontop
applies at query-rewrite time. Two things rdflib 7.6 does differently from RDF 1.1 and from
Ontop are neutralised here so that the row counts are the ones the VKG gives: a simple
literal and an xsd:string literal are treated as the same term, and `?x IN (...)` is expanded
into equalities. The query files themselves are read unchanged.
"""
import glob, io, os, re, signal, sys, time
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Literal
from rdflib.namespace import XSD

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# rdflib orders the triple patterns of a basic graph pattern once, by how many terms each has
# bound before evaluation starts. Two patterns such as `?a rdf:type :X` and `?b rdf:type :Y`
# both come first and are evaluated as a cross product. The join order used here is chosen
# step by step instead: at each step, the pattern with the fewest unbound terms given what is
# already bound, preferring one that shares a variable with the bindings so far. The answers
# are the same; only the order of evaluation differs.
import rdflib.plugins.sparql as _sparql
from rdflib.plugins.sparql.sparql import AlreadyBound
from rdflib.term import Variable, BNode

def _bgp(ctx, triples):
    if not triples:
        yield ctx.solution()
        return
    def cost(t):
        unbound = [n for n in t if isinstance(n, (Variable, BNode)) and ctx[n] is None]
        joined = any(isinstance(n, (Variable, BNode)) and ctx[n] is not None for n in t)
        return (len(set(unbound)), 0 if joined else 1)
    i = min(range(len(triples)), key=lambda k: cost(triples[k]))
    s, p, o = triples[i]
    rest = triples[:i] + triples[i + 1:]
    _s, _p, _o = ctx[s], ctx[p], ctx[o]
    for ss, sp, so in ctx.graph.triples((_s, _p, _o)):
        c = ctx.push() if None in (_s, _p, _o) else ctx
        if _s is None:
            c[s] = ss
        try:
            if _p is None:
                c[p] = sp
        except AlreadyBound:
            continue
        try:
            if _o is None:
                c[o] = so
        except AlreadyBound:
            continue
        for x in _bgp(c, rest):
            yield x

def _eval(ctx, part):
    if part.name == "BGP":
        return _bgp(ctx, list(part.triples))
    raise NotImplementedError()

_sparql.CUSTOM_EVALS["stepwise_join_order"] = _eval

ABOX = sys.argv[1]
DUMP = sys.argv[sys.argv.index("--dump") + 1] if "--dump" in sys.argv else None
if DUMP: os.makedirs(DUMP, exist_ok=True)
g = Graph()
g.parse("ontology/ratr-o.ttl", format="turtle")
g.parse(ABOX, format="turtle")
print("ontology+abox triples:", len(g))

# RDF 1.1: a simple literal and an xsd:string-typed literal are the same term.
_n = 0
for s_, p_, o_ in list(g.triples((None, None, None))):
    if isinstance(o_, Literal) and o_.datatype == XSD.string:
        g.remove((s_, p_, o_)); g.add((s_, p_, Literal(str(o_)))); _n += 1
print("xsd:string literals canonicalised:", _n)

# Minimal QL-relevant closure, which is what Ontop applies at query-rewrite time.
sup = {}
for s, _, o in g.triples((None, RDFS.subClassOf, None)):
    if isinstance(o, URIRef): sup.setdefault(s, set()).add(o)
def anc(c, seen=None):
    seen = seen or set()
    for p in sup.get(c, ()):
        if p not in seen:
            seen.add(p); anc(p, seen)
    return seen
add = []
for s, _, c in g.triples((None, RDF.type, None)):
    for d in anc(c): add.append((s, RDF.type, d))
for t in add: g.add(t)
psup = {}
for s, _, o in g.triples((None, RDFS.subPropertyOf, None)):
    psup.setdefault(s, set()).add(o)
for p, parents in psup.items():
    for s, _, o in list(g.triples((None, p, None))):
        for q in parents: g.add((s, q, o))
for p, _, q in list(g.triples((None, OWL.inverseOf, None))):
    for s, _, o in list(g.triples((None, p, None))): g.add((o, q, s))
    for s, _, o in list(g.triples((None, q, None))): g.add((o, p, s))
print("after closure:", len(g))

class TO(Exception): pass
def h(*a): raise TO()
signal.signal(signal.SIGALRM, h)

rows_out, empties, errors = [], [], []
for f in sorted(glob.glob("queries/*.rq"), key=lambda x: int(re.match(r"Q(\d+)", os.path.basename(x)).group(1))):
    name = os.path.basename(f)[:-3]
    q = io.open(f, encoding="utf-8").read()
    # Expand `?x IN (a, b)` into `(?x = a || ?x = b)`.
    def _expand(m):
        var, items = m.group(1), m.group(2)
        parts, buf, inq = [], [], False
        for ch in items:
            if ch == '"': inq = not inq
            if ch == "," and not inq:
                parts.append("".join(buf)); buf = []
            else:
                buf.append(ch)
        if "".join(buf).strip(): parts.append("".join(buf))
        parts = [x.strip() for x in parts if x.strip()]
        return "(" + " || ".join("%s = %s" % (var, x) for x in parts) + ")"
    q2 = re.sub(r"(\?\w+)\s+IN\s*\(([^()]*)\)", _expand, q)
    q2 = q2.replace("^^xsd:string", "").replace("^^<http://www.w3.org/2001/XMLSchema#string>", "")
    rewritten = q2 != q
    q = q2
    t0 = time.time()
    signal.alarm(60)
    try:
        res = list(g.query(q))
        # A query with no OPTIONAL and no UNION binds every projected variable. rdflib returns
        # rows with unbound variables when a group is joined with an empty subquery; a
        # conformant engine returns none, so those rows are not counted.
        if not re.search(r"\b(OPTIONAL|UNION)\b", q):
            res = [r for r in res if all(v is not None for v in r)]
        signal.alarm(0)
        dt = time.time() - t0
        if DUMP:
            full = list(g.query(re.sub(r"\bLIMIT\s+\d+\s*$", "", q)))
            if not re.search(r"\b(OPTIONAL|UNION)\b", q):
                full = [r for r in full if all(v is not None for v in r)]
            with io.open(os.path.join(DUMP, name + ".tsv"), "w", encoding="utf-8") as out:
                for r in full:
                    out.write("\t".join("" if v is None else str(v).replace("\t", " ").replace("\n", " ") for v in r) + "\n")
        rows_out.append((name, len(res), round(dt, 2), "IN-rewritten" if rewritten else ""))
        if len(res) == 0: empties.append(name)
    except TO:
        signal.alarm(0); errors.append((name, "not finished in 60 s by the in-memory runner"))
    except Exception as e:
        signal.alarm(0); errors.append((name, type(e).__name__ + ": " + str(e)[:110]))

print("\n%-44s %8s %7s" % ("query", "rows", "sec"))
for n, r, d, w in rows_out: print("%-44s %8d %7.2f  %s" % (n, r, d, w))
print("\nexecuted: %d of %d   with rows: %d" % (len(rows_out), len(rows_out) + len(errors), len(rows_out) - len(empties)))
if errors: print("\nNOT FINISHED:"); [print("  %-44s %s" % e) for e in errors]

# Compare with the row counts published in docs/validation/QUERY_EXECUTION_REPORT.md.
report = os.path.join(ROOT, "docs", "validation", "QUERY_EXECUTION_REPORT.md")
published = {m[0]: (int(m[1]), int(m[2])) for m in
             re.findall(r"^\| `(Q\d+_\w+)` \| (\d+) \| (\d+) \|", open(report, encoding="utf-8").read(), re.M)}
got = {n: r for n, r, d, w in rows_out}
for column, state in ((0, "seeds"), (1, "seeds plus CTDC")):
    if got == {n: v[column] for n, v in published.items()}:
        print("row counts equal the published ones (%s)" % state)
        break
else:
    column = 1 if any(str(o).startswith("https://w3id.org/ratr-o/data/victim/") for o in g.subjects(RDF.type, URIRef("https://w3id.org/ratr-o#Victim"))) else 0
    diff = sorted(n for n in set(got) | set(published) if got.get(n) != published.get(n, (None, None))[column])
    print("row counts differ from the published ones: " + ", ".join(diff))
    sys.exit(1)
