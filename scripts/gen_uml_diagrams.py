#!/usr/bin/env python3
"""Generate the UML-style class diagrams of RATR-O from ontology/ratr-o.ttl.

Nothing about the ontology is typed in by hand here. Each sheet below only says which classes
to draw and where; the class names, the attributes (datatype properties and their ranges), the
associations (object properties with their domain and range), the generalisations, the
disjointness constraints and the existential restrictions are all read from the Turtle file.
The script fails if a class or an object property of the ontology ends up on no sheet.

Reading the notation:
  box                 owl:Class; attributes are the datatype properties whose domain it is
  arrow with a name   object property, from its domain to its range
  hollow triangle     rdfs:subClassOf, pointing at the superclass
  {subsets p}         rdfs:subPropertyOf p        {inverse of p}   owl:inverseOf p
  «subclasses»        direct subclasses listed instead of drawn, to keep a sheet legible

Output: docs/diagrams/ratr-o-uml-<n>-<name>.svg
"""
from __future__ import annotations
import math, sys
from collections import defaultdict
from pathlib import Path
import rdflib
from rdflib.namespace import OWL, RDF, RDFS

ROOT = Path(__file__).resolve().parent.parent
TTL = ROOT / "ontology" / "ratr-o.ttl"
OUT = ROOT / "docs" / "diagrams"
NS = "https://w3id.org/ratr-o#"

g = rdflib.Graph(); g.parse(TTL, format="turtle")
def L(u):
    u = str(u)
    if u.startswith(NS): return u[len(NS):]
    if "XMLSchema#" in u: return "xsd:" + u.split("#")[-1]
    if u.endswith("rdf-schema#Literal"): return "rdfs:Literal"
    return u.split("#")[-1]

VERSION = str(g.value(rdflib.URIRef("https://w3id.org/ratr-o"), OWL.versionInfo))
CLASSES = sorted(L(s) for s in g.subjects(RDF.type, OWL.Class) if str(s).startswith(NS))
SUP = defaultdict(list); SUB = defaultdict(list)
for s, _, o in g.triples((None, RDFS.subClassOf, None)):
    if str(s).startswith(NS) and str(o).startswith(NS):
        SUP[L(s)].append(L(o)); SUB[L(o)].append(L(s))
ATTRS = defaultdict(list)
for p in g.subjects(RDF.type, OWL.DatatypeProperty):
    for d in g.objects(p, RDFS.domain):
        ATTRS[L(d)].append("%s : %s" % (L(p), L(g.value(p, RDFS.range))))
for k in ATTRS: ATTRS[k].sort(key=str.lower)
OPS = []
for p in sorted(g.subjects(RDF.type, OWL.ObjectProperty), key=L):
    if not str(p).startswith(NS): continue
    dom = g.value(p, RDFS.domain); rng = g.value(p, RDFS.range)
    tags = ["subsets " + L(x) for x in g.objects(p, RDFS.subPropertyOf)] + \
           ["inverse of " + L(x) for x in g.objects(p, OWL.inverseOf)]
    OPS.append((L(p), L(dom) if dom is not None else "owl:Thing", L(rng), tags))
CONSTRAINTS = defaultdict(list)
for s, _, o in g.triples((None, RDFS.subClassOf, None)):
    if (o, RDF.type, OWL.Restriction) in g:
        CONSTRAINTS[L(s)].append("⊑ ∃ %s . %s" % (L(g.value(o, OWL.onProperty)), L(g.value(o, OWL.someValuesFrom))))
DISJ = defaultdict(set)
for s, _, o in g.triples((None, OWL.disjointWith, None)):
    for par in set(SUP[L(s)]) & set(SUP[L(o)]):
        DISJ[par].add(tuple(sorted((L(s), L(o)))))

