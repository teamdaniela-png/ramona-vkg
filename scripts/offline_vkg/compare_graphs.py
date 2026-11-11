"""Compare two RDF graphs triple for triple. Usage: compare_graphs.py <a.ttl> <b.ttl>"""
import sys
from rdflib import Graph
a = Graph(); a.parse(sys.argv[1]); b = Graph(); b.parse(sys.argv[2])
sa, sb = set(a), set(b)
print("%s: %d triples | %s: %d triples | only in first: %d | only in second: %d"
      % (sys.argv[1], len(sa), sys.argv[2], len(sb), len(sa - sb), len(sb - sa)))
sys.exit(0 if sa == sb else 1)
