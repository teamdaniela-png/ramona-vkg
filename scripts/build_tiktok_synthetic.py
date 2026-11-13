#!/usr/bin/env python3
"""
Lexicon and synthetic data of criminal recruitment on TikTok.

Source of the lexicon: Seminario sobre Violencia y Paz, El Colegio de México (2025),
"Del scroll al 'jale': cómo se recluta en TikTok" (100 videos, 15 March to 31 August 2025).
Each term carries the page and the image of the report it comes from.
tipo = verbatim_colmex    -> text that appears as such in a screenshot or quotation of the report
tipo = variante_sintetica -> a spelling variant or extension written for this dataset, not in the report

Outputs:
  data/lexicon/tiktok_reclutamiento_lexicon.csv
  data/synthetic/tiktok_reclutamiento_sintetico.csv  (schema of data/operational plus extra columns)
  data/synthetic/tiktok_reclutamiento_sintetico.jsonl (format of scripts/classify_llm.py)
  data/synthetic/tiktok_reclutamiento_stats.json

Usage: python3 scripts/build_tiktok_synthetic.py [--seed 2026]
Deterministic: the same seed gives the same dataset.
"""
import argparse
import csv
import json
import random
import re
import unicodedata
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = "Colmex SVP 2025, Del scroll al jale"

