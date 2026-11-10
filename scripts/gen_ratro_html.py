#!/usr/bin/env python3
"""
Regenera ontology/ratr-o.html desde ontology/ratr-o.ttl.
Conserva del HTML anterior las secciones fijas (estilo, alineacion con HUTRO, referencias).
Uso: .venv/bin/python scripts/gen_ratro_html.py
"""
import html
import re
from pathlib import Path

import rdflib
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

ROOT = Path(__file__).resolve().parent.parent
TTL = ROOT / "ontology/ratr-o.ttl"
OUT = ROOT / "ontology/ratr-o.html"
NS = "https://w3id.org/ratr-o#"
ONT = rdflib.URIRef("https://w3id.org/ratr-o")
DC = rdflib.Namespace("http://purl.org/dc/elements/1.1/")

COLMEX_REF = ("<li>Arias Vásquez, A. (coord.), Peña González, R. (dir.) and Aguayo Quezada, S. (coord. gral.) (2025). "
              "<em>Del scroll al “jale”: cómo se recluta en TikTok</em>. Seminario sobre Violencia y Paz, "
              "El Colegio de México.</li>")


def local(u):
    return str(u).replace(NS, "") if str(u).startswith(NS) else None


def lit(g, s, p, lang):
    for o in g.objects(s, p):
        if getattr(o, "language", None) == lang:
            return str(o)
    if lang == "en":
        for o in g.objects(s, p):
            if getattr(o, "language", None) is None:
                return str(o)
    return None


def code(u):
    n = local(u)
    if n:
        return f'<a href="#{n}"><code>:{n}</code></a>'
    if isinstance(u, rdflib.URIRef) and str(u).startswith(str(XSD)):
        return f"<code>{str(u).replace(str(XSD), '')}</code>"
    return f"<code>{html.escape(str(u))}</code>"


def restriction_text(g, b):
    p = g.value(b, OWL.onProperty)
    f = g.value(b, OWL.someValuesFrom)
    if p is not None and f is not None:
        return f"{code(p)} <em>some</em> {code(f)}"
    return None


def term_block(g, s, kind):
    n = local(s)
    en = lit(g, s, RDFS.label, "en") or n
    es = lit(g, s, RDFS.label, "es")
    cm = lit(g, s, RDFS.comment, "en")
    rows = []
    if kind == "class":
        sup = [code(o) for o in g.objects(s, RDFS.subClassOf) if isinstance(o, rdflib.URIRef)]
        sup += [restriction_text(g, o) for o in g.objects(s, RDFS.subClassOf)
                if isinstance(o, rdflib.BNode) and restriction_text(g, o)]
        sub = sorted(code(x) for x in g.subjects(RDFS.subClassOf, s) if local(x))
        dis = [code(o) for o in g.objects(s, OWL.disjointWith)] + [code(x) for x in g.subjects(OWL.disjointWith, s)]
        cm_ = [html.escape(str(o)) for o in g.objects(s, SKOS.closeMatch)]
        if sup: rows.append(("Subclass of", ", ".join(sup)))
        if sub: rows.append(("Superclass of", ", ".join(sub)))
        if dis: rows.append(("Disjoint with", ", ".join(dis)))
        if cm_: rows.append(("Close match", ", ".join(f'<a href="{c}">{c}</a>' for c in cm_)))
    else:
        d = g.value(s, RDFS.domain); r = g.value(s, RDFS.range)
        if d is not None: rows.append(("Domain", code(d)))
        if r is not None: rows.append(("Range", code(r)))
    see = [str(o) for o in g.objects(s, RDFS.seeAlso)]
    if see: rows.append(("See also", ", ".join(f'<a href="{html.escape(u)}">{html.escape(u)}</a>' for u in see)))
    note = lit(g, s, SKOS.note, "en")
    if note: rows.append(("Note", html.escape(note)))
    out = [f'<div class="term" id="{n}">', f"<h3><code>:{n}</code> &mdash; {html.escape(en)}</h3>"]
    if es: out.append(f'<p class="lang">es: <em>{html.escape(es)}</em></p>')
    if cm: out.append(f'<p class="comment">{html.escape(cm)}</p>')
    if rows:
        out.append("<table class='meta'>")
        out += [f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows]
        out.append("</table>")
    out.append("</div>")
    return "\n".join(out)


