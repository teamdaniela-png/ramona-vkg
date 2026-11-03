# Data sintética: reclutamiento criminal en TikTok

**Todo lo que hay en esta carpeta es SINTÉTICO.** No son publicaciones reales, no hay cuentas,
teléfonos ni personas. Sirve para entrenar y evaluar detectores, y para poblar el VKG con
`:ForcedCriminalityScheme` y `:ChildRecruitmentCriminalScheme` mientras llegan datos operativos.

## De dónde salen las palabras

Léxico en `data/lexicon/tiktok_reclutamiento_lexicon.csv` (79 términos, 71 verbatim).
Fuente: Seminario sobre Violencia y Paz, El Colegio de México (2025), *Del scroll al "jale":
cómo se recluta en TikTok* (100 videos, 15 de marzo a 31 de agosto de 2025).

Cada término trae página e imagen del informe. Las palabras reales están en las **capturas**
(texto sobre video y comentarios), no en el cuerpo del texto. Columna `tipo`:

- `verbatim_colmex`: aparece tal cual en el informe.
- `variante_sintetica`: variante nuestra (ortografía, hashtags genéricos). No citar como hallazgo.

Categorías: `oferta_llamado`, `oferta_alcance`, `pago`, `contacto_privado`, `codigo_grupo`,
`emoji_grupo`, `hashtag`, `aspiracion_fatalismo`, `aspiracion_familia`, `autopostulacion`,
`menciona_menor`, `respuesta_reclutador`.

## Qué contiene el dataset (seed 2026, 1,500 filas)

| label | n | qué es | relato Colmex |
|---|---|---|---|
| `reclutamiento_directo` | 600 | anuncio con llamado explícito (NR) | enrolarse (NR*ECC) o conexión emocional (NR*A) |
| `aspiracion_belica` | 150 | aspiración sin oferta explícita | bélicos (ECC*A*AVC) |
| `autopostulacion` | 250 | comentario de alguien pidiendo entrar | n/a |
| `respuesta_reclutador` | 50 | respuesta corta en comentarios ("manda mensaje") | NR |
| `cultura_sin_reclutamiento` | 150 | corridos y fans, sin oferta (control difícil) | n/a |
| `legitima_control` | 300 | oferta real con el mismo slang: jale, chamba, plaza, al privado | n/a |

El 78% de los controles legítimos activa al menos un término del léxico. Eso es a propósito:
un detector por palabras clave solas falla, y este dataset lo demuestra.

Columnas = esquema de `data/operational/ramona_offers_template.csv` + extras:
`synthetic`, `content_type`, `label`, `relato_colmex`, `colmex_conditions`, `ratro_scheme`,
`crim_flags`, `hashtags`, `audio_hint`, `visual_hint`, `lexicon_term_ids`, `template_source`.

`crim_flags`: llamado_privado, codigo_grupo, emoji_grupo, pago_semanal_alto, apela_familia,
menciona_edad_menor, invita_mujeres, alcance_nacional, hashtag_reclutamiento, fatalismo.
Si hay `menciona_edad_menor`, el esquema pasa a `:ChildRecruitmentCriminalScheme`.

## Regenerar

```bash
python3 scripts/build_tiktok_synthetic.py --seed 2026
```

## Límites (decirlos en el paper)

1. Las plantillas recombinan frases del informe. La distribución NO representa lo que circula en
   TikTok; el propio Colmex aclara que su corpus de 100 videos no es representativo.
2. El componente visual y sonoro (ECC, A) va como texto descriptivo en `visual_hint` y `audio_hint`.
3. Ninguna cifra de este dataset es un hallazgo empírico. Sirve para probar el pipeline, no para afirmar prevalencias.
4. Los sueldos de los controles legítimos son rangos plausibles, no una encuesta salarial.
