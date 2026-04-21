-- Reference seed data for Ramona demo VKG
SET search_path TO ramona, public;

-- Countries -------------------------------------------------------------------
INSERT INTO countries (country_code, country_name) VALUES
 ('MX','Mexico'),
 ('CO','Colombia'),
 ('PE','Peru'),
 ('AR','Argentina'),
 ('CL','Chile'),
 ('GT','Guatemala'),
 ('US','United States'),
 ('ES','Spain');

-- Languages -------------------------------------------------------------------
INSERT INTO languages (language_code, language_name) VALUES
 ('es','Spanish'),
 ('en','English'),
 ('pt','Portuguese');

-- Platforms -------------------------------------------------------------------
INSERT INTO platforms (platform_name, platform_type, platform_country) VALUES
 ('WhatsApp',         'whatsapp',     NULL),
 ('Telegram',         'telegram',     NULL),
 ('Facebook Messenger','messenger',   NULL),
 ('SMS Gateway',      'sms',          NULL),
 ('TikTok',           'tiktok',       NULL),
 ('OCC Mundial',      'classifieds',  'MX'),
 ('CompuTrabajo',     'classifieds',  'MX'),
 ('Facebook Marketplace','facebook',  NULL);

-- Evidence sources ------------------------------------------------------------
INSERT INTO evidence_sources (source_title, source_outlet, source_url, source_date) VALUES
 ('"Pedian Ir Sola": Narran Como Eran Citas de Trabajo en Edificio Donde Hallaron a Edith Guadalupe',
  'N+', 'https://www.nmas.com.mx/', DATE '2026-04-17'),
 ('Grupos delictivos refinan reclutamiento en redes sociales tras caso del Rancho Izaguirre',
  'El Sol de Mexico', 'https://www.elsoldemexico.com.mx/', DATE '2026-03-14'),
 ('Como detectar las ofertas de trabajo falsas (infografia Ramona AI)',
  'Ramona AI', 'https://ramonaaliadalaboral.com/', DATE '2025-11-01'),
 ('Estadisticas de victimas de ofertas falsas: Consejo Ciudadano CDMX',
  'Consejo Ciudadano para la Seguridad y Justicia CDMX', 'https://consejociudadanomx.org/', DATE '2025-09-15'),
 ('Alerta de seguridad: Rancho Izaguirre y reclutamiento forzado CJNG',
  'Yahoo Noticias', 'https://es-us.noticias.yahoo.com/', DATE '2025-03-20');

-- Trafficking routes ----------------------------------------------------------
INSERT INTO trafficking_routes (route_name, origin_country, destination_country, known_since, evidence_source) VALUES
 ('CDMX interna: Benito Juarez (Revolucion 829)', 'MX','MX', DATE '2026-04-15',
   (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('Guadalajara metropolitana -> Teuchitlan (Rancho Izaguirre)', 'MX','MX', DATE '2025-03-05',
   (SELECT source_id FROM evidence_sources WHERE source_outlet = 'El Sol de Mexico')),
 ('Mexico -> Guatemala (Tapachula corridor)', 'MX','GT', DATE '2024-01-10',
   (SELECT source_id FROM evidence_sources WHERE source_outlet = 'Yahoo Noticias')),
 ('Colombia interna: Medellin -> Necocli (maritima)', 'CO','CO', DATE '2024-06-01', NULL),
 ('Peru: Lima -> Madre de Dios (mineria ilegal)', 'PE','PE', DATE '2023-11-15', NULL),
 ('Argentina: Buenos Aires -> interior (domestic)', 'AR','AR', DATE '2024-08-20', NULL),
 ('Chile: Santiago -> Antofagasta (trabajo agricola)', 'CL','CL', DATE '2025-02-01', NULL);

-- Survivor testimony patterns (derived from documented real cases) ------------
INSERT INTO survivor_patterns (pattern_name, pattern_description, evidence_source) VALUES
 ('messenger_to_whatsapp',
  'Primer contacto por Facebook Messenger, luego migracion forzada a WhatsApp donde desaparece la trazabilidad del perfil publico.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('filtro_datos_personales',
  'Antes de la entrevista piden datos personales sensibles: edad, estado civil, si tiene hijos, disponibilidad para viajar.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('solicita_ir_sola',
  'Indicacion explicita de acudir sin acompañante al lugar de la entrevista.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('solicita_sin_identificacion',
  'Indicacion explicita de no llevar credencial de elector u otra identificacion oficial.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('empresa_sin_nombre',
  'La supuesta empresa no proporciona nombre comercial, RFC, ni sitio web.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('sin_logo_whatsapp',
  'La cuenta de WhatsApp desde la que se contacta no tiene foto de perfil ni logo institucional.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('sueldos_4k_12k_semanal',
  'Rango salarial semanal ofrecido entre 4,000 y 12,000 MXN, patron documentado en reclutamiento CJNG post-Rancho Izaguirre.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'El Sol de Mexico')),
 ('cita_central_autobuses',
  'Primera cita en central camionera o punto de reunion publico antes de traslado a destino real.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'El Sol de Mexico')),
 ('cita_edificio_multiusos',
  'Cita en inmueble catalogado como "edificio multiusos" o vivienda privada sin senialetica corporativa.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('gancho_seguridad_privada',
  'Oferta disfrazada de "vacante de seguridad privada" o "guardia" con sueldos por encima de mercado.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'El Sol de Mexico')),
 ('horarios_flexibles_madres_solteras',
  'Gancho explicito a madres solteras o jefas de hogar con promesa de horarios flexibles.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'N+')),
 ('traslado_pagado',
  'La supuesta empresa ofrece pagar el transporte del candidato al lugar de la entrevista.',
  (SELECT source_id FROM evidence_sources WHERE source_outlet = 'Ramona AI'));
