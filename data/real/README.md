# Documented data

## `press_offers.csv`, `press_offer_sources.csv`, `press_offers_verified.csv`

352 descriptions of job offers extracted from 321 press articles, each with the links to its sources.
`press_offers_verified.csv` adds the result of the independent review: 295 verified, 55 doubtful and
2 discarded. Only the verified ones are loaded into the VKG. Method: `docs/results/REAL_OFFERS_RESULTS.md`.

## `consejo_cifras_clave.csv`, `consejo_desgloses.csv`

Aggregate figures published by the Consejo Ciudadano para la Seguridad y Justicia de la Ciudad de México.
Each row carries the sentence of the source document (`cita_textual`) and its link (`url`).
`CONSEJO_DESGLOSES.md` describes the breakdowns.

Any publication, presentation or paper that uses these figures cites the source:

> Fuente: Consejo Ciudadano para la Seguridad y Justicia de la Ciudad de México (Consejo Ciudadano),
> datos de la Línea y Chat Nacional contra la Trata de Personas, publicados en sus reportes y boletines
> (consejociudadanomx.org).

## `legit_offers.csv`

51 job advertisements captured from formal job boards on 4 November 2026, with a note on whether the
employer could be verified in public sources (37 verified). Loaded into the VKG by
`scripts/build_legit_offers_module.py`. The comparison with the documented cases is between advertisements
on formal job boards and documented cases.
