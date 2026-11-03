#!/usr/bin/env python3
"""
Materializa el ABox del modulo de redes (mismas reglas que los mapeos M-Social-*) a Turtle,
para probar consistencia con un razonador (HermiT via ROBOT) sin Postgres ni Ontop.
Uso: .venv/bin/python scripts/materialize_social_abox.py /ruta/salida.ttl
"""
import csv
import sys
from pathlib import Path

import rdflib
from rdflib import Literal, URIRef
from rdflib.namespace import RDF, XSD

ROOT = Path(__file__).resolve().parent.parent
O = rdflib.Namespace("https://w3id.org/ratr-o#")
D = "https://w3id.org/ratr-o/data"
SIG = {"codigo_grupo": "GroupCodeSignal", "emoji_grupo": "GroupEmojiSignal", "llamado_privado": "PrivateChannelCallSignal",
       "pago_semanal_alto": "HighWeeklyPaySignal", "apela_familia": "FamilyAppealSignal", "menciona_edad_menor": "MinorAgeMentionSignal",
       "invita_mujeres": "WomenInvitationSignal", "alcance_nacional": "NationalReachSignal",
       "hashtag_reclutamiento": "RecruitmentHashtagSignal", "fatalismo": "FatalismSignal"}

g = rdflib.Graph()
for t in csv.DictReader(open(ROOT / "data/lexicon/tiktok_reclutamiento_lexicon.csv", encoding="utf-8")):
    u = URIRef(f"{D}/lexicon/{t['term_id']}")
    g.add((u, RDF.type, O.LexiconTerm)); g.add((u, O.lexiconTermText, Literal(t["termino"])))
    if t["tipo"] == "verbatim_colmex":
        g.add((u, O.termDocumentedIn, O.ColmexScrollAlJale2025))
tiktok = URIRef(f"{D}/platform/5")
for r in csv.DictReader(open(ROOT / "data/synthetic/tiktok_reclutamiento_sintetico.csv", encoding="utf-8")):
    u = URIRef(f"{D}/social/{r['offer_id']}")
    post = r["content_type"] != "comentario"
    conds = set(filter(None, r["colmex_conditions"].split(";")))
    g.add((u, RDF.type, O.SocialMediaPost if post else O.SocialMediaComment))
    g.add((u, O.itemText, Literal(r["offer_text"]))); g.add((u, O.itemPostedOn, tiktok))
    g.add((u, O.itemPostedAt, Literal(r["first_contact_at"], datatype=XSD.dateTime)))
    g.add((u, O.itemIsSynthetic, Literal(True)))
    if r["label"] == "autopostulacion": g.add((u, RDF.type, O.SelfApplicationComment))
    if r["label"] == "respuesta_reclutador": g.add((u, RDF.type, O.RecruiterReplyComment))
    if post:
        for c, cls in (("nr", O.DirectRecruitmentPost), ("ecc", O.CriminalCultureExaltationPost),
                       ("avc", O.CriminalLifeAspirationPost), ("a", O.AcousticFramingPost)):
            if c in conds: g.add((u, RDF.type, cls))
        if {"nr", "ecc"} <= conds: g.add((u, RDF.type, O.EnrolInCrimeStoryPost))
        if {"nr", "a"} <= conds: g.add((u, RDF.type, O.EmotionalConnectionStoryPost))
        if {"ecc", "a", "avc"} <= conds: g.add((u, RDF.type, O.BelicoStoryPost))
    for s in filter(None, r["crim_flags"].split(";")):
        su = URIRef(f"{D}/social/{r['offer_id']}/signal/{s}")
        g.add((u, O.itemHasSignal, su)); g.add((su, RDF.type, O[SIG[s]]))
    for t in filter(None, r["lexicon_term_ids"].split(";")):
        g.add((u, O.itemMatchesTerm, URIRef(f"{D}/lexicon/{t}")))
g.serialize(sys.argv[1], format="turtle")
print(f"{len(g)} triples -> {sys.argv[1]}")
