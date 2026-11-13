# Real offer corpus: first results (v1.10, 3 Nov 2026)

## Corpus

- Source: 2,124 press articles on recruitment cases (`data/raw/press.jsonl`, scraped Apr to Jun 2026).
- 532 articles contain passages describing an offer (`scripts/extract_offer_snippets.py`).
- Every passage read and structured without inference (job, pay, platform, location, target, requirements,
  contact, verbatim quote, Type A / Type B flags, scheme, outcome). Verbatim quotes are checked as exact substrings.
- 352 offer descriptions after merging (295 verified after the independent audit below) (`data/real/press_offers.csv`), **215 in Mexico**, documented by 321 articles
  (`data/real/press_offer_sources.csv`). 48 carry a verbatim quote of the ad or recruiter message.
- Deduplication is conservative: heavily covered cases (e.g. Teuchitlán) may still appear more than once.

## Independent audit (4 Nov 2026)

Every offer was re-read by an independent reviewer against its source text, and the result was checked by code (`scripts/apply_audit.py`):
evidence sentences must be literal substrings of the source.

| Status | Offers | Rule |
|---|---:|---|
| **verificada** | **295** | reviewer says the offer was deceptive or criminal recruitment AND gives a literal sentence that proves it |
| dudosa | 55 | the text does not state explicitly that the offer was deceptive (kept, not counted) |
| descartada | 2 | not a deceptive offer |

77 field values were corrected or emptied in 70 offers (e.g. the place where the victim ended up recorded
as the offer location; the forced job recorded as the promised job; victim testimony recorded as a recruiter
quote). Only **verificada** offers are loaded into the VKG (`db/12_press_offers_real.sql`).
Output: `data/real/press_offers_verified.csv` (columns `audit_status`, `audit_evidence`, `audit_changes`).

## Reasoning check

Ontology v1.10 + 295 verified offers + 1,500 synthetic items: **consistent under HermiT** (ROBOT 1.9.11).
SPARQL answers over the reasoned graph match the direct counts on the CSV.

## Answers (verified offers only)

**Q36. Who is targeted (Mexico, 167 verified offers, 103 state a profile):** young people 48, women 27,
adolescents or minors 22, men 8, migrants 6, students 5, Indigenous people 3.

**Q37. Where the job was said to be (Mexico, 133 state a place):** Jalisco 51, CDMX 9, Puebla 8,
Quintana Roo 7, Chihuahua 6. Jalisco is inflated by repeated coverage of the Teuchitlán case.

**Q38. Exact wording:** 39 verified quotes of the ad or recruiter message (victim and witness testimony excluded),
e.g. "Ocupamos gente hombres que le interesa trabajar para la 'empresa cuatro letras'" (RTVE),
"Hombres que quieran trabajar para la empresa (nombre del grupo criminal) se les pagará 8 mil por semana"
(El Informador), "estamos reclutando gente… Inbox" (International Crisis Group).

**Q39. Type A vs Type B (191 verified offers with at least one flag):** only classic 118, only credible-lethal 38,
both 35. **73 of 191 (38%) carry at least one credible-lethal signal.** Press-documented offers: not a prevalence.

**Q40. Channels of criminal-recruitment offers (verified, naming a platform):** TikTok 13, Facebook 9, WhatsApp 2.

Other verified counts (Mexico): 93 of 167 are criminal recruitment; most frequent promised job is security guard
or private security (45); median promised weekly pay 6,000 MXN (23 offers with weekly MXN pay).

## External benchmark: Consejo Ciudadano (CDMX), public figures

`scripts/scrape_consejo_ciudadano.py` read 503 bulletins and 192 PDF reports (695 documents, 164 on topic,
739 sentences with figures: `data/processed/consejo/cifras_consejo.csv`). 21 key figures, each verified against
its source sentence, are in `data/real/consejo_cifras_clave.csv`.

Share of trafficking cases reported to the National Anti-Trafficking Hotline (LNCTP) where the lure was a
fake job offer, as published by the Consejo: 47% (2019-2020 analysis), 44% (Jul 2021), 41% (2021), 35% (Jul 2022),
30.6% (4th annual report, Jul 2024), 34.8% among adult women (6th report, 2025-2026), about 30% (Apr 2026).
Among victims recruited through fake job offers: 75% women, 56% destined to prostitution, 52% aged 18 to 31 (Apr 2026).
Fake job offers are the first recruitment method in every annual report since the pandemic.

**Required citation (Consejo Ciudadano, 4 Nov 2026): always cite the source as "Consejo Ciudadano para la Seguridad y Justicia de la Ciudad de México", with the document of origin.** These are the Consejo's own aggregates (hotline reports), not a reanalysis. They give the population-level
frame for the press-offer corpus above.

## Formality bias (limitation flagged by the Consejo Ciudadano, 4 Nov 2026)

Consejo Ciudadano staff (personal communication) report that recruitment by organised crime happens mostly
through informal "chambitas" (supposed motorcycle sales, call centres) that are not even formal companies, and in
marginalised areas through word of mouth. The legitimate-offer sample (`data/real/legit_offers.csv`) comes from formal
job boards, so a rule learned from "trap vs legitimate" risks learning "informal vs formal". Mitigation: (1) report the
contrast as formal-legitimate vs trap, not as legitimate vs trap in general; (2) seek informal legitimate offers
(e.g. Ramona reports judged legitimate); (3) treat word-of-mouth recruitment as outside what text-based detection can see.