# ---------------------------------------------------------------- sheets
# name -> (title, canvas (w, h), {class: (x, y[, options])}, edges to leave to another sheet)
# options: "c" compact (no attributes; they are on another sheet), "s" list direct subclasses
SHEETS = [
 ("1-core", "Core: offers, agents, platforms, routes and risk", (1660, 1120), {
    "Platform": (50, 50, "s"), "Country": (50, 420), "TraffickingRoute": (50, 650),
    "Candidate": (50, 890), "Submission": (50, 1000),
    "CriminalRecruitmentOffer": (520, 120), "JobOffer": (610, 250),
    "Agent": (930, 30), "Recruiter": (1330, 50), "Employer": (1330, 180),
    "Language": (1260, 300), "RiskClassification": (1230, 420, "s"), "RedFlag": (1200, 690, "s"),
    "SurvivorTestimonyPattern": (430, 990, "c"), "EvidenceSource": (760, 990, "c"),
    "FraudScheme": (1010, 990, "c"),
  }, {"recruiterCountry", "recruitsFor", "candidateDefraudedBy", "schemeTypicalRoute", "operatesIn",
      "derivedFrom", "evidenceFor", "observedInCountry"}),
 ("2-victims-palermo", "Victim records, TIP events and the Palermo Protocol triad", (1560, 1090), {
    "AgeGroup": (60, 50), "Gender": (330, 40), "VulnerabilityFactor": (560, 50),
    "DemographicProfile": (300, 200), "Country": (310, 480, "c"),
    "Victim": (700, 290),
    "TypeOfExploitation": (1200, 60), "RecruitmentMethod": (1200, 200), "CommunicationTool": (1200, 340),
    "TransportationMeans": (1200, 480), "DocumentationType": (1200, 620, "s"),
    "Agent": (60, 700, "c"), "TIPEvent": (700, 700),
    "PalermoAction": (260, 890, "s"), "PalermoMeans": (640, 890, "s"), "PalermoPurpose": (1080, 890, "s"),
  }, set()),
 ("3-fraud-schemes", "Fraud schemes and what each one is tied to", (1660, 1000), {
    "FraudScheme": (620, 250, "s"),
    "Recruiter": (60, 60, "c"), "Candidate": (60, 210, "c"), "Country": (300, 360, "c"),
    "TraffickingRoute": (60, 520, "c"), "CommunicationTool": (60, 680, "c"), "AgeGroup": (60, 840, "c"),
    "Gender": (420, 880, "c"), "TypeOfExploitation": (720, 900, "c"),
    "PressArticle": (1240, 60, "c"), "JobOffer": (1240, 240, "c"), "Victim": (1240, 400, "c"),
    "PalermoAction": (1240, 560, "c"), "PalermoMeans": (1240, 700, "c"), "PalermoPurpose": (1160, 880, "c"),
  }, {"victimOfOffer", "exploitedInCountry", "contactedThrough", "victimOfExploitation", "associatedWithRoute",
      "inCountry", "leadsToExploitation", "exhibitsAction", "exhibitsMeans", "exhibitsPurpose",
      "originCountry", "destinationCountry", "offeredByRecruiter"}),
 ("4-social-media", "Social-media criminal-recruitment module", (1660, 900), {
    "Platform": (80, 80, "c"), "SocialMediaItem": (560, 50),
    "SocialMediaPost": (250, 300, "s"), "SocialMediaComment": (740, 330, "s"),
    "DirectRecruitmentPost": (60, 620), "JobOffer": (520, 640, "c"), "CriminalRecruitmentOffer": (520, 780),
    "RedFlag": (1280, 50, "c"), "SocialMediaRecruitmentSignal": (1220, 220, "s"),
    "LexiconTerm": (1240, 560), "EvidenceSource": (1260, 780, "c"),
  }, {"exhibitsFraudScheme", "hasRedFlag", "containsRedFlag", "postedVia", "hostsOffer", "offerDocumentedIn"}),
 ("5-patterns-evidence", "Survivor-testimony patterns, official statistics and the evidence behind every fact", (1660, 900), {
    "JobOffer": (540, 50, "c"), "SurvivorTestimonyPattern": (480, 280, "s"),
    "DominanceBucket": (70, 320), "Country": (70, 520, "c"), "OfficialStatistic": (60, 660),
    "owl:Thing": (1180, 40, "c"), "EvidenceSource": (1100, 230),
    "PressArticle": (940, 610), "OpenDatasetRecord": (1150, 610), "ResearchReport": (1400, 610),
  }, {"inCountry"}),
 ("6-offer-links", "What an offer can be tied to beyond the core", (1360, 760), {
    "JobOffer": (580, 320, "c"),
    "Victim": (70, 60, "c"), "FraudScheme": (70, 320, "c"), "RecruitmentMethod": (70, 570, "c"),
    "TypeOfExploitation": (560, 600, "c"),
    "PalermoAction": (1080, 70, "c"), "PalermoMeans": (1080, 320, "c"), "PalermoPurpose": (1080, 570, "c"),
  }, {"schemePalermoAction", "schemePalermoMeans", "schemePalermoPurpose", "schemeExploitationType",
      "victimOfFraudScheme", "victimOfExploitation", "recruitedVia"}),
]

