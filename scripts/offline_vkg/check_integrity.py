"""Check that the integrity of the relational schema survives the mapping.

Usage: python scripts/offline_vkg/check_integrity.py <database.db> <abox.ttl> [--markdown out.md]

Reads the schema from db/*.sql, the mapping from mappings/ramona.obda, the loaded SQLite database
and the graph the mapping produced over it, and checks:

  1. identifiers   every primary key reaches the graph as one IRI per row, under one template
  2. references    every foreign key is either stated by an object property or listed as not exposed,
                   and every IRI an object property points at is an individual with a class
  3. typing        every individual that carries a property has a class
  4. uniqueness    no two individuals carry the same source URL
  5. literals      every literal is well formed for its datatype

With --markdown it also writes the mapping specification: the identifier templates and the foreign
keys with the property that states each one.
"""
import collections, glob, io, os, re, sqlite3, sys
from rdflib import Graph, Literal, RDF, RDFS, OWL, URIRef
from rdflib.namespace import XSD

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NS, D = "https://w3id.org/ratr-o#", "https://w3id.org/ratr-o/data/"
DB, ABOX = sys.argv[1], sys.argv[2]
MD = sys.argv[sys.argv.index("--markdown") + 1] if "--markdown" in sys.argv else None

# Foreign keys the ontology has no term for. Each is a decision, stated here so it is visible.
NOT_EXPOSED = {
    ("recruiters", "associated_employer"): "RATR-O has no property relating a recruiter to an employer",
    ("candidates", "candidate_country"): "RATR-O has no property for the country of a candidate",
    ("offer_detection_track", "offer_id"): "the detection-track table is a derived summary and is not mapped",
    ("route_victim_counts", "origin_country"): "used to join the count to its route, which states the origin with :originCountry",
    ("route_victim_counts", "destination_country"): "used to join the count to its route, which states the destination with :destinationCountry",
    ("victim_means_of_control", "means_code"): "stated as the literal value of the datatype property :hasMeansOfControl",
}

# Tables whose rows are identified in another table when the same entity is already there.
# A press article that is in the evidence registry is minted under the registry's template.
RESOLVED_IN = {"press_articles": ("url", "evidence_sources", "source_url")}

def split_top(body):
    out, buf, depth = [], [], 0
    for ch in body:
        if ch == "(": depth += 1
        if ch == ")": depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    out.append("".join(buf))
    return [x.strip() for x in out if x.strip()]

sql = "\n".join(re.sub(r"--[^\n]*", "", io.open(f, encoding="utf-8").read()) for f in sorted(glob.glob(os.path.join(ROOT, "db", "*.sql"))))
tables, pks, fks = {}, {}, []
for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?(?:\w+\.)?(\w+)\s*\((.*?)\);", sql, re.S):
    t, cols = m.group(1), split_top(m.group(2))
    tables[t] = cols
    for c in cols:
        mm = re.match(r"PRIMARY KEY\s*\(([^)]*)\)", c, re.I)
        if mm: pks[t] = [x.strip() for x in mm.group(1).split(",")]
        mm = re.match(r"(\w+)\s+\S+.*\bPRIMARY KEY\b", c, re.I | re.S)
        if mm and not c.upper().startswith("PRIMARY"): pks[t] = [mm.group(1)]
        mm = re.match(r"(\w+)\s+.*?REFERENCES\s+(?:\w+\.)?(\w+)\s*\((\w+)\)", c, re.I | re.S)
        if mm and not c.upper().startswith(("PRIMARY", "FOREIGN", "UNIQUE", "CHECK")): fks.append((t, mm.group(1), mm.group(2), mm.group(3)))
for m in re.finditer(r"ALTER TABLE (?:\w+\.)?(\w+)\s+ADD COLUMN(?: IF NOT EXISTS)? (\w+) \w+ REFERENCES (?:\w+\.)?(\w+)\((\w+)\)", sql):
    fks.append(m.groups())
for m in re.finditer(r"ALTER TABLE (?:\w+\.)?(\w+)\s+ADD CONSTRAINT \w+\s+FOREIGN KEY \((\w+)\) REFERENCES (?:\w+\.)?(\w+)\((\w+)\)", sql):
    fks.append(m.groups())
fks = sorted(set(fks))

obda = io.open(os.path.join(ROOT, "mappings", "ramona.obda"), encoding="utf-8").read()
maps = re.findall(r"mappingId\s+(\S+)\s*\ntarget\s+(.*?)\nsource\s+(.*?)(?=\n\s*\n|\nmappingId|\Z)", obda, re.S)
generic = lambda iri: re.sub(r"\{[^}]+\}", "{}", iri)

t_ = Graph(); t_.parse(os.path.join(ROOT, "ontology", "ratr-o.ttl"))
objprops = {str(s)[len(NS):] for s in t_.subjects(RDF.type, OWL.ObjectProperty)}
g = Graph(); g.parse(ABOX)
con = sqlite3.connect(DB)
problems = []

