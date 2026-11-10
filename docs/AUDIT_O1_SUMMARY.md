# Audit O1 — Executive summary

**Audit date:** 10 November 2026 (first audit 22 April 2026, re-audited in full before delivery).
**Auditor:** self, to the reviewer standard of Ortiz & Šimkus (2012).
**Scope:** Objective 1 of the TU Wien Dialogue Residency proposal — the RATR-O ontology in OWL 2 QL
covering Ramona AI's operational entities.
**Version audited:** RATR-O v1.10.1.

## Bottom line

**O1 is ready for review.** No blockers and no SHOULD-grade findings remain. The ontology is in the
OWL 2 QL profile by the OWL API checker, consistent under HermiT both alone and together with the
full ABox, every term it publishes is defined, and every term used by the mappings and the queries
is declared in it.

What the delivery does **not** include: the Ontop demonstrator running over Postgres (O3, blocked on
Docker on this machine), a Zenodo DOI (`.zenodo.json` ready, not deposited), and OOPS!/FOOPS!
scans (web services, pending).

## The five defects this audit found in v1.10

They matter because each one was invisible to the checks that existed before.

| # | Defect | Why it escaped | Status |
|---|---|---|---|
| 1 | `:hasMeansOfControl` used by both mappings and by `queries/Q13` and `Q26`, never declared in the TBox | no check read the queries and the TBox together | declared, with a definition distinguishing it from `:PalermoMeans` |
| 2 | `:sourceUrl` has range `xsd:anyURI`; the v1.10 press mappings and materialiser emitted `xsd:string`, so HermiT derives `owl:Thing ⊑ owl:Nothing` | the two ABoxes were only ever reasoned separately | all three producers emit `xsd:anyURI`; merged graph consistent |
| 3 | 158 of 281 classes and properties carried a label but no definition | the script only checked for labels | every class and property now carries an `rdfs:comment` |
| 4 | annotation text referencing IRIs that are not declared (`:fraudAxis`, `:exploitationAxis`, `:traffickingAxis`, `:labour_agriculture`), and 18 Spanish labels written without accents | nothing checked prose inside annotations | comments rewritten, labels corrected |
| 5 | `db/08_enriched_countries.sql` filled `country_code CHAR(2) PRIMARY KEY` with the first two letters of the alpha-3 code; 39 keys collided, so its `ON CONFLICT` upsert overwrote Colombia with Comoros, Spain with Estonia and Argentina with Armenia, and never defined `MX` | the audit only ever read the ontology, never the seed against the schema | codes taken from the ISO 3166 tables in `pycountry`; 248 rows, 248 distinct keys, all 11 country codes the other seeds reference now resolve correctly |

Defect 5 is in the demonstrator database, not in O1, but it would have corrupted every
country-level answer the VKG gives, so it is reported here. The claim in the v1.10 validation
report that the real-offer graph was consistent under HermiT was wrong. It holds from v1.10.1 on. `docs/validation/VALIDATION_REPORT.md` says so in those words.

`scripts/audit_o1.py` now carries a check for each of the first four. Run against the v1.10 file it
reports 4 blockers and 162 SHOULD-grade findings; against v1.10.1, none.

## Verification method

`scripts/audit_o1.py` reads `ontology/ratr-o.ttl`, both mapping files and `queries/*.rq`, and checks:

1. OWL 2 QL profile conformance, including the restricted datatype map of OWL 2 Profiles §3.2.
2. Consistency hygiene — unused classes, missing labels, missing domain or range, near-duplicates.
3. Coverage — the eight entities named in Magdalena's O1 brief are present.
4. Provenance — every FraudScheme has an `rdfs:seeAlso` or a substantive `rdfs:comment`; every
   `skos:closeMatch` points to a URL.
5. Naming conventions — UpperCamelCase for classes, lowerCamelCase for properties.
6. Mapping consistency — OBDA and R2RML exist, parse, and emit datatypes that agree with the
   declared ranges.
7. Data-ontology alignment — every declared class has a materialisation path.
8. Definitions — every class and property has an `rdfs:comment`.
9. Vocabulary closure — every term used in the queries and mappings is declared in the ontology.

Independently of the script: ROBOT 1.9.11 for the profile check, HermiT for consistency, and an
HTTP check of every external URL in the ontology.

## Findings

| Severity | v1.10 | v1.10.1 |
|---|---:|---:|
| BLOCKER | 4 | **0** |
| SHOULD | 162 | **0** |
| NIT | 69 | 69 |
| NOTE | 2 | 2 |

The 69 NITs are all the same observation: a leaf class that appears in no axiom other than its own
`rdfs:subClassOf`. That is what a leaf of a taxonomy looks like, so they are accepted rather than
fixed. The 2 NOTEs record that two FraudScheme classes get their instances from
`db/09_fraudscheme_examples.sql` rather than from a mapping assertion.

## Current size

