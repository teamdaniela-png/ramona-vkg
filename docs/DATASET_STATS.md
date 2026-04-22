# Ramona VKG — Dataset statistics (v1.3)

Updated: 22 April 2026 (scraper finished, full classifier pass).

## Sources summary

| Source | Records | Kind | Access |
|---|---:|---|---|
| **CTDC Global Synthetic Dataset v2025** (IOM) | 257,969 | victim-centric, 27 variables | CSV on local disk, ingested via `scripts/ingest_ctdc.py` |
| **Trafficking routes extracted from CTDC** (>= 5 victims per route) | **1,304** | (citizenship, CountryOfExploitation) pairs | `db/06_ctdc_routes.sql` (committed) |
| **Press observatory** (Google News RSS, 23 queries, Mexico + LatAm focus) | 1,400 articles scraped | article-level, classified | `data/raw/press.jsonl` (gitignored) |
| **Press observatory, case-relevant** | 1,332 | after rule-based classification | `data/processed/press_cases.jsonl` (gitignored) |
| **Survivor-testimony patterns extracted from press** | **38** | across 5 pattern kinds | `db/07_press_patterns.sql` (committed) |
| **Seed v1.2** (synthetic offers derived from classified press) | 1,332 offers | one offer per classified article, anchored to real press source | `db/05_seed_cases_v1_2.sql` (committed) |
| **Seed v1.0** (hand-written synthetic) | 50 offers | documented Mexican cases | `db/03_seed_cases.sql` (committed) |
| **Evidence sources catalogue (primary)** | 5 | documented in prose | `docs/EVIDENCE_SOURCES.md` |
| **Evidence sources in DB** | 1,337 | press URLs + primary catalogue | via `db/05_seed_cases_v1_2.sql` |
| **Total processable through VKG** | **~259,300** | cases, victims, routes, patterns | — |

## Press observatory — classification breakdown

From 1,400 scraped articles, rule-based classifier labels:

| Metric | Value |
|---|---:|
| Articles classified as case-relevant | 1,332 (95%) |
| Type A only (classic red flags) | 63 |
| **Type B only (credible-lethal patterns)** | **625** |
| Type A and Type B (both tracks) | 128 |
| Neither track, but case-relevant | 516 |

**Ratio Type-B-only : Type-A-only = 9.9x.** The central observatory statistic.

For every case where the advertised conditions themselves flag the scheme (high salary, urgent hire, paid travel), roughly ten cases show a plausible offer whose risk is only legible in the logistics of the first contact.

## Top patterns observed (from 1,332 case-relevant articles)

Extracted by `scripts/extract_patterns.py` and loaded via `db/07_press_patterns.sql`.

### Type B credible-lethal patterns

| Pattern | Occurrences | % of cases | Bucket |
|---|---:|---:|---|
| `filtro_datos_personales` | 578 | 54.3% | hot |
| `cita_edificio_multiusos` | 48 | 4.5% | warm |
| `horario_atipico` | 22 | 2.1% | warm |
| `rol_plausible_limpieza_hosteleria` | 10 | 0.9% | cold |
| `messenger_to_whatsapp` | 4 | 0.4% | cold |
| `solicita_sin_identificacion` | 3 | 0.3% | cold |
| `solicita_ir_sola` | 2 | 0.2% | cold |

### Type A classic red flags (Ramona's 7-flag infographic)

| Pattern | Occurrences | % of cases | Bucket |
|---|---:|---:|---|
| `aceptacion_urgente` | 148 | 13.9% | hot |
| `sin_experiencia` | 6 | 0.6% | cold |
| `pago_adelantado` | 1 | 0.1% | cold |
| `empleo_fuera_estado` | 1 | 0.1% | cold |
| `entrevista_lejana_traslado` | 1 | 0.1% | cold |

### Recruitment methods (the myth-breaker)

| Method | Occurrences | % of cases |
|---|---:|---:|
| **Redes sociales** | **499** | **46.9%** |
| **Familia** | **336** | **31.5%** |
| Secuestro directo | 119 | 11.2% |
| Amigo | 110 | 10.3% |
| Pareja romántica | 73 | 6.9% |
| Oferta laboral falsa (explícita) | 69 | 6.5% |
| Enganchador / labour broker | 51 | 4.8% |
| Clasificados | 48 | 4.5% |
| En la calle | 14 | 1.3% |

**The myth-breaker: 48% of documented cases are recruited by someone close (family, friend, intimate partner). The recruiter is rarely a stranger.**

