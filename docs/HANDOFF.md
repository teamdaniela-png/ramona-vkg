# Ramona VKG — Handoff document

**Any Claude session picking this project up: read THIS file completely before taking any action.** It contains the current state, the history of decisions, and the rules of engagement.

This file is the repo-side counterpart of `~/.claude/projects/-Users-danielacamberos-Downloads/memory/ramona_vkg_residency.md`, which is the persistent Claude memory entry. Both should be kept in sync.

Last updated: 26 June 2026 (state-sync). Original: 21 April 2026.

## CURRENT STATE SNAPSHOT (26 June 2026) — read this block first

The week plan below was largely executed. Repo is at **RATR-O v1.6.1** (last commit `742d4f2`, 22 Apr). Verified metrics and gap:

**DONE and audited:**
- **O1 Ontology** v1.6.1: 86 classes, 60 object properties, 80 datatype properties, ~24 named FraudScheme classes. OWL 2 QL validated. Audit passed with 0 blockers / 0 SHOULDs (`docs/AUDIT_O1.md`, `docs/AUDIT_O1_SUMMARY.md`). Aligned to HUTRO + Palermo Protocol + ICS-TIP + UNODC GLOTIP.
- **O2 Mapping**: both `mappings/ramona.obda` and `mappings/ramona.r2rml.ttl` (W3C R2RML) exist.
- **30 SPARQL queries** in `queries/*.rq` (target 30+, met).
- **Paper-grade artefacts**: `docs/COMPETENCY_QUESTIONS.md`, `docs/HUTRO_vs_RATRO_comparison.md`, `docs/RIGOR_STATEMENT.md`, `docs/ZENODO_SETUP.md`, `.zenodo.json`.
- **Datasets**: CTDC 257,969 records present locally; press scrape **expanded to 2,591 articles, 2,418 case-relevant, 18 countries** (v1.7, 26 Jun: scraper grew 23→70 queries covering all LatAm + Brazil + Spain + platforms + cyber-trafficking).
- **Tags shipped**: v1.1, v1.3, v1.4, v1.5, v1.6, v1.6.1, v1.7.

**STILL PENDING (the gap to "todo completo" for Vienna):**
1. **The paper** — never written. No `docs/paper_draft*`. Highest-value remaining item.
2. **O3 demonstrator** — Docker is NOT running; the Ontop VKG was never booted or queried over real data. `docker-compose.yml` (Postgres 16 + Ontop 5.2.0) is ready to go. Known risk: Docker Desktop on the Mac.
3. **`docs/READY_FOR_VIENNA.md`** — not created.

**Headline number — WITHDRAWN (v1.8, 26 Jun 2026).** The Type-B:Type-A ratio (claimed 10.4x, then 9.9x, then 10.0x) is NOT measurable from press and has been retired. Validation (`docs/CLASSIFIER_VALIDATION.md`): the rule-based classifier had large false positives (`ine`→define/imagine inflated the dominant Type-B pattern 1,255 vs true 46; `bar`→Barcelona; `urge`→journalistic urgency), and an LLM read of 120 articles found only 8.3% actually describe the offer terms. Press reports outcomes, not offers. Do NOT cite any A:B ratio from press anywhere. The credible-lethal hypothesis must be measured from Ramona's operational reports via `scripts/classify_llm.py`. Press observatory's real contributions: 18-country coverage, volume (2,591 articles), provenance, documented-case corpus.

## Project summary

Ramona AI is preparing for a BMEIA-funded Dialogue Residency at TU Wien, Institute of Logic and Computation, May to July 2026. Host: Prof. Magdalena Ortiz. The residency has three declared objectives:

- **O1**: design and publish a domain ontology in OWL 2 QL (DL-Lite fragment) covering Ramona's operational context (job offers, employers, recruiters, candidates, red flags, trafficking routes, platforms, risk classifications).
- **O2**: R2RML mapping (W3C standard) between Ramona's Postgres and the ontology.
- **O3**: Ontop-based Virtual Knowledge Graph demonstrator serving SPARQL over Ramona's data plus open anti-trafficking datasets.

The residency agreement has been drafted and approved in principle by Magdalena. It lives in `~/Downloads/Residency_Agreement_V3.docx`. Do not modify this file.

## Current state (21 April 2026, end of day)

