# Ramona AI — Virtual Knowledge Graph Observatory

A Virtual Knowledge Graph (VKG) over a public-interest human-trafficking observatory, built on the ontology-based-data-access paradigm of Xiao, Ding, Cogrel and Calvanese (2019). Prepared for the BMEIA Dialogue Residency at the Institute of Logic and Computation, TU Wien, 2 November to 2 December 2026.

## What this repository contains

- **Postgres 16** with Ramona's operational schema (offers, recruiters, platforms, red flags, classifications, survivor patterns, trafficking routes, and provenance) plus the v1.0 observatory extension (victim-centric tables aligned to CTDC).
- **RATR-O v1.10.6** (`ontology/ratr-o.ttl`, persistent IRI `https://w3id.org/ratr-o`): the Ramona Anti-Trafficking and Recruitment-fraud Ontology in OWL 2 QL (114 classes, 69 object properties, 103 datatype properties, every one of them carrying a definition), aligned to the generalisable fragment of HUTRO (Human Trafficking Ontology, Danial Zemchal Tesfahans, BioPortal, 2025) on eight concepts, recorded by concept label in a `skos:note` rather than by `skos:closeMatch`: HUTRO's submission declares the placeholder namespace `http://www.example.com` and BioPortal serves it behind a bot challenge, so its concept IRIs could not be verified. In profile by the OWL API checker and consistent under HermiT together with the full ABox: `docs/validation/VALIDATION_REPORT.md`, `docs/AUDIT_O1_SUMMARY.md`.
- **UML-style class diagrams** of the ontology, six sheets generated from the Turtle file (`docs/diagrams/`).
- **Ontop mapping** (`mappings/ramona.obda`) connecting the Postgres schema to RATR-O.
- **Ontop mapping in W3C R2RML** (`mappings/ramona.r2rml.ttl`), generated from the native one and verified to produce the same graph.
- **SPARQL endpoint** served by Ontop on port 8080 once the Docker stack is up.
- **40 reference SPARQL queries** (`queries/`, Q1 to Q40) answering 36 competency questions (`docs/COMPETENCY_QUESTIONS.md`).
- **Real offer corpus (v1.10)**: 352 real offer descriptions extracted from press, of which **295 are verified** and loaded (167 in Mexico), with provenance and verbatim quotes (`data/real/`, `docs/results/REAL_OFFERS_RESULTS.md`). The 55 doubtful and 2 discarded ones are kept in the CSV with their audit status and are not loaded.
- **Social-media criminal-recruitment module (v1.9)**: classes for the conditions and recruitment stories of El Colegio de México (2025), *Del scroll al "jale"*, a 79-term TikTok recruitment lexicon and 1,500 synthetic items (`docs/MODULE_SOCIAL_RECRUITMENT.md`, `data/synthetic/README.md`).
- **A multi-source dataset pipeline** under `scripts/`: press scraping (Mexico + LatAm), CTDC (IOM) ingestion, rule-based classification into Type A (classic red flags) and Type B (credible-lethal patterns) tracks.
- **Evidence source catalogue** (`docs/EVIDENCE_SOURCES.md`) and **CTDC–HUTRO–RATR-O mapping workbook** (`docs/CTDC_HUTRO_RATRO_mapping.xlsx`).

No personally identifiable information appears anywhere in the demo. All victim records are anonymised: CTDC records use Microsoft Research's differential-privacy synthetic generation, and press records are aggregated at the article level with outlet, title, URL and structured classification only.

## The "nobody is exempt" framing

The observatory publishes two parallel classifications for every case:

| Track | What it captures | Examples |
|-------|------------------|----------|
| **Type A — classic red flags** | The 7 red flags from Ramona's public infographic: high salary, flexible hours, no experience needed, advance payment, urgent acceptance, distant interview with paid travel, job in another state. | Obvious scam-style offers. |
| **Type B — credible-lethal patterns** | Plausible offers (market salary, realistic role) whose signal is logistic: no company logo, nameless WhatsApp, meet at a multi-use building, come alone, no ID, Messenger-to-WhatsApp funnel, personal-data filtering, atypical hours, last-minute relocation. | The Edith Guadalupe family of cases. |

**On the Type-A and Type-B distribution:** the press corpus is a corpus of documented cases, not a sample, so no prevalence or ratio between the two tracks is derived from it. Press articles mostly report outcomes rather than the terms of the offer; `docs/CLASSIFIER_VALIDATION.md` has the measurement.

## Prerequisites

- Docker Desktop (or any Docker engine) with Docker Compose v2.
- About 1 GB of free disk and 2 GB of free memory.
- Python 3.11+ for the ingestion and scraping scripts.
- A browser for the Ontop SPARQL UI.

## Start the VKG demo

The stack below is the demonstrator of Objective 3. The ontology, the mappings and the queries can be
validated without it: `scripts/offline_vkg/run_all.sh` loads the same `db/*.sql` files, executes the
same mapping file and runs the same 40 queries, and `docs/validation/` has the results.

Ontop's image ships no JDBC driver. Download the PostgreSQL one once:

```bash
mkdir -p jdbc
curl -L -o jdbc/postgresql-42.7.4.jar \
  https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar
```