# ---------------------------------------------------------------------------
# 1. LEXICO
# (id, termino, patron_regex, categoria, tipo, pagina, elemento)
# Every pattern is anchored on word boundaries.
# ---------------------------------------------------------------------------
LEX = [
    # Oferta / llamado directo (condicion NR del Colmex)
    ("L001", "jale", r"\bjale\b", "oferta_llamado", "verbatim_colmex", "41,49,70", "Imagenes 2, 17, 22; titulo"),
    ("L002", "¿Quieres jale?", r"\bquieres jale\b", "oferta_llamado", "verbatim_colmex", "70", "Imagen 22"),
    ("L003", "todavía hay plazas", r"\btodavia (hay|ahi) plazas?\b", "oferta_llamado", "verbatim_colmex", "70", "Imagen 22 (escrito 'ahi')"),
    ("L004", "plaza", r"\bplazas?\b", "oferta_llamado", "verbatim_colmex", "49", "Texto: 'si hay jale, trabajo, plaza'"),
    ("L005", "no tienes trabajo y estás buscando", r"\bno tienes trabajo\b", "oferta_llamado", "verbatim_colmex", "24", "Imagen 3"),
    ("L006", "estamos buscando personal", r"\bbuscando personal\b", "oferta_llamado", "verbatim_colmex", "24", "Imagen 3"),
    ("L007", "seguimos con el reclutamiento activo", r"\breclutamiento activo\b", "oferta_llamado", "verbatim_colmex", "41", "Imagen 10"),
    ("L008", "sigue reclutando", r"\bsigue(n)? reclutando\b", "oferta_llamado", "verbatim_colmex", "56", "Imagen 19"),
    ("L009", "andamos reclutando", r"\b(andamos|anda) reclutando\b", "oferta_llamado", "verbatim_colmex", "47,57", "Imagenes 15 y 21"),
    ("L010", "no pierdas la oportunidad", r"\bno pierdas la oportunidad\b", "oferta_llamado", "verbatim_colmex", "56", "Imagen 19"),
    ("L011", "trabajo para hombres y mujeres", r"\bhombres y mujeres\b", "oferta_llamado", "verbatim_colmex", "56", "Imagen 19"),
    ("L012", "esta es tu oportunidad para salir adelante", r"\bsalir adelante\b", "oferta_llamado", "verbatim_colmex", "56", "Imagen 19"),
    ("L013", "¿quién se quiere unir?", r"\bse quiere unir\b", "oferta_llamado", "verbatim_colmex", "47", "Imagen 14"),
    ("L014", "kien le entra", r"\b(kien|quien) le entra\b", "oferta_llamado", "verbatim_colmex", "26", "Imagen 4"),
    ("L015", "gente de 🥚🥚 conscientes del trabajo", r"\bcon?sc?ientes del trabajo\b", "oferta_llamado", "verbatim_colmex", "41", "Imagen 10 (escrito 'consientes')"),
    ("L016", "todo México", r"\btodo mexico\b", "oferta_alcance", "verbatim_colmex", "41", "Imagen 10"),
    ("L017", "no rajarse", r"\bno (te )?rajes?\b|\bno se raje\b|\bno rajarse\b", "oferta_llamado", "verbatim_colmex", "30", "Texto sobre NR directo"),
    ("L018", "chamba", r"\bchambas?\b", "oferta_llamado", "verbatim_colmex", "44", "Texto: 'conseguir chamba'"),
    ("L019", "chambear", r"\bchambear\b", "oferta_llamado", "verbatim_colmex", "57", "Imagen 20"),
    ("L020", "seguimos laborando", r"\bseguimos laborando\b", "oferta_llamado", "verbatim_colmex", "45", "Cancion en Imagen 11"),
    ("L021", "únete a la fila", r"\b(unete|une te) a la fila\b", "oferta_llamado", "verbatim_colmex", "57", "Imagen 21 ('une te ala fila')"),
    # Pago
    ("L030", "pagamos 10mil a 15mil pesos semanales", r"\bpagamos \d+ ?mil\b", "pago", "verbatim_colmex", "24", "Imagen 3"),
    ("L031", "pesos semanales / pagos semanales", r"\b(pesos|pagos?) semanal(es)?\b", "pago", "verbatim_colmex", "23,24", "Imagen 3; video del reclutador"),
    ("L032", "vacaciones", r"\bvacaciones\b", "pago", "verbatim_colmex", "23", "Video del reclutador: 'pagos semanales y vacaciones'"),
    ("L033", "feria", r"\bferia\b", "pago", "verbatim_colmex", "51", "Imagen 18"),
    ("L034", "ocupamos dinero", r"\bocupamos dinero\b", "pago", "verbatim_colmex", "23", "Video del reclutador"),
    # Contacto / llamado a privado
    ("L040", "escribe al privado", r"\b(escribe|manda|manden|mandar) (mensaje )?al privado\b", "contacto_privado", "verbatim_colmex", "56,57", "Imagenes 19 y 21"),
    ("L041", "comenta para inf", r"\bcomenta para inf", "contacto_privado", "verbatim_colmex", "56", "Imagen 19"),
    ("L042", "para más info mandar mensaje", r"\b(mandar|manda|manden) mensaje\b", "contacto_privado", "verbatim_colmex", "41,47", "Imagenes 10 y 14"),
    ("L043", "DM", r"\bdm\b", "contacto_privado", "verbatim_colmex", "47", "Imagen 13"),
    # Codigos de grupo (identidad)
    ("L050", "4 letras / 4L", r"\b4 ?l\b|\b4 letras\b|\bcuatro letras\b", "codigo_grupo", "verbatim_colmex", "26,52,56", "Imagenes 4 y 19; cancion 'Doble R'"),
    ("L051", "NG / 🆖", r"\bng\b|🆖", "codigo_grupo", "verbatim_colmex", "24,56,70", "Imagenes 3, 19, 22"),
    ("L052", "los Jaliscos", r"\blos jaliscos\b", "codigo_grupo", "verbatim_colmex", "24", "Imagen 3"),
    ("L053", "la maña", r"\b(la|ala|a la) mana\b", "codigo_grupo", "verbatim_colmex", "44,50,51,52", "Imagenes 11, 18; trend 'arriba la maña'"),
    ("L054", "arriba la maña", r"\barriba la mana\b", "codigo_grupo", "verbatim_colmex", "52", "Trend con 'Doble R'"),
    ("L055", "la mz", r"\bla mz\b", "codigo_grupo", "verbatim_colmex", "22", "Imagen 2 (comentario)"),
    ("L056", "plebada bélica", r"\bplebada\b|\bbelik?c?a\b", "codigo_grupo", "verbatim_colmex", "46", "Imagen 12"),
    ("L057", "monstruas", r"\bmonstruas?\b", "codigo_grupo", "verbatim_colmex", "33", "Texto: autos blindados"),
    ("L058", "🐓 (gallo)", r"🐓", "emoji_grupo", "verbatim_colmex", "70", "Imagen 22"),
    # Emojis
    ("L060", "👹 / 😈 (diablo)", r"👹|😈|👿", "emoji_grupo", "verbatim_colmex", "34,41,49,51,56", "Imagenes 10, 17, 18, 19"),
    ("L061", "🥷 (encapuchado)", r"🥷", "emoji_grupo", "verbatim_colmex", "49,56", "Imagenes 17 y 19"),
    ("L062", "😎", r"😎", "emoji_grupo", "verbatim_colmex", "49", "Imagenes 16 y 17"),
    ("L063", "🫡 (saludo)", r"🫡", "emoji_grupo", "verbatim_colmex", "56", "Imagen 19"),
    ("L064", "💀", r"💀", "emoji_grupo", "verbatim_colmex", "51", "Imagen 18"),
    ("L065", "🥚🥚 (huevos = valor)", r"🥚", "emoji_grupo", "verbatim_colmex", "41", "Imagen 10"),
    ("L066", "🇲🇽", r"🇲🇽", "emoji_grupo", "verbatim_colmex", "24,41", "Imagenes 3 y 10"),
    ("L067", "💵 / 💸 (dinero)", r"💵|💸|💰", "emoji_pago", "verbatim_colmex", "24", "Imagen 3"),
    # Hashtags
    ("L070", "#reclutamiento", r"#reclutamiento\b", "hashtag", "verbatim_colmex", "23,27", "Video del reclutador; ruta de navegacion"),
    # Aspiracion / fatalismo (condicion AVC)
    ("L080", "disfruto mi vida quizás mañana ya no esté", r"\bmanana ya no\b", "aspiracion_fatalismo", "verbatim_colmex", "48,49", "Imagen 16"),
    ("L081", "al único círculo social que me interesa pertenecer", r"\bcirculo social\b", "aspiracion_fatalismo", "verbatim_colmex", "32", "Imagen 6"),
    ("L082", "de aquí ya no sales", r"\bde aqui ya no sales\b", "aspiracion_fatalismo", "verbatim_colmex", "51", "Imagen 18"),
    ("L083", "qué harías por tu mamá", r"\bque harias por tu (mama|jefita)\b", "aspiracion_familia", "verbatim_colmex", "51", "Texto sobre Imagen 18"),
    ("L084", "sacar a mi jefita adelante", r"\bjefita\b", "aspiracion_familia", "verbatim_colmex", "51", "Imagen 18"),
    ("L085", "entramos aquí para nuestras familias", r"\b(nuestras|tu|tus) familias?\b", "aspiracion_familia", "verbatim_colmex", "23", "Video del reclutador"),
    ("L086", "bienvenido cuando quieras", r"\bbienvenido cuando quieras\b", "respuesta_reclutador", "verbatim_colmex", "51", "Imagen 18"),
    ("L087", "le pedí chamba a la maña", r"\bpedi chamba\b", "aspiracion_fatalismo", "verbatim_colmex", "44", "Imagen 11"),
    ("L088", "mi compa me pide que le consiga jale", r"\bconsig(a|ua) jale\b", "aspiracion_fatalismo", "verbatim_colmex", "48,49", "Imagen 17"),
    # Autopostulacion de la audiencia (comentarios)
    ("L090", "yo quiero trabajar para", r"\b(yo )?(quiero|kiero) trabajar\b", "autopostulacion", "verbatim_colmex", "22,70", "Imagenes 2 y 22"),
    ("L091", "busco jale", r"\bbusco jale\b", "autopostulacion", "verbatim_colmex", "22", "Imagen 2"),
    ("L092", "mujeres también entran", r"\bmujeres tambien entran\b", "autopostulacion", "verbatim_colmex", "26", "Imagen 4"),
    ("L093", "cómo se le hace para entrar", r"\bpara entra(r)?\b", "autopostulacion", "verbatim_colmex", "26", "Imagen 4"),
    ("L094", "qué se ocupa para entrar", r"\bque se ocupa\b", "autopostulacion", "verbatim_colmex", "26", "Imagen 4"),
    ("L095", "quiero entrar / le quiero entrar", r"\b(quiero|kiero) entrar\b|\ble quiero entrar\b", "autopostulacion", "verbatim_colmex", "47,57", "Imagenes 15 y 20"),
    ("L096", "fui antiguo ex militar", r"\bex ?militar\b", "autopostulacion", "verbatim_colmex", "57", "Imagen 20"),
    ("L097", "¿alguien anda reclutando? soy de ...", r"\bsoy de\b", "autopostulacion", "verbatim_colmex", "47", "Imagen 15 (Nogales)"),
    ("L098", "puedo entrar con 16", r"\bentrar con 1[0-7]\b|\btengo 1[0-7]\b", "menciona_menor", "verbatim_colmex", "70", "Imagen 22"),
    ("L099", "a la orden, qué hay que hacer para merecer", r"\ba la orden\b|\bala orden\b", "autopostulacion", "verbatim_colmex", "70", "Imagen 22"),
    ("L100", "jalo, ¿vienen por uno o a dónde hay que ir?", r"\bjalo\b|\bvienen por uno\b", "autopostulacion", "verbatim_colmex", "70", "Imagen 22"),
    ("L101", "si me puedo meter a la maña", r"\bmeter a ?la mana\b", "autopostulacion", "verbatim_colmex", "51", "Imagen 18"),
    ("L102", "puedo", r"^puedo\W*$", "autopostulacion", "verbatim_colmex", "47", "Imagen 14"),
    ("L103", "is this a job offer?", r"\bjob offer\b", "autopostulacion", "verbatim_colmex", "47", "Imagen 13"),
    # Variantes nuestras (NO verbatim): ortografia y extensiones plausibles
    ("V001", "jalar / jalas", r"\bjala(r|s)?\b", "oferta_llamado", "variante_sintetica", "", "Forma verbal de 'jale' (Colmex p.44 cita 'jalar')"),
    ("V002", "se ocupa gente", r"\bse ocupa gente\b", "oferta_llamado", "variante_sintetica", "", "Regionalismo 'ocupar' = necesitar"),
    ("V003", "no se ocupa experiencia", r"\bno se ocupa experiencia\b|\bsin experiencia\b", "oferta_requisito", "variante_sintetica", "", "Mapea a type_a_flags.sin_experiencia"),
    ("V004", "de todos los estados", r"\btodos los estados\b", "oferta_alcance", "variante_sintetica", "", "Variante de 'todo Mexico'"),
    ("V005", "info / inf", r"\binfo?\b", "contacto_privado", "variante_sintetica", "", "Abreviatura"),
    ("V006", "#parati / #fyp", r"#parati\b|#fyp\b|#foryou\b", "hashtag", "variante_sintetica", "", "Hashtags genericos de alcance en TikTok"),
    ("V007", "#jale / #chamba", r"#jale\b|#chamba\b", "hashtag", "variante_sintetica", "", "Hashtag derivado del lexico"),
    ("V008", "raza / plebes", r"\braza\b|\bplebes?\b", "codigo_grupo", "variante_sintetica", "", "'Raza' aparece en Imagen 21"),
]