### Ontology (O1)
- Version: **1.2**, OWL 2 QL profile validated.
- Metrics: 48 classes, 34 object properties, 46 datatype properties, 518 triples.
- File: `ontology/ratr-o.ttl`.
- HTML documentation: `ontology/ratr-o.html` and https://teamdaniela-png.github.io/ramona-vkg/ontology/ratr-o.html.
- Alignments via `skos:closeMatch`: HUTRO (Tesfahans, BioPortal, 2025) on 8 concepts.
- FraudScheme taxonomy: 16 named schemes covering recruitment fraud + labour exploitation + trafficking. The 16 are:
  IdentityTheftScheme, PyramidScheme, PayToWorkScheme, VisaFraudScheme, InPersonLureScheme, DebtBondageTraffickingScheme, DomesticWorkerLockInScheme, OnlineCryptoJobScheme, ModelingAgencyScheme, CallCenterScamScheme, FakeMaquilaScheme, MLMHealthBeautyScheme (subclass of PyramidScheme), GigEconomyFakeDriverScheme, ForcedCriminalityScheme, OnlineInfluencerSalesScheme, ForeignLanguageTeacherScheme.
- Next version (v1.3 onward) is on the week plan below.

### Mapping (O2)
- Ontop native OBDA mapping exists at `mappings/ramona.obda`.
- Covers operational layer (offers, recruiters, employers, platforms, red flags, classifications, routes, patterns, candidates, submissions) plus v1.0 observatory layer (victims, demographics, HUTRO-aligned vocabularies, cross-source evidence sources).
- R2RML conversion (W3C standard form) is scheduled for Fri 24 Apr / Sat 25 Apr in the week plan. Script target: `scripts/obda_to_r2rml.py`, output: `mappings/ramona.r2rml.ttl`.

### Demonstrator (O3)
- `docker-compose.yml` stands at repo root (Postgres 16 + Ontop 5.2.0).
- Not started on any developer machine yet as of 21 Apr evening.
- Boot and data-load scheduled for Sat 25 Apr.

### Dataset (not in repo, local)
- **CTDC Global Synthetic Dataset v2025 (IOM)**: 257,969 records. CSV at `/Users/danielacamberos/Downloads/CTDC_global_synthetic_data_v2025.csv`. Codebook PDF alongside.
- **Press observatory**: at least 1,145 articles as of 21 Apr 23:00. Collected by `scripts/scrape_press.py` into `data/raw/press.jsonl` (gitignored). Scraper PID 30765, running as background process started 21 Apr ~11:37.
- **Classified press output**: `data/processed/press_cases.jsonl`, produced by `scripts/classify_press.py`. Summary JSON in `data/processed/press_summary.json`.

### Seed data (in repo)
- `db/01_schema.sql` — Ramona operational schema.
- `db/02_seed_reference.sql` — reference vocabularies (countries, languages, platforms, 14 survivor patterns).
- `db/03_seed_cases.sql` — first hand-written 50 offers.
- `db/04_schema_extension_v1.sql` — victim-centric observatory tables, aligned to CTDC and HUTRO.
- `db/05_seed_cases_v1_2.sql` — **1,065 offers** synthesised from classified press. Each anchored to a real press URL as evidence source.

### Key empirical finding (the headline)
From 1,127 classified press articles: **Type-B-only cases (credible-lethal patterns, like the Edith Guadalupe archetype) outnumber Type-A-only cases (classic red flags) by 10.4x**. For every case where the advertised terms themselves flag the scheme, there are about ten cases where the offer looks plausible and the signal sits in the logistics of the first contact (nameless WhatsApp, come alone, no ID, multi-use building).

Recorded in `docs/DATASET_STATS.md`. This is the single most important story Daniela will tell in Vienna.

