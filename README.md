# Ramona AI — Virtual Knowledge Graph Observatory

A running Virtual Knowledge Graph (VKG) over a public-interest human-trafficking observatory, built on the ontology-based-data-access paradigm of Xiao, Ding, Cogrel and Calvanese (2019). Prepared for the Dialogue Residency at the Institute of Logic and Computation, TU Wien, May to July 2026.

## What this repository contains

- **Postgres 16** with Ramona's operational schema (10 tables: offers, recruiters, platforms, red flags, classifications, survivor patterns, trafficking routes, and provenance) plus the v1.0 observatory extension (victim-centric tables aligned to CTDC).
- **RATR-O v1.0** (`ontology/ratr-o.ttl`): the Ramona Anti-Trafficking Recruitment Ontology in OWL 2 QL, aligned to the generalisable fragment of HUTRO (Human Trafficking Ontology, BioPortal, 2025) via `skos:closeMatch`.
- **Ontop mapping** (`mappings/ramona.obda`) connecting the Postgres schema to RATR-O.
- **SPARQL endpoint** served by Ontop on port 8080.
- **Fourteen reference SPARQL queries** (`queries/Q1..Q14`) covering Ramona operational questions and observatory statistics.
- **A multi-source dataset pipeline** under `scripts/`: press scraping (Mexico + LatAm), CTDC (IOM) ingestion, rule-based classification into Type A (classic red flags) and Type B (credible-lethal patterns) tracks.
- **Evidence source catalogue** (`docs/EVIDENCE_SOURCES.md`) and **CTDC–HUTRO–RATR-O mapping workbook** (`docs/CTDC_HUTRO_RATRO_mapping.xlsx`).

No personally identifiable information appears anywhere in the demo. All victim records are anonymised: CTDC records use Microsoft Research's differential-privacy synthetic generation, and press records are aggregated at the article level with outlet, title, URL and structured classification only.

## The "nobody is exempt" framing

The observatory publishes two parallel classifications for every case:

| Track | What it captures | Examples |
|-------|------------------|----------|
| **Type A — classic red flags** | The 7 red flags from Ramona's public infographic: high salary, flexible hours, no experience needed, advance payment, urgent acceptance, distant interview with paid travel, job in another state. | Obvious scam-style offers. |
| **Type B — credible-lethal patterns** | Plausible offers (market salary, realistic role) whose signal is logistic: no company logo, nameless WhatsApp, meet at a multi-use building, come alone, no ID, Messenger-to-WhatsApp funnel, personal-data filtering, atypical hours, last-minute relocation. | The Edith Guadalupe family of cases. |

**On measuring the Type-A vs Type-B distribution:** an earlier draft reported ~10x more Type-B-only than Type-A-only cases from press. That figure was withdrawn after validation: press articles describe outcomes, not offer terms (an LLM read found only ~8% of articles contain the offer), so the ratio cannot be measured from press. See `docs/CLASSIFIER_VALIDATION.md`. The Type-A/Type-B distinction is a modelling contribution of the ontology; its empirical distribution will be measured from Ramona's operational reports, where the offer text exists. The press observatory's measurable contributions are geographic coverage (18 countries), volume, provenance, and a documented-case corpus.

## Prerequisites

- Docker Desktop (or any Docker engine) with Docker Compose v2.
- About 1 GB of free disk and 2 GB of free memory.
- Python 3.11+ for the ingestion and scraping scripts.
- A browser for the Ontop SPARQL UI.

## Start the VKG demo

From this directory:

```bash
docker compose up -d
```

First run:
1. pulls Postgres 16 and Ontop 5.2.0;
2. creates the `ramona` database and runs `db/01_schema.sql`, `db/02_seed_reference.sql`, `db/03_seed_cases.sql`, `db/04_schema_extension_v1.sql` via `/docker-entrypoint-initdb.d/`;
3. starts Ontop with `ontology/ratr-o.ttl` + `mappings/ramona.obda`.

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
DSN="postgresql://ramona:ramona@localhost:5432/ramona" \
python scripts/ingest_press.py --in data/processed/press_cases.jsonl

# ingest CTDC (once you have the CSV from https://www.ctdatacollaborative.org/page/global-synthetic-dataset)
DSN="postgresql://ramona:ramona@localhost:5432/ramona" \
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

