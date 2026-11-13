"""Compare the graph Ontop materialises with the graph of the offline validation.

Usage: python3 scripts/ontop/compare_with_offline.py <ontop.nt> <offline_abox.ttl>

<ontop.nt> is the output of `ontop materialize` over the running database; <offline_abox.ttl>
is the ABox that scripts/offline_vkg/run_all.sh writes. Ontop's output contains the asserted
triples and those entailed by the ontology, so the offline ABox is closed under the subclass,
subproperty, inverse, domain and range axioms before the comparison. Numeric literals are
compared by value, and a simple literal and an xsd:string literal as the same term.
Exits with status 1 if the two graphs differ.
"""
import os, sys
from decimal import Decimal, InvalidOperation
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Literal
from rdflib.namespace import XSD

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NUMERIC = {XSD.integer, XSD.decimal, XSD.double, XSD.float, XSD.int, XSD.long, XSD.nonNegativeInteger}


def norm(o):
    if isinstance(o, Literal):
        dt = o.datatype
        if dt in NUMERIC:
            try:
                return ("number", Decimal(str(o)).normalize())
            except InvalidOperation:
                pass
        return ("literal", str(o), None if dt == XSD.string else dt, o.language)
    return o


def triples(g):
    return {(s, p, norm(o)) for s, p, o in g}


def closure(abox, tbox):
    def table(pred, symmetric=False):
        t = {}
        for s, _, o in tbox.triples((None, pred, None)):
            if isinstance(o, URIRef):
                t.setdefault(s, set()).add(o)
                if symmetric:
                    t.setdefault(o, set()).add(s)
        return t
    sub, subp = table(RDFS.subClassOf), table(RDFS.subPropertyOf)
    for k, v in table(OWL.equivalentClass, True).items():
        sub.setdefault(k, set()).update(v)
    for k, v in table(OWL.equivalentProperty, True).items():
        subp.setdefault(k, set()).update(v)
    inv, dom, rng = table(OWL.inverseOf, True), table(RDFS.domain), table(RDFS.range)
    objprop = set(tbox.subjects(RDF.type, OWL.ObjectProperty))
    out, todo = set(abox), list(abox)

    def add(t):
        if t not in out:
            out.add(t)
            todo.append(t)
    while todo:
        s, p, o = todo.pop()
        if p == RDF.type:
            for c in sub.get(o, ()):
                add((s, p, c))
            continue
        for q in subp.get(p, ()):
            add((s, q, o))
        for c in dom.get(p, ()):
            add((s, RDF.type, c))
        if p in objprop and isinstance(o, URIRef):
            for q in inv.get(p, ()):
                add((o, q, s))
            for c in rng.get(p, ()):
                add((o, RDF.type, c))
    return out


def main():
    ontop_path, offline_path = sys.argv[1:3]
    tbox = Graph().parse(os.path.join(ROOT, "ontology", "ratr-o.ttl"), format="turtle")
    ontop = triples(Graph().parse(ontop_path, format="nt")) - triples(tbox)
    offline = triples(Graph().parse(offline_path, format="turtle"))
    closed = closure(offline, tbox)
    print("offline ABox: %d triples | closed under the ontology: %d" % (len(offline), len(closed)))
    print("Ontop materialisation, ontology triples left out: %d" % len(ontop))
    missing, extra = closed - ontop, ontop - closed
    print("asserted offline, absent from Ontop: %d" % len(offline - ontop))
    print("entailed offline, absent from Ontop: %d" % len(missing - offline))
    print("in Ontop, not entailed offline: %d" % len(extra))
    for label, group in (("absent from Ontop", missing), ("only in Ontop", extra)):
        for t in sorted(group, key=str)[:10]:
            print("  %s: %s" % (label, " ".join(str(x) for x in t)))
    if missing or extra:
        sys.exit(1)
    print("the two graphs are the same")


if __name__ == "__main__":
    main()
