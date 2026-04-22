# Rigor statement — Ramona VKG

Any reviewer inspecting the repository should find this document first. It documents, in plain terms, the provenance of every number cited in `docs/DATASET_STATS.md` and what is or is not an observed fact.

## What is an observed fact

- **1,332 offers in `db/05_seed_cases_v1_2.sql`** — each row is anchored to a real press article URL via its `evidence_source`. The offer row does not reproduce the article text (copyright-safe); it records the categorical signals that the rule-based classifier extracted from the article. **The press articles are real. The offers are synthesised structured records that summarise each real article.**
- **50 offers in `db/03_seed_cases.sql`** — hand-written at the start of the project, inspired by specific publicly documented Mexican cases named in `docs/EVIDENCE_SOURCES.md`. They do not reproduce any real victim's file. They are labelled as synthetic-inspired in the file header.
- **1,771 trafficking routes in `db/06_ctdc_routes.sql`** — every route is a unique (citizenship, country_of_exploitation) pair with at least 3 attested victims in the CTDC Global Synthetic Dataset v2025. The CTDC dataset itself is a differentially-private synthetic release from IOM and partners; it is not observed victim records, it is a privacy-preserving release. This distinction is stated up-front in `docs/DATASET_STATS.md`.
- **38 survivor-testimony patterns + 50 deep-textual patterns in `db/07_press_patterns.sql` and `db/10_deep_patterns.sql`** — each pattern has an `observed_count` equal to the number of press articles whose text matched the pattern's regex. Zero inference beyond the regex match.
- **101 FraudScheme exemplars in `db/09_fraudscheme_examples.sql`** — each row is a real press article URL plus the single FraudScheme it was assigned by the rule-based detector. The detector's code is in `scripts/enrich_data.py`. Reviewers can reproduce every assignment.
- **248 countries in `db/08_enriched_countries.sql`** — the full ISO 3166-1 alpha-3 list. Each row is flagged with `attested_in_ctdc` TRUE or FALSE so the reviewer knows which 92 of the 248 are supported by at least one CTDC victim record.

## What is not in the data and why

- **There are no synthetic offers derived from CTDC records.** An earlier draft of the repo included 668 offers of this kind labelled `[Sintetizado desde CTDC synthetic record N]`. They were removed for rigor: a "job offer" is not an observable concept in CTDC, and synthesising one from a victim record without attestation would mix observation layers. The repo ships with 1,382 offers only (1,332 press + 50 hand-written seed).
- **There are no invented document references.** Every `rdfs:seeAlso` and `skos:closeMatch` in `ontology/ratr-o.ttl` points to a real, reachable URL: UNODC documents, UNICEF pages, ILO publications, FIFPro reports, Palermo Protocol on OHCHR, HUTRO on BioPortal, CTDC on ctdatacollaborative.org.
- **There are no fabricated victims, recruiters or employers.** Every recruiter is a deterministic SHA-256 stub computed from the press article ID. Every employer is either NULL or references a real institution named in a real press article.
- **There are no invented FraudSchemes.** Each of the 24 FraudScheme subclasses cites at least one official source in its `rdfs:seeAlso` or `rdfs:comment`:
  - UNODC (for OrganRemoval, BeggingRing, AgriculturalBondage, ConstructionBondage)
  - UNICEF + REDIM (for ForcedChildMarriage, ChildRecruitmentCriminal, GangRecruitmentSchools)
  - ILO (for FishingVessel, ConstructionBondage, AgriculturalBondage)
  - FIFPro (for SportsTalent)
  - Palermo Protocol (for all that invoke trafficking purpose)
  - Secretaría de las Mujeres Oaxaca (for ForcedChildMarriage recognition as trata)
  - ENADID 2014 statistics (for ForcedChildMarriage prevalence)
  - Gobierno de Zapopan (for GangRecruitmentSchools prevention programme)
  - CTDC GTM→USA corridor data (for CentralAmericanMigrantLabour)

## What the ontology does not claim

- It does not claim that a given offer will produce a given outcome. `:leadsToExploitation` is only asserted when the press article or CTDC record confirms an exploitation outcome.
- It does not attribute a specific FraudScheme to a victim without evidence. The `:victimOfFraudScheme` relation is asserted only for victims whose source article or CTDC record provides the signal that the detector fires on.
- It does not claim completeness. The 1,771 routes are only those with ≥3 CTDC victims. The 1,400 scraped articles are a rolling subset of what Google News RSS returned for 23 Spanish-language queries between 21 and 22 April 2026. Both numbers will grow as the scraper runs.

## Numerical gaps that are deliberately left open

- **Ontology triples: 992, not 1,000.** I did not pad to a round number. 992 is the honest count of triples RDF-serialised from the TTL.
- **Seed offers: 1,382, not 2,000.** See the "no synthetic offers derived from CTDC" section above.
- **Countries attested in CTDC: 92 of 248.** The other 156 are catalog entries flagged as such.

## How to verify

- `python -c "import rdflib; g=rdflib.Graph(); g.parse('ontology/ratr-o.ttl','turtle'); print(len(g))"` returns the triple count.
- `grep -c 'INSERT INTO offers' db/03_seed_cases.sql db/05_seed_cases_v1_2.sql` returns the offer count.
- `grep -c '^  (' db/08_enriched_countries.sql` returns 248.
- `scripts/test_queries.sh` runs all 30 reference SPARQL queries against the Ontop endpoint. Output is deterministic given the same Postgres state.

## Licences

- Ontology (RATR-O): CC BY 4.0.
- Demonstrator code, scripts and SQL: Apache 2.0.
- CTDC Global Synthetic Dataset: CC BY 4.0, IOM and partners, downloaded by each user from the CTDC website with attribution.
- Press article references: URL attribution under fair dealing; no article text is reproduced in the repository.

Author: Daniela Camberos, Ramona AI.
Reviewer: Prof. Magdalena Ortiz, TU Wien, Institute of Logic and Computation (proposed).
Last updated: 22 April 2026.