# ---------------------------------------------------------------------------
# 2. POOLS PARA PLANTILLAS
# ---------------------------------------------------------------------------
EMO_GRUPO = ["👹", "😈", "🥷", "😎", "🫡", "💀", "🐓", "🆖", "🇲🇽", "🥚🥚", "🔥"]
EMO_PAGO = ["💵", "💸", "💰", "🙌"]
CIUDADES = [  # mencionadas en el informe + vecinas de los estados del estudio Satyarthi
    ("Nuevo Laredo", "Tamaulipas"), ("Nogales", "Sonora"), ("Tijuana", "Baja California"),
    ("Zacatecas", "Zacatecas"), ("Guadalajara", "Jalisco"), ("Zapopan", "Jalisco"),
    ("Tlaquepaque", "Jalisco"), ("León", "Guanajuato"), ("Celaya", "Guanajuato"),
    ("Irapuato", "Guanajuato"), ("Uruapan", "Michoacán"), ("Morelia", "Michoacán"),
    ("Apatzingán", "Michoacán"), ("Puebla", "Puebla"), ("Ciudad de México", "CDMX"),
    ("Ecatepec", "Estado de México"), ("Toluca", "Estado de México"), ("Culiacán", "Sinaloa"),
]
GRUPO_CODE = ["las 4L", "los de las 4 letras", "la empresa", "la compañía", "la maña", "la mz", "los del 🐓", "🆖"]
VISUAL_ECC = [
    "camioneta pick-up en la sierra", "convoy de camionetas en terracería", "monstrua (vehículo blindado artesanal)",
    "hombre con chaleco táctico y casco de espaldas en una camioneta", "atardecer con razer y luces LED",
    "tablero de auto de noche", "moto en camino de terracería", "grupo encapuchado junto a camionetas",
    "cráneo con boina militar (ilustración)", "avioneta en construcción improvisada",
]
AUDIO = [
    ("corrido bélico (sin título visible)", "a"), ("trap bélico", "a"), ("Operativa bélica", "a"),
    ("Seguimos laborando - Grupo 360", "a"), ("Que empiece el juego - Chicho Castro y Sus Alia2", "a"),
    ("El Doble R", "a"), ("Ratón y queso - Alberto Ramón", "a"), ("audio de radio de comunicación", "a"),
    ("audio de disparos con risas de fondo", "a"),
]