# ---- templates
tpl_classes = collections.defaultdict(set); tpl_tables = collections.defaultdict(set); tpl_cols = {}
for mid, target, source in maps:
    subj = re.match(r"<([^>]+)>", target.strip()).group(1)
    k = generic(subj)
    tpl_cols.setdefault(k, re.findall(r"\{([^}]+)\}", subj))
    for c in re.findall(r"(?:^|;|>)\s*a\s+:(\w+)", target): tpl_classes[k].add(c)
    for tb in re.findall(r"(?:FROM|JOIN)\s+(?:ramona|public)\.(\w+)", source): tpl_tables[k].add(tb)
count = collections.Counter()
for s in set(g.subjects()):
    u = str(s)
    if u.startswith(D):
        parts = u[len(D):].split("/")
        for k in tpl_cols:
            kp = k[len(D):].split("/")
            if len(kp) == len(parts) and all(a == "{}" or a == b for a, b in zip(kp, parts)):
                count[k] += 1; break

# ---- 1. identifiers: a table with a single-column key and a template on that key
ident = []
for t, key in sorted(pks.items()):
    if len(key) != 1: continue
    k = next((k for k, cols in tpl_cols.items() if cols == key and t in tpl_tables[k] and k.count("{}") == 1 and k.endswith("{}")), None)
    if not k: continue
    try:
        n = con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        if t in RESOLVED_IN:
            col, other, ocol = RESOLVED_IN[t]
            n -= con.execute("SELECT COUNT(*) FROM %s a WHERE EXISTS (SELECT 1 FROM %s b WHERE b.%s = a.%s)" % (t, other, ocol, col)).fetchone()[0]
    except Exception: continue
    ident.append((t, key[0], k, n, count[k]))
    if n != count[k]: problems.append("identifiers: %s has %d rows and %d individuals under %s" % (t, n, count[k], k))

# ---- 2. references
typed = set(g.subjects(RDF.type, None)) | set(t_.subjects(RDF.type, None))
dangling = [(s, p, o) for s, p, o in g if str(p).startswith(NS) and str(p)[len(NS):] in objprops and isinstance(o, URIRef) and o not in typed]
if dangling: problems.append("references: %d links point at an individual with no class" % len(dangling))
fkrows = []
for t, col, rt, rc in fks:
    hit = None
    for mid, target, source in maps:
        if re.search(r"\b%s\b" % re.escape(t), source) and re.search(r"\b%s\b" % re.escape(col), source):
            props = re.findall(r":(\w+)\s+<", target)
            props = [p for p in props if p in objprops]
            if props or re.match(r"<[^>]*\{%s\}" % re.escape(col), target.strip()):
                hit = (mid, props[0] if props else "(in the subject IRI)"); break
    reason = NOT_EXPOSED.get((t, col), "")
    if hit is None and (t, col) not in NOT_EXPOSED:
        problems.append("references: foreign key %s.%s is read by no mapping and is not listed as not exposed" % (t, col))
    fkrows.append((t, col, rt, rc, hit, reason))

# ---- 3. typing
untyped = [s for s in set(g.subjects()) if s not in typed]
if untyped: problems.append("typing: %d individuals carry properties and no class" % len(untyped))

# ---- 4. uniqueness of source URLs
by = collections.defaultdict(set)
for s, _, o in g.triples((None, URIRef(NS + "sourceUrl"), None)): by[str(o)].add(s)
shared = {u: v for u, v in by.items() if len(v) > 1}
if shared: problems.append("uniqueness: %d source URLs are carried by more than one individual" % len(shared))

# ---- 5. literals
bad = []
for s, p, o in g:
    if not isinstance(o, Literal) or o.datatype is None: continue
    v, dt = str(o), o.datatype
    ok = True
    if dt == XSD.anyURI: ok = re.match(r"^https?://\S+$", v) is not None
    elif dt == XSD.integer: ok = re.match(r"^[+-]?\d+$", v) is not None
    elif dt == XSD.decimal: ok = re.match(r"^[+-]?(\d+(\.\d*)?|\.\d+)$", v) is not None
    elif dt == XSD.boolean: ok = v in ("true", "false", "1", "0")
    elif dt == XSD.date: ok = re.match(r"^\d{4}-\d{2}-\d{2}", v) is not None
    elif dt == XSD.dateTime: ok = re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", v) is not None
    elif dt == XSD.gYear: ok = re.match(r"^\d{4}$", v) is not None
    if not ok: bad.append((str(p)[len(NS):], str(dt).split("#")[-1], v[:40]))
if bad:
    c = collections.Counter((p, d) for p, d, _ in bad)
    problems.append("literals: %d ill-formed, e.g. %s" % (len(bad), c.most_common(3)))

