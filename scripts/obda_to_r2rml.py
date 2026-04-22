#!/usr/bin/env python3
"""
Convert Ontop OBDA mapping to W3C R2RML.

Reads mappings/ramona.obda, parses each [MappingDeclaration] block, and emits
mappings/ramona.r2rml.ttl. Preserves prefixes, templates and SQL sources.

R2RML output follows the W3C Recommendation (https://www.w3.org/TR/r2rml/).

Limitations of this converter:
  - OBDA allows pattern-based target atoms like
      <https://ramona.ai/offer/{offer_id}> a :JobOffer ; :hasTitle {title} .
    R2RML requires explicit rr:TriplesMap blocks with rr:subjectMap and
    rr:predicateObjectMap. We produce one rr:TriplesMap per OBDA mappingId.
  - Typed literals {value}^^xsd:int are emitted as rr:datatype.
  - OBDA prefixes are copied verbatim.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/Users/danielacamberos/Downloads/ramona_vkg_demo")
IN = ROOT / "mappings" / "ramona.obda"
OUT = ROOT / "mappings" / "ramona.r2rml.ttl"


def parse_obda(text: str):
    """Yield (prefixes, list of (mapping_id, target, source))."""
    prefixes = {}
    mappings = []
    in_prefix = False
    in_map = False
    current = {}
    lines = text.splitlines()
    for line in lines:
        s = line.strip()
        if s.startswith("[PrefixDeclaration]"):
            in_prefix = True
            continue
        if s.startswith("[MappingDeclaration]"):
            in_prefix = False
            in_map = True
            continue
        if in_prefix and s and not s.startswith("["):
            parts = s.split(None, 1)
            if len(parts) == 2:
                name, uri = parts
                prefixes[name.rstrip(":")] = uri
        if in_map:
            if s.startswith("mappingId"):
                if current:
                    mappings.append(current)
                current = {"id": s.split(None, 1)[1].strip()}
            elif s.startswith("target"):
                current["target"] = s.split(None, 1)[1].strip()
            elif s.startswith("source"):
                current["source"] = s.split(None, 1)[1].strip()
            elif s.startswith("]]"):
                if current:
                    mappings.append(current)
                    current = {}
                in_map = False
    return prefixes, mappings


# regex to match URI templates like <https://ramona.ai/offer/{offer_id}>
URI_TEMPLATE_RE = re.compile(r"<([^>]+\{[^}]+\}[^>]*)>")
# regex to match typed literal like {value}^^xsd:int
TYPED_LIT_RE = re.compile(r"\{([^}]+)\}\^\^([\w:]+)")
# regex to match plain literal {value}
PLAIN_LIT_RE = re.compile(r"\{([^}]+)\}(?![\w^])")
# regex to match prefixed IRI like :JobOffer or ont:Something
PREFIXED_IRI_RE = re.compile(r"(?:^|\s)((?:[a-zA-Z][\w]*)?:[\w-]+)")


def iri_to_template(iri: str) -> str:
    """Turn <https://.../{x}> into a string R2RML template value."""
    # remove angle brackets first
    inner = iri.strip("<>")
    return inner  # R2RML rr:template accepts bare string with {col} placeholders


def convert_target(target: str):
    """Very-small parser for OBDA target atoms.

    Returns a subject template plus a list of (predicate, object_desc).
    object_desc is a dict with keys: kind (iri|literal), value, datatype (optional).
    """
    target = target.strip().rstrip(".").strip()
    # the subject is the first angle-bracketed template
    m = URI_TEMPLATE_RE.match(target)
    if not m:
        return None
    subj_tpl = m.group(1)
    rest = target[m.end():].strip()

    # 'a :Class'  -> rdf:type
    # ';'         -> separator
    # predicate object pairs
    pairs = []
    # normalise: we split on ';' and for each part get predicate + object
    # but URIs can contain ';', so split cautiously: since our targets are
    # curated we use semicolons at top level only.
    parts = [p.strip() for p in rest.split(";") if p.strip()]
    for p in parts:
        tokens = p.split(None, 1)
        if len(tokens) != 2:
            continue
        pred, obj = tokens
        if pred == "a":
            pred = "rdf:type"
        obj = obj.strip()
        # object types
        if obj.startswith("<"):
            mobj = URI_TEMPLATE_RE.match(obj)
            if mobj:
                pairs.append((pred, {"kind": "iri_template", "value": mobj.group(1)}))
            else:
                pairs.append((pred, {"kind": "iri", "value": obj.strip("<>")}))
        else:
            mt = TYPED_LIT_RE.match(obj)
            if mt:
                pairs.append((pred, {"kind": "literal", "value": mt.group(1), "datatype": mt.group(2)}))
            else:
                ml = PLAIN_LIT_RE.match(obj)
                if ml:
                    pairs.append((pred, {"kind": "literal", "value": ml.group(1)}))
                elif obj.startswith(":") or ":" in obj:
                    pairs.append((pred, {"kind": "iri_prefixed", "value": obj}))
    return {"subject_template": subj_tpl, "pairs": pairs}