### First-contact communication tool

| Tool | % of cases |
|---|---:|
| WhatsApp | 21.3% |
| Telegram | 7.3% |
| Email | 5.3% |
| In person | 2.5% |
| SMS | 2.3% |
| Messenger | 1.2% |

### Exploitation outcome (when detected)

| Type | % of cases |
|---|---:|
| Labour: hospitality | 48.9% |
| Sexual: prostitution | 23.3% |
| Labour: construction | 13.6% |
| Labour: other | 10.1% |
| Forced criminality | 4.9% |
| Organ removal | 3.2% |
| Sexual: pornography | 2.5% |
| Labour: agriculture | 1.6% |
| Labour: domestic | 0.8% |
| Forced marriage | 0.7% |

## CTDC routes — top 20 trafficking corridors

Extracted by `scripts/extract_routes.py` from 257,969 CTDC victim records. Loaded via `db/06_ctdc_routes.sql`.

| Origin | Destination | Victims | Year range | Dominant exploitation |
|---|---|---:|---|---|
| USA | USA (internal) | 10,927 | 2012–2023 | sexual |
| UKR | UKR (internal) | 7,603 | 2003–2023 | forced labour |
| **MEX** | **USA** | **7,037** | **2015–2023** | **forced labour** |
| MDA | MDA (internal) | 5,772 | 2002–2023 | sexual |
| UKR | RUS | 4,099 | 2004–2023 | forced labour |
| PHL | PHL (internal) | 1,994 | 2016–2023 | other |
| NGA | LBY | 1,692 | 2006–2023 | forced labour |
| PHL | USA | 1,212 | 2002–2023 | forced labour |
| BLR | RUS | 1,159 | 2003–2022 | forced labour |
| VNM | CHN | 1,100 | 2012–2023 | other |
| UKR | POL | 1,036 | 2004–2023 | forced labour |
| CHN | USA | 1,030 | 2002–2023 | sexual |
| NGA | MLI | 958 | 2012–2023 | sexual |
| MMR | IDN | 942 | 2012–2021 | forced labour |
| **GTM** | **USA** | **842** | **2009–2023** | **forced labour** |
| KHM | KHM (internal) | 826 | 2017–2019 | sexual |
| MDA | UKR | 666 | 2003–2023 | forced labour |
| IDN | MYS | 627 | 2005–2022 | domestic labour |
| MMR | BGD | 625 | 2007–2023 | forced labour |
| KGZ | RUS | 600 | 2008–2020 | forced labour |

**Total routes with >= 5 victims: 1,304.** **Mexico to USA is the third-largest corridor in the CTDC dataset (7,037 victims, 2015–2023).** Guatemala to USA is a major secondary corridor (842 victims).

## Country coverage in press

| Country (detected mention in article) | Articles |
|---|---:|
| Mexico | ~730 |
| Colombia | ~230 |
| USA | ~180 |
| Peru | ~140 |
| Argentina | ~90 |
| Venezuela | ~60 |
| Chile | ~30 |
| Guatemala | ~25 |
| Honduras | ~20 |
| El Salvador | ~18 |

## Top outlets

Infobae (152), El Sol de México (50), Milenio (39), Argentina.gob.ar (38), EL PAÍS (28), **UNODC (27)**, REDIM (26), N+ (24), El Universal (22), La Jornada (18), BBC (16), El Informador (15), La Silla Rota (14), El Financiero (14), Proceso (12), TV Azteca (12), El Heraldo (11), LatinUS (11), Yahoo (10), El Colombiano (10).

## Notes and caveats

- **Classifier is rule-based.** A follow-up pass with an LLM will refine assignments. The rule-based pass is conservative: it avoids false positives by firing only on literal keyword patterns. That is why many Type A flags have low counts — the regex is narrow by design.
- **Press articles do not correspond to individual victims.** One article may describe dozens of victims or an investigation-level summary. The seed row represents the article as a single anchor point; it does not claim one victim per row.
- **CTDC data is NOT in this repository.** The CSV is downloaded by each user from the CTDC website under CC BY 4.0 attribution. The ingestion script maps it into the Postgres victim-centric tables.
- **Percentages for exploitation types sum to more than 100** because one victim can be exploited in multiple ways, and one article can reference multiple exploitation outcomes (see CTDC Codebook Section 6).
- **No personally identifiable information.** All offer, recruiter and employer references are deterministic hash stubs. Victim records from CTDC are differentially-private synthetic records generated by Microsoft Research.
