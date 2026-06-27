# Classifier validation and the limits of press as a source

Updated: 26 June 2026.

This document records an internal validation of the press classifier and an honest
statement of what the press observatory can and cannot measure. It supersedes the
earlier "Type-B-only outnumbers Type-A-only by ~10x" headline, which did not survive
validation.

## Why we audited

The rule-based classifier (`scripts/classify_press.py`) reported that the dominant
Type-B pattern, `filtro_datos_personales`, fired in 51.9% of case-relevant articles,
and that Type-B-only cases outnumbered Type-A-only cases by roughly 10:1. Both numbers
were suspiciously high, so we audited the regex and then validated against a human-grade
LLM read of a sample.

## Finding 1 — the regex had large false-positive rates

Several patterns matched substrings inside unrelated words because they lacked word
boundaries:

| Pattern | Reported count | True count | Cause |
|---|---:|---:|---|
| `filtro_datos_personales` (Type-B) | 1,255 | 46 | the token `ine` (no `\b`) matched *define, imagine, examine, termine* |
| `aceptacion_urgente` (Type-A) | 298 | noise-dominated | `urge(nte)?` matched journalistic urgency (*rescate urgente*, *llamado urgente*, even *surge*), not offer urgency |
| `labour_hospitality` | 47.8% of cases | 10.6% | the token `bar` (no `\b`) matched *bárbaro, embargo, barrio, Barcelona* |
| `family` (recruitment) | 31.5% | 27.7% | `prim[oa]` matched *primavera, primaria, primordial* |

After adding word boundaries and requiring request-context for `filtro_datos_personales`,
the A:B ratio did not just shrink, it inverted (to ~0.5x). That inversion was the signal
that the ratio itself was an artefact of the method, not a property of the world.

## Finding 2 — press articles rarely contain the offer (LLM validation)

We sampled 120 case-relevant articles (deterministic stride over the corpus) and had an
LLM annotator read the title plus the first ~700 characters of each, with strict
instructions and an explicit "not determinable" option.

| Metric | Result |
|---|---:|
| Articles that actually describe the **terms of a job offer** (salary, schedule, contact, location) | **10 of 120 (8.3%)** |
| Type-A only (red flags explicit in the offer) | 4 |
| Type-B only (plausible role, risk in first-contact logistics) | 6 |
| Type-A and Type-B | 0 |
| Case-relevant but the article does **not** describe the offer | **110 of 120 (91.7%)** |

The annotator's note: even in unambiguous recruitment-by-fake-job cases (Edith Guadalupe,
Rancho Izaguirre, disappearance-after-interview), the article reports the investigation or
the rescue, not the salary, schedule, or contact channel. The offer text is simply not in
the news article.

## Conclusion — what the press observatory can and cannot measure

**Cannot measure (do not report as data):**
- The Type-A vs Type-B ratio. The offer terms are present in only ~8% of articles, and
  among those the sample is too small (6 vs 4) to support any ratio. This is a property of
  the source, not a fixable bug. **The "credible-lethal offers outnumber classic-red-flag
  offers by 10x" claim is withdrawn.**

**Can measure (defensible from press, with the corrected classifier):**
- **Geographic coverage**: 18 countries observed (Mexico, Colombia, USA, Argentina, Peru,
  Bolivia, Ecuador, Spain, Chile, Venezuela, Brazil, Paraguay, Dominican Republic,
  Guatemala, Honduras, El Salvador, Costa Rica, Nicaragua).
- **Volume and provenance**: 2,591 articles, 2,379 case-relevant, anchored to real URLs
  including UNODC and REDIM.
- **Exploitation outcome** (when stated): sexual, labour, forced criminality, organ
  removal, forced begging. Reported as directional shares, not precise rates.
- **A documented-case corpus**: the articles themselves, usable as evidence anchors and as
  a catalogue of named schemes.

## Where the Type-A/Type-B signal actually lives

The offer terms needed to separate Type-A from Type-B live in the **reports users submit
to Ramona** (the operational platform), not in press. When that data is available, the LLM
classifier (`scripts/classify_llm.py`) can run over it to produce a defensible A:B figure.
Until then, the credible-lethal hypothesis is stated as a hypothesis, not a measured ratio.

## Reproducibility

- Corrected rule-based classifier: `scripts/classify_press.py`.
- LLM classifier (for offer-bearing data, requires an API key): `scripts/classify_llm.py`.
- Validation sample: regenerated deterministically from `data/processed/press_cases.jsonl`.
