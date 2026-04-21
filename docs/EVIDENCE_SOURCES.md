# Evidence Sources Catalogue

Every survivor testimony pattern and every trafficking route in the demo is linked to a public document. No pattern was invented. This file maps each `evidence_source` row in the Postgres seed to its real citation.

## Sources used

### 1. N+ (Televisa) — case of Edith Guadalupe Valdez Saldívar

- **Title**: "Pedían Ir Sola": Narran Cómo Eran Citas de Trabajo en Edificio Donde Hallaron a Edith Guadalupe
- **Outlet**: N+ (TelevisaUnivision)
- **Date**: 17 April 2026
- **URL**: https://www.nmas.com.mx/
- **Case**: 21-year-old woman found dead in the basement of a building on Avenida Revolución 829, Benito Juárez, CDMX. She had gone to an alleged job interview. A second woman who had been cited to the same building shared her testimony with N+ about how the modus operandi worked.
- **Patterns derived**: `messenger_to_whatsapp`, `filtro_datos_personales`, `solicita_ir_sola`, `solicita_sin_identificacion`, `empresa_sin_nombre`, `sin_logo_whatsapp`, `cita_edificio_multiusos`, `horarios_flexibles_madres_solteras`.
- **Route derived**: `CDMX interna: Benito Juárez (Revolución 829)`.

### 2. El Sol de México — Grupos delictivos refinan reclutamiento en redes sociales

- **Title**: Grupos delictivos refinan reclutamiento en redes sociales tras caso del Rancho Izaguirre
- **Author**: Jorge Salcedo
- **Outlet**: El Sol de México
- **Date**: 14 March 2026
- **URL**: https://www.elsoldemexico.com.mx/
- **Study cited in article**: "A un año del hallazgo del Rancho Izaguirre" by the Seminario sobre Violencia y Paz, Colegio de México.
- **Patterns derived**: `sueldos_4k_12k_semanal`, `cita_central_autobuses`, `gancho_seguridad_privada`.
- **Route derived**: `Guadalajara metropolitana -> Teuchitlán (Rancho Izaguirre)`.

### 3. Ramona AI — public infographic "¿Cómo detectar las ofertas de trabajo falsas?"

- **Outlet**: Ramona AI official social channels.
- **Date**: approximately November 2025.
- **URL**: https://ramonaaliadalaboral.com/
- **Content**: seven red flags used as the canonical flag taxonomy in the VKG: `sueldo_alto`, `horarios_flexibles`, `sin_experiencia`, `pago_adelantado`, `aceptacion_urgente`, `entrevista_lejana_traslado`, `empleo_fuera_estado`.
- **Pattern derived**: `traslado_pagado`.

### 4. Consejo Ciudadano para la Seguridad y Justicia CDMX

- **Outlet**: Consejo Ciudadano (María Elena Esparza Guevara, consejera en Género).
- **Date**: approximately September 2025.
- **URL**: https://consejociudadanomx.org/
- **Content**: demographic statistics used to size the synthetic seed. 41% of victims between 18 and 30 years old. 5% older than 60. Majority contacted via WhatsApp, Telegram or SMS.

### 5. Yahoo Noticias / Facebook source — Rancho Izaguirre CJNG

- **Outlet**: Yahoo Noticias (compiled from multiple public reports).
- **Date**: approximately March 2025.
- **Content**: the Rancho Izaguirre case in Teuchitlán, Jalisco. Recruits were contacted with offers of "private security" at 4,000 to 12,000 MXN weekly, cited at bus terminals, then transported to the ranch to be trained as sicarios or used for forced labour.
- **Route derived**: `Mexico -> Guatemala (Tapachula corridor)`.

## Notes for the Institute of Logic and Computation (TU Wien)

All patterns and routes in RATR-O v0.1 are traceable to these public sources via the `:derivedFrom` property connecting a `:SurvivorTestimonyPattern` or a `:TraffickingRoute` to an `:EvidenceSource`. This traceability is one of the contributions of the proposed VKG: auditors, regulators and partner institutions can follow any detection claim back to its documentary source.

No personally identifiable information about survivors, candidates, recruiters or victims appears in the demo. The synthetic offers in `db/03_seed_cases.sql` are inspired by the patterns in these public sources but do not reproduce any real victim's case file.
