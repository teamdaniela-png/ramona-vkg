"""Execute mappings/ramona.r2rml.ttl against the SQLite copy of the seeds.

Written against the W3C R2RML recommendation, so that the graph a standard R2RML engine
would produce can be compared with the one the Ontop native mapping produces.

Usage: materialize_r2rml.py <mapping.r2rml.ttl> <database.db> <output.ttl>
"""
import re, sqlite3, sys, urllib.parse
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF

RR = "http://www.w3.org/ns/r2rml#"
def rr(t): return URIRef(RR + t)

mapfile, db, out = sys.argv[1], sys.argv[2], sys.argv[3]
m = Graph(); m.parse(mapfile, format="turtle")
con = sqlite3.connect(db); con.row_factory = sqlite3.Row

def one(s, p):
    for o in m.objects(s, p): return o
    return None

def fill(tpl, row, as_iri):
    out, i, n = [], 0, 0
    while i < len(tpl):
        if tpl[i] == "{":
            j = tpl.index("}", i); col = tpl[i+1:j]
            if col not in row.keys(): return None
            v = row[col]
            if v is None: return None
            out.append(urllib.parse.quote(str(v), safe="-._~") if as_iri else str(v))
            n += 1; i = j + 1
        else:
            out.append(tpl[i]); i += 1
    return "".join(out)

g = Graph()
tms = list(m.subjects(RDF.type, rr("TriplesMap")))
stats = []
for tm in tms:
    lt = one(m, URIRef(RR+"logicalTable")) if False else one(tm, rr("logicalTable"))
    sql = str(one(lt, rr("sqlQuery")))
    sql = re.sub(r"\b(ramona|public)\.", "", sql)
    rows = con.execute(sql).fetchall()
    sm = one(tm, rr("subjectMap"))
    stpl = str(one(sm, rr("template")))
    classes = list(m.objects(sm, rr("class")))
    poms = []
    for pom in m.objects(tm, rr("predicateObjectMap")):
        pred = one(pom, rr("predicate"))
        # rr:object <X> is the R2RML constant shortcut for rr:objectMap [ rr:constant <X> ]
        const = one(pom, rr("object"))
        om = one(pom, rr("objectMap"))
        if const is None and om is not None:
            const = one(om, rr("constant"))
        col = one(om, rr("column")) if om is not None else None
        tpl = one(om, rr("template")) if om is not None else None
        dt = one(om, rr("datatype")) if om is not None else None
        lang = one(om, rr("language")) if om is not None else None
        poms.append((pred, col, tpl, dt, lang, const))
    before = len(g)
    for row in rows:
        s = fill(stpl, row, True)
        if s is None: continue
        su = URIRef(s)
        for c in classes: g.add((su, RDF.type, c))
        for pred, col, tpl, dt, lang, const in poms:
            if const is not None:
                g.add((su, pred, const))
            elif tpl is not None:
                o = fill(str(tpl), row, True)
                if o is None: continue
                g.add((su, pred, URIRef(o)))
            else:
                if str(col) not in row.keys(): continue
                v = row[str(col)]
                if v is None: continue
                g.add((su, pred, Literal(str(v), datatype=dt, lang=str(lang) if lang else None)))
    stats.append((str(tm).split("#")[-1], len(rows), len(g) - before))

g.serialize(out, format="turtle")
print("triples maps:", len(tms), "| graph:", len(g))
empty = [s for s in stats if s[2] == 0]
print("triples maps that produced nothing:", len(empty))
for e in empty: print("   ", e[0], "rows=%d" % e[1])