# Reclutamiento directo (NR). Plantillas compuestas por bloques.
OPENERS = [
    "¿Quieres jale?", "¿Quieres jale? Todavía hay plazas!!!", "No tienes trabajo y estás buscando 🤷",
    "¿Buscas chamba?", "Seguimos con el reclutamiento activo", "{grupo} sigue reclutando, no pierdas la oportunidad",
    "Andamos reclutando raza", "¿Quién se quiere unir?", "Kien le entra con {grupo}", "Todavía hay plazas!!!",
    "Se ocupa gente", "Hay jale para los que no se rajan", "¿Quién jala?", "Se les apareció la plebada belika, seguimos reclutando",
]
BODIES = [
    "estamos buscando personal", "trabajo para hombres y mujeres 🙋‍♀️🙋‍♂️", "gente de 🥚🥚 conscientes del trabajo",
    "no se ocupa experiencia", "se ocupa gente que no se raje", "todo México 🇲🇽", "aceptamos de todos los estados",
    "los Jaliscos estamos buscando personal 🆖🇲🇽", "puro jale serio",
]
PAGOS = [
    ("pagamos {a}mil a {b}mil pesos semanales {m}", "range"), ("pagos semanales y vacaciones", None),
    ("pago semanal de ${n}", "single"), ("buena feria cada semana {m}", None), ("", None), ("", None),
]
CTAS = [
    "escribe al privado o comenta para inf", "para más info mandar mensaje", "manda DM",
    "manden mensaje al privado y únete a la fila", "comenta info y te escribimos", "manda mensaje",
]
CLOSERS = [
    "esta es tu oportunidad para salir adelante 🫡", "es por tu familia", "aquí sí hay futuro", "",
    "", "el que no se arriesga no gana 😎", "aquí entramos por nuestras familias, ocupamos dinero",
]
HASHTAGS_REC = ["#reclutamiento", "#jale", "#chamba", "#trabajo", "#parati", "#fyp"]