# where along a line its label sits (0 = domain end, 1 = range end), when 0.5 collides
LABEL_AT = {
    ("3-fraud-schemes", "TraffickingRoute", "TypeOfExploitation"): 0.78,
    ("1-core", "EvidenceSource", "JobOffer"): 0.74,
    ("1-core", "FraudScheme", "JobOffer"): 0.40,
    ("1-core", "JobOffer", "SurvivorTestimonyPattern"): 0.58,
}

# ---------------------------------------------------------------- drawing
CH, LH, HDR, PAD = 6.05, 15, 26, 9          # char width, line height, header height, padding
def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def wrap_names(names, width_chars=40):
    lines, cur = [], ""
    for n in names:
        if cur and len(cur) + len(n) + 2 > width_chars:
            lines.append(cur + ","); cur = n
        else:
            cur = (cur + ", " + n) if cur else n
    if cur: lines.append(cur)
    return lines

def subclass_lines(c):
    """Direct subclasses first; then, for each one that has subclasses of its own, a line that
    lists them. A class with several superclasses is listed under each, as the ontology has it."""
    direct = sorted(SUB.get(c, []))
    lines = wrap_names(direct)
    for k in direct:
        deeper = sorted(all_descendants(k))
        if deeper:
            lines += wrap_names(["under %s: %s" % (k, deeper[0])] + deeper[1:])
    return lines

def all_descendants(c):
    out = set()
    for k in SUB.get(c, []):
        out.add(k); out |= all_descendants(k)
    return out

def box_content(c, opts):
    attrs = [] if "c" in opts else list(ATTRS.get(c, []))
    extra = list(CONSTRAINTS.get(c, []))
    for pair in sorted(DISJ.get(c, [])): extra.append("{disjoint: %s, %s}" % pair)
    subs = []
    if "s" in opts and SUB.get(c):
        subs = ["«subclasses»"] + subclass_lines(c)
    return attrs, extra, subs

def box_size(c, opts):
    attrs, extra, subs = box_content(c, opts)
    lines = attrs + extra + subs
    w = max([len(c) * 7.4 + 30] + [len(l) * CH + 2 * PAD for l in lines] + [130])
    h = HDR
    for part in (attrs, extra, subs):
        if part: h += len(part) * LH + 8
    if "c" in opts and not (extra or subs): h = HDR + 6
    return w, h

