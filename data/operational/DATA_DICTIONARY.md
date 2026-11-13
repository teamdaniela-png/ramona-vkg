# Data dictionary of an offer export

The format in which a table of job offers is read by `scripts/classify_llm.py` and by the synthetic
dataset in `data/synthetic/`. One row is one offer.

- `ramona_offers_template.csv`: the header and two example rows.
- `ramona_offers_ejemplo.jsonl`: the same two examples as JSON Lines.

No export is published in this repository. `data/operational/private/` is git-ignored.

## The offer

| Column | Type | Values |
|---|---|---|
| `offer_id` | text | an internal identifier, for example OFR-0001 |
| `offer_text` | text | the message or post, with names and telephone numbers removed |
| `offer_screenshot_url` | URL | optional |
| `source_platform` | code | facebook, instagram, tiktok, whatsapp, telegram, computrabajo, indeed, linkedin, olx, marketplace, otro |
| `channel_type` | code | red_social, app_mensajeria, bolsa_trabajo, clasificados, referido, otro |
| `job_title` | text | the job offered |
| `promised_salary_amount` | number | the amount alone |
| `promised_salary_currency` | code | MXN, USD, COP, ARS, PEN, EUR, otro |
| `promised_salary_period` | code | mensual, quincenal, semanal, diario, por_tarea |
| `schedule` | text | the schedule stated |
| `requirements` | text | the requirements stated |
| `declared_location` | text | where the offer says the job is |
| `offer_language` | code | es, pt, en |
| `first_contact_at` | date and time | ISO 8601 |

## The assessment

| Column | Type | Values |
|---|---|---|
| `ramona_verdict` | code | fraude, sospechosa, legitima, no_concluyente |
| `risk_level` | code | bajo, medio, alto, critico |
| `risk_axis` | codes separated by `;` | fraude, explotacion, trata |
| `classifier_confidence` | number from 0 to 1 | |
| `human_reviewed` | boolean | true, false |
| `human_label` | code | fraude_confirmado, creible_letal_confirmado, legitima_confirmada, descartado |

## The signals

Codes separated by `;`. Empty when none applies.

| Column | Values |
|---|---|
| `type_a_flags`, classic red flags | sueldo_alto, sin_experiencia, contratacion_urgente, pago_adelantado, traslado_pagado, horario_flexible, empleo_fuera_estado |
| `type_b_flags`, credible-lethal signals | empresa_sin_nombre, whatsapp_sin_logo, cita_edificio_multiusos, pidio_ir_sola, pidio_sin_identificacion, messenger_a_whatsapp, horario_atipico, pidio_datos_personales, rol_plausible_gancho, cambio_ubicacion_ultimo_momento |

## The outcome

| Column | Type | Values |
|---|---|---|
| `outcome_known` | boolean | true, false |
| `outcome` | code | asistio_sin_dano, no_asistio, dano_reportado, desaparicion, rescate, desconocido |

## Context

| Column | Type | Values |
|---|---|---|
| `candidate_age_range` | code | 18-24, 25-34, 35-44, 45-54, 55+, nd |
| `candidate_gender` | code | F, M, otro, nd |
| `candidate_state` | text | state or country |
| `report_date` | date | ISO 8601 |
| `notes` | text | |

## Privacy

An export carries no names, telephone numbers, e-mail addresses, identity numbers, exact addresses or
photographs of persons. The text of an offer is kept with personal data removed or replaced, for example
"manda WhatsApp al [TELEFONO]". Where a recruiter or a candidate has to be followed across rows, the
identifier is a SHA-256 hash of the datum.