| | Count |
|---|---:|
| Classes | 114 |
| Object properties | 66 |
| Datatype properties | 101 |
| TBox triples | 1,582 |
| `skos:closeMatch` alignments to HUTRO | 8 |
| R2RML mapping triples | 1,511 |
| Competency questions / SPARQL queries | 36 / 40 |

## External citation check (10 November 2026)

39 URLs in the ontology, 27 of them external (the rest are W3C, Creative Commons or the RATR-O
namespace itself).

| Result | Count | Reading |
|---|---:|---|
| HTTP 200 | 10 | fine |
| HTTP 403 or 406 | 15 | BioPortal, OHCHR, CTDC and the REDIM blog refuse automated requests; all open in a browser |
| HTTP 500 | 1 | `oaxaca.gob.mx` child-marriage page, broken at the source |
| no response | 1 | `zapopan.gob.mx` prevention programme page |

The two that no longer serve are kept as the primary citation and an Internet Archive snapshot is
cited next to each, with a `skos:note` giving the date of the check. No citation in the ontology is
dead without a working alternative beside it.

## Statistics stated inside the ontology

| Claim | Source | Result |
|---|---|---|
| GTM → USA: 842 victims, 2009-2023 | CTDC Global Synthetic Dataset v2025 | exact match, recomputed from the CSV |
| MEX → USA: 7,037 victims, 2015-2023 | CTDC Global Synthetic Dataset v2025 | exact match |
| ENADID 2014: Chiapas 44.82%, Guerrero 42.41%, Oaxaca 39.17% | INEGI / SCJN / Secretaría de las Mujeres de Oaxaca | verified against three official sources |
| 26 items from the REDIM blog in the press corpus | `data/processed/press_summary.json` | recomputed, 26; the wording in the ontology was corrected to say items from that outlet, not articles about school recruitment |
| 1,771 trafficking routes with ≥3 victims | `scripts/extract_routes.py` over CTDC | reproducible from the committed script |
| 2,379 case-relevant press articles of 2,591 scraped | `data/processed/press_cases.jsonl` | recounted, 2,379. The April audit cited 1,332, which was that month's smaller corpus |
| ~~Type-B-only : Type-A-only ratio 9.9x~~ **withdrawn 26 June 2026** | was a rule-based classifier over press | failed validation. Press reports outcomes, not offer terms (an LLM read found the terms in ~8% of articles), so the ratio is not measurable from this source. See `CLASSIFIER_VALIDATION.md` |

No statistic in the ontology is fabricated. Every number either comes from a verified external
source or is computed by a committed script over committed data.

## Real-offer corpus, after its own audit

Of 352 offer descriptions extracted from press, 295 are **verified** (a reviewer confirmed the
offer was deceptive or criminal recruitment and quoted the sentence that proves it), 55 remain
**doubtful** and 2 were **discarded**. Only the 295 are loaded into the VKG. All figures reported
anywhere in the repository are over the 295: 167 in Mexico, 93 of those criminal recruitment,
39 verbatim quotes, and of 191 offers carrying at least one flag, 118 classic only, 38
credible-lethal only and 35 both. Two quotes that circulated earlier ("sola y sin INE", "puras
jovencitas") stayed doubtful and are not presented as confirmed data.

## FraudScheme provenance (26 named subclasses)

Every FraudScheme cites at least one authoritative source: UNODC, UNICEF, ILO, FIFPro, the Palermo
Protocol, REDIM, SCJN, the Secretaría de las Mujeres de Oaxaca, CTDC and UNODC GLOTIP, Human Rights
Watch, Polaris Project, the Environmental Justice Foundation, or the Gobierno de Zapopan. None is
undocumented and no citation is invented.

## Volume check, so nothing reads as inflated

- **Countries:** 248 loaded, keyed by the ISO 3166-1 alpha-2 code; 92 attested in CTDC. Every row
  carries an `attested_in_ctdc` flag, so a reviewer can separate catalogue from data.
- **Patterns:** 102 (14 curated from literature, 38 by regex over press, 50 by deep-textual regex).
  Each carries the exact number of articles it matched.
- **Social-media items:** 1,500, all synthetic and all carrying `:itemIsSynthetic true`, so no
  figure can mix them with real items unknowingly.
- **TBox triples:** 1,582. Not padded.

## Reproducibility

```bash
git clone https://github.com/teamdaniela-png/ramona-vkg
cd ramona-vkg
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/audit_o1.py            # this audit
python scripts/extract_routes.py      # route extraction
```

ROBOT commands are in `docs/validation/VALIDATION_REPORT.md`.

## Conclusion

The ontology is in OWL 2 QL (the DL-Lite fragment of Calvanese et al. 2007), consistent with its
full ABox, aligned to HUTRO, the Palermo Protocol, ICS-TIP and UNODC GLOTIP, defined term by term,
closed over the vocabulary its own queries and mappings use, and free of dead citations without an
archived alternative. It is submitted for review knowing that O3 and the DOI are still open.

Prepared by Daniela Camberos, Ramona AI, 10 November 2026.
For review by Prof. Magdalena Ortiz, Institute of Logic and Computation, TU Wien.
