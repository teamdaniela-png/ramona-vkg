# Datos reales

## `press_offers.csv`, `press_offer_sources.csv`
352 descripciones de ofertas de trabajo extraídas de 321 notas de prensa (cada oferta con sus ligas).
Método y límites: `docs/results/REAL_OFFERS_RESULTS.md`.

## `consejo_cifras_clave.csv`

**Fuente obligatoria en toda publicación, presentación o paper que use estas cifras:**

> Fuente: Consejo Ciudadano para la Seguridad y Justicia de la Ciudad de México (Consejo Ciudadano),
> datos de la Línea y Chat Nacional contra la Trata de Personas, publicados en sus reportes y boletines
> (consejociudadanomx.org). Se cita cada cifra con el documento de origen (columna `url`).

Condición expresa del Consejo Ciudadano (4 nov 2026): los datos están en sus reportes de consulta
gratuita y solo piden que **siempre se cite al Consejo Ciudadano como fuente**.

Cada fila trae la cita textual del documento (`cita_textual`) y su liga (`url`). Son cifras agregadas
del propio Consejo, no un reanálisis.

## `legit_offers.csv`
51 anuncios de empleo capturados de bolsas de trabajo formales el 4 de noviembre de 2026, con una nota sobre
si el empleador pudo verificarse en fuentes públicas (37 verificados, 14 no verificados o casos frontera).
Se cargan al VKG con `scripts/build_legit_offers_module.py`. Vienen de bolsas formales, así que la comparación
con los casos documentados es entre anuncios formales y casos, no entre lo legítimo y lo fraudulento en general
(ver `docs/results/REAL_OFFERS_RESULTS.md`).