### GitHub and publication
- Repo: https://github.com/teamdaniela-png/ramona-vkg
- Account used: `teamdaniela-png` (authenticated via `gh` CLI on Daniela's Mac).
- GitHub Pages: enabled, builds from `main` branch root.
- Release tag: `v1.1` (first public release). v1.2 commits on `main` since.
- Recent commits (most recent first):
  1. `f802cab` Seed v1.2: 1,065 offers synthesised from classified press
  2. `03847f4` RATR-O v1.2: expand FraudScheme taxonomy from 6 to 16
  3. `a78e91a` RATR-O v1.1: add FraudScheme taxonomy
  4. `dd5bf26` Add docker-compose and Ontop configuration
  5. `18dc304` RATR-O v1.0: initial publication

### Auxiliary deliverables
- `docs/EVIDENCE_SOURCES.md` — 5 primary public sources used in the v1.0 seed.
- `docs/CTDC_HUTRO_RATRO_mapping.xlsx` — 4-tab workbook mapping CTDC variables and HUTRO concepts to RATR-O, plus the dual detection-track description.
- `docs/DATASET_STATS.md` — dataset statistics with breakdown by country, outlet, exploitation type, Type A / Type B.
- `README.md` — user-facing description of the whole repo with setup instructions.

## Week plan (21 April to 2 May 2026)

Each day has a cron one-shot task scheduled in this Claude session with a self-contained prompt. If the session dies and the tasks are lost, Daniela will ping with a short message and the new Claude is expected to pick up here.

| Day | Deliverable | Details |
|---|---|---|
| Wed 22 Apr | v1.3 | Extract 200+ routes from CTDC (citizenship + country-of-exploitation pairs with ≥5 victims), 50+ patterns from press articles. |
| Thu 23 Apr | v1.4 | Align with ICS-TIP, Palermo Protocol (add `:PalermoAction`, `:PalermoMeans`, `:PalermoPurpose`), UNODC GLOTIP. |
| Fri 24 Apr | v1.5 | Grow SPARQL queries from 14 to 30+. Start R2RML conversion script. |
| Sat 25 Apr | O2 + O3 | Finalise R2RML. Boot Docker stack. Ingest CTDC. Run all queries. Report. |
| Mon 28 Apr | Audit Day 1 | Put on Magdalena's hat. DL-Lite rigor and ontology consistency. Write `docs/AUDIT_DAY1_dl_lite_consistency.md`. |
| Tue 29 Apr | Audit Day 2 | Coverage and provenance. Apply Day 1 fixes. Produce v1.5.1. Write `docs/AUDIT_DAY2_coverage_provenance.md`. |
| Wed 30 Apr | Paper draft v0.1 | ~15 pages in `docs/paper_draft_v0.1.md`. Structure in the cron prompt. |
| Thu 1 May | Paper polish | Editorial pass. `docs/REVIEWER_RESPONSE_template.md`. `docs/READY_FOR_VIENNA.md`. |

## Daniela's preferences (binding)

- Spanish (Mexico). Short answers. Conversational.
- **No em dashes.** Hates them. Use periods or commas.
- Wants things FAST. Don't over-explain. Don't hedge. Just do.
- Prefers verified references. Never invent DOIs, document codes or institutional citations.
- Uses "no me metas gol" when she wants to avoid over-promising. Be conservative in promises.

## Rules of engagement

1. **Do not redo work.** Read this file and `docs/DATASET_STATS.md` before writing anything.
2. **Commit and push every meaningful change.** The repo is the source of truth.
3. **When uncertain about a standard, audit don't invent.** Document as `rdfs:seeAlso` and flag provisional.
4. **Empirical claims need numbers.** Use `docs/DATASET_STATS.md`.
5. **Do not send emails on Daniela's behalf.** Draft only. She reviews.
6. **Do not alter `~/Downloads/Residency_Agreement_V3.docx`.** It is frozen.
7. **Git identity:** use `user.name="Daniela Camberos" user.email="daniela@ramonaaliadalaboral.com"` for commits on this repo.
8. **Prefer `gh` CLI over raw API calls** for GitHub operations. Account in use: `teamdaniela-png`.
9. **Do not add PII.** All contact info is SHA-256 stub. All victim records are either CTDC differential-privacy synthetic or press-article anchor.

## Blockers and gotchas

- **Scraper PID 30765** started 21 Apr 11:37. It was running when this handoff was written and should be checked with `ps -p 30765` by any future session.
- **Docker Desktop** may or may not be running on the Mac. Check with `docker info`. If not running, the O3 step should produce a `docs/O3_STATUS.md` describing the blocker rather than failing.
- **Bash tool does not preserve cwd** between calls. Always `cd /Users/danielacamberos/Downloads/ramona_vkg_demo` at the start of each bash command that uses relative paths.
- **CTDC download is Akamai-protected.** If a user asks to re-download, the direct page `https://www.ctdatacollaborative.org/page/global-synthetic-dataset` must be opened in a real browser, it will not work from `curl` or `WebFetch`.
- **HTML generator script** lives at `/tmp/gen_ratro_html.py`. It may not survive reboots. If missing, regenerate from the template inside prior commits.

## Contacts

- **Daniela Camberos** (Ramona AI). Calendly: https://calendly.com/daniela-324
- **Prof. Magdalena Ortiz** (TU Wien, Institute of Logic and Computation). Her last email to Daniela (April 2026) asked for: extended KR justification in the agreement, two additional verified references, and introduced HUTRO as a relevant prior ontology to look at.

End of handoff document.