Then, from this directory:

```bash
docker compose up -d
```

First run:
1. pulls Postgres 16 and Ontop 5.2.0;
2. creates the `ramona` database and runs the fourteen files `db/01_schema.sql` to `db/14_route_victim_counts.sql`, in order, via `/docker-entrypoint-initdb.d/`;
3. starts Ontop with `ontology/ratr-o.ttl` + `mappings/ramona.obda`.

The victim tables are created empty. The CTDC release that fills them is not redistributed here; see
"Populate the observatory" below.

Wait for Ontop to report as healthy:

```bash
docker compose logs -f ontop
```

Then open http://localhost:8080/ for the SPARQL UI, or run the whole reference query suite:

```bash
./scripts/test_queries.sh
```

## Populate the observatory

```bash
# one-time
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# scrape press
python scripts/scrape_press.py --out data/raw/press.jsonl --max-per-query 100

# classify into Type A / Type B
python scripts/classify_press.py \
    --in data/raw/press.jsonl \
    --out data/processed/press_cases.jsonl \
    --summary data/processed/press_summary.json

# ingest press into Postgres
DSN="postgresql://ramona:ramona_demo@localhost:5432/ramona" \
python scripts/ingest_press.py --in data/processed/press_cases.jsonl

# ingest CTDC (once you have the CSV from https://www.ctdatacollaborative.org/page/global-synthetic-dataset)
DSN="postgresql://ramona:ramona_demo@localhost:5432/ramona" \
python scripts/ingest_ctdc.py --csv ~/Downloads/ctdc_global_synthetic_v2025.csv
```

## Reference queries

| File | What it answers |
|------|-----------------|
| `Q1_highrisk_by_platform.rq` | High-risk and fraudulent offers grouped by platform (Ramona operational). |
| `Q2_multicountry_recruiters.rq` | Cross-border recruiters with multiple flags this quarter. |
| `Q3_pattern_matches.rq` | Offers matching survivor patterns, plus source that documents each pattern. |
| `Q4_route_unclassified.rq` | Offers on a known trafficking route that have not been classified. |
| `Q5_cjng_salary_pattern.rq` | Offers matching the CJNG post-Rancho Izaguirre pattern. |
| `Q6_edith_pattern_bundle.rq` | Offers bundling the Edith Guadalupe credible-lethal patterns. |
| `Q7_messenger_whatsapp_funnel.rq` | Messenger-to-WhatsApp funnel with personal-data filtering. |
| `Q8_fraudulent_counts_by_country.rq` | Confirmed-fraudulent offers by country, with average risk score. |
| `Q9_ctdc_exploitation_by_country.rq` | CTDC victims by country of exploitation and exploitation type. |
| `Q10_type_b_only_cases.rq` | Press cases that match Type B patterns but not Type A red flags. |
| `Q11_recruitment_channels_distribution.rq` | First-contact communication tool distribution across all sources. |
| `Q12_cross_source_age_gender.rq` | Age × gender × exploitation type (requires ≥3 victims per cell). |
| `Q13_means_of_control_stack.rq` | Means of control by exploitation type. |
| `Q14_mexico_press_vs_ctdc.rq` | Mexico: press-documented vs CTDC-registered victims (cross-source federation). |
| `Q15_fraudscheme_by_country.rq` | Fraud schemes by country. |
| `Q16_palermo_triad_coverage.rq` | Coverage of the Palermo triad (action, means, purpose) per TIP event. |
| `Q17_scheme_vs_tool_heatmap.rq` | Fraud scheme by communication tool. |
| `Q18_age_gender_per_scheme.rq` | Demographic profile (age, gender) per fraud scheme. |
| `Q19_outlets_by_scheme.rq` | Press outlets that document each scheme. |
| `Q20_type_b_over_a_by_country.rq` | Offers matching only credible-lethal patterns and offers matching only classic red flags, by country. Not a prevalence estimate; see `docs/CLASSIFIER_VALIDATION.md`. |
| `Q21_pattern_cooccurrence.rq` | Pairs of patterns that co-occur on offers from the same source. |
| `Q22_recruitment_x_exploitation.rq` | Recruitment method by exploitation type (CTDC). |
| `Q23_whatsapp_funnel_schemes.rq` | Schemes that share WhatsApp as the first channel. |
| `Q24_new_routes_from_press.rq` | Routes documented in the press and not attested in CTDC. |
| `Q25_trend_by_year.rq` | Victims registered in CTDC by year. |
| `Q26_means_of_control_network.rq` | Co-occurrence of means of control (CTDC). |
| `Q27_vulnerability_x_exploitation.rq` | Vulnerability factor by exploitation type. |
| `Q28_crossborder_with_press.rq` | Cross-border CTDC corridors that also have press coverage. |
| `Q29_edith_cohort.rq` | Offers matching credible-lethal patterns and none of the classic red flags. |
| `Q30_schemes_in_both_sources.rq` | Fraud schemes attested in CTDC and in the press. |
| `Q31_tiktok_dm_plus_group_code.rq` | Social-media posts that combine a call to a private channel with a coded reference to a criminal group. |
| `Q32_minor_self_application.rq` | Comments in which an adolescent offers themselves to a criminal group. |
| `Q33_existential_forced_criminality.rq` | Offers that exhibit some forced-criminality scheme (exercises an existential axiom). |
| `Q34_recruitment_stories.rq` | Posts per Colmex recruitment story, and direct-recruitment posts that are also job offers. |
| `Q35_lexicon_false_positive_rate.rq` | Lexicon terms that also fire on posts that are not recruitment. |
| `Q36_who_is_targeted_mx.rq` | Who real recruitment offers in Mexico target. |
| `Q37_where_offers_mx.rq` | Where real recruitment offers in Mexico are located. |
| `Q38_verbatim_wording.rq` | Verbatim wording of real offers, with the source. |
| `Q39_type_a_vs_type_b_real.rq` | Real offers with at least one red flag: classic only, credible-lethal only, or both. Not a prevalence estimate. |
| `Q40_criminal_recruitment_channels.rq` | Platforms through which real criminal-recruitment offers arrive. |

