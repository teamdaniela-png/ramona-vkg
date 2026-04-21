# Ramona VKG — Dataset statistics

Updated: 21 April 2026 (preliminary, scraper still running).

## Sources

| Source | Records | Kind | Access |
|---|---:|---|---|
| **CTDC Global Synthetic Dataset v2025** (IOM) | 257,969 | victim-centric, 27 variables | CSV on user's local disk, ingested via `scripts/ingest_ctdc.py` |
| **Press observatory (Google News RSS, 23 queries, Mexico + LatAm focus)** | 1,127 articles | article-level, classified | `data/raw/press.jsonl` (gitignored) |
| **Seed v1.2 (synthetic offers derived from classified press)** | 1,065 offers | one offer per classified article, anchored to real press source | `db/05_seed_cases_v1_2.sql` (committed) |
| **Seed v1.0 (hand-written synthetic)** | 50 offers | documented Mexican cases | `db/03_seed_cases.sql` (committed) |
| **Survivor testimony patterns** | 14 | codebook entries | `db/02_seed_reference.sql` |
| **Evidence sources catalogue** | 5 primary + 1,065 press articles | documented in `docs/EVIDENCE_SOURCES.md` + seed v1.2 |
| **Total processable through VKG** | **~260,000** cases/victims | — | — |

## Press observatory — classification breakdown

From the current 1,127 scraped articles, the rule-based classifier labels:

| Metric | Value |
|---|---:|
| Articles classified as case-relevant | 1,065 (94%) |
| Type A only (classic red flags) | 49 |
| **Type B only (credible-lethal patterns)** | **507** |
| Type A and Type B (both tracks) | 105 |
| Neither track, but case-relevant | 404 |

**Ratio Type-B-only : Type-A-only = 10.4x.**
This is the central observatory statistic: for every case where the advertised conditions themselves flag the scheme (high salary, urgent hire, paid travel), roughly ten cases show a plausible offer whose risk is only legible in the logistics of the first contact (nameless WhatsApp, come alone, no ID, multi-use building). Ramona's published contribution is making this distribution visible, at scale, with provenance.

## Press observatory — country coverage

| Country (detected mention in article) | Articles |
|---|---:|
| Mexico | 582 |
| Colombia | 184 |
| USA | 146 |
| Peru | 112 |
| Argentina | 73 |
| Venezuela | 47 |
| Chile | 23 |
| Guatemala | 19 |
| Honduras | 15 |
| El Salvador | 14 |

## Press observatory — top outlets

Infobae, Milenio, El Sol de México, El País, El Universal, UNODC (United Nations Office on Drugs and Crime), REDIM (Red por los Derechos de la Infancia en México), N+, El Financiero, La Jornada, El Informador, La Silla Rota, BBC, LatinUS, Proceso, El Heraldo de México, TV Azteca, Yahoo, El Colombiano, Cimac Noticias.

## Press observatory — exploitation types detected

| Exploitation type | Occurrences in articles |
|---|---:|
| Labour: hospitality | 493 |
| Sexual exploitation: prostitution | 208 |
| Labour: construction | 135 |
| Labour: other | 91 |
| Forced criminality | 51 |
| Organ removal | 28 |
| Sexual exploitation: pornography | 24 |
| Labour: agriculture | 17 |
| Labour: domestic | 8 |
| Forced marriage | 6 |

## FraudScheme detection in seed v1.2

Of the 1,065 seed offers synthesised from press, the scheme detector assigned the following named FraudScheme tags (from RATR-O v1.2):

- IdentityTheftScheme (heuristic: articles mentioning data harvesting / CURP / INE)
- ForcedCriminalityScheme (all articles mentioning `forced_criminality` exploitation type)
- FakeMaquilaScheme (title mentions maquila)
- ModelingAgencyScheme (title mentions modelaje / actuación)
- OnlineCryptoJobScheme (title mentions crypto / forex / blockchain)
- GigEconomyFakeDriverScheme (title mentions Uber / DiDi / conductor)
- MLMHealthBeautyScheme (title mentions multinivel / piramidal)
- OnlineInfluencerSalesScheme (title mentions influencer / embajador)
- ForeignLanguageTeacherScheme (title mentions maestro / profesor / idiomas)
- DomesticWorkerLockInScheme (title mentions nanny / niñera without international cue)
- VisaFraudScheme (nanny + Canada / France / Paris)
- InPersonLureScheme (Type B patterns: ven sola, edificio multiusos)
- PayToWorkScheme (pago_adelantado classic flag)
- general (no single scheme matched; kept as un-tagged case-relevant source)

Precise scheme counts will be published in v1.3 after the scraper completes (~1,500 articles expected).

## Notes and caveats

- **Classifier is rule-based.** A follow-up pass with an LLM will refine assignments, especially for disambiguating ModelingAgency vs OnlineInfluencer, or CallCenterScam vs legitimate call-centre employment dispute. The rule-based pass is conservative: it avoids false positives by only firing on literal keyword patterns.
- **Press articles do not correspond to individual victims.** One article may describe dozens of victims or an investigation-level summary. The seed row represents the article as a single anchor point; it does not claim one victim per row.
- **CTDC data is NOT in this repository.** The CSV is downloaded by each user from the CTDC website under CC BY 4.0 attribution. The ingestion script maps it into the Postgres victim-centric tables.
- **No personally identifiable information.** All offer, recruiter and employer references are deterministic hash stubs. Victim records from CTDC are differentially-private synthetic records generated by Microsoft Research.
