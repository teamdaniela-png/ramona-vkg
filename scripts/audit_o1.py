#!/usr/bin/env python3
"""
Structural checks of RATR-O (version read from the ontology header) and of its mappings and
queries. Produces a severity-graded
report covering OWL 2 QL profile conformance, ontology consistency,
coverage, provenance, naming, and data-ontology alignment.

Severity levels:
  BLOCKER  — must be fixed before a release
  SHOULD   — should be fixed before the residency starts
  NIT      — minor polish, can be left
  NOTE     — observation, not a finding
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import rdflib
from rdflib import OWL, RDF, RDFS, SKOS, URIRef, Literal
from rdflib.namespace import DC, DCTERMS

ROOT = Path(__file__).resolve().parent.parent
TTL = ROOT / "ontology" / "ratr-o.ttl"
OBDA = ROOT / "mappings" / "ramona.obda"
R2RML = ROOT / "mappings" / "ramona.r2rml.ttl"

NS = rdflib.Namespace("https://w3id.org/ratr-o#")

g = rdflib.Graph()
g.parse(TTL, "turtle")


def log(severity: str, finding: str, detail: str = ""):
    findings.append({"severity": severity, "finding": finding, "detail": detail})


findings: list[dict] = []


# =========================================================================
# Section 1: OWL 2 QL profile conformance
# =========================================================================
print("=== 1. OWL 2 QL profile ===")
DISALLOWED_PROPS = {
    OWL.oneOf, OWL.hasValue, OWL.cardinality, OWL.maxCardinality,
    OWL.minCardinality, OWL.hasKey, OWL.propertyChainAxiom,
    OWL.qualifiedCardinality, OWL.maxQualifiedCardinality,
    OWL.minQualifiedCardinality, OWL.hasSelf,
}
DISALLOWED_TYPES = {
    OWL.FunctionalProperty, OWL.InverseFunctionalProperty,
    OWL.TransitiveProperty, OWL.SymmetricProperty,
    OWL.AsymmetricProperty, OWL.ReflexiveProperty,
    OWL.IrreflexiveProperty,
}
for s, p, o in g:
    if p in DISALLOWED_PROPS:
        log("BLOCKER", "OWL 2 QL violation: disallowed predicate used",
            f"{s} {p} {o}")

for s, p, o in g.triples((None, RDF.type, None)):
    if o in DISALLOWED_TYPES:
        log("BLOCKER", "OWL 2 QL violation: disallowed property type",
            f"{s} is a {o}")

# Datatypes: OWL 2 QL admits only the datatypes of its datatype map (OWL 2 Profiles, sec. 3.2).
# xsd:boolean, xsd:date, xsd:gYear, xsd:double, xsd:float are NOT in it. This check was missing
# before v1.9 and the ROBOT/OWL API profile checker caught 16 such ranges.
QL_DATATYPES = {RDFS.Literal, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"),
                URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral"), OWL.real, OWL.rational}
QL_DATATYPES |= {URIRef("http://www.w3.org/2001/XMLSchema#" + t) for t in (
    "decimal integer nonNegativeInteger string normalizedString token Name NCName NMTOKEN "
    "hexBinary base64Binary anyURI dateTime dateTimeStamp").split()}
for s_, _, o_ in g.triples((None, RDFS.range, None)):
    if (s_, RDF.type, OWL.DatatypeProperty) in g and o_ not in QL_DATATYPES:
        log("BLOCKER", "OWL 2 QL violation: data range outside the QL datatype map", f"{s_} range {o_}")

# Check for existentials on LHS of subClassOf (owl:someValuesFrom only allowed on RHS in QL)
for s, p, o in g.triples((None, OWL.someValuesFrom, None)):
    # Check whether s appears on the left side of rdfs:subClassOf
    for sub, _, sup in g.triples((None, RDFS.subClassOf, None)):
        if sub == s or any(s == bn for bn in g.objects(sub, RDF.type)):
            log("BLOCKER", "OWL 2 QL violation: someValuesFrom on LHS of subClassOf",
                f"{sub}")

# Check for allValuesFrom anywhere (disallowed)
for s, p, o in g.triples((None, OWL.allValuesFrom, None)):
    log("BLOCKER", "OWL 2 QL violation: allValuesFrom used", f"{s}")

print(f"  (flagged {sum(1 for f in findings if 'OWL 2 QL' in f['finding'])} issues)")


# =========================================================================
# Section 2: Ontology consistency
# =========================================================================
print("=== 2. Consistency ===")

classes = {s for s in g.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)}
obj_props = {s for s in g.subjects(RDF.type, OWL.ObjectProperty) if isinstance(s, URIRef)}
data_props = {s for s in g.subjects(RDF.type, OWL.DatatypeProperty) if isinstance(s, URIRef)}

# 2a. Classes never used in any property domain/range
classes_in_use = set()
for p in obj_props | data_props:
    for d in g.objects(p, RDFS.domain):
        classes_in_use.add(d)
    for r in g.objects(p, RDFS.range):
        classes_in_use.add(r)
for c in classes:
    for sub in g.subjects(RDFS.subClassOf, c):
        classes_in_use.add(c)
    for sup in g.objects(c, RDFS.subClassOf):
        classes_in_use.add(sup)

unused_classes = [c for c in classes if c not in classes_in_use and str(c).startswith(str(NS))]
# A class is isolated when nothing ties it to the rest of the ontology: it has no superclass and
# no subclass, appears in no domain or range, and no mapping types an individual with it. A leaf
# class under a parent is not isolated.
_map_txt_iso = OBDA.read_text(encoding="utf-8")
for c in classes:
    if not str(c).startswith(str(NS)):
        continue
    local = str(c).split("#")[-1]
    tied = (list(g.objects(c, RDFS.subClassOf)) or list(g.subjects(RDFS.subClassOf, c))
            or c in classes_in_use or re.search(r"\ba :%s\b" % re.escape(local), _map_txt_iso))
    if not tied:
        log("SHOULD", "Class is isolated: no superclass, no subclass, in no domain or range, typed by no mapping", ":" + local)

# 2b. Properties with no domain or range
for p in obj_props | data_props:
    if not str(p).startswith(str(NS)):
        continue
    doms = list(g.objects(p, RDFS.domain))
    # A property may be deliberately domain-free (cross-cutting provenance, for example).
    # The exemption is only granted when the comment says so in those words, so the
    # omission has to be an explicit decision recorded in the ontology, not an oversight.
    if not doms and any("no domain" in str(c) for c in g.objects(p, RDFS.comment)):
        continue
    rans = list(g.objects(p, RDFS.range))
    if not doms:
        log("SHOULD", "Property missing rdfs:domain",
            str(p).replace(str(NS), ":"))
    if not rans:
        log("SHOULD", "Property missing rdfs:range",
            str(p).replace(str(NS), ":"))

# 2c. Redundant classes (same label)
labels_to_classes = defaultdict(list)
for c in classes:
    if not str(c).startswith(str(NS)):
        continue
    for o in g.objects(c, RDFS.label):
        if isinstance(o, Literal) and o.language == "en":
            labels_to_classes[str(o).lower()].append(c)
for label, cs in labels_to_classes.items():
    if len(cs) > 1:
        log("SHOULD", "Two classes share the same English label (potential duplicate)",
            f"'{label}': {[str(c).replace(str(NS), ':') for c in cs]}")

# 2d. Classes without any label
for c in classes:
    if not str(c).startswith(str(NS)):
        continue
    labels = list(g.objects(c, RDFS.label))
    if not labels:
        log("SHOULD", "Class without any rdfs:label",
            str(c).replace(str(NS), ":"))
    has_en = any(isinstance(o, Literal) and o.language == "en" for o in labels)
    has_es = any(isinstance(o, Literal) and o.language == "es" for o in labels)
    if not has_en:
        log("NIT", "Class without English label", str(c).replace(str(NS), ":"))
    if not has_es:
        log("NIT", "Class without Spanish label", str(c).replace(str(NS), ":"))

# 2e. Properties without label
for p in obj_props | data_props:
    if not str(p).startswith(str(NS)):
        continue
    labels = list(g.objects(p, RDFS.label))
    if not labels:
        log("SHOULD", "Property without any rdfs:label",
            str(p).replace(str(NS), ":"))

# 2f. Orphan SKOS closeMatch targets that are relative and cannot be dereferenced
for s, p, o in g.triples((None, SKOS.closeMatch, None)):
    if str(o).startswith("https://bioportal.bioontology.org/ontologies/HUTRO") and len(str(o)) < 60:
        log("NIT", "skos:closeMatch to HUTRO has short IRI (fragment may not dereference cleanly)",
            str(o))

print(f"  (flagged {sum(1 for f in findings if f['severity'] in ('SHOULD','NIT','BLOCKER'))} issues total so far)")


# =========================================================================
# Section 3: Coverage against the entities Objective 1 names
# =========================================================================
print("=== 3. Coverage ===")
required_entities = {
    "Job offers": ":JobOffer",
    "Employers": ":Employer",
    "Recruiters": ":Recruiter",
    "Candidates": ":Candidate",
    "Trafficking red-flags": ":RedFlag",
    "Geographic routes": ":TraffickingRoute",
    "Platform origin": ":Platform",
    "Risk classifications": ":RiskClassification",
}
for name, iri_short in required_entities.items():
    iri = URIRef(str(NS) + iri_short.lstrip(":"))
    if iri not in classes:
        log("BLOCKER", f"Required O1 entity missing: {name} ({iri_short})")

# Disjointness between Employer and Recruiter
EMP = URIRef(str(NS) + "Employer")
REC = URIRef(str(NS) + "Recruiter")
disjoint_seen = False
for s, p, o in g.triples((None, OWL.disjointWith, None)):
    if (s == EMP and o == REC) or (s == REC and o == EMP):
        disjoint_seen = True
if not disjoint_seen:
    log("SHOULD", "Employer and Recruiter not declared disjoint", "Add :Employer owl:disjointWith :Recruiter for OWL 2 QL (super class disjointness is allowed in QL).")


# =========================================================================
# Section 4: Provenance and citations
# =========================================================================
print("=== 4. Provenance ===")

# 4a. Every FraudScheme subclass must have at least one rdfs:seeAlso OR a comment
# longer than 100 chars (i.e. justifies its existence).
fraud_root = URIRef(str(NS) + "FraudScheme")
def descendants(root, seen=None):
    seen = seen or set()
    seen.add(root)
    for s in g.subjects(RDFS.subClassOf, root):
        if s not in seen:
            seen |= descendants(s, seen)
    return seen

fraud_subtree = descendants(fraud_root) - {fraud_root}
for fs in fraud_subtree:
    short = str(fs).replace(str(NS), ":")
    has_seealso = bool(list(g.objects(fs, RDFS.seeAlso)))
    comments = list(g.objects(fs, RDFS.comment))
    comment_len = sum(len(str(c)) for c in comments)
    if not has_seealso and comment_len < 150:
        log("SHOULD", f"FraudScheme '{short}' lacks rdfs:seeAlso AND has short/no comment",
            f"comment_len={comment_len}")

# 4b. Every skos:closeMatch must dereference (we can't check HTTP in offline mode, but we can check URL shape)
cm_count = 0
for s, p, o in g.triples((None, SKOS.closeMatch, None)):
    cm_count += 1
    if not (str(o).startswith("http://") or str(o).startswith("https://")):
        log("BLOCKER", "skos:closeMatch target is not a URL", str(o))

# 4c. Ontology header must include dc:creator, dct:license, owl:versionInfo
header = URIRef("https://w3id.org/ratr-o")
if not list(g.objects(header, DC.creator)):
    log("SHOULD", "Ontology header missing dc:creator")
if not list(g.objects(header, DCTERMS.license)):
    log("SHOULD", "Ontology header missing dct:license")
if not list(g.objects(header, OWL.versionInfo)):
    log("BLOCKER", "Ontology header missing owl:versionInfo")

# =========================================================================
# Section 5: Naming conventions
# =========================================================================
print("=== 5. Naming ===")
# Classes should be UpperCamelCase
for c in classes:
    if not str(c).startswith(str(NS)):
        continue
    name = str(c).replace(str(NS), "")
    if name and not name[0].isupper():
        log("NIT", f"Class does not start with uppercase: :{name}")
    if re.search(r"[_\- ]", name):
        log("NIT", f"Class name contains underscore/hyphen/space: :{name}")

# Properties should be lowerCamelCase
for p in obj_props | data_props:
    if not str(p).startswith(str(NS)):
        continue
    name = str(p).replace(str(NS), "")
    if name and not name[0].islower():
        log("NIT", f"Property does not start with lowercase: :{name}")
    if re.search(r"[_\- ]", name):
        log("NIT", f"Property name contains underscore/hyphen/space: :{name}")


# =========================================================================
# Section 6: Mapping consistency (OBDA and R2RML)
# =========================================================================
print("=== 6. Mapping consistency ===")
if OBDA.exists():
    obda_text = OBDA.read_text()
    obda_mapping_count = obda_text.count("mappingId")
    if obda_mapping_count < 30:
        log("SHOULD", f"OBDA has only {obda_mapping_count} mapping entries",
            "Ontology is larger than what the mapping expresses. Consider expanding to cover new v1.4-v1.6 classes.")
else:
    log("BLOCKER", "OBDA mapping file missing")

if R2RML.exists():
    try:
        rg = rdflib.Graph()
        rg.parse(R2RML, "turtle")
        r2rml_triples = len(rg)
    except Exception as e:
        log("BLOCKER", f"R2RML mapping does not parse: {e}")
        r2rml_triples = 0
else:
    log("SHOULD", "R2RML mapping file missing")
    r2rml_triples = 0


# =========================================================================
# Section 9: Definitions, dangling references, vocabulary closure, datatypes
# =========================================================================
print("=== 9. Definitions, dangling refs, vocabulary closure, datatypes ===")

import glob as _glob

_all_entities = set(classes) | set(obj_props) | set(data_props)
for _e in sorted(_all_entities):
    if not list(g.objects(_e, RDFS.comment)):
        log("SHOULD", "Entity has no rdfs:comment (definition)", str(_e).split("#")[-1])

# dangling :Name references inside annotation text
_declared_names = {str(e).split("#")[-1] for e in _all_entities}
_declared_names |= {str(e).split("#")[-1] for e in g.subjects(RDF.type, OWL.NamedIndividual)}
_ttl_text = TTL.read_text(encoding="utf-8")
for _lit in re.findall(r'"((?:[^"\\]|\\.)*)"@[a-z]{2}', _ttl_text):
    for _ref in re.findall(r"(?<![\w:]):([A-Z]\w+|[a-z]\w*)\b", _lit):
        if _ref not in _declared_names:
            log("SHOULD", "Annotation text references an undeclared IRI",
                f":{_ref} is mentioned in an rdfs:comment or skos:note but is not declared in the ontology")

# vocabulary closure over queries and mappings
_obda_text = OBDA.read_text(encoding="utf-8")
_r2rml_text = R2RML.read_text(encoding="utf-8")
_sources = {"mappings/ramona.obda": _obda_text, "mappings/ramona.r2rml.ttl": _r2rml_text}
for _f in sorted(_glob.glob(str(ROOT / "queries" / "*.rq"))):
    _raw = Path(_f).read_text(encoding="utf-8")
    _sources["queries/" + Path(_f).name] = "\n".join(l.split("#")[0] for l in _raw.split("\n"))
for _name, _text in _sources.items():
    for _used in sorted(set(re.findall(r"(?<![\w<#/:]):([A-Za-z]\w*)", _text))):
        if _used not in _declared_names:
            log("BLOCKER", "Vocabulary used outside the ontology is not declared in it",
                f":{_used} is used in {_name} but never declared in ratr-o.ttl")

# datatype ranges: QL datatype map and agreement with what the mappings emit
_QL_DATATYPES = {
    "string", "integer", "decimal", "dateTime", "dateTimeStamp", "anyURI",
    "nonNegativeInteger", "normalizedString", "token", "Name", "NCName",
    "NMTOKEN", "hexBinary", "base64Binary", "real", "rational",
    "PlainLiteral", "XMLLiteral", "Literal",
}
_ranges = {}
for _p in data_props:
    for _r in g.objects(_p, RDFS.range):
        _ranges[str(_p).split("#")[-1]] = str(_r).split("#")[-1].split("/")[-1]
for _prop, _r in sorted(_ranges.items()):
    if _r not in _QL_DATATYPES:
        log("BLOCKER", "Datatype range outside the OWL 2 QL datatype map",
            f":{_prop} has range xsd:{_r}; OWL 2 Profiles section 3.2 does not admit it in QL")
_emitted = []
for _prop, _dt in re.findall(r":(\w+)\s+\{[^}]*\}\^\^xsd:(\w+)", _obda_text):
    _emitted.append(("mappings/ramona.obda", _prop, _dt))
_r2 = rdflib.Graph()
_r2.parse(R2RML, "turtle")
for _row in _r2.query(
    """PREFIX rr: <http://www.w3.org/ns/r2rml#>
       SELECT ?p ?d WHERE { ?pom rr:predicate ?p ; rr:objectMap ?om . ?om rr:datatype ?d }"""):
    _emitted.append(("mappings/ramona.r2rml.ttl", str(_row.p).split("#")[-1], str(_row.d).split("#")[-1]))
for _src, _prop, _dt in _emitted:
    _r = _ranges.get(_prop)
    if _r and _r != "Literal" and _r != _dt:
        log("BLOCKER", "Mapping emits a datatype that clashes with the declared range",
            f":{_prop} has range xsd:{_r} but {_src} emits xsd:{_dt}; HermiT reports the merged graph inconsistent")


# =========================================================================
# Section 10: Alignments, mapping coverage, IRI templates, SQL widths
# =========================================================================
print("=== 10. Alignments, coverage, IRI templates, SQL widths ===")

_PORTAL_PAGE_PREFIXES = (
    "https://bioportal.bioontology.org/ontologies/",
    "http://bioportal.bioontology.org/ontologies/",
    "https://agroportal.lirmm.fr/ontologies/",
    "https://www.ebi.ac.uk/ols4/ontologies/",
)
# A target of the shape <portal>/<ACRONYM><local_name> is suspicious but not wrong on its
# own: BioPortal does serve HUTRO's concepts under exactly that concatenated form. What the
# audit can demand is evidence. Every such target must carry, on the same subject, a note
# that says the IRI itself was verified and on what date. Shape alone settles nothing; an
# unverified claim is.
for _s, _p, _o in g.triples((None, SKOS.closeMatch, None)):
    _t = str(_o)
    for _pref in _PORTAL_PAGE_PREFIXES:
        if not _t.startswith(_pref):
            continue
        _rest = _t[len(_pref):]
        if not _rest or _rest.strip("/").isupper():
            continue  # plain ontology page, handled by check 2f
        _notes = " ".join(str(_n) for _n in g.objects(_s, SKOS.note))
        if "verified" not in _notes.lower():
            log("BLOCKER", "skos:closeMatch target is a portal URL with a local name appended and no note states the IRI was verified",
                f"{str(_s).split('#')[-1]} -> {_t}")
        elif not re.search(r"\b(19|20)\d\d\b", _notes):
            log("SHOULD", "skos:closeMatch verification note does not record the date of the check",
                str(_s).split("#")[-1])

# every class that names an external vocabulary in a note must say when it was checked
for _s in set(g.subjects(SKOS.note, None)):
    for _n in g.objects(_s, SKOS.note):
        _txt = str(_n)
        if ("HUTRO" in _txt or "archive.org" in _txt) and "2026" not in _txt and "2025" not in _txt:
            log("SHOULD", "External-alignment or archived-citation note does not record the date of the check",
                str(_s).split("#")[-1])

# mapping coverage: what the ontology declares but no mapping produces
_obda_t = OBDA.read_text(encoding="utf-8")
_r2_t = R2RML.read_text(encoding="utf-8")
_map_text = _obda_t + _r2_t
def _mapped(_e):
    return re.search(r"(?<![\w<#/:])%s(?![\w])" % re.escape(str(_e).split("#")[-1]).join([":", ""]), _map_text) is not None
_unmapped_p = sorted(str(e).split("#")[-1] for e in (set(obj_props) | set(data_props)) if not _mapped(e))
_unmapped_c = sorted(str(e).split("#")[-1] for e in classes if not _mapped(e))
# one IRI template per class: catches the same real-world entity minted under two different keys
_tpl = defaultdict(set)
for _m in re.finditer(r"^target\s+(.*)$", _obda_t, re.M):
    _line = _m.group(1)
    for _subj, _cls in re.findall(r"<(https://w3id\.org/ratr-o/data/[^>]+)>\s+a\s+(:\w+)", _line):
        _tpl[_cls].add(re.sub(r"\{[^}]*\}", "{}", _subj))
    for _obj_iri in re.findall(r"<(https://w3id\.org/ratr-o/data/[^>]+)>", _line):
        pass
# object-property ranges: the IRI template used as object must match the template the range class is minted under
for _m in re.finditer(r"^target\s+(.*)$", _obda_t, re.M):
    for _prop, _obj in re.findall(r"(:\w+)\s+<(https://w3id\.org/ratr-o/data/[^>]+)>", _m.group(1)):
        _pr = NS[_prop[1:]]
        if _pr not in obj_props:
            continue
        _rng = next(iter(g.objects(_pr, RDFS.range)), None)
        if _rng is None:
            continue
        # the range is satisfied by the range class or any of its subclasses, so collect
        # the IRI templates of the whole subtree
        _sub = {_rng}
        _frontier = [_rng]
        while _frontier:
            _cur = _frontier.pop()
            for _child in g.subjects(RDFS.subClassOf, _cur):
                if _child not in _sub:
                    _sub.add(_child); _frontier.append(_child)
        _want = set()
        for _c in _sub:
            _want |= _tpl.get(":" + str(_c).split("#")[-1], set())
        if not _want:
            continue
        _got = re.sub(r"\{[^}]*\}", "{}", _obj)
        if _got not in _want:
            log("BLOCKER", "A mapping points an object property at an IRI template the range class is never minted under",
                f"{_prop} -> {_got}, but {_rcls} is minted as {sorted(_want)}")

# SQL: string literals wider than the CHAR(n) column they are inserted into
_sql_cols = {}
for _f in sorted(ROOT.glob("db/*.sql")):
    _s = _f.read_text(encoding="utf-8")
    for _m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?(?:ramona\.)?(\w+)\s*\((.*?)\n\);", _s, re.S):
        for _line in _m.group(2).split("\n"):
            _cm = re.match(r"\s*(\w+)\s+(CHAR\((\d+)\)|VARCHAR\((\d+)\))", _line, re.I)
            if _cm and not re.match(r"\s*(PRIMARY|FOREIGN|UNIQUE|CONSTRAINT|CHECK)", _line, re.I):
                _sql_cols[(_m.group(1), _cm.group(1))] = int(_cm.group(3) or _cm.group(4))
_width_bad = Counter()
for _f in sorted(ROOT.glob("db/*.sql")):
    _s = _f.read_text(encoding="utf-8")
    for _m in re.finditer(r"INSERT INTO (?:ramona\.)?(\w+)\s*\(([^)]*)\)\s*VALUES(.*?);\s*$", _s, re.S | re.M):
        _tb = _m.group(1)
        _cols = [c.strip() for c in _m.group(2).split(",")]
        for _row in re.findall(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)", _m.group(3)):
            _parts, _cur, _q, _dep = [], "", False, 0
            for _ch in _row:
                if _ch == "'":
                    _q = not _q
                if _ch == "," and not _q and _dep == 0:
                    _parts.append(_cur.strip()); _cur = ""
                else:
                    if _ch == "(" and not _q: _dep += 1
                    if _ch == ")" and not _q: _dep -= 1
                    _cur += _ch
            _parts.append(_cur.strip())
            if len(_parts) != len(_cols):
                continue
            for _col, _val in zip(_cols, _parts):
                _n = _sql_cols.get((_tb, _col))
                if not _n:
                    continue
                _lit = re.match(r"^'((?:[^']|'')*)'$", _val)
                if _lit and len(_lit.group(1)) > _n:
                    _width_bad[(_f.name, _tb, _col, _n)] += 1
for (_fn, _tb, _col, _n), _cnt in sorted(_width_bad.items()):
    log("BLOCKER", "A seed inserts string literals wider than the column accepts, so the file cannot load",
        f"{_fn}: {_cnt} rows put a value longer than {_n} characters into {_tb}.{_col}")

# =========================================================================
# Section 8: Final counts
# =========================================================================
print("=== 8. Counts ===")
print(f"  classes:          {len(classes)}")
print(f"  object properties: {len(obj_props)}")
print(f"  datatype properties: {len(data_props)}")
print(f"  triples:           {len(g)}")
print(f"  skos:closeMatch:   {cm_count}")

# Emit report
report_path = ROOT / "docs" / "AUDIT_O1.md"
by_sev = defaultdict(list)
_seen = set()
for f in findings:
    _key = (f["severity"], f["finding"], f["detail"])
    if _key in _seen:
        continue
    _seen.add(_key)
    by_sev[f["severity"]].append(f)

_version = next((str(o) for o in g.objects(URIRef("https://w3id.org/ratr-o"), OWL.versionInfo)), "unversioned")
lines = [
    f"# RATR-O v{_version}: structural checks",
    "",
    "Structural checks of the ontology, its mappings and its queries. Generated by `scripts/audit_o1.py` reading `ontology/ratr-o.ttl`, `mappings/ramona.obda`, `mappings/ramona.r2rml.ttl`, and `queries/*.rq`.",
    "",
    "**Summary**",
    "",
    f"- Classes: {len(classes)}",
    f"- Object properties: {len(obj_props)}",
    f"- Datatype properties: {len(data_props)}",
    f"- Triples: {len(g)}",
    f"- skos:closeMatch edges: {cm_count}",
    f"- R2RML mapping triples: {r2rml_triples}",
    "",
    "**Findings by severity**",
    "",
    f"- BLOCKER: {len(by_sev['BLOCKER'])}",
    f"- SHOULD:  {len(by_sev['SHOULD'])}",
    f"- NIT:     {len(by_sev['NIT'])}",
    f"- NOTE:    {len(by_sev['NOTE'])}",
    "",
    "---",
    "",
]

for sev in ("BLOCKER", "SHOULD", "NIT", "NOTE"):
    items = by_sev.get(sev, [])
    if not items:
        continue
    lines.append(f"## {sev}")
    lines.append("")
    for item in items:
        lines.append(f"- **{item['finding']}**")
        if item["detail"]:
            lines.append(f"  - {item['detail']}")
    lines.append("")

lines.append("## Checklist")
lines.append("")
checks = [
    ("OWL 2 QL profile validated", len(by_sev["BLOCKER"]) == 0 or all("OWL 2 QL" not in f["finding"] for f in by_sev["BLOCKER"])),
    ("All eight O1 required entities present", not any("Required O1 entity missing" in f["finding"] for f in by_sev["BLOCKER"])),
    ("Every FraudScheme subclass cites at least one official source", not any("FraudScheme" in f["finding"] and "lacks rdfs:seeAlso" in f["finding"] for f in by_sev["SHOULD"])),
    ("Ontology header has version, creator, license", not any("Ontology header missing" in f["finding"] for f in findings if f["severity"] in ("BLOCKER", "SHOULD"))),
    ("Every property has a range and, unless documented as general, a domain", not any("Property missing" in f["finding"] for f in by_sev["SHOULD"])),
    ("Every skos:closeMatch target under a portal URL carries a verified-IRI note", not any("no note states the IRI was verified" in f["finding"] for f in by_sev["BLOCKER"])),

    ("Every object property points at the IRI template its range class is minted under", not any("range class is never minted under" in f["finding"] for f in by_sev["BLOCKER"])),
    ("Every db/ seed fits the column widths it inserts into", not any("wider than the column accepts" in f["finding"] for f in by_sev["BLOCKER"])),
    ("R2RML parses cleanly", r2rml_triples > 0),
    ("OBDA has enough mappings to populate the VKG", not any("OBDA has only" in f["finding"] for f in by_sev["SHOULD"])),
    ("Every class and property carries an rdfs:comment definition", not any("no rdfs:comment" in f["finding"] for f in by_sev["SHOULD"])),
    ("No annotation text references an undeclared IRI", not any("undeclared IRI" in f["finding"] for f in by_sev["SHOULD"])),
    ("Every term used in the queries and mappings is declared in the ontology", not any("not declared in it" in f["finding"] for f in by_sev["BLOCKER"])),
    ("Every datatype range is inside the OWL 2 QL datatype map", not any("outside the OWL 2 QL datatype map" in f["finding"] for f in by_sev["BLOCKER"])),
    ("No mapping emits a datatype that clashes with the declared range", not any("clashes with the declared range" in f["finding"] for f in by_sev["BLOCKER"])),
]
for text, ok in checks:
    mark = "[x]" if ok else "[ ]"
    lines.append(f"- {mark} {text}")

report_path.write_text("\n".join(lines))
print(f"\nwrote {report_path}")
print(f"\nFindings by severity: {dict((k, len(v)) for k, v in by_sev.items())}")