Which of these return rows over the shipped seeds, which need the CTDC release loaded, and why the
rest return none, is in `docs/validation/QUERY_EXECUTION_REPORT.md`.

## Layout

```
ramona_vkg_demo/
├── README.md
├── docker-compose.yml
├── requirements.txt
├── db/                                     # 14 files, run in order by Postgres on first start
│   ├── 01_schema.sql ... 03_seed_cases.sql # operational schema and the 47 hand-curated offers
│   ├── 04_schema_extension_v1.sql          # victim-centric extension and reference vocabularies
│   ├── 05 ... 12                           # press-synthesised offers, CTDC routes, patterns, countries, social module, verified press offers
│   ├── 13_offer_provenance.sql             # offer-to-source links and source kinds
│   └── 14_route_victim_counts.sql          # victim counts of the CTDC corridors
├── ontology/
│   ├── ratr-o.ttl                          # RATR-O v1.10.6 in OWL 2 QL, aligned to HUTRO
│   ├── ratr-o.rdf                          # the same graph in RDF/XML, for content negotiation
│   ├── ratr-o.jsonld                       # the same graph in JSON-LD
│   ├── ratr-o.nt                           # the same graph in N-Triples
│   └── ratr-o.html                         # generated documentation
├── mappings/
│   ├── ramona.obda                         # Ontop native mapping, 173 mapping assertions
│   └── ramona.r2rml.ttl                    # the same in W3C R2RML, generated by scripts/obda_to_r2rml.py
├── ontop/
│   └── ontop.properties
├── queries/
│   └── Q1 ... Q40_*.rq                     # the 40 reference queries listed above
├── scripts/
│   ├── scrape_press.py                     # Google News RSS + trafilatura
│   ├── classify_press.py                   # Type A / Type B rule-based classification
│   ├── ingest_press.py                     # press → Postgres observatory tables
│   ├── ingest_ctdc.py                      # CTDC CSV → Postgres observatory tables
│   ├── offline_vkg/                        # validate mappings and queries without Docker
│   └── test_queries.sh
├── data/
│   ├── raw/                                # scraper output (JSONL, git-ignored)
│   └── processed/                          # classified output (JSONL + summary JSON)
└── docs/
    ├── diagrams/                           # UML-style class diagrams, generated by scripts/gen_uml_diagrams.py
    ├── COMPETENCY_QUESTIONS.md             # the 36 competency questions and the query answering each
    ├── MAPPING_COVERAGE.md                 # which terms a mapping produces and which it does not
    ├── HUTRO_vs_RATRO_comparison.md        # the alignment to HUTRO
    ├── validation/                         # validation report and the execution of the 40 queries
    ├── EVIDENCE_SOURCES.md                 # real-world sources behind every pattern and route
    └── CTDC_HUTRO_RATRO_mapping.xlsx       # mapping workbook prepared for Prof. Ortiz
```

## Stopping and cleaning up

```bash
docker compose down        # stop containers, keep the volume
docker compose down -v     # stop and wipe the Postgres volume
```

## Credits and licence

- Ontology (RATR-O), documentation, competency questions and synthetic data: CC BY 4.0 (full text in [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0)).
- Code (SQL, OBDA mappings, SPARQL queries, scripts, Docker setup): Apache 2.0 (full text in [`LICENSE`](LICENSE)).
- Third-party material in `data/raw/` and the press quotes in `data/real/` keep the terms of their original sources and are included for research reference only.
- CTDC Global Synthetic Dataset: IOM and partners, CC BY 4.0 with source attribution.
- HUTRO: Danial Zemchal Tesfahans, BioPortal, 2025.
- Framework: Xiao, G., Ding, L., Cogrel, B. and Calvanese, D. (2019). *Virtual Knowledge Graphs: An Overview of Systems and Use Cases.* Data Intelligence, 1(3), 201–223. DOI: 10.1162/dint_a_00011.
- Ontop: Calvanese et al. (2017), https://ontop-vkg.org.

Prepared by Daniela Camberos (Ramona AI) for the Dialogue Residency at TU Wien, Institute of Logic and Computation.
