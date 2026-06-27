# Ramona VKG — Dataset statistics (v1.7)

Updated: 26 June 2026 (v1.7: press observatory nearly doubled — expanded scraper from 23 to 70 queries covering all of LatAm + Brazil + Spain + platforms + cyber-trafficking).

## v1.7 additions in this iteration

- **Press observatory expanded from 1,400 to 2,591 articles** (+1,191). Scraper query set grew from 23 to 70: every Spanish-speaking LatAm country, Brazil (Portuguese), Spain, recruitment platforms (Instagram, TikTok, Computrabajo, Indeed, LinkedIn, OLX), and cyber-trafficking / "pig butchering" scam-center recruitment.
- **Case-relevant articles: 1,332 → 2,418.**
- **Country coverage in press grew from 10 to 18 countries.** New: Bolivia (166), Ecuador (161), Spain (138), Brazil (92), Paraguay (61), Dominican Republic (55), Costa Rica (21), Nicaragua (14).
- **Two new exploitation categories detected**: cyber scam-center (`cyber_scam_center`) and forced begging (`forced_begging`).
- **Headline statistic re-validated at scale: Type-B-only : Type-A-only = 10.0x** (1,106 vs 111). With the dataset nearly doubled the ratio held, confirming it is not an artefact of a small sample. (Prior figure was 9.9x on 1,332 articles.)

## v1.4 additions (prior iteration)

- **Palermo Protocol Article 3 formally modelled** as three class hierarchies: `:PalermoAction`, `:PalermoMeans`, `:PalermoPurpose`, each with verbatim sub-concepts from the UN Protocol text (coercion, abduction, fraud, deception, abuse of power, abuse of vulnerability, payment-for-consent; sexual exploitation, forced labour, slavery, servitude, organ removal).
- **`:TIPEvent` class** introduced as the central unit of classification from ICS-TIP (IOM and UNODC, 2023), with object properties linking it to victims, actions, means and purposes.
- **ICS-TIP close-match alignment** via `rdfs:seeAlso` on `:RecruitmentMethod`, `:TypeOfExploitation`, `:VulnerabilityFactor`, `:TraffickingRoute`.
- **UNODC GLOTIP alignment** via `rdfs:seeAlso` on `:Victim`.
- **Countries table enriched from 8 to 92 countries** with ISO3 codes and Spanish + English names, built from every unique citizenship and country-of-exploitation observed in the 257,969 CTDC records.
- **FraudScheme exemplars (31 real press articles) linked** across 8 schemes: every scheme has up to 5 representative documented cases with URL attribution. Loaded via `db/09_fraudscheme_examples.sql`.
- **50 deep textual patterns** extracted from the full text of case-relevant press articles via extended regex analysis. Loaded via `db/10_deep_patterns.sql`. 12 of them have attested matches in the corpus already.
- RATR-O v1.4 ontology now stands at **76 classes, 42 object properties, 52 datatype properties, 709 triples.** OWL 2 QL profile validated.


## Sources summary

| Source | Records | Kind | Access |
|---|---:|---|---|
| **CTDC Global Synthetic Dataset v2025** (IOM) | 257,969 | victim-centric, 27 variables | CSV on local disk, ingested via `scripts/ingest_ctdc.py` |
| **Trafficking routes extracted from CTDC** (>= 5 victims per route) | **1,304** | (citizenship, CountryOfExploitation) pairs | `db/06_ctdc_routes.sql` (committed) |
| **Press observatory** (Google News RSS, 70 queries, LatAm + Brazil + Spain + platforms + cyber-trafficking) | 2,591 articles scraped | article-level, classified | `data/raw/press.jsonl` (gitignored) |
| **Press observatory, case-relevant** | 2,418 | after rule-based classification | `data/processed/press_cases.jsonl` (gitignored) |
| **Survivor-testimony patterns extracted from press** | **38** | across 5 pattern kinds | `db/07_press_patterns.sql` (committed) |
| **Seed v1.2** (synthetic offers derived from classified press) | 1,332 offers | one offer per classified article, anchored to real press source | `db/05_seed_cases_v1_2.sql` (committed) |
| **Seed v1.0** (hand-written synthetic) | 50 offers | documented Mexican cases | `db/03_seed_cases.sql` (committed) |
| **Evidence sources catalogue (primary)** | 5 | documented in prose | `docs/EVIDENCE_SOURCES.md` |
| **Evidence sources in DB** | 1,337 | press URLs + primary catalogue | via `db/05_seed_cases_v1_2.sql` |
| **Total processable through VKG** | **~259,300** | cases, victims, routes, patterns | — |

## Press observatory — classification breakdown

From 2,591 scraped articles, rule-based classifier labels:

| Metric | Value |
|---|---:|
| Articles classified as case-relevant | 2,418 (93%) |
| Type A only (classic red flags) | 111 |
| **Type B only (credible-lethal patterns)** | **1,106** |
| Type A and Type B (both tracks) | 212 |

