# Audit O1 — Executive summary

**Audit date:** 10 November 2026 (first audit 22 April 2026, re-audited in full before delivery).
**Auditor:** self, to the reviewer standard of Ortiz & Šimkus (2012).
**Scope:** Objective 1 of the TU Wien Dialogue Residency proposal — the RATR-O ontology in OWL 2 QL
covering Ramona AI's operational entities.
**Version audited:** RATR-O v1.10 through v1.10.4, in four passes.

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
   external alignment either carries a verified IRI or a `skos:note` saying why it could not be verified.
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
| TBox triples | 1,704 |
| HUTRO alignments, by concept label in a `skos:note` | 8 |
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
- **TBox triples:** 1,704. Not padded.

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

## Fourth pass (v1.10.4): the artefacts nobody had executed

The third pass executed the queries and the seeds. The fourth executed the things that are published
alongside the ontology and had only ever been generated, never checked, and ran the one external
quality checker that had not been used.

**`mappings/ramona.r2rml.ttl` was executed for the first time.** It is generated from the `.obda` by
`scripts/obda_to_r2rml.py`, and anyone using a standard R2RML engine gets that file rather than the
Ontop native one, so the claim that the two say the same thing was load-bearing and untested. An
R2RML interpreter was written against the W3C recommendation and run over the same SQLite copy of the
seeds. Result: **71,963 triples from each, identical triple for triple.** The converter is faithful.
One genuine finding on the way: the generated file declared `rdf:` and `xsd:` twice, which is legal
Turtle and reads as an oversight; the generator now writes each prefix once and lets the `.obda` win.

A first run of the diff reported 71 `:termDocumentedIn` triples missing from the R2RML side. That was
wrong, and it was the interpreter's fault, not the converter's: `rr:object <IRI>` is the R2RML
shortcut for `rr:objectMap [ rr:constant <IRI> ]`, and the interpreter only looked for `rr:objectMap`.
It is recorded here because the finding was withdrawn before it was reported, which is the point of
checking a tool against a specification rather than against its own output.

**The four published serialisations were checked for isomorphism.** `ratr-o.rdf`, `.jsonld` and `.nt`
are each isomorphic to `ratr-o.ttl` at 1,704 triples, and the Turtle and the RDF/XML are both in the
OWL 2 QL profile. They are generated by `scripts/gen_ratro_html.py` so they cannot drift.

**`robot report` was run, the one external quality checker that had not been used.** 879 violations,
in exactly three rules, and the useful work was telling apart the real finding from the two
convention mismatches:

| Rule | Count | Verdict |
| --- | --- | --- |
| `multiple_labels` (ERROR) | 566 | Not a defect. OBO convention is exactly one `rdfs:label` per term; RATR-O is bilingual and gives each term an `@en` and an `@es` label. Checked term by term: no term carries two labels in the same language and none carries an untagged label. 566 is 283 terms times 2. |
| `missing_definition` (WARN) | 283 | Not a defect. The rule looks for `obo:IAO_0000115`; every one of the 283 terms carries an `rdfs:comment`. Adding an OBO annotation property to a non-OBO ontology to satisfy the checker would duplicate every definition, so it was not done. |
| `missing_superclass` (INFO) | 30 | Not a defect. The 30 are the top-level domain categories (`:JobOffer`, `:Victim`, `:Country`, `:Platform`, `:FraudScheme`, the three Palermo roots, and so on). Each was read; none belongs under another. |

The real finding came out of looking into the first rule rather than dismissing it: **82 of the 283
terms carried only an English label**, 54 object properties and 28 datatype properties, while all 114
classes and the remaining 101 properties were bilingual. The ontology was bilingual for its classes
and half bilingual for its properties. All 82 now carry a Spanish label and all 283 terms are
cleanly bilingual.

**Two more defects of my own making, both caught by checking a published artefact against the repo:**

- The commit that added the FAIR metadata and the three extra serialisations changed
  `ontology/ratr-o.ttl` while still calling it 1.10.3, so the tag `v1.10.3` and the branch disagreed
  about which graph 1.10.3 denotes. A version IRI has to identify one immutable snapshot. The version
  to cite is **1.10.4**; the tag `v1.10.3` is left pointing where it pointed, and the ontology's own
  note records the ambiguity instead of hiding it.
- Six current-state counts in the documentation were stale after the third and fourth passes: the
  README still said v1.10.1 and 66 object properties, and `1,582` TBox triples survived in
  `AUDIT_O1_SUMMARY.md`, `HANDOFF.md`, `RIGOR_STATEMENT.md` and the validation report, whose
  merged-graph row was also from the v1.10.1 run. All six now carry the counted figure: 114 classes,
  68 object properties, 101 datatype properties, 1,704 TBox triples, 71,963 ABox triples and 85,173
  in the merged graph. Statements in past tense about what an earlier version contained were left
  alone; `docs/DATASET_STATS.md` is a dated log whose last entry is v1.8 and is left as it is.

**Competency questions crossed against the queries.** All 36 name a query file that exists, no query
cites a competency question that is not in the document, and four of the 40 queries answer no
competency question of their own. The document's header said 26 questions over `Q1..Q30`; it now says
36 and names the four. Every `ratr-o` term used in all 40 queries is declared in the ontology.

**The persistent IRIs were resolved rather than assumed.** `https://w3id.org/ratr-o/1.10.1`, `/1.10.2`
and `/1.10.3` each resolve to the Turtle of their tag; a version that does not exist returns 404;
`/data/country/MEX` resolves to the documentation as designed. Note for a reader: the versioned IRIs
are served by `raw.githubusercontent.com` as `text/plain`, so a strict client may need to be told the
format.

## Conclusion

The ontology is in OWL 2 QL (the DL-Lite fragment of Calvanese et al. 2007), consistent with its
full ABox, aligned to HUTRO, the Palermo Protocol, ICS-TIP and UNODC GLOTIP, defined term by term,
closed over the vocabulary its own queries and mappings use, and free of dead citations without an
archived alternative. It is submitted for review knowing that O3 and the DOI are still open.

Prepared by Daniela Camberos, Ramona AI, 10 November 2026.
For review by Prof. Magdalena Ortiz, Institute of Logic and Computation, TU Wien.
