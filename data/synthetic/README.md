# Synthetic data: criminal recruitment on TikTok

Everything in this folder is synthetic. There are no real posts, accounts, telephone numbers or persons.
The items populate the VKG with `:ForcedCriminalityScheme` and `:ChildRecruitmentCriminalScheme` and serve
to test detectors.

## Where the words come from

Lexicon: `data/lexicon/tiktok_reclutamiento_lexicon.csv`, 79 terms, 71 of them verbatim.
Source: Seminario sobre Violencia y Paz, El Colegio de México (2025), *Del scroll al "jale": cómo se
recluta en TikTok* (100 videos, 15 March to 31 August 2025). Each term carries the page and the image of
the report it comes from. Column `tipo`:

- `verbatim_colmex`: appears as such in the report.
- `variante_sintetica`: a spelling or hashtag variant written for this dataset.

Categories: `oferta_llamado`, `oferta_alcance`, `pago`, `contacto_privado`, `codigo_grupo`, `emoji_grupo`,
`hashtag`, `aspiracion_fatalismo`, `aspiracion_familia`, `autopostulacion`, `menciona_menor`,
`respuesta_reclutador`.

## What the dataset contains (seed 2026, 1,500 rows)

| label | n | what it is | Colmex story |
|---|---|---|---|
| `reclutamiento_directo` | 600 | post with an explicit call (NR) | enrol in crime (NR*ECC) or emotional connection (NR*A) |
| `aspiracion_belica` | 150 | aspiration without an explicit offer | warlike (ECC*A*AVC) |
| `autopostulacion` | 250 | comment of someone asking to join | n/a |
| `respuesta_reclutador` | 50 | short reply in the comments | NR |
| `cultura_sin_reclutamiento` | 150 | music and fan content without an offer | n/a |
| `legitima_control` | 300 | legitimate offer written with the same slang | n/a |

78% of the legitimate controls trigger at least one lexicon term, by design: a detector that relies on
keywords alone does not separate them.

Columns: the schema of `data/operational/ramona_offers_template.csv` plus `synthetic`, `content_type`,
`label`, `relato_colmex`, `colmex_conditions`, `ratro_scheme`, `crim_flags`, `hashtags`, `audio_hint`,
`visual_hint`, `lexicon_term_ids`, `template_source`.

`crim_flags`: llamado_privado, codigo_grupo, emoji_grupo, pago_semanal_alto, apela_familia,
menciona_edad_menor, invita_mujeres, alcance_nacional, hashtag_reclutamiento, fatalismo. An item with
`menciona_edad_menor` is assigned `:ChildRecruitmentCriminalScheme`.

## Regenerating

```bash
python3 scripts/build_tiktok_synthetic.py --seed 2026
```

## Scope

1. The templates recombine phrases of the report. The distribution does not represent what circulates on
   TikTok; the report states that its 100 videos are not a representative sample.
2. The visual and sound components (ECC, A) are given as descriptive text in `visual_hint` and `audio_hint`.
3. No figure computed over this dataset is an empirical finding.
4. The salaries of the legitimate controls are plausible ranges.
