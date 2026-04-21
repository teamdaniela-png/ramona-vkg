-- Case seed data for Ramona demo VKG
-- 50 anonymized offers inspired by documented Mexican cases (Edith Guadalupe, Rancho Izaguirre, Consejo Ciudadano).
-- No PII. All contact hashes are deterministic SHA-256 stubs for demo reproducibility.

SET search_path TO ramona, public;

-- Employers -------------------------------------------------------------------
INSERT INTO employers (employer_name, has_verified_identity, tax_id_hash, historical_offer_count, historical_flag_count) VALUES
 ('Servicios Integrales SA de CV',  TRUE,  'SHA_VRF_001', 120, 0),
 ('Asistencia Domestica MX',        TRUE,  'SHA_VRF_002',  85, 2),
 (NULL,                             FALSE, NULL,           14, 12),
 (NULL,                             FALSE, NULL,           23, 19),
 (NULL,                             FALSE, NULL,            7,  7),
 ('Corporativo Seguridad Jalisco',  FALSE, NULL,           48, 41),
 ('Plataforma Niñera MX',           TRUE,  'SHA_VRF_003',  60, 1);

-- Recruiters (contact_hash is a deterministic stub) ---------------------------
INSERT INTO recruiters (contact_hash, agent_name, recruiter_country, first_seen_at, historical_offer_count, historical_flag_count, associated_employer) VALUES
 ('HSH_R_0001','Reclutador A', 'MX', DATE '2025-11-10', 18, 14, 3),
 ('HSH_R_0002','Reclutador B', 'MX', DATE '2025-12-02', 23, 19, 4),
 ('HSH_R_0003','Reclutador C', 'MX', DATE '2026-01-20',  7,  7, 5),
 ('HSH_R_0004','Reclutador D', 'MX', DATE '2025-08-15', 48, 41, 6),
 ('HSH_R_0005','Agencia E',    'MX', DATE '2025-05-01',120,  0, 1),
 ('HSH_R_0006','Niñeras MX',   'MX', DATE '2025-06-12', 60,  1, 7),
 ('HSH_R_0007','Reclutador G', 'CO', DATE '2025-09-01', 12,  9, NULL),
 ('HSH_R_0008','Reclutador H', 'PE', DATE '2025-10-15',  8,  6, NULL),
 ('HSH_R_0009','Reclutador I', 'AR', DATE '2025-11-22',  5,  3, NULL),
 ('HSH_R_0010','Reclutador J', 'CL', DATE '2026-01-05',  9,  7, NULL);

-- Candidates ------------------------------------------------------------------
INSERT INTO candidates (candidate_id_hash, candidate_country) VALUES
 ('HSH_C_0001','MX'),('HSH_C_0002','MX'),('HSH_C_0003','MX'),('HSH_C_0004','MX'),
 ('HSH_C_0005','MX'),('HSH_C_0006','CO'),('HSH_C_0007','CO'),('HSH_C_0008','PE'),
 ('HSH_C_0009','AR'),('HSH_C_0010','CL');

-- Classifications -------------------------------------------------------------
INSERT INTO classifications (classification_id, risk_level, explanation_text, classified_at, classifier_version) VALUES
 (1,'safe',       'Oferta verificada con empleador registrado.',               DATE '2026-04-10','ramona-v0.9'),
 (2,'suspicious', 'Uno o dos red flags, empleador no verificable.',            DATE '2026-04-11','ramona-v0.9'),
 (3,'high-risk',  'Tres o mas red flags. Coincide con patrones documentados.', DATE '2026-04-12','ramona-v0.9'),
 (4,'fraudulent', 'Vinculado a caso confirmado en prensa.',                    DATE '2026-04-14','ramona-v0.9');
SELECT setval(pg_get_serial_sequence('classifications','classification_id'), 4);

-- Offers ----------------------------------------------------------------------
-- Mix of fraudulent (vinculados a Edith / Rancho Izaguirre), high-risk, suspicious y safe.

INSERT INTO offers (raw_text, offered_role, offered_location, offered_salary_mxn, posted_at,
                    source_platform, country_code, language_code, recruiter_id, employer_id, classification_id, risk_score) VALUES