def edge_point(cx, cy, w, h, tx, ty):
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0: return cx, cy
    sx = (w / 2) / abs(dx) if dx else float("inf")
    sy = (h / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s

def render(key, title, canvas, placed, skip):
    W, H = canvas
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H),
         '<defs><marker id="arr" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M0,0.8 L10,5 L0,9.2" fill="none" stroke="#333" stroke-width="1.3"/></marker>'
         '<marker id="tri" viewBox="0 0 14 14" refX="13" refY="7" markerWidth="15" markerHeight="15" orient="auto"><path d="M1,1 L13,7 L1,13 Z" fill="#fff" stroke="#333" stroke-width="1.2"/></marker></defs>',
         '<rect width="100%%" height="100%%" fill="#ffffff"/>',
         '<text x="24" y="%d" font-size="17" font-weight="bold" fill="#111">RATR-O %s. %s</text>' % (H - 34, esc(VERSION), esc(title)),
         '<text x="24" y="%d" font-size="11" fill="#555">Generated from ontology/ratr-o.ttl by scripts/gen_uml_diagrams.py. Box: class with its datatype properties. Named arrow: object property, domain to range. Hollow triangle: subclass of. Grey box: attributes drawn on another sheet.</text>' % (H - 14)]
    geo = {}
    for c, spec in placed.items():
        x, y = spec[0], spec[1]; opts = spec[2] if len(spec) > 2 else ""
        w, h = box_size(c, opts); geo[c] = (x, y, w, h, opts)
    centre = lambda c: (geo[c][0] + geo[c][2] / 2, geo[c][1] + geo[c][3] / 2)
    body, labels = [], []
    # generalisations between drawn boxes
    for c in placed:
        for par in SUP.get(c, []):
            if par in placed:
                (cx, cy), (px, py) = centre(c), centre(par)
                x1, y1 = edge_point(cx, cy, geo[c][2], geo[c][3], px, py)
                x2, y2 = edge_point(px, py, geo[par][2], geo[par][3], cx, cy)
                body.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#333" stroke-width="1.2" marker-end="url(#tri)"/>' % (x1, y1, x2, y2))
    # associations: one line per pair of boxes. When properties run both ways between the same
    # two classes the line carries an arrowhead at each end and every name says where it points.
    pairs = defaultdict(list); shown = set()
    for name, d, r, tags in OPS:
        if name in skip: continue
        if d in placed and r in placed:
            pairs[tuple(sorted((d, r)))].append((name, d, r, tags)); shown.add(name)
    for (a_, b_), props in sorted(pairs.items()):
        dirs = {(d, r) for _, d, r, _ in props}
        both = len(dirs) > 1
        d0, r0 = sorted(dirs)[0]
        (cx, cy), (tx, ty) = centre(d0), centre(r0)
        x1, y1 = edge_point(cx, cy, geo[d0][2], geo[d0][3], tx, ty)
        x2, y2 = edge_point(tx, ty, geo[r0][2], geo[r0][3], cx, cy)
        body.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#333" stroke-width="1.1" marker-end="url(#arr)"%s/>'
                    % (x1, y1, x2, y2, ' marker-start="url(#arr)"' if both else ""))
        names = []
        for name, d, r, tags in sorted(props):
            n = name + (" → " + r if both else "")
            if tags: n += " {%s}" % "; ".join(tags)
            names.append(n)
        t = LABEL_AT.get((key, a_, b_), 0.5)
        lx, ly = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        tw = max(len(n) for n in names) * 5.5 + 8; th = len(names) * 13 + 4
        labels.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#fff" fill-opacity="0.93"/>' % (lx - tw / 2, ly - th / 2, tw, th))
        for i, n in enumerate(names):
            labels.append('<text x="%.1f" y="%.1f" font-size="10.5" font-style="italic" text-anchor="middle" fill="#1a3d7c">%s</text>' % (lx, ly - th / 2 + 12 + i * 13, esc(n)))
    o += body + labels
    for c, (x, y, w, h, opts) in geo.items():
        attrs, extra, subs = box_content(c, opts)
        fill = "#eef0f2" if "c" in opts else "#fffbe8"
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#222" stroke-width="1.2"/>' % (x, y, w, h, fill))
        o.append('<text x="%.1f" y="%.1f" font-size="13" font-weight="bold" text-anchor="middle" fill="#111">%s</text>' % (x + w / 2, y + 18, esc(c)))
        yy = y + HDR
        for part, style in ((attrs, ""), (extra, ' fill="#8a2be2"'), (subs, ' fill="#444"')):
            if not part: continue
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#222" stroke-width="0.8"/>' % (x, yy, x + w, yy))
            for i, l in enumerate(part):
                o.append('<text x="%.1f" y="%.1f" font-size="11"%s>%s</text>' % (x + PAD, yy + 15 + i * LH, style, esc(l)))
            yy += len(part) * LH + 8
        bx, by = x + w, y + h
        if bx > W - 5 or by > H - 55: print("  WARNING %s: box %s runs off the canvas (%d,%d)" % (key, c, bx, by))
    o.append("</svg>")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / ("ratr-o-uml-%s.svg" % key)
    path.write_text("\n".join(o), encoding="utf-8")
    drawn = set(placed)
    listed = set()
    for c, (_, _, _, _, opts) in geo.items():
        if "s" in opts: listed |= all_descendants(c)
    return shown, drawn, listed, path

def main():
    all_shown, all_classes = set(), set()
    for key, title, canvas, placed, skip in SHEETS:
        for c in placed:
            if c != "owl:Thing" and c not in CLASSES: sys.exit("sheet %s names %s, which is not a class of the ontology" % (key, c))
        shown, drawn, listed, path = render(key, title, canvas, placed, skip)
        all_shown |= shown; all_classes |= drawn | listed
        print("wrote %s: %d boxes, %d object properties" % (path.relative_to(ROOT), len(drawn), len(shown)))
    miss_p = sorted(n for n, _, _, _ in OPS if n not in all_shown)
    miss_c = sorted(c for c in CLASSES if c not in all_classes)
    print("object properties on at least one sheet: %d of %d" % (len(OPS) - len(miss_p), len(OPS)))
    print("classes drawn or listed on at least one sheet: %d of %d" % (len(CLASSES) - len(miss_c), len(CLASSES)))
    if miss_p or miss_c:
        sys.exit("NOT COVERED  properties: %s  classes: %s" % (miss_p, miss_c))

if __name__ == "__main__":
    main()