# AVC: aspiracion belica sin oferta explicita (relato 'belicos': ECC*A*AVC)
ASPIRACION = [
    "Disfruto mi vida quizás mañana ya no esté ✌️😎",
    "Al único círculo social que me interesa pertenecer (en proceso)",
    "Mi compa me pide que le consiga jale donde trabajo. Yo en corto: 😎🥷👹",
    "Mi vida es tan privada que nadie sabe que le pedí chamba a la maña",
    "Qué harías por tu mamá",
    "Arriba la maña 🫡",
    "Por mi jefita lo que sea 💀",
    "Vivir rápido, morir joven 👹",
    "Yo ya escogí mi camino 🥷",
    "Cuatro letras y una sola palabra 🫡",
]

# Comentarios de autopostulacion (la audiencia pide entrar)
AUTOPOST = [
    "yo quiero trabajar para {grupo}", "busco jale {estado_corto}", "mujeres también entran??",
    "cómo se le hace para entrar o q", "que se ocupa para entrar", "quiero entrar a chambear con ustedes fui ex militar estoy en {ciudad} me ayudan",
    "quiero contactos le quiero entrar", "alguien anda reclutando? soy de {ciudad}", "yo kiero trabajar bro",
    "k rollo mi apa puedo entrar con {edad} o k", "ala orden que hay que hacer para merecer", "jalo vienen por uno o a dónde hay q ir",
    "Puedo", "si me puedo meter ala maña o q 👹", "hay jale? soy de {ciudad}", "pásenme el contacto le quiero entrar",
    "tengo {edad} pero le entro a lo que sea", "aún hay plazas? soy de {estado_corto}", "Is this a job offer?",
]
RESP_RECLUTADOR = ["si", "manda mensaje", "DM", "Que rollo mijo, si eres bienvenido cuando quieras 👹👹",
                   "Solo recuerda que de aquí ya no sales 😢👹💀", "al privado", "si hay, escribe"]

# Cultura sin reclutamiento: corridos / fans (falso positivo tipico de un detector por palabras)
CULTURA = [
    "Corridos para el camino 🔥", "Esta rola pega bien duro 🔥🔥", "Concierto de anoche, qué ambiente 🎶",
    "Plebes de {ciudad} presentes 🇲🇽", "La troca quedó al cien 😎", "Viernes de corridos con la raza",
    "Nuevo video de la banda, apoyen 🙌", "Bélico pero con sentimiento 🎶",
]
HASH_CULT = ["#corridos", "#corridostumbados", "#musica", "#parati", "#fyp", "#regional"]

# Controles legitimos: ofertas reales con el mismo slang (jale, chamba, plaza, pago semanal, al privado)
LEGIT = [
    ("Hay jale en obra en {ciudad}. Se buscan ayudantes de albañil, pago semanal de ${n}, entrada 8am. Traer INE y comprobante. Info al privado", "Ayudante de albañil", (2400, 3200), "semanal"),
    ("Plaza disponible de cajero(a) en tienda de conveniencia en {ciudad}. Sueldo ${n} mensual más prestaciones de ley. Mayor de 18, bachillerato", "Cajero", (8500, 11000), "mensual"),
    ("Chamba de repartidor en moto propia en {ciudad}, pago por entrega más propinas, horario flexible. Manda mensaje con tu solicitud", "Repartidor", (2200, 3500), "semanal"),
    ("Seguimos contratando operadores de producción en {ciudad}. Turno fijo, transporte de personal, IMSS desde el primer día. Sueldo ${n} semanal", "Operador de producción", (2300, 2900), "semanal"),
    ("¿Buscas trabajo? Vacante de mesero(a) fines de semana en {ciudad}, ${n} semanal más propinas. Presentarse con solicitud elaborada", "Mesero", (1200, 1800), "semanal"),
    ("Se ocupa gente para cosecha de aguacate en {ciudad}, pago semanal de ${n}, transporte desde la plaza principal. Contrato y alta en IMSS", "Jornalero", (2000, 2800), "semanal"),
    ("Jale de guardia de seguridad intramuros en plaza comercial de {ciudad}. Empresa con permiso de la SSPC, ${n} quincenal, curso de capacitación pagado", "Guardia de seguridad", (4800, 6200), "quincenal"),
    ("Vacante: auxiliar de almacén en {ciudad}. ${n} mensual, prestaciones superiores, examen médico. Envía CV por mensaje al privado", "Auxiliar de almacén", (9500, 12500), "mensual"),
]

