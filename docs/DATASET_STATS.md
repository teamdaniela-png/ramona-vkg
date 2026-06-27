# Ramona VKG — Dataset statistics (v1.8)

Updated: 26 June 2026 (v1.8: press observatory expanded AND classifier validated; the Type-A/Type-B ratio is withdrawn after validation).

## v1.8 — validation and correction (read `docs/CLASSIFIER_VALIDATION.md`)

- **The earlier "Type-B-only outnumbers Type-A-only by ~10x" headline is WITHDRAWN.** It did not survive validation. The rule-based classifier had large false-positive rates (the token `ine` without a word boundary matched *define/imagine/examine*, inflating the dominant Type-B pattern from a true 46 to a reported 1,255; `bar` matched *Barcelona/embargo*; `urge` matched journalistic urgency). After correcting the regex the ratio inverted, which exposed it as an artefact of the method.
- **LLM validation on a 120-article sample**: only **8.3% (10/120)** of case-relevant articles actually describe the terms of a job offer; 91.7% report the outcome (rescue, disappearance, operation, law reform), not the offer. The offer terms needed to separate Type-A from Type-B are simply not in the press.
- **Conclusion**: the press observatory cannot measure the A:B ratio (source limitation, not a bug). It can measure geography, volume, provenance, exploitation outcome, and serve as a documented-case corpus. The credible-lethal hypothesis now belongs to Ramona's operational reports, not to press.

## v1.7 additions (press expansion, retained)

- **Press observatory expanded from 1,400 to 2,591 articles** (+1,191). Scraper query set grew from 23 to 70: every Spanish-speaking LatAm country, Brazil (Portuguese), Spain, recruitment platforms (Instagram, TikTok, Computrabajo, Indeed, LinkedIn, OLX), and cyber-trafficking / "pig butchering" scam-center recruitment.
- **Case-relevant articles: 1,332 → ~2,380.**
- **Country coverage in press grew from 10 to 18 countries.** New: Bolivia (166), Ecuador (161), Spain (138), Brazil (92), Paraguay (61), Dominican Republic (55), Costa Rica (21), Nicaragua (14).
- **Two new exploitation categories detected**: cyber scam-center (`cyber_scam_center`) and forced begging (`forced_begging`).

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

From 2,591 scraped articles, the corrected rule-based classifier labels ~2,379 as
case-relevant. **The Type-A vs Type-B split is intentionally NOT reported here**: LLM
validation showed only 8.3% of articles describe the offer terms at all, so any A:B figure
from press is an artefact. See `docs/CLASSIFIER_VALIDATION.md`. Type-A/Type-B will be
measured from Ramona's operational reports, where the offer text exists.

The pattern-occurrence tables below are kept only as a description of what keyword signals
appear in the corpus, NOT as evidence of offer characteristics.

### Recruitment methods (directional, from corrected classifier)

| Method | % of case-relevant articles |
|---|---:|
| **Redes sociales** | **38.8%** |
| **Familia / conocido cercano** | **27.7%** |
| Secuestro directo | 10.4% |
| Amigo | 8.1% |
| Pareja romántica | 6.4% |
| Oferta laboral falsa (explícita) | 4.4% |

Note: even these are keyword mentions inside the article, not verified recruitment channels.
The LLM sample found `metodo` "no determinable" in 42 of 120 articles, so treat these as
directional. The "recruited by someone close" pattern is suggestive but not yet a measured
rate; it should be confirmed against operational reports.

### Exploitation outcome (directional, when stated)

| Type | % of case-relevant articles |
|---|---:|
| Sexual: prostitution | 27.6% |
| Labour: other | 15.6% |
| Labour: hospitality | 10.6% |
| Labour: construction | 7.9% |
| Forced criminality | 4.8% |

(Earlier "labour: hospitality 47.8%" was a false positive: the token `bar` matched
*Barcelona, embargo, barrio*. Corrected above.)

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