-- Caso tipo Edith Guadalupe (abril 2026) --------------------------------------
 ('Solicito empleada domestica, horarios flexibles, buen sueldo, cita en CDMX. Mandame WhatsApp.',
  'empleada domestica', 'Benito Juarez CDMX', 0,
  DATE '2026-04-02', 3, 'MX','es', 1, 3, 4, 0.97),
 ('Vacante niñera, no se pide experiencia, sueldos atractivos. Interesadas acudir solas, sin INE.',
  'niñera', 'CDMX', 0,
  DATE '2026-04-05', 1, 'MX','es', 1, 3, 4, 0.95),
 ('Empleadas para hogar CDMX. Horarios flexibles, ideal madres solteras. Acudir sola a entrevista.',
  'empleada domestica', 'CDMX', 0,
  DATE '2026-04-08', 3, 'MX','es', 1, 3, 3, 0.88),
 ('Se buscan mujeres para trabajo en edificio multiusos, sueldo semanal alto. Cita previa WhatsApp.',
  'no especificado', 'CDMX', 0,
  DATE '2026-04-10', 1, 'MX','es', 1, 3, 3, 0.85),

-- Caso tipo Rancho Izaguirre / CJNG (sueldos 4-12k semanal, seguridad privada) -
 ('Vacante guardia de seguridad privada. Sueldo 8000 semanal. Viajes pagados. Cita en Central Camionera GDL.',
  'guardia de seguridad', 'Guadalajara', 8000,
  DATE '2025-11-20', 5, 'MX','es', 4, 6, 4, 0.99),
 ('Seguridad privada, no se pide experiencia, hospedaje y traslado pagados. Sueldo 10000 semanal.',
  'seguridad privada', 'Zona metropolitana GDL', 10000,
  DATE '2025-12-15', 2, 'MX','es', 4, 6, 4, 0.98),
 ('Guardias, 12000 semanales, pago adelantado. Traslado Teuchitlan. Aceptacion rapida.',
  'guardia', 'Teuchitlan', 12000,
  DATE '2026-01-10', 2, 'MX','es', 4, 6, 4, 0.99),
 ('Urgente guardias de seguridad, sin experiencia. Sueldo 6000 semanal + bono. Cita central camionera.',
  'guardia', 'Jalisco', 6000,
  DATE '2026-02-05', 1, 'MX','es', 4, 6, 3, 0.92),
 ('Seguridad para evento, 4000 semanal, hospedaje pagado, traslado a destino.',
  'seguridad', 'Jalisco', 4000,
  DATE '2026-03-01', 5, 'MX','es', 4, 6, 3, 0.87),

-- High-risk mixto ------------------------------------------------------------
 ('Trabajo facil, sin experiencia, 5000 semanal. Deposita 500 por uniforme al aceptar.',
  'no especificado', 'Estado de Mexico', 5000,
  DATE '2026-02-20', 1, 'MX','es', 2, 4, 3, 0.90),
 ('Oportunidad inmediata. Sueldo alto, horario flexible. Pago por adelantado para tramites.',
  'asistente', 'CDMX', 7000,
  DATE '2026-03-03', 1, 'MX','es', 2, 4, 3, 0.84),
 ('Vacantes en Estados Unidos, no se pide experiencia, visa tramitada por la empresa.',
  'operario', 'Estados Unidos', 9000,
  DATE '2026-03-10', 2, 'MX','es', 2, 4, 3, 0.82),
 ('Urgente choferes, sueldo semanal alto. Envia foto y documentos por WhatsApp para agilizar.',
  'chofer', 'Monterrey', 7500,
  DATE '2026-03-15', 1, 'MX','es', 3, 5, 3, 0.80),
 ('Se solicita personal, sueldo por encima del mercado, aceptacion en 24h. Sin preguntas.',
  'no especificado', 'Guadalajara', 8500,
  DATE '2026-03-20', 2, 'MX','es', 3, 5, 3, 0.86),