def main():
    g = rdflib.Graph(); g.parse(TTL)
    old = OUT.read_text(encoding="utf-8")
    style = re.search(r"<style>.*?</style>", old, re.S).group(0)
    tail = re.search(r"<h2>Alignment with HUTRO</h2>.*?(?=<footer)", old, re.S).group(0)
    if "Del scroll" not in tail:
        tail = tail.replace("</ul>", COLMEX_REF + "\n</ul>", 1)

    kinds = [("Classes", OWL.Class, "class"), ("Object properties", OWL.ObjectProperty, "prop"),
             ("Datatype properties", OWL.DatatypeProperty, "prop")]
    terms = {k: sorted((s for s in set(g.subjects(RDF.type, t)) if local(s)), key=lambda x: local(x).lower())
             for k, t, _ in kinds}

    meta = [
        ("Version", g.value(ONT, OWL.versionInfo)), ("Version IRI", f"<code>{g.value(ONT, OWL.versionIRI)}</code>"),
        ("Issued", g.value(ONT, DCTERMS.issued)), ("Modified", g.value(ONT, DCTERMS.modified)),
        ("Creator", g.value(ONT, DC.creator)), ("Contributor", g.value(ONT, DCTERMS.contributor)),
        ("Licence", f'<a href="{g.value(ONT, DCTERMS.license)}">{g.value(ONT, DCTERMS.license)}</a>'),
        ("Ontology IRI", "<code>https://w3id.org/ratr-o</code>"), ("Profile", "OWL 2 QL (DL-Lite fragment)"),
        ("Download", '<a href="ratr-o.ttl">ratr-o.ttl</a> (Turtle)'),
        ("See also", '<a href="https://bioportal.bioontology.org/ontologies/HUTRO">HUTRO on BioPortal</a>'),
    ]
    titles = [str(o) for o in g.objects(ONT, DC.title)]
    title_en = next(t for t in titles if "Ontology" in t)
    title_es = next((t for t in titles if "Ontología" in t), "")
    abstract = lit(g, ONT, RDFS.comment, "en")

    h = ["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
         f"<title>{html.escape(title_en)}</title>", style, "</head>", "<body>",
         f"<h1>{html.escape(title_en)}</h1>", f"<p><em>{html.escape(title_es)}</em></p>", "",
         '<div class="meta-box">', "<dl>"]
    h += [f"  <dt>{k}</dt><dd>{v}</dd>" for k, v in meta if v is not None]
    h += ["</dl>", "</div>", "", "<h2>Abstract</h2>", f"<p>{html.escape(abstract)}</p>", "",
          "<h2>v1.9 module: social-media criminal recruitment</h2>",
          "<p>Derived from El Colegio de México (2025), <em>Del scroll al “jale”</em>. The four QCA conditions of the report "
          "(NR, ECC, AVC, A) are classes of posts; the three recruitment stories are subclasses with the necessary direction "
          "axiomatised and the sufficient direction (a conjunction, outside OWL 2 QL) computed in the mapping. Entry points: "
          f"{code(rdflib.URIRef(NS + 'SocialMediaItem'))}, {code(rdflib.URIRef(NS + 'DirectRecruitmentPost'))}, "
          f"{code(rdflib.URIRef(NS + 'SocialMediaRecruitmentSignal'))}, {code(rdflib.URIRef(NS + 'LexiconTerm'))}. "
          'Design note: <a href="https://github.com/teamdaniela-png/ramona-vkg/blob/main/docs/MODULE_SOCIAL_RECRUITMENT.md">MODULE_SOCIAL_RECRUITMENT.md</a>.</p>',
          "", "<h2>Table of contents</h2>"]
    for k, _, _ in kinds:
        h.append(f"<h3>{k} ({len(terms[k])})</h3>")
        h.append('<ul class="toc">' + "".join(f'<li><a href="#{local(s)}"><code>:{local(s)}</code></a></li>' for s in terms[k]) + "</ul>")
    for k, _, kind in kinds:
        h.append(f"\n<h2>{k}</h2>")
        h += [term_block(g, s, kind) for s in terms[k]]
    h += ["", tail.rstrip(), "",
          '<footer style="margin-top:3em;color:#888;font-size:.85em;border-top:1px solid #eee;padding-top:1em;">',
          "Prepared by Daniela Camberos, Ramona AI, for the BMEIA Dialogue Residency at TU Wien, Institute of Logic and Computation (2 November to 2 December 2026).",
          'Licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.', "</footer>", "</body>", "</html>", ""]
    OUT.write_text("\n".join(h), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: " + ", ".join(f"{k} {len(v)}" for k, v in terms.items()))
    write_serialisations(g)


def write_serialisations(g):
    """Keep the RDF/XML, JSON-LD and N-Triples copies in step with the Turtle.

    https://w3id.org/ratr-o negotiates on the media type the client asks for, so these three
    files have to exist and have to say the same thing as ratr-o.ttl. They are generated, not
    edited: FOOPS! reported the ontology as unavailable in RDF when only Turtle was served.
    """
    for fmt, ext in (("pretty-xml", "rdf"), ("json-ld", "jsonld"), ("nt", "nt")):
        out = OUT.with_suffix("." + ext)
        g.serialize(destination=str(out), format=fmt)
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