COLMEX_PAGE_FOR = {
    "reclutamiento_directo": "p.24 Img3; p.41 Img10; p.56 Img19; p.70 Img22",
    "aspiracion_belica": "p.32 Img6; p.49 Img16-17; p.51 Img18",
    "autopostulacion": "p.22 Img2; p.26 Img4; p.47 Img13-15; p.57 Img20; p.70 Img22",
    "respuesta_reclutador": "p.26 Img4; p.47 Img13-14; p.51 Img18",
    "cultura_sin_reclutamiento": "control propio (corridos sin NR ni AVC)",
    "legitima_control": "control propio (oferta legitima con mismo slang)",
}

# ---------------------------------------------------------------------------
OP_COLS = [
    "offer_id", "offer_text", "offer_screenshot_url", "source_platform", "channel_type", "job_title",
    "promised_salary_amount", "promised_salary_currency", "promised_salary_period", "schedule", "requirements",
    "declared_location", "offer_language", "first_contact_at", "ramona_verdict", "risk_level", "risk_axis",
    "classifier_confidence", "human_reviewed", "human_label", "type_a_flags", "type_b_flags", "outcome_known",
    "outcome", "candidate_age_range", "candidate_gender", "candidate_state", "report_date", "notes",
]
EXTRA_COLS = [
    "synthetic", "content_type", "label", "relato_colmex", "colmex_conditions", "ratro_scheme",
    "crim_flags", "hashtags", "audio_hint", "visual_hint", "lexicon_term_ids", "template_source",
]


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn" or c in "⃣")


LEX_RE = [(t[0], re.compile(t[2], re.IGNORECASE)) for t in LEX]


def lexicon_hits(text):
    n = norm(text)
    return [lid for lid, rx in LEX_RE if rx.search(n) or rx.search(text)]


def crim_flags(text, label, amount, period):
    n = norm(text)
    f = []
    if re.search(r"privado|\bdm\b|mandar? mensaje|manden mensaje|comenta (para )?inf", n):
        f.append("llamado_privado")
    if re.search(r"4 ?l\b|4 letras|cuatro letras|\bng\b|🆖|jaliscos|la mana|ala mana|la mz|🐓", n + text):
        f.append("codigo_grupo")
    if re.search(r"[👹😈🥷💀🫡]", text):
        f.append("emoji_grupo")
    if amount and period == "semanal" and amount >= 8000:
        f.append("pago_semanal_alto")
    if re.search(r"familia|jefita|mama", n):
        f.append("apela_familia")
    if re.search(r"entrar con 1[0-7]|tengo 1[0-7]", n):
        f.append("menciona_edad_menor")
    if re.search(r"mujeres", n) and label != "legitima_control":
        f.append("invita_mujeres")
    if re.search(r"todo mexico|todos los estados", n):
        f.append("alcance_nacional")
    if re.search(r"#reclutamiento", n):
        f.append("hashtag_reclutamiento")
    if re.search(r"manana ya no|ya no sales|morir joven", n):
        f.append("fatalismo")
    return f


def type_a(text, amount, period, label):
    if label not in ("reclutamiento_directo", "legitima_control"):
        return []
    n = norm(text)
    f = []
    if amount and ((period == "semanal" and amount >= 8000) or (period == "mensual" and amount >= 30000)):
        f.append("sueldo_alto")
    if re.search(r"sin experiencia|no se ocupa experiencia", n):
        f.append("sin_experiencia")
    if re.search(r"todavia (hay|ahi) plazas|no pierdas la oportunidad", n):
        f.append("contratacion_urgente")
    if re.search(r"todo mexico|todos los estados", n):
        f.append("empleo_fuera_estado")
    if re.search(r"horario flexible", n):
        f.append("horario_flexible")
    return f