-- Suspicious -----------------------------------------------------------------
 ('Trabajo medio tiempo desde casa, 3500 semanal, horario flexible.',
  'home office', 'CDMX', 3500,
  DATE '2026-03-25', 1, 'MX','es', 2, 4, 2, 0.55),
 ('Empleo en otro estado, viajes pagados. Entrevista presencial.',
  'no especificado', 'Veracruz', 4500,
  DATE '2026-04-01', 1, 'MX','es', 2, 4, 2, 0.62),
 ('Se solicita personal joven, sueldo atractivo, entrevista urgente.',
  'no especificado', 'CDMX', 5500,
  DATE '2026-04-03', 1, 'MX','es', 2, 4, 2, 0.58),
 ('Vacante urgente, no se pide experiencia, capacitacion pagada.',
  'operario', 'Puebla', 3800,
  DATE '2026-04-06', 3, 'MX','es', 3, 5, 2, 0.50),

-- Safe / verified ------------------------------------------------------------
 ('Asistente administrativa, horario 9 a 18, empleador con RFC.',
  'asistente administrativa', 'CDMX', 2500,
  DATE '2026-03-18', 6, 'MX','es', 5, 1, 1, 0.10),
 ('Cuidadora de adultos mayores, empresa registrada, 3200 semanal + prestaciones.',
  'cuidadora', 'CDMX', 3200,
  DATE '2026-03-22', 6, 'MX','es', 5, 1, 1, 0.12),
 ('Niñera con experiencia documentada, plataforma verificada.',
  'niñera', 'Monterrey', 3500,
  DATE '2026-03-28', 7, 'MX','es', 6, 7, 1, 0.08),
 ('Auxiliar de cocina restaurante familiar, empleador con RFC.',
  'auxiliar cocina', 'Queretaro', 2800,
  DATE '2026-04-02', 6, 'MX','es', 5, 1, 1, 0.11),

-- Casos Colombia -------------------------------------------------------------
 ('Empleo en Medellin, sueldo alto, no experiencia, viajes pagados a Necocli.',
  'no especificado', 'Medellin', 6000,
  DATE '2026-02-12', 1, 'CO','es', 7, NULL, 4, 0.94),
 ('Vacante urgente CO, sueldo por arriba del mercado, sin requisitos.',
  'no especificado', 'Bogota', 5500,
  DATE '2026-03-05', 2, 'CO','es', 7, NULL, 3, 0.83),
 ('Mesera restaurante Medellin, horario fijo, empleador registrado.',
  'mesera', 'Medellin', 2200,
  DATE '2026-03-15', 6, 'CO','es', 7, NULL, 1, 0.15),
 ('Se solicitan mujeres jovenes, cita individual, sin identificacion oficial.',
  'no especificado', 'Cartagena', 5000,
  DATE '2026-03-20', 1, 'CO','es', 7, NULL, 4, 0.96),

-- Casos Peru -----------------------------------------------------------------
 ('Trabajo en minas Madre de Dios, sueldo alto, traslado pagado.',
  'minero', 'Madre de Dios', 7000,
  DATE '2025-11-10', 1, 'PE','es', 8, NULL, 4, 0.97),
 ('Empleo Lima, horario flexible, sin experiencia.',
  'asistente', 'Lima', 3500,
  DATE '2026-02-25', 2, 'PE','es', 8, NULL, 2, 0.58),
 ('Vacante urgente, sueldo encima de mercado, cita en terminal terrestre.',
  'no especificado', 'Cusco', 4800,
  DATE '2026-03-10', 1, 'PE','es', 8, NULL, 3, 0.88),

-- Casos Argentina ------------------------------------------------------------
 ('Empleada domestica, cita sola, sueldo semanal alto.',
  'empleada domestica', 'Buenos Aires', 6200,
  DATE '2026-02-18', 1, 'AR','es', 9, NULL, 3, 0.81),
 ('Vacante urgente campo, traslado pagado a interior.',
  'trabajador rural', 'Interior', 4000,
  DATE '2026-03-12', 2, 'AR','es', 9, NULL, 4, 0.92),
 ('Mesera Buenos Aires, empleador registrado, horario fijo.',
  'mesera', 'Buenos Aires', 2800,
  DATE '2026-03-28', 6, 'AR','es', 9, NULL, 1, 0.10),

-- Casos Chile ----------------------------------------------------------------
 ('Trabajo agricola Antofagasta, traslado pagado, hospedaje incluido.',
  'trabajador agricola', 'Antofagasta', 5500,
  DATE '2026-01-30', 2, 'CL','es', 10, NULL, 4, 0.93),
 ('Cuidadora Santiago, empleador verificado.',
  'cuidadora', 'Santiago', 3100,
  DATE '2026-03-18', 6, 'CL','es', 10, NULL, 1, 0.14),
 ('Vacantes urgentes norte de Chile, sueldo alto, sin experiencia.',
  'no especificado', 'Antofagasta', 6500,
  DATE '2026-03-25', 1, 'CL','es', 10, NULL, 3, 0.86),

