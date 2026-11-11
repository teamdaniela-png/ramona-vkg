"""Execute the .obda mappings against the SQLite copy of the seeds and write the ABox.

It reads the same mapping file Ontop reads, runs the same SQL and applies the same IRI and
literal templates, so the graph it writes is the one the VKG exposes.

Usage: materialize_obda.py <mapping.obda> <database.db> <output.ttl>
"""
import io, re, sys, sqlite3, urllib.parse
from rdflib import Graph

OBDA, DB, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
txt = io.open(OBDA, encoding="utf-8").read()

prefixes = {}
m = re.search(r"\[PrefixDeclaration\](.*?)\[", txt, re.S)
for line in m.group(1).strip().split("\n"):
    if not line.strip(): continue
    k, v = re.split(r"\s+", line.strip(), maxsplit=1)
    prefixes[k.rstrip(":") + ":"] = v.strip()

blocks = re.findall(r"mappingId\s+(\S+)\s*\ntarget\s+(.*?)\nsource\s+(.*?)(?=\n\s*\n|\nmappingId|\Z)", txt, re.S)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

def esc(v):
    s = str(v)
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))

def iri_esc(v):
    return urllib.parse.quote(str(v), safe="-._~:/?#[]@!$&'()*+,;=")

def split_po(target):
    """subject, [predicate-object strings]"""
    t = target.strip().rstrip(".").strip()
    # subject is the first <...> or prefixed name
    mm = re.match(r"(<[^>]*>|\S+)\s+(.*)", t, re.S)
    subj, rest = mm.group(1), mm.group(2)
    parts, buf, depth, inq = [], [], 0, False
    for ch in rest:
        if ch == '"': inq = not inq
        if ch == "<" and not inq: depth += 1
        if ch == ">" and not inq: depth -= 1
        if ch == ";" and depth == 0 and not inq:
            parts.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip(): parts.append("".join(buf))
    return subj, [p.strip() for p in parts if p.strip()]

def fill(tpl, row, literal_ok=True):
    """Substitute {col}. Returns None when a referenced column is NULL."""
    out, i, inangle = [], 0, False
    while i < len(tpl):
        c = tpl[i]
        if c == "<": inangle = True
        if c == ">": inangle = False
        if c == "{":
            j = tpl.index("}", i)
            col = tpl[i+1:j]
            if col not in row.keys():
                return None
            v = row[col]
            if v is None: return None
            out.append(iri_esc(v) if inangle else '"%s"' % esc(v))
            i = j + 1
            continue
        out.append(c); i += 1
    return "".join(out)

lines = ["@prefix %s <%s> ." % (k, v) for k, v in prefixes.items()]
g = Graph()
total = 0
skipped = []
for mid, target, source in blocks:
    sql = re.sub(r"\b(ramona|public)\.", "", source.strip())
    try:
        rows = con.execute(sql).fetchall()
    except Exception as e:
        skipped.append((mid, "SQL: " + str(e)[:110])); continue
    subj_tpl, pos = split_po(target)
    body = []
    for row in rows:
        s = fill(subj_tpl, row)
        if s is None: continue
        for po in pos:
            o = fill(po, row)
            if o is None: continue
            body.append("%s %s ." % (s, o))
    if not body:
        skipped.append((mid, "0 triples (%d rows)" % len(rows))); continue
    chunk = "\n".join(lines) + "\n" + "\n".join(body) + "\n"
    try:
        g.parse(data=chunk, format="turtle")
    except Exception as e:
        skipped.append((mid, "turtle: " + str(e)[:110])); continue
    total += len(body)

g.serialize(OUT, format="turtle")
print("mappings:", len(blocks), "triples emitted:", total, "graph size:", len(g))
print("\nmappings that produced nothing or failed:")
for mid, why in skipped: print("  %-34s %s" % (mid, why))
