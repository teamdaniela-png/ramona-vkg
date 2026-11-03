# Real offer corpus: first results (v1.10, 3 Nov 2026)

## Corpus

- Source: 2,124 press articles on recruitment cases (`data/raw/press.jsonl`, scraped Apr to Jun 2026).
- 532 articles contain passages describing an offer (`scripts/extract_offer_snippets.py`).
- Every passage read and structured without inference (job, pay, platform, location, target, requirements,
  contact, verbatim quote, Type A / Type B flags, scheme, outcome). Verbatim quotes are checked as exact substrings.
- 352 offer descriptions after merging (`data/real/press_offers.csv`), **215 in Mexico**, documented by 321 articles
  (`data/real/press_offer_sources.csv`). 48 carry a verbatim quote of the ad or recruiter message.
- Deduplication is conservative: heavily covered cases (e.g. Teuchitlán) may still appear more than once.

## Reasoning check

Ontology v1.10 + 352 real offers + 1,500 synthetic social-media items (50,600 triples after reasoning):
**consistent under HermiT** (ROBOT 1.9.11). The ontology remains in the OWL 2 QL profile.

## Answers (SPARQL over the HermiT-materialised graph; Ontop run pending Docker)

**Q36. Who is targeted (Mexico, offers that state a profile):** young people 74, women 42, adolescents or minors 25,
migrants 7, students 7, Indigenous people 4.

**Q37. Where (Mexico, offered location as reported):** Jalisco 71, CDMX 21, Chihuahua 15, Puebla 9, Quintana Roo 8,
Guanajuato 5. Jalisco is inflated by repeated coverage of the Teuchitlán case.

**Q38. Exact wording:** 48 verbatim quotes with outlet and URL, e.g. "tienes que venir sola y sin INE" (La Silla Rota),
"puras jovencitas" (BajaNews), "estamos reclutando gente… Inbox" (International Crisis Group).

**Q39. Type A vs Type B (all countries, 229 offers with at least one flag):** only classic flags 141, only
credible-lethal 46, both 42. **88 of 229 offers (38%) carry at least one credible-lethal signal.**
This is a property of press-documented offers, not a prevalence estimate; the withdrawn press ratio of v1.7 is
not reinstated (`docs/CLASSIFIER_VALIDATION.md`).

**Q40. Channels of criminal-recruitment offers:** TikTok 13, Facebook 10, WhatsApp 2 (offers that name a platform).

## Limits

Press reports cases that reached the news (selection bias towards outcomes such as disappearance and rescue).
Ramona operational reports and Consejo Ciudadano figures are the next sources.

## Reproduce

```bash
python3 scripts/build_real_offers.py
python3 scripts/build_press_offers_module.py
.venv/bin/python scripts/materialize_press_abox.py /tmp/press.ttl
.venv/bin/python scripts/materialize_social_abox.py /tmp/social.ttl
java -jar robot.jar merge --input ontology/ratr-o.ttl --input /tmp/press.ttl --input /tmp/social.ttl \
  reason --reasoner hermit --axiom-generators "ClassAssertion" --include-indirect true --output /tmp/all.ttl
# then run queries/Q36..Q40 against /tmp/all.ttl
```

## External benchmark: Consejo Ciudadano (CDMX), public figures

`scripts/scrape_consejo_ciudadano.py` read 503 bulletins and 192 PDF reports (695 documents, 164 on topic,
739 sentences with figures: `data/processed/consejo/cifras_consejo.csv`). 21 key figures, each verified against
its source sentence, are in `data/real/consejo_cifras_clave.csv`.

Share of trafficking cases reported to the National Anti-Trafficking Hotline (LNCTP) where the lure was a
fake job offer, as published by the Consejo: 47% (2019-2020 analysis), 44% (Jul 2021), 41% (2021), 35% (Jul 2022),
30.6% (4th annual report, Jul 2024), 34.8% among adult women (6th report, 2025-2026), about 30% (Apr 2026).
Among victims recruited through fake job offers: 75% women, 56% destined to prostitution, 52% aged 18 to 31 (Apr 2026).
Fake job offers are the first recruitment method in every annual report since the pandemic.

These are the Consejo's own aggregates (hotline reports), not a reanalysis. They give the population-level
frame for the press-offer corpus above.
