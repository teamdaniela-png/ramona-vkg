#!/usr/bin/env python3
"""
Materializa el ABox de las ofertas reales de prensa con las mismas reglas que los mapeos M-Press-*,
para razonar con HermiT y consultar con SPARQL sin Postgres ni Ontop.
Uso: .venv/bin/python scripts/materialize_press_abox.py /ruta/salida.ttl
"""
import csv
import hashlib
import sys
from pathlib import Path

import rdflib
from rdflib import Literal, URIRef
from rdflib.namespace import RDF, XSD

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_press_offers_module import PLATFORM, SCHEMES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
O = rdflib.Namespace("https://w3id.org/ratr-o#")
D = "https://w3id.org/ratr-o/data"
ISO2 = {"MEX": "MX", "COL": "CO", "PER": "PE", "USA": "US", "ESP": "ES", "ARG": "AR", "ECU": "EC", "VEN": "VE",
        "GTM": "GT", "BOL": "BO", "CHL": "CL", "SLV": "SV", "BRA": "BR", "DOM": "DO", "HND": "HN", "PRY": "PY", "CRI": "CR"}
PLAT_ID = {"WhatsApp": 1, "Telegram": 2, "TikTok": 5, "OCC Mundial": 6, "CompuTrabajo": 7, "Facebook": 101, "Instagram": 102, "Indeed": 103}

g = rdflib.Graph()
VER = {o["offer_uid"] for o in csv.DictReader(open(ROOT / "data/real/press_offers_verified.csv", encoding="utf-8")) if o["audit_status"] == "verificada"}
for o in csv.DictReader(open(ROOT / "data/real/press_offers_verified.csv", encoding="utf-8")):
    if o["offer_uid"] not in VER:
        continue
    u = URIRef(f"{D}/press-offer/{o['offer_uid']}")
    g.add((u, RDF.type, O.JobOffer)); g.add((u, O.extractionConfidence, Literal(o["confidence"])))
    for col, p in (("job_title", O.offeredRole), ("offer_location", O.offeredLocation), ("target_profile", O.offerTargetProfile),
                   ("verbatim_quote", O.offerVerbatimQuote), ("paraphrase", O.offerSummary), ("outcome", O.offerOutcome),
                   ("pay_period", O.offerPayPeriod)):
        if o[col]:
            g.add((u, p, Literal(o[col])))
    iso3 = "MEX" if "MEX" in o["countries"] else (o["countries"].split(";")[0] if o["countries"] else "")
    if iso3 in ISO2:
        g.add((u, O.inCountry, URIRef(f"{D}/country/{ISO2[iso3]}")))
    if PLATFORM.get(o["platform"]):
        p = URIRef(f"{D}/platform/{PLAT_ID[PLATFORM[o['platform']]]}")
        g.add((u, O.postedVia, p)); g.add((p, O.platformName, Literal(PLATFORM[o["platform"]])))
    if o["pay_amount"] and o["pay_currency"]:
        g.add((u, O.offerPayAmount, Literal(o["pay_amount"], datatype=XSD.decimal)))
        g.add((u, O.offerPayCurrency, Literal(o["pay_currency"])))
    if o["criminal_recruitment"] == "True":
        g.add((u, RDF.type, O.CriminalRecruitmentOffer))
    if o["scheme"] in SCHEMES:
        s = URIRef(f"{D}/press-offer/{o['offer_uid']}/scheme")
        g.add((u, O.exhibitsFraudScheme, s)); g.add((s, RDF.type, O[o["scheme"]]))
    for track, cls in (("type_a_flags", O.ClassicRedFlag), ("type_b_flags", O.CredibleLethalRedFlag)):
        for f in filter(None, o[track].split(";")):
            fu = URIRef(f"{D}/press-offer/{o['offer_uid']}/flag/{f}")
            g.add((u, O.hasRedFlag, fu)); g.add((fu, RDF.type, cls)); g.add((fu, O.flagType, Literal(f)))
for s in csv.DictReader(open(ROOT / "data/real/press_offer_sources.csv", encoding="utf-8")):
    if s["offer_uid"] not in VER:
        continue
    a = URIRef(f"{D}/press/{hashlib.sha1(s['url'].encode()).hexdigest()[:12]}")
    g.add((URIRef(f"{D}/press-offer/{s['offer_uid']}"), O.offerDocumentedIn, a))
    g.add((a, RDF.type, O.PressArticle)); g.add((a, O.sourceUrl, Literal(s["url"]))); g.add((a, O.sourceOutlet, Literal(s["outlet"])))
g.serialize(sys.argv[1], format="turtle")
print(f"{len(g)} triples -> {sys.argv[1]}")
