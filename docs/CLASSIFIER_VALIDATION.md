# What the press corpus measures

The press observatory is a corpus of documented cases. This note records what a press article contains
about the offer behind a case, and therefore which questions the corpus can answer.

## Do press articles describe the offer?

120 case-relevant articles were sampled with a fixed stride over the corpus. An LLM annotator read the
title and the first 700 characters of each, with strict instructions and an explicit "not determinable"
option (`scripts/classify_llm.py`).

| | Articles |
|---|---:|
| Describe the terms of a job offer (salary, schedule, contact, location) | 10 of 120 (8.3%) |
| of which, classic red flags only (Type A) | 4 |
| of which, credible offer with risk in the first-contact logistics only (Type B) | 6 |
| of which, both | 0 |
| Case-relevant, the offer is not described | 110 of 120 (91.7%) |

Press articles report the investigation, the rescue or the outcome. The salary, the schedule and the
contact channel of the offer are seldom part of the story.

## What follows

- **Type A against Type B.** The press corpus does not support a ratio or a prevalence of the two tracks.
  The distinction is part of the ontology (`:ClassicRedFlag`, `:CredibleLethalRedFlag`); the counts the
  repository reports are counts of documented offers (`docs/results/REAL_OFFERS_RESULTS.md`).
- **Geographic coverage.** 18 countries: Mexico, Colombia, United States, Argentina, Peru, Bolivia, Ecuador,
  Spain, Chile, Venezuela, Brazil, Paraguay, Dominican Republic, Guatemala, Honduras, El Salvador, Costa Rica
  and Nicaragua.
- **Volume and provenance.** 2,591 articles, 2,379 of them case-relevant, each anchored to its URL.
- **Exploitation outcome**, when the article states it: sexual, labour, forced criminality, organ removal,
  forced begging. Reported as shares of documented cases.
- **A documented-case corpus.** The articles are evidence anchors and a catalogue of named schemes.

The terms of an offer are in the offers themselves. `scripts/classify_llm.py` runs over a table of offers
in the format of `data/operational/ramona_offers_template.csv`.

## Reproducing

- Rule-based classifier: `scripts/classify_press.py`.
- LLM annotator: `scripts/classify_llm.py` (needs an API key).
- The sample is drawn deterministically from `data/processed/press_cases.jsonl`.