**Ratio Type-B-only : Type-A-only = 10.0x.** The central observatory statistic, re-validated on a nearly-doubled dataset (was 9.9x on 1,332 articles).

For every case where the advertised conditions themselves flag the scheme (high salary, urgent hire, paid travel), roughly ten cases show a plausible offer whose risk is only legible in the logistics of the first contact.

## Top patterns observed (from 2,418 case-relevant articles)

Computed directly from the classifier output `data/processed/press_cases.jsonl`.

### Type B credible-lethal patterns

| Pattern | Occurrences | % of cases |
|---|---:|---:|
| `filtro_datos_personales` | 1,255 | 51.9% |
| `cita_edificio_multiusos` | 85 | 3.5% |
| `horario_atipico` | 32 | 1.3% |
| `rol_plausible_limpieza_hosteleria` | 19 | 0.8% |
| `solicita_sin_identificacion` | 8 | 0.3% |
| `messenger_to_whatsapp` | 7 | 0.3% |
| `solicita_ir_sola` | 4 | 0.2% |

### Type A classic red flags (Ramona's 7-flag infographic)

| Pattern | Occurrences | % of cases |
|---|---:|---:|
| `aceptacion_urgente` | 298 | 12.3% |
| `sin_experiencia` | 15 | 0.6% |
| `empleo_fuera_estado` | 10 | 0.4% |
| `entrevista_lejana_traslado` | 4 | 0.2% |
| `sueldo_alto` | 4 | 0.2% |
| `pago_adelantado` | 1 | 0.0% |

### Recruitment methods (the myth-breaker)

| Method | Occurrences | % of cases |
|---|---:|---:|
| **Redes sociales** | **923** | **38.2%** |
| **Familia** | **692** | **28.6%** |
| Secuestro directo | 247 | 10.2% |
| Amigo | 200 | 8.3% |
| Pareja romántica | 163 | 6.7% |
| Oferta laboral falsa (explícita) | 105 | 4.3% |
| Enganchador / labour broker | 93 | 3.8% |
| Clasificados | 79 | 3.3% |
| En la calle | 51 | 2.1% |

**The myth-breaker: 44% of documented cases are recruited by someone close (family, friend, intimate partner). The recruiter is rarely a stranger.**

### First-contact communication tool

| Tool | % of cases |
|---|---:|
| WhatsApp | 16.1% |
| Telegram | 5.0% |
| Email | 3.8% |
| In person | 2.6% |
| SMS | 1.7% |
| Messenger | 1.1% |

### Exploitation outcome (when detected)

| Type | % of cases |
|---|---:|
| Labour: hospitality | 47.8% |
| Sexual: prostitution | 27.2% |
| Labour: other | 15.4% |
| Labour: construction | 14.2% |
| Forced criminality | 4.8% |
| Organ removal | 2.9% |
| Sexual: pornography | 2.4% |
| Labour: agriculture | 2.2% |
| Forced begging | 1.6% |
| Forced marriage | 0.8% |
| Labour: domestic | 0.7% |
| Cyber scam-center | 0.7% |

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

## Country coverage in press (18 countries)

| Country (detected mention in article) | Articles |
|---|---:|
| Mexico | 1,283 |
| Colombia | 401 |
| USA | 331 |
| Argentina | 233 |
| Peru | 214 |
| Bolivia | 166 |
| Ecuador | 161 |
| Spain | 138 |
| Chile | 130 |
| Venezuela | 119 |
| Brazil | 92 |
| Paraguay | 61 |
| Dominican Republic | 55 |
| Guatemala | 51 |
| Honduras | 38 |
| El Salvador | 34 |
| Costa Rica | 21 |
| Nicaragua | 14 |

## Top outlets

Infobae (296), El Sol de México (67), La Jornada (54), El Universal (54), N+ (53), EL PAÍS (52), Milenio (49), **UNODC (41)**, Argentina.gob.ar (40), Proceso (30), La Silla Rota (29), El Informador (27), **REDIM (26)**, El Financiero (26), LatinUS (25), Grupo Animal (22), TV Azteca (21), El Economista (20), El Heraldo de México (19), BBC.

## Notes and caveats

- **Classifier is rule-based.** A follow-up pass with an LLM will refine assignments. The rule-based pass is conservative: it avoids false positives by firing only on literal keyword patterns. That is why many Type A flags have low counts — the regex is narrow by design.
- **Press articles do not correspond to individual victims.** One article may describe dozens of victims or an investigation-level summary. The seed row represents the article as a single anchor point; it does not claim one victim per row.
- **CTDC data is NOT in this repository.** The CSV is downloaded by each user from the CTDC website under CC BY 4.0 attribution. The ingestion script maps it into the Postgres victim-centric tables.
- **Percentages for exploitation types sum to more than 100** because one victim can be exploited in multiple ways, and one article can reference multiple exploitation outcomes (see CTDC Codebook Section 6).
- **No personally identifiable information.** All offer, recruiter and employer references are deterministic hash stubs. Victim records from CTDC are differentially-private synthetic records generated by Microsoft Research.