| `Q15_fraudscheme_by_country.rq` | Distribución de FraudSchemes por país (cross-source). |
| `Q16_palermo_triad_coverage.rq` | Cobertura del triángulo Palermo (Action × Means × Purpose) por TIPEvent. |
| `Q17_scheme_vs_tool_heatmap.rq` | Heatmap FraudScheme × CommunicationTool. |
| `Q18_age_gender_per_scheme.rq` | Perfil demográfico (edad × género) por FraudScheme. |
| `Q19_outlets_by_scheme.rq` | Outlets de prensa que más documentan cada esquema. |
| `Q20_type_b_over_a_by_country.rq` | Ratio Type-B:Type-A por país. |
| `Q21_pattern_cooccurrence.rq` | Pares de patrones que co-ocurren en el mismo artículo. |
| `Q22_recruitment_x_exploitation.rq` | Método de reclutamiento × tipo de explotación (CTDC). |
| `Q23_whatsapp_funnel_schemes.rq` | Esquemas que comparten WhatsApp como primer canal. |
| `Q24_new_routes_from_press.rq` | Rutas nuevas documentadas por prensa aún no atestadas en CTDC. |
| `Q25_trend_by_year.rq` | Tendencia 2002-2023 de víctimas registradas en CTDC. |
| `Q26_means_of_control_network.rq` | Red de co-ocurrencia de Means of Control (CTDC). |
| `Q27_vulnerability_x_exploitation.rq` | Factor de vulnerabilidad × tipo de explotación. |
| `Q28_crossborder_with_press.rq` | Corredores transfronterizos con prensa reciente. |
| `Q29_edith_cohort.rq` | Cohorte Edith Guadalupe (Type-B-only explícito). |
| `Q30_schemes_in_both_sources.rq` | FraudSchemes atestados en CTDC y prensa (intersección). |

## Layout

```
ramona_vkg_demo/
├── README.md
├── docker-compose.yml
├── requirements.txt
├── db/
│   ├── 01_schema.sql
│   ├── 02_seed_reference.sql
│   ├── 03_seed_cases.sql
│   └── 04_schema_extension_v1.sql          # victim-centric v1.0 extension
├── ontology/
│   └── ratr-o.ttl                          # RATR-O v1.0 in OWL 2 QL, aligned to HUTRO
├── mappings/
│   └── ramona.obda                         # Ontop native mapping, operational + observatory layers
├── ontop/
│   └── ontop.properties
├── queries/
│   ├── Q1..Q8_*.rq                         # Ramona operational reference queries
│   └── Q9..Q14_*.rq                        # Observatory-layer queries
├── scripts/
│   ├── scrape_press.py                     # Google News RSS + trafilatura
│   ├── classify_press.py                   # Type A / Type B rule-based classification
│   ├── ingest_press.py                     # press → Postgres observatory tables
│   ├── ingest_ctdc.py                      # CTDC CSV → Postgres observatory tables
│   └── test_queries.sh
├── data/
│   ├── raw/                                # scraper output (JSONL, git-ignored)
│   └── processed/                          # classified output (JSONL + summary JSON)
└── docs/
    ├── EVIDENCE_SOURCES.md                 # real-world sources behind every pattern and route
    └── CTDC_HUTRO_RATRO_mapping.xlsx       # mapping workbook prepared for Prof. Ortiz
```

## Stopping and cleaning up

```bash
docker compose down        # stop containers, keep the volume
docker compose down -v     # stop and wipe the Postgres volume
```

## Credits and licence

- Ontology (RATR-O) and scholarly outputs: CC BY 4.0.
- Demonstrator code (SQL, OBDA, scripts, README): Apache 2.0.
- CTDC Global Synthetic Dataset: IOM and partners, CC BY 4.0 with source attribution.
- HUTRO: Danial Zemchal Tesfahans, BioPortal, 2025.
- Framework: Xiao, G., Ding, L., Cogrel, B. and Calvanese, D. (2019). *Virtual Knowledge Graphs: An Overview of Systems and Use Cases.* Data Intelligence, 1(3), 201–223. DOI: 10.1162/dint_a_00011.
- Ontop: Calvanese et al. (2017), https://ontop-vkg.org.

Prepared by Daniela Camberos (Ramona AI) for the Dialogue Residency at TU Wien, Institute of Logic and Computation.