-- Casos cross-country (mismo recruiter en varios paises) --------------------
 ('Se buscan empleadas CDMX, sueldo alto, cita individual. Mismo numero contacta en varios paises.',
  'no especificado', 'CDMX', 7500,
  DATE '2026-03-30', 1, 'MX','es', 7, NULL, 4, 0.99),
 ('Empleo urgente Lima, sueldo arriba de mercado, mismo patron Medellin.',
  'no especificado', 'Lima', 7200,
  DATE '2026-04-01', 1, 'PE','es', 7, NULL, 4, 0.98),

-- TikTok / Messenger pattern --------------------------------------------------
 ('Vi anuncio en TikTok, enviaron por Messenger y movieron a WhatsApp. No dan nombre de empresa.',
  'no especificado', 'CDMX', 5800,
  DATE '2026-04-08', 3, 'MX','es', 2, 4, 4, 0.95),
 ('Oferta llegada por TikTok. Piden datos edad, estado civil, hijos. Sin empresa.',
  'asistente', 'Monterrey', 5400,
  DATE '2026-04-11', 5, 'MX','es', 3, 5, 3, 0.87),

-- Mas ofertas safe para balance ---------------------------------------------
 ('Recepcionista consultorio dental, horario fijo, empleador con RFC.',
  'recepcionista', 'CDMX', 2600,
  DATE '2026-03-10', 7, 'MX','es', 5, 1, 1, 0.09),
 ('Mesero restaurante, cadena registrada.',
  'mesero', 'CDMX', 2400,
  DATE '2026-03-12', 6, 'MX','es', 5, 1, 1, 0.08),
 ('Auxiliar administrativa, convocatoria plataforma verificada.',
  'auxiliar administrativa', 'Guadalajara', 2700,
  DATE '2026-03-19', 6, 'MX','es', 5, 1, 1, 0.07),
 ('Programador junior, contrato por la empresa directamente.',
  'programador', 'Monterrey', 12000,
  DATE '2026-03-22', 7, 'MX','es', 5, 1, 1, 0.05),
 ('Asistente de ventas, tienda con presencia fisica verificada.',
  'asistente ventas', 'Leon', 2900,
  DATE '2026-03-30', 6, 'MX','es', 5, 1, 1, 0.12),

-- Mas high-risk con patrones mixtos -----------------------------------------
 ('Empleada, sueldo 8500 semanal, cita edificio multiusos, acudir sola sin INE.',
  'empleada', 'CDMX', 8500,
  DATE '2026-04-12', 1, 'MX','es', 1, 3, 4, 0.98),
 ('Guardia, pago adelantado de uniforme 800, sueldo 7000 semanal.',
  'guardia', 'Guadalajara', 7000,
  DATE '2026-04-14', 2, 'MX','es', 4, 6, 3, 0.91),
 ('Vacante urgente, sueldo arriba mercado, sin experiencia, viaje al extranjero pagado.',
  'no especificado', 'USA', 10000,
  DATE '2026-04-15', 1, 'MX','es', 3, 5, 4, 0.96);

-- Red flags for each fraudulent / high-risk offer ---------------------------
-- Idx-based: cada oferta lleva sus flags segun el patron.