def clean(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([,.!?])", r"\1", s)
    return s.strip(" ,")


def build(seed):
    rnd = random.Random(seed)
    t0 = datetime(2025, 3, 15)
    span = (datetime(2026, 10, 31) - t0).days
    rows = []

    def when():
        d = t0 + timedelta(days=rnd.randrange(span), minutes=rnd.randrange(1440))
        return d.strftime("%Y-%m-%dT%H:%M:00"), d.strftime("%Y-%m-%d")

    def city():
        return rnd.choice(CIUDADES)

    def add(label, content_type, text, relato="", conds="", scheme="", hashtags="", audio="", visual="",
            job="", amount=None, period="", loc="", verdict="", risk="", axis="", req=""):
        ts, d = when()
        text = clean(text)
        cf = crim_flags(text + " " + hashtags, label, amount, period)
        if scheme == ":ForcedCriminalityScheme" and "menciona_edad_menor" in cf:
            scheme = ":ChildRecruitmentCriminalScheme"
        r = {c: "" for c in OP_COLS + EXTRA_COLS}
        r.update({
            "offer_text": text, "source_platform": "tiktok", "channel_type": "red_social", "job_title": job,
            "promised_salary_amount": amount or "", "promised_salary_currency": "MXN" if amount else "",
            "promised_salary_period": period, "requirements": req, "declared_location": loc, "offer_language": "es",
            "first_contact_at": ts, "report_date": d, "ramona_verdict": verdict, "risk_level": risk, "risk_axis": axis,
            "human_reviewed": "false", "type_a_flags": ";".join(type_a(text, amount, period, label)),
            "outcome_known": "false", "notes": "SINTETICO. Plantilla basada en Colmex 2025: " + COLMEX_PAGE_FOR[label],
            "synthetic": "true", "content_type": content_type, "label": label, "relato_colmex": relato,
            "colmex_conditions": conds, "ratro_scheme": scheme, "crim_flags": ";".join(cf), "hashtags": hashtags,
            "audio_hint": audio, "visual_hint": visual,
            "lexicon_term_ids": ";".join(lexicon_hits(text + " " + hashtags + " " + audio)),
            "template_source": "colmex_lexicon" if label not in ("legitima_control", "cultura_sin_reclutamiento") else "control",
        })
        rows.append(r)

    # 600 reclutamiento directo: relato 'enrolarse' (NR*ECC) o 'conexion emocional' (NR*A)
    for _ in range(600):
        grupo = rnd.choice(GRUPO_CODE)
        parts = [rnd.choice(OPENERS).format(grupo=grupo), rnd.choice(BODIES)]
        tpl, kind = rnd.choice(PAGOS)
        amount, period = None, ""
        if kind == "range":
            a = rnd.choice([8, 10, 12, 15]); b = a + rnd.choice([3, 5, 8])
            parts.append(tpl.format(a=a, b=b, m=rnd.choice(EMO_PAGO))); amount, period = a * 1000, "semanal"
        elif kind == "single":
            amount = rnd.choice([8000, 9000, 10000, 12000, 15000, 18000, 20000]); period = "semanal"
            parts.append(tpl.format(n=f"{amount:,}"))
        elif tpl:
            parts.append(tpl.format(m=rnd.choice(EMO_PAGO))); period = "semanal"
        parts.append(rnd.choice(CTAS)); parts.append(rnd.choice(CLOSERS))
        parts.append("".join(rnd.sample(EMO_GRUPO, rnd.randint(1, 3))))
        sep = rnd.choice([", ", ". ", " "])
        text = sep.join(p for p in parts if p)
        if rnd.random() < 0.5:
            relato, conds = "enrolarse_en_lo_criminal", "nr;ecc"
            visual, audio = rnd.choice(VISUAL_ECC), (rnd.choice(AUDIO)[0] if rnd.random() < 0.3 else "")
            if audio:
                conds += ";a"
        else:
            relato, conds = "conexion_emocional", "nr;a"
            visual, audio = (rnd.choice(VISUAL_ECC) if rnd.random() < 0.4 else ""), rnd.choice(AUDIO)[0]
            if visual:
                conds += ";ecc"
        c = city() if rnd.random() < 0.35 else None
        if c:
            text += f" {rnd.choice(['zona', 'jale en', 'plaza'])} {c[0]}"
        tags = " ".join(rnd.sample(HASHTAGS_REC, rnd.randint(0, 3)))
        add("reclutamiento_directo", rnd.choice(["texto_sobre_video", "descripcion"]), text, relato, conds,
            ":ForcedCriminalityScheme", tags, audio, visual, "no declarado", amount, period,
            f"{c[0]}, {c[1]}" if c else ("todo México" if "todo México" in text else ""), "sospechosa", "critico",
            "trata;explotacion", "sin experiencia" if "experiencia" in text else "")

    # 150 aspiracion belica (ECC*A*AVC, sin NR)
    for _ in range(150):
        text = rnd.choice(ASPIRACION)
        if rnd.random() < 0.4:
            text += " " + "".join(rnd.sample(EMO_GRUPO, 2))
        add("aspiracion_belica", "texto_sobre_video", text, "belicos", "ecc;a;avc", ":ForcedCriminalityScheme",
            " ".join(rnd.sample(HASH_CULT + ["#belico"], rnd.randint(0, 2))), rnd.choice(AUDIO)[0],
            rnd.choice(VISUAL_ECC), verdict="no_concluyente", risk="alto", axis="trata")

    # 250 autopostulacion (comentarios de la audiencia)
    for _ in range(250):
        c = city()
        edad = rnd.choice([15, 16, 17, 18, 19, 20, 22])
        text = rnd.choice(AUTOPOST).format(grupo=rnd.choice(GRUPO_CODE), ciudad=c[0], estado_corto=c[1].split()[0].lower(), edad=edad)
        add("autopostulacion", "comentario", text, "", "", ":ForcedCriminalityScheme", loc=f"{c[0]}, {c[1]}" if c[0] in text else "",
            verdict="no_concluyente", risk="alto", axis="trata")

    # 50 respuestas del reclutador en comentarios
    for _ in range(50):
        add("respuesta_reclutador", "comentario", rnd.choice(RESP_RECLUTADOR), "", "nr", ":ForcedCriminalityScheme",
            verdict="sospechosa", risk="critico", axis="trata")

    # 150 cultura sin reclutamiento (control negativo dificil)
    for _ in range(150):
        c = city()
        text = rnd.choice(CULTURA).format(ciudad=c[0])
        add("cultura_sin_reclutamiento", "descripcion", text, "", "a" if rnd.random() < 0.8 else "",
            hashtags=" ".join(rnd.sample(HASH_CULT, rnd.randint(1, 3))), audio=rnd.choice(AUDIO[:3])[0],
            visual=rnd.choice(["concierto", "troca en carretera", "fiesta familiar", "bocina en patio"]),
            verdict="legitima", risk="bajo", axis="")

    # 300 controles legitimos con el mismo slang
    for _ in range(300):
        tpl, job, (lo, hi), period = rnd.choice(LEGIT)
        c = rnd.choice([x for x in CIUDADES if x[1] in ("Michoacán", "Jalisco")]) if "aguacate" in tpl else city()
        amount = rnd.randrange(lo, hi + 1, 50)
        text = tpl.format(ciudad=c[0], n=f"{amount:,}")
        add("legitima_control", "descripcion", text, job=job, amount=amount, period=period, loc=f"{c[0]}, {c[1]}",
            hashtags=" ".join(rnd.sample(["#empleo", "#vacante", "#trabajo", "#chamba", "#jale", "#parati"], rnd.randint(0, 2))),
            verdict="legitima", risk="bajo", req="INE" if "INE" in text else "")

    rnd.shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["offer_id"] = f"SYN-TT-{i:04d}"
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    lexdir, syndir = ROOT / "data/lexicon", ROOT / "data/synthetic"
    lexdir.mkdir(parents=True, exist_ok=True); syndir.mkdir(parents=True, exist_ok=True)

    with open(lexdir / "tiktok_reclutamiento_lexicon.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["term_id", "termino", "patron_regex", "categoria", "tipo", "fuente", "pagina", "elemento"])
        for t in LEX:
            w.writerow([t[0], t[1], t[2], t[3], t[4], SRC if t[4] == "verbatim_colmex" else "", t[5], t[6]])

    rows = build(args.seed)
    with open(syndir / "tiktok_reclutamiento_sintetico.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OP_COLS + EXTRA_COLS)
        w.writeheader(); w.writerows(rows)
    with open(syndir / "tiktok_reclutamiento_sintetico.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"id": r["offer_id"], "title": r["job_title"], "text": r["offer_text"],
                                "source_platform": "tiktok", "label": r["label"], "synthetic": True,
                                "first_contact_at": r["first_contact_at"]}, ensure_ascii=False) + "\n")

    hits = Counter(l for r in rows for l in r["lexicon_term_ids"].split(";") if l)
    stats = {
        "seed": args.seed, "n_rows": len(rows), "n_lexicon_terms": len(LEX),
        "n_lexicon_verbatim": sum(1 for t in LEX if t[4] == "verbatim_colmex"),
        "by_label": Counter(r["label"] for r in rows), "by_relato": Counter(r["relato_colmex"] or "-" for r in rows),
        "by_scheme": Counter(r["ratro_scheme"] or "-" for r in rows),
        "crim_flags": Counter(f for r in rows for f in r["crim_flags"].split(";") if f),
        "lexicon_terms_never_hit": sorted(t[0] for t in LEX if hits[t[0]] == 0),
        "legit_with_lexicon_hit_pct": round(100 * sum(1 for r in rows if r["label"] == "legitima_control" and r["lexicon_term_ids"]) /
                                            max(1, sum(1 for r in rows if r["label"] == "legitima_control")), 1),
    }
    (syndir / "tiktok_reclutamiento_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