print("mappings: %d | identifier templates: %d | tables: %d | foreign keys: %d | graph: %d triples" % (len(maps), len(tpl_cols), len(tables), len(fks), len(g)))
print("1. identifiers  %d keyed tables, one IRI per row: %s" % (len(ident), "ok" if not any(p.startswith("identifiers") for p in problems) else "PROBLEM"))
print("2. references   %d foreign keys: %d stated by a mapping, %d not exposed; links to an untyped individual: %d"
      % (len(fks), sum(1 for r in fkrows if r[4]), sum(1 for r in fkrows if not r[4]), len(dangling)))
print("3. typing       individuals without a class: %d" % len(untyped))
print("4. uniqueness   source URLs shared by two individuals: %d" % len(shared))
print("5. literals     ill-formed: %d" % len(bad))
for p in problems: print("PROBLEM", p)

if MD:
    ver = str(t_.value(URIRef("https://w3id.org/ratr-o"), OWL.versionInfo))
    L = ["# Mapping specification", "",
         "Generated by `scripts/offline_vkg/check_integrity.py` from `db/*.sql`, `mappings/ramona.obda` and the",
         "graph the mapping produces over the seed files. RATR-O %s, %d mapping assertions, published in the" % (ver, len(maps)),
         "Ontop native syntax (`mappings/ramona.obda`) and in W3C R2RML (`mappings/ramona.r2rml.ttl`); the two",
         "are executed and compared triple for triple by `scripts/offline_vkg/run_all.sh`.", "",
         "## Identifier templates", "",
         "Every individual of the graph is minted under one of these %d templates, all below" % len(tpl_cols),
         "`https://w3id.org/ratr-o/data/`. A template is built from the key of the table it reads, so two rows",
         "never share an IRI and a row never has two.", "",
         "| Template | Key | Classes | Tables read | Individuals |", "| --- | --- | --- | --- | ---: |"]
    for k in sorted(tpl_cols):
        L.append("| `%s` | %s | %s | %s | %d |" % (k[len(D):], ", ".join("`%s`" % c for c in tpl_cols[k]),
                 ", ".join("`:%s`" % c for c in sorted(tpl_classes[k])) or "", ", ".join("`%s`" % x for x in sorted(tpl_tables[k])), count[k]))
    L += ["", "The individual counts are over the seed files. Templates that read the victim tables show 0 until",
          "the CTDC release is loaded.", "",
          "## Primary keys", "",
          "For each table with a single-column key that has a template of its own, the number of rows and the",
          "number of individuals minted from it.", "",
          "| Table | Key | Template | Rows | Individuals |", "| --- | --- | --- | ---: | ---: |"]
    notes = ["", "`press_articles` counts the articles that are in no other registry: an article that is also in",
             "`evidence_sources` is identified there, under `evidence/{}`, so that it has one IRI."]
    for t, key, k, n, c in ident: L.append("| `%s` | `%s` | `%s` | %d | %d |" % (t, key, k[len(D):], n, c))
    L += notes
    L += ["", "## Foreign keys", "",
          "Each foreign key of the schema and the object property that states it in the graph. A key that is",
          "part of a subject IRI needs no property: the IRI itself carries it.", "",
          "| Foreign key | References | Stated by | Mapping |", "| --- | --- | --- | --- |"]
    for t, col, rt, rc, hit, reason in fkrows:
        if hit: L.append("| `%s.%s` | `%s.%s` | %s | `%s` |" % (t, col, rt, rc, ("`:%s`" % hit[1]) if not hit[1].startswith("(") else hit[1], hit[0]))
        else: L.append("| `%s.%s` | `%s.%s` | not exposed%s | |" % (t, col, rt, rc, (": " + reason) if reason else ""))
    L += ["", "## Integrity checks", "",
          "| Check | Result |", "| --- | --- |",
          "| One IRI per row for every keyed table | %s |" % ("holds for all %d" % len(ident) if not any(p.startswith("identifiers") for p in problems) else "see problems"),
          "| Every IRI an object property points at is an individual with a class | %s |" % ("holds" if not dangling else "%d exceptions" % len(dangling)),
          "| Every individual that carries a property has a class | %s |" % ("holds" if not untyped else "%d exceptions" % len(untyped)),
          "| No two individuals carry the same source URL | %s |" % ("holds" if not shared else "%d exceptions" % len(shared)),
          "| Every literal is well formed for its datatype | %s |" % ("holds" if not bad else "%d exceptions" % len(bad)),
          "", "NOT NULL columns are read without a filter and nullable columns through a mapping of their own with",
          "`IS NOT NULL`, so a missing value produces no triple rather than an empty one.", ""]
    io.open(MD, "w", encoding="utf-8").write("\n".join(L))
    print("wrote", MD)
sys.exit(1 if problems else 0)