def emit_r2rml(prefixes: dict, mappings: list) -> str:
    out = []
    out.append("# Ramona VKG — W3C R2RML mapping")
    out.append("# Converted from mappings/ramona.obda (Ontop native format) by scripts/obda_to_r2rml.py")
    out.append("# Licence: Apache 2.0.")
    out.append("")
    out.append("@prefix rr:   <http://www.w3.org/ns/r2rml#> .")
    out.append("@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    out.append("@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .")
    for name, uri in prefixes.items():
        if name:
            out.append(f"@prefix {name}: <{uri}> .")
        else:
            out.append(f"@prefix : <{uri}> .")
    out.append("")

    for m in mappings:
        if not m.get("target") or not m.get("source"):
            continue
        parsed = convert_target(m["target"])
        if not parsed:
            continue
        tm_name = "<#TM_" + m["id"].replace("-", "_") + ">"
        out.append(f"{tm_name} a rr:TriplesMap ;")
        # logical table: rr:sqlQuery
        sql = m["source"].replace("\n", " ").strip().rstrip(";")
        sql_escaped = sql.replace('"""', '"\\"\\"\\""')
        out.append(f'    rr:logicalTable [ rr:sqlQuery """{sql_escaped}""" ] ;')
        out.append("    rr:subjectMap [")
        out.append(f'        rr:template "{parsed["subject_template"]}" ;')
        # Is there a pair whose predicate is rdf:type? Then the subject gets rr:class.
        classes = [p for p in parsed["pairs"] if p[0] == "rdf:type"]
        if classes:
            cls = classes[0][1]
            v = cls["value"]
            if cls["kind"] == "iri":
                out.append(f'        rr:class <{v}> ;')
            else:
                out.append(f'        rr:class {v} ;')
        non_type = [p for p in parsed["pairs"] if p[0] != "rdf:type"]
        # subjectMap ends with ';' if there are predicateObjectMaps, else with '.'
        out.append("    ] " + (";" if non_type else "."))
        for i, (pred, obj) in enumerate(non_type):
            trailing = " ;" if i < len(non_type) - 1 else " ."
            out.append("    rr:predicateObjectMap [")
            out.append(f"        rr:predicate {pred} ;")
            if obj["kind"] == "iri_template":
                out.append(f'        rr:objectMap [ rr:template "{obj["value"]}" ]')
            elif obj["kind"] == "literal":
                col = obj["value"]
                if "datatype" in obj:
                    out.append(f'        rr:objectMap [ rr:column "{col}" ; rr:datatype {obj["datatype"]} ]')
                else:
                    out.append(f'        rr:objectMap [ rr:column "{col}" ]')
            elif obj["kind"] == "iri":
                out.append(f'        rr:object <{obj["value"]}>')
            else:
                out.append(f'        rr:object {obj["value"]}')
            out.append("    ]" + trailing)
        out.append("")
    return "\n".join(out)


def main():
    text = IN.read_text()
    prefixes, mappings = parse_obda(text)
    print(f"parsed {len(prefixes)} prefixes, {len(mappings)} mappings")
    out_text = emit_r2rml(prefixes, mappings)
    OUT.write_text(out_text)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")

    # Sanity: try to parse the output with rdflib
    try:
        import rdflib
        g = rdflib.Graph()
        g.parse(OUT, format="turtle")
        print(f"rdflib parsed OK: {len(g)} triples")
    except Exception as e:
        print(f"WARNING: rdflib parse failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