INSERT INTO red_flags (offer_id, flag_type, flag_confidence, detected_by) VALUES
 -- Offer 1 (Edith-like)
 (1, 'horarios_flexibles',          0.92, 'nlp'),
 (1, 'sueldo_alto',                 0.75, 'rule'),
 -- Offer 2
 (2, 'sin_experiencia',             0.95, 'rule'),
 (2, 'sueldo_alto',                 0.80, 'rule'),
 -- Offer 3
 (3, 'horarios_flexibles',          0.90, 'nlp'),
 (3, 'sin_experiencia',             0.85, 'rule'),
 -- Offer 4
 (4, 'sueldo_alto',                 0.85, 'rule'),
 -- Offer 5 (CJNG-like)
 (5, 'sueldo_alto',                 0.95, 'rule'),
 (5, 'sin_experiencia',             0.90, 'rule'),
 (5, 'entrevista_lejana_traslado',  0.95, 'nlp'),
 -- Offer 6
 (6, 'sin_experiencia',             0.95, 'rule'),
 (6, 'entrevista_lejana_traslado',  0.90, 'nlp'),
 (6, 'sueldo_alto',                 0.95, 'rule'),
 -- Offer 7
 (7, 'sueldo_alto',                 0.99, 'rule'),
 (7, 'pago_adelantado',             0.95, 'rule'),
 (7, 'aceptacion_urgente',          0.90, 'nlp'),
 (7, 'entrevista_lejana_traslado',  0.95, 'nlp'),
 -- Offer 8
 (8, 'sin_experiencia',             0.95, 'rule'),
 (8, 'aceptacion_urgente',          0.90, 'nlp'),
 -- Offer 9
 (9, 'entrevista_lejana_traslado',  0.95, 'nlp'),
 -- Offer 10
 (10,'sin_experiencia',             0.90, 'rule'),
 (10,'sueldo_alto',                 0.80, 'rule'),
 (10,'pago_adelantado',             0.99, 'rule'),
 -- Offer 11
 (11,'sueldo_alto',                 0.85, 'rule'),
 (11,'horarios_flexibles',          0.80, 'nlp'),
 (11,'pago_adelantado',             0.90, 'rule'),
 -- Offer 12
 (12,'sin_experiencia',             0.90, 'rule'),
 (12,'empleo_fuera_estado',         0.99, 'rule'),
 (12,'sueldo_alto',                 0.85, 'rule'),
 -- Offer 13
 (13,'sueldo_alto',                 0.80, 'rule'),
 (13,'aceptacion_urgente',          0.85, 'nlp'),
 -- Offer 14
 (14,'sueldo_alto',                 0.90, 'rule'),
 (14,'aceptacion_urgente',          0.90, 'nlp'),
 -- Offer 15 (suspicious)
 (15,'horarios_flexibles',          0.70, 'nlp'),
 -- Offer 16
 (16,'empleo_fuera_estado',         0.80, 'rule'),
 (16,'entrevista_lejana_traslado',  0.70, 'nlp'),
 -- Offer 17
 (17,'sueldo_alto',                 0.70, 'rule'),
 (17,'aceptacion_urgente',          0.65, 'nlp'),
 -- Offer 18
 (18,'sin_experiencia',             0.80, 'rule'),
 -- Offers 19-22 safe, no flags
 -- Offer 23 (Colombia)
 (23,'empleo_fuera_estado',         0.90, 'rule'),
 (23,'sueldo_alto',                 0.85, 'rule'),
 (23,'sin_experiencia',             0.90, 'rule'),
 (23,'entrevista_lejana_traslado',  0.90, 'nlp'),
 -- Offer 24
 (24,'sueldo_alto',                 0.80, 'rule'),
 (24,'aceptacion_urgente',          0.75, 'nlp'),
 -- Offer 25 safe
 -- Offer 26
 (26,'sin_experiencia',             0.85, 'rule'),
 (26,'sueldo_alto',                 0.80, 'rule'),
 -- Offer 27 (Peru)
 (27,'sueldo_alto',                 0.95, 'rule'),
 (27,'entrevista_lejana_traslado',  0.95, 'nlp'),
 -- Offer 28 suspicious
 (28,'horarios_flexibles',          0.65, 'nlp'),
 (28,'sin_experiencia',             0.70, 'rule'),
 -- Offer 29
 (29,'sueldo_alto',                 0.85, 'rule'),
 (29,'aceptacion_urgente',          0.80, 'nlp'),
 -- Offer 30 (Argentina)
 (30,'sueldo_alto',                 0.80, 'rule'),
 -- Offer 31
 (31,'entrevista_lejana_traslado',  0.90, 'nlp'),
 -- Offer 32 safe
 -- Offer 33 (Chile)
 (33,'entrevista_lejana_traslado',  0.90, 'nlp'),
 (33,'sueldo_alto',                 0.85, 'rule'),
 -- Offer 34 safe
 -- Offer 35
 (35,'sueldo_alto',                 0.85, 'rule'),
 (35,'sin_experiencia',             0.90, 'rule'),
 -- Offer 36 (cross-country MX)
 (36,'sueldo_alto',                 0.95, 'rule'),
 -- Offer 37 (cross-country PE)
 (37,'sueldo_alto',                 0.95, 'rule'),
 -- Offer 38 (TikTok pattern)
 (38,'sueldo_alto',                 0.85, 'rule'),
 (38,'aceptacion_urgente',          0.80, 'nlp'),
 -- Offer 39
 (39,'sueldo_alto',                 0.80, 'rule'),
 -- Offers 40-44 safe
 -- Offer 45
 (45,'sueldo_alto',                 0.90, 'rule'),
 (45,'horarios_flexibles',          0.75, 'nlp'),
 -- Offer 46
 (46,'sueldo_alto',                 0.85, 'rule'),
 (46,'pago_adelantado',             0.95, 'rule'),
 -- Offer 47
 (47,'sueldo_alto',                 0.90, 'rule'),
 (47,'sin_experiencia',             0.90, 'rule'),
 (47,'empleo_fuera_estado',         0.95, 'rule');

