"""Type every individual by the domain and range axioms of the properties it takes part in,
and report any inferred class that lies outside the hierarchy of the class it is asserted in.

Usage: python scripts/offline_vkg/check_domain_range.py <abox.ttl>

An OWL domain or range is an axiom from which membership is inferred. A mapping that states a
property on the wrong kind of subject does not make the ontology inconsistent unless the two
classes are disjoint, but it does change the answers to queries. This check finds those cases.
"""
import collections, os, sys
from rdflib import Graph, RDF, RDFS, OWL, URIRef

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NS = "https://w3id.org/ratr-o#"
t = Graph(); t.parse(os.path.join(ROOT, "ontology", "ratr-o.ttl"))
L = lambda u: str(u)[len(NS):] if str(u).startswith(NS) else str(u)
cls = {s for s in t.subjects(RDF.type, OWL.Class) if str(s).startswith(NS)}
a = Graph(); a.parse(sys.argv[1])
sup=collections.defaultdict(set)
for s,_,o in t.triples((None,RDFS.subClassOf,None)):
    if isinstance(o,URIRef): sup[s].add(o)
def anc(c,seen=None):
    seen=seen if seen is not None else set()
    for p in sup.get(c,()):
        if p not in seen: seen.add(p); anc(p,seen)
    return seen
def root(c):
    A=anc(c)|{c}
    return {x for x in A if not sup.get(x)}
psup=collections.defaultdict(set)
for s,_,o in t.triples((None,RDFS.subPropertyOf,None)): psup[s].add(o)
def panc(p,seen=None):
    seen=seen if seen is not None else set()
    for q in psup.get(p,()):
        if q not in seen: seen.add(q); panc(q,seen)
    return seen
asserted=collections.defaultdict(set); inferred=collections.defaultdict(lambda: collections.defaultdict(set))
for s,_,c in a.triples((None,RDF.type,None)): asserted[s].add(c)
# individuals declared in the ontology itself keep the classes they are given there
for s,_,c in t.triples((None,RDF.type,None)):
    if c in cls: asserted[s].add(c)
for s,p,o in a:
    if p==RDF.type: continue
    for q in {p}|panc(p):
        for d in t.objects(q,RDFS.domain): inferred[s][d].add(L(p))
        if isinstance(o,URIRef):
            for r in t.objects(q,RDFS.range):
                if r in cls: inferred[o][r].add("^"+L(p))
conf=collections.Counter(); ex={}
for x,dd in inferred.items():
    roots_a=set()
    for c in asserted.get(x,()): roots_a|=root(c)
    for c,via in dd.items():
        rc=root(c)
        if roots_a and not (rc & roots_a):
            key=(tuple(sorted(L(r) for r in roots_a)), L(c), tuple(sorted(via))[0])
            conf[key]+=1; ex.setdefault(key,str(x))
        if not roots_a:
            key=("(untyped)", L(c), tuple(sorted(via))[0]); conf[key]+=1; ex.setdefault(key,str(x))
print("individuals typed outside the hierarchy of their asserted class: %d" % sum(conf.values()))
for k,n in conf.most_common(40): print("   %5d  asserted=%s  inferred=%s  via %s   e.g. %s"%(n,k[0],k[1],k[2],ex[k].replace("https://w3id.org/ratr-o/data/","")))
