# Diccionario de datos — Export de ofertas de Ramona para el VKG (TU Wien)

Esta es la guía para reunir los datos operativos de Ramona que alimentarán el Virtual
Knowledge Graph y el paper de la residencia en TU Wien. Cada fila del CSV es UNA oferta
reportada o detectada por Ramona.

Archivos en esta carpeta:
- `ramona_offers_template.csv` — la plantilla con encabezados y 2 filas de ejemplo.
- `ramona_offers_ejemplo.jsonl` — el mismo ejemplo en JSONL (formato que consume `scripts/classify_llm.py`).
- Los datos REALES con cualquier dato sensible van en `data/operational/private/` (esa
  carpeta NO se sube a GitHub, ver `.gitignore`).

## Reglas de oro

1. **Una fila = una oferta.** No mezcles varias ofertas en una fila.
2. **Nada de datos personales (PII) en el export.** Ver sección "Privacidad" al final.
3. **Si no sabes un dato, déjalo vacío.** No inventes. Vacío es información válida.
4. **Lo mínimo viable son las columnas marcadas [CORE].** El resto suma, pero empieza por esas.
5. **Meta de captura: 300 a 500 ofertas con etiqueta humana revisada.** Con eso ya hay paper.

## Columnas

### Tier 1 — La oferta (CORE)

| Columna | Tipo | Valores / formato | Notas |
|---|---|---|---|
| `offer_id` [CORE] | texto | ID único, ej. OFR-0001 | NO uses el nombre o teléfono. Solo un folio interno. |
| `offer_text` [CORE] | texto | el mensaje/publicación completo | Lo más importante. Quita nombres y teléfonos del texto. |
| `offer_screenshot_url` | URL | enlace al screenshot | Opcional pero muy útil. Que no exponga PII. |
| `source_platform` [CORE] | catálogo | facebook, instagram, tiktok, whatsapp, telegram, computrabajo, indeed, linkedin, olx, marketplace, otro | De dónde salió la oferta. |
| `channel_type` | catálogo | red_social, app_mensajeria, bolsa_trabajo, clasificados, referido, otro | Tipo de canal. |
| `job_title` | texto | ej. Empacador, Recepcionista | Puesto ofrecido. |
| `promised_salary_amount` | número | ej. 9000 | Solo el número. |
| `promised_salary_currency` | catálogo | MXN, USD, COP, ARS, PEN, EUR, otro | Moneda. |
| `promised_salary_period` | catálogo | mensual, quincenal, semanal, diario, por_tarea | Periodo del sueldo. |
| `schedule` | texto | ej. flexible, medio turno, fijo | Horario declarado. |
| `requirements` | texto | ej. sin experiencia, bachillerato | Requisitos declarados. |
| `declared_location` | texto | ciudad y estado/país declarados | Dónde dice estar el trabajo. |
| `offer_language` | catálogo | es, pt, en | Idioma de la oferta. |
| `first_contact_at` | fecha-hora | ISO 8601, ej. 2026-07-03T10:22:00 | Cuándo fue el primer contacto. |

### Tier 2 — El veredicto (GROUND TRUTH, lo más valioso)

| Columna | Tipo | Valores / formato | Notas |
|---|---|---|---|
| `ramona_verdict` [CORE] | catálogo | fraude, sospechosa, legitima, no_concluyente | Veredicto de Ramona. |
| `risk_level` | catálogo | bajo, medio, alto, critico | Nivel de riesgo. |
| `risk_axis` | catálogo múltiple | fraude, explotacion, trata (separa con `;`) | Eje(s) de riesgo. Una oferta puede tener varios. |
| `classifier_confidence` | número 0 a 1 | ej. 0.91 | Confianza del modelo de Ramona, si existe. |
| `human_reviewed` [CORE] | booleano | true, false | ¿Un humano revisó esta etiqueta? Las revisadas son oro. |
| `human_label` | catálogo | fraude_confirmado, creible_letal_confirmado, legitima_confirmada, descartado | Etiqueta del revisor humano. |

### Tier 3 — Las señales (lo que separa Type-A de Type-B)

Llena con valores del catálogo, separados por `;`. Deja vacío si no aplica.

| Columna | Catálogo de valores permitidos |
|---|---|
| `type_a_flags` (red flags clásicas) | sueldo_alto, sin_experiencia, contratacion_urgente, pago_adelantado, traslado_pagado, horario_flexible, empleo_fuera_estado |
| `type_b_flags` (creíble-letal) | empresa_sin_nombre, whatsapp_sin_logo, cita_edificio_multiusos, pidio_ir_sola, pidio_sin_identificacion, messenger_a_whatsapp, horario_atipico, pidio_datos_personales, rol_plausible_gancho, cambio_ubicacion_ultimo_momento |

Estas dos columnas son las que permiten medir el ratio Type-A vs Type-B DE VERDAD (el que
no se pudo medir desde prensa). Mientras más ofertas con estas señales marcadas, más fuerte
el hallazgo.

### Tier 4 — Desenlace (difícil pero muy valioso si lo tienes)

| Columna | Tipo | Valores / formato |
|---|---|---|
| `outcome_known` | booleano | true, false |
| `outcome` | catálogo | asistio_sin_dano, no_asistio, dano_reportado, desaparicion, rescate, desconocido |

Conectar la oferta con lo que pasó después es lo que prueba la "letalidad". Aunque sea para
pocas ofertas, vale muchísimo.

### Tier 5 — Contexto y demografía (sin PII)

| Columna | Tipo | Valores / formato |
|---|---|---|
| `candidate_age_range` | catálogo | 18-24, 25-34, 35-44, 45-54, 55+, nd |
| `candidate_gender` | catálogo | F, M, otro, nd |
| `candidate_state` | texto | estado de México o país |
| `report_date` | fecha | ISO, ej. 2026-07-03 |
| `notes` | texto | observaciones libres |

## Privacidad (obligatorio para que el trabajo sea publicable)

- **No incluyas:** nombres reales, teléfonos, correos, CURP, INE, direcciones exactas de
  personas, fotos de personas.
- **Sí puedes incluir:** el texto de la oferta CON los datos personales borrados o
  reemplazados (ej. "manda WhatsApp al [TELEFONO]").
- **Anonimiza identificadores:** si necesitas rastrear al reclutador o candidato entre
  filas, usa un hash (SHA-256) del dato, nunca el dato real. La ontología ya está diseñada
  para trabajar con hashes.
- **Base legal:** ten claro el consentimiento o la base legal bajo la que Ramona puede usar
  estos reportes para investigación. Magdalena lo va a preguntar.

## Cuando tengas los datos

1. Pon el CSV/JSONL real en `data/operational/private/`.
2. Conviértelo a JSONL si hace falta (una línea por oferta, con al menos `id` y `text`).
3. Corre `python scripts/classify_llm.py --in data/operational/private/tus_datos.jsonl ...`
   para clasificar con LLM y obtener el ratio Type-A vs Type-B real y defendible.