-- Offer -> SurvivorTestimonyPattern links -----------------------------------
-- Patron mapping: 1=messenger_to_whatsapp, 2=filtro_datos_personales,
-- 3=solicita_ir_sola, 4=solicita_sin_identificacion, 5=empresa_sin_nombre,
-- 6=sin_logo_whatsapp, 7=sueldos_4k_12k_semanal, 8=cita_central_autobuses,
-- 9=cita_edificio_multiusos, 10=gancho_seguridad_privada,
-- 11=horarios_flexibles_madres_solteras, 12=traslado_pagado

INSERT INTO offer_patterns (offer_id, pattern_id) VALUES
 -- Edith-like
 (1,9),(1,11),
 (2,3),(2,4),(2,9),
 (3,11),(3,3),
 (4,5),(4,6),(4,9),
 -- CJNG-like
 (5,7),(5,8),(5,10),(5,12),
 (6,7),(6,10),(6,12),
 (7,7),(7,8),(7,10),
 (8,8),(8,10),
 (9,10),(9,12),
 -- High-risk mixto
 (10,5),(10,6),
 (11,5),(11,11),
 (12,12),
 (13,1),
 (14,5),
 -- TikTok pattern
 (38,1),(38,2),(38,5),
 (39,1),(39,2),
 -- Cross-country
 (36,3),(36,5),(36,6),
 (37,5),(37,6),
 -- Colombia
 (23,12),
 (26,2),(26,4),
 -- Peru
 (27,8),
 -- Argentina/Chile
 (30,3),
 (31,12),
 (33,12),
 (45,3),(45,4),(45,9),
 (46,7),(46,10),
 (47,12);

-- Offer -> Route links -----------------------------------------------------
INSERT INTO offer_routes (offer_id, route_id) VALUES
 -- Route 1: CDMX Benito Juarez
 (1,1),(2,1),(3,1),(4,1),(45,1),
 -- Route 2: Guadalajara -> Teuchitlan
 (5,2),(6,2),(7,2),(8,2),(9,2),(46,2),
 -- Route 3: MX -> GT
 (12,3),(47,3),
 -- Route 4: Medellin -> Necocli
 (23,4),
 -- Route 5: Peru
 (27,5),
 -- Route 6: AR
 (31,6),
 -- Route 7: CL
 (33,7);

-- Submissions (candidates who asked Ramona to verify these offers) --------
INSERT INTO submissions (candidate_id, offer_id, submitted_at) VALUES
 (1, 1, DATE '2026-04-03'),
 (2, 2, DATE '2026-04-06'),
 (3, 3, DATE '2026-04-09'),
 (4, 5, DATE '2025-11-21'),
 (5, 7, DATE '2026-01-11'),
 (6,23, DATE '2026-02-13'),
 (7,26, DATE '2026-03-21'),
 (8,27, DATE '2025-11-11'),
 (9,30, DATE '2026-02-19'),
 (10,33, DATE '2026-01-31'),
 (1,38, DATE '2026-04-09'),
 (2,45, DATE '2026-04-13'),
 (3,46, DATE '2026-04-15'),
 (4,47, DATE '2026-04-16');
