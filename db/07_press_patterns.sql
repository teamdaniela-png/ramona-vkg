-- Press-derived survivor-testimony patterns
-- Extracted from 1,332 case-relevant articles classified by rules
-- 38 distinct patterns across 5 kinds (classic_a, credible_b, communication, recruitment, exploitation)

SET search_path TO ramona, public;

-- Extend the survivor_patterns table with two optional columns if they
-- do not already exist. Required for v1.3 observatory stats.
ALTER TABLE ramona.survivor_patterns ADD COLUMN IF NOT EXISTS pattern_kind TEXT;
ALTER TABLE ramona.survivor_patterns ADD COLUMN IF NOT EXISTS observed_count INTEGER;
ALTER TABLE ramona.survivor_patterns ADD COLUMN IF NOT EXISTS dominance_bucket TEXT;

INSERT INTO survivor_patterns (pattern_name, pattern_description, pattern_kind, observed_count, dominance_bucket, evidence_source) VALUES
  ('aceptacion_urgente', 'Oferta exige contratación inmediata o presión de decisión rápida.', 'classic_a', 184, 'hot', NULL),
  ('sin_experiencia', 'Oferta anuncia que no se requiere experiencia.', 'classic_a', 6, 'cold', NULL),
  ('pago_adelantado', 'Oferta menciona pago adelantado o bono inicial en efectivo.', 'classic_a', 1, 'cold', NULL),
  ('empleo_fuera_estado', 'Oferta implica mudarse fuera del estado o del país.', 'classic_a', 2, 'cold', NULL),
  ('entrevista_lejana_traslado', 'Oferta pide entrevista fuera de la ciudad con traslado pagado.', 'classic_a', 1, 'cold', NULL),
  ('filtro_datos_personales', 'Se solicitan datos personales sensibles (CURP, INE, estado civil, lazos familiares) antes del contrato.', 'credible_b', 719, 'hot', NULL),
  ('rol_plausible_limpieza_hosteleria', 'Rol ofrecido es plausible (limpieza, mesera, recepción, cocina) pero acompañado de patrones Type B.', 'credible_b', 10, 'cold', NULL),
  ('solicita_sin_identificacion', 'El reclutador pide que la candidata no lleve identificación oficial.', 'credible_b', 3, 'cold', NULL),
  ('cita_edificio_multiusos', 'La cita se programa en un edificio multiusos, bodega, sótano o departamento particular.', 'credible_b', 48, 'warm', NULL),
  ('messenger_to_whatsapp', 'Primer contacto en Facebook Messenger migrado rápidamente a WhatsApp.', 'credible_b', 4, 'cold', NULL),
  ('horario_atipico', 'La cita se programa en horario no laboral: noche, domingo, madrugada.', 'credible_b', 22, 'warm', NULL),
  ('solicita_ir_sola', 'El reclutador insiste en que la candidata acuda sola.', 'credible_b', 2, 'cold', NULL),
  ('comm_telegram', 'Primer contacto o reclutamiento a través de Telegram.', 'communication', 80, 'hot', NULL),
  ('comm_whatsapp', 'Primer contacto o reclutamiento a través de WhatsApp.', 'communication', 247, 'hot', NULL),
  ('comm_sms', 'Contacto inicial por mensaje de texto.', 'communication', 24, 'warm', NULL),
  ('comm_in_person', 'Contacto inicial en persona.', 'communication', 32, 'warm', NULL),
  ('comm_email', 'Contacto inicial por correo electrónico.', 'communication', 66, 'warm', NULL),
  ('comm_voice_call', 'Contacto inicial por llamada telefónica directa.', 'communication', 5, 'cold', NULL),
  ('comm_messenger', 'Primer contacto a través de Facebook Messenger.', 'communication', 13, 'cold', NULL),
  ('recr_social_media', 'Reclutamiento a través de redes sociales (Facebook, Instagram, TikTok, Marketplace).', 'recruitment', 535, 'hot', NULL),
  ('recr_family', 'Reclutamiento a través de un miembro de la familia de la víctima.', 'recruitment', 384, 'hot', NULL),
  ('recr_labour_broker', 'Reclutador tipo enganchador o ''labour broker''.', 'recruitment', 74, 'hot', NULL),
  ('recr_abduction', 'Secuestro directo o reclutamiento forzado sin pretexto laboral.', 'recruitment', 146, 'hot', NULL),
  ('recr_intimate_partner', 'Reclutamiento a través de la pareja sentimental de la víctima.', 'recruitment', 87, 'hot', NULL),
  ('recr_friend', 'Reclutamiento a través de un amigo cercano.', 'recruitment', 121, 'hot', NULL),
  ('recr_false_job_offer', 'Oferta de trabajo falsa anunciada explícitamente (aparece en título o cuerpo del artículo).', 'recruitment', 69, 'hot', NULL),
  ('recr_in_person_street', 'Abordaje en la calle sin intermediación digital.', 'recruitment', 21, 'warm', NULL),
  ('recr_classifieds', 'Oferta publicada en avisos clasificados o sitios tipo Marketplace.', 'recruitment', 51, 'warm', NULL),
  ('exp_labour_construction', 'Explotación laboral en construcción u obra.', 'exploitation', 203, 'hot', NULL),
  ('exp_labour_hospitality', 'Explotación laboral en hospitalidad: meseros, cocina, hotelería.', 'exploitation', 659, 'hot', NULL),
  ('exp_labour_other', 'Explotación laboral de tipo no especificado.', 'exploitation', 243, 'hot', NULL),
  ('exp_sex_prostitution', 'Explotación sexual forzada, prostitución.', 'exploitation', 360, 'hot', NULL),
  ('exp_sex_pornography', 'Explotación sexual en producción de material pornográfico.', 'exploitation', 37, 'warm', NULL),
  ('exp_labour_domestic', 'Explotación en trabajo doméstico, incluyendo niñeras y cuidadoras.', 'exploitation', 14, 'warm', NULL),
  ('exp_forced_criminality', 'Trabajo forzado en estructuras criminales: halcones, sicariato, ''seguridad privada''.', 'exploitation', 59, 'warm', NULL),
  ('exp_labour_agriculture', 'Explotación laboral agrícola, jornaleros, corte de caña u hortalizas.', 'exploitation', 35, 'warm', NULL),
  ('exp_organ_removal', 'Extracción forzada de órganos o pretexto médico como lure.', 'exploitation', 45, 'warm', NULL),
  ('exp_forced_marriage', 'Matrimonio forzado.', 'exploitation', 11, 'cold', NULL)
ON CONFLICT (pattern_name) DO UPDATE SET
  pattern_description = EXCLUDED.pattern_description,
  pattern_kind = EXCLUDED.pattern_kind,
  observed_count = EXCLUDED.observed_count,
  dominance_bucket = EXCLUDED.dominance_bucket;
