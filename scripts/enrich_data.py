#!/usr/bin/env python3
"""
Enrich the Ramona VKG demo with additional structured data derived from:
  - CTDC CSV: every unique citizenship and country_of_exploitation (ISO3)
  - press_cases.jsonl: grouped by FraudScheme, select 5 representative examples

Outputs:
  db/08_enriched_countries.sql  — all ISO3 countries observed in CTDC
  db/09_fraudscheme_examples.sql — per-scheme press article examples
  db/10_deep_patterns.sql       — additional patterns from deeper regex
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/danielacamberos/Downloads/ramona_vkg_demo")
CTDC = Path("/Users/danielacamberos/Downloads/CTDC_global_synthetic_data_v2025.csv")

# ISO3 -> (Spanish name, English name)
ISO3_NAMES = {
    "AFG": ("Afganistán", "Afghanistan"), "ALB": ("Albania", "Albania"),
    "DZA": ("Argelia", "Algeria"), "ARG": ("Argentina", "Argentina"),
    "ARM": ("Armenia", "Armenia"), "AUS": ("Australia", "Australia"),
    "AUT": ("Austria", "Austria"), "AZE": ("Azerbaiyán", "Azerbaijan"),
    "BHS": ("Bahamas", "Bahamas"), "BHR": ("Baréin", "Bahrain"),
    "BGD": ("Bangladesh", "Bangladesh"), "BRB": ("Barbados", "Barbados"),
    "BLR": ("Bielorrusia", "Belarus"), "BEL": ("Bélgica", "Belgium"),
    "BLZ": ("Belice", "Belize"), "BEN": ("Benín", "Benin"),
    "BTN": ("Bután", "Bhutan"), "BOL": ("Bolivia", "Bolivia"),
    "BIH": ("Bosnia y Herzegovina", "Bosnia and Herzegovina"),
    "BWA": ("Botsuana", "Botswana"), "BRA": ("Brasil", "Brazil"),
    "BRN": ("Brunéi", "Brunei"), "BGR": ("Bulgaria", "Bulgaria"),
    "BFA": ("Burkina Faso", "Burkina Faso"), "BDI": ("Burundi", "Burundi"),
    "KHM": ("Camboya", "Cambodia"), "CMR": ("Camerún", "Cameroon"),
    "CAN": ("Canadá", "Canada"), "CPV": ("Cabo Verde", "Cape Verde"),
    "CAF": ("República Centroafricana", "Central African Republic"),
    "TCD": ("Chad", "Chad"), "CHL": ("Chile", "Chile"),
    "CHN": ("China", "China"), "COL": ("Colombia", "Colombia"),
    "COM": ("Comoras", "Comoros"), "COG": ("Congo", "Congo"),
    "COD": ("RD del Congo", "DR Congo"),
    "CRI": ("Costa Rica", "Costa Rica"), "CIV": ("Costa de Marfil", "Côte d'Ivoire"),
    "HRV": ("Croacia", "Croatia"), "CUB": ("Cuba", "Cuba"),
    "CYP": ("Chipre", "Cyprus"), "CZE": ("Chequia", "Czechia"),
    "DNK": ("Dinamarca", "Denmark"), "DJI": ("Yibuti", "Djibouti"),
    "DOM": ("República Dominicana", "Dominican Republic"),
    "ECU": ("Ecuador", "Ecuador"), "EGY": ("Egipto", "Egypt"),
    "SLV": ("El Salvador", "El Salvador"),
    "GNQ": ("Guinea Ecuatorial", "Equatorial Guinea"),
    "ERI": ("Eritrea", "Eritrea"), "EST": ("Estonia", "Estonia"),
    "SWZ": ("Esuatini", "Eswatini"), "ETH": ("Etiopía", "Ethiopia"),
    "FJI": ("Fiyi", "Fiji"), "FIN": ("Finlandia", "Finland"),
    "FRA": ("Francia", "France"), "GAB": ("Gabón", "Gabon"),
    "GMB": ("Gambia", "Gambia"), "GEO": ("Georgia", "Georgia"),
    "DEU": ("Alemania", "Germany"), "GHA": ("Ghana", "Ghana"),
    "GRC": ("Grecia", "Greece"), "GTM": ("Guatemala", "Guatemala"),
    "GIN": ("Guinea", "Guinea"), "GNB": ("Guinea-Bisáu", "Guinea-Bissau"),
    "GUY": ("Guyana", "Guyana"), "HTI": ("Haití", "Haiti"),
    "HND": ("Honduras", "Honduras"), "HUN": ("Hungría", "Hungary"),
    "ISL": ("Islandia", "Iceland"), "IND": ("India", "India"),
    "IDN": ("Indonesia", "Indonesia"),
    "IRN": ("Irán", "Iran"), "IRQ": ("Irak", "Iraq"),
    "IRL": ("Irlanda", "Ireland"), "ISR": ("Israel", "Israel"),
    "ITA": ("Italia", "Italy"), "JAM": ("Jamaica", "Jamaica"),
    "JPN": ("Japón", "Japan"), "JOR": ("Jordania", "Jordan"),
    "KAZ": ("Kazajistán", "Kazakhstan"), "KEN": ("Kenia", "Kenya"),
    "KWT": ("Kuwait", "Kuwait"), "KGZ": ("Kirguistán", "Kyrgyzstan"),
    "LAO": ("Laos", "Laos"), "LVA": ("Letonia", "Latvia"),
    "LBN": ("Líbano", "Lebanon"), "LSO": ("Lesoto", "Lesotho"),
    "LBR": ("Liberia", "Liberia"), "LBY": ("Libia", "Libya"),
    "LTU": ("Lituania", "Lithuania"), "LUX": ("Luxemburgo", "Luxembourg"),
    "MDG": ("Madagascar", "Madagascar"), "MWI": ("Malaui", "Malawi"),
    "MYS": ("Malasia", "Malaysia"), "MDV": ("Maldivas", "Maldives"),
    "MLI": ("Malí", "Mali"), "MLT": ("Malta", "Malta"),
    "MRT": ("Mauritania", "Mauritania"), "MUS": ("Mauricio", "Mauritius"),
    "MEX": ("México", "Mexico"), "MDA": ("Moldavia", "Moldova"),
    "MNG": ("Mongolia", "Mongolia"), "MNE": ("Montenegro", "Montenegro"),
    "MAR": ("Marruecos", "Morocco"), "MOZ": ("Mozambique", "Mozambique"),
    "MMR": ("Myanmar", "Myanmar"), "NAM": ("Namibia", "Namibia"),
    "NPL": ("Nepal", "Nepal"), "NLD": ("Países Bajos", "Netherlands"),
    "NZL": ("Nueva Zelanda", "New Zealand"), "NIC": ("Nicaragua", "Nicaragua"),
    "NER": ("Níger", "Niger"), "NGA": ("Nigeria", "Nigeria"),
    "PRK": ("Corea del Norte", "North Korea"),
    "MKD": ("Macedonia del Norte", "North Macedonia"),
    "NOR": ("Noruega", "Norway"), "OMN": ("Omán", "Oman"),
    "PAK": ("Pakistán", "Pakistan"), "PSE": ("Palestina", "Palestine"),
    "PAN": ("Panamá", "Panama"), "PNG": ("Papúa Nueva Guinea", "Papua New Guinea"),
    "PRY": ("Paraguay", "Paraguay"), "PER": ("Perú", "Peru"),
    "PHL": ("Filipinas", "Philippines"), "POL": ("Polonia", "Poland"),
    "PRT": ("Portugal", "Portugal"), "QAT": ("Catar", "Qatar"),
    "ROU": ("Rumania", "Romania"), "RUS": ("Rusia", "Russia"),
    "RWA": ("Ruanda", "Rwanda"), "STP": ("Santo Tomé y Príncipe", "São Tomé and Príncipe"),
    "SAU": ("Arabia Saudita", "Saudi Arabia"), "SEN": ("Senegal", "Senegal"),
    "SRB": ("Serbia", "Serbia"), "SLE": ("Sierra Leona", "Sierra Leone"),
    "SGP": ("Singapur", "Singapore"), "SVK": ("Eslovaquia", "Slovakia"),
    "SVN": ("Eslovenia", "Slovenia"), "SOM": ("Somalia", "Somalia"),
    "ZAF": ("Sudáfrica", "South Africa"), "KOR": ("Corea del Sur", "South Korea"),
    "SSD": ("Sudán del Sur", "South Sudan"), "ESP": ("España", "Spain"),
    "LKA": ("Sri Lanka", "Sri Lanka"), "SDN": ("Sudán", "Sudan"),
    "SUR": ("Surinam", "Suriname"), "SWE": ("Suecia", "Sweden"),
    "CHE": ("Suiza", "Switzerland"), "SYR": ("Siria", "Syria"),
    "TJK": ("Tayikistán", "Tajikistan"), "TZA": ("Tanzania", "Tanzania"),
    "THA": ("Tailandia", "Thailand"), "TLS": ("Timor Oriental", "Timor-Leste"),
    "TGO": ("Togo", "Togo"), "TTO": ("Trinidad y Tobago", "Trinidad and Tobago"),
    "TUN": ("Túnez", "Tunisia"), "TUR": ("Turquía", "Turkey"),
    "TKM": ("Turkmenistán", "Turkmenistan"), "UGA": ("Uganda", "Uganda"),
    "UKR": ("Ucrania", "Ukraine"),
    "ARE": ("Emiratos Árabes Unidos", "United Arab Emirates"),
    "GBR": ("Reino Unido", "United Kingdom"), "USA": ("Estados Unidos", "United States"),
    "URY": ("Uruguay", "Uruguay"), "UZB": ("Uzbekistán", "Uzbekistan"),
    "VEN": ("Venezuela", "Venezuela"), "VNM": ("Vietnam", "Vietnam"),
    "YEM": ("Yemen", "Yemen"), "ZMB": ("Zambia", "Zambia"),
    "ZWE": ("Zimbabue", "Zimbabwe"), "GNB": ("Guinea-Bisáu", "Guinea-Bissau"),
    "MHL": ("Islas Marshall", "Marshall Islands"),
}


def sql_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def enrich_countries():
    observed = set()
    with CTDC.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in ("citizenship", "CountryOfExploitation"):
                v = (row.get(k) or "").strip()
                if v and v.upper() != "NULL":
                    observed.add(v)
    path = ROOT / "db" / "08_enriched_countries.sql"
    lines = [
        "-- Enriched country catalogue",
        f"-- {len(observed)} ISO3 codes attested in the CTDC Global Synthetic Dataset v2025",
        "",
        "SET search_path TO ramona, public;",
        "",
        "-- Ensure the ISO3 column exists",
        "ALTER TABLE ramona.countries ADD COLUMN IF NOT EXISTS country_iso3 TEXT;",
        "ALTER TABLE ramona.countries ADD COLUMN IF NOT EXISTS country_name_es TEXT;",
        "",
        "INSERT INTO countries (country_code, country_name, country_iso3, country_name_es) VALUES",
    ]
    rows = []
    for iso3 in sorted(observed):
        name_es, name_en = ISO3_NAMES.get(iso3, (iso3, iso3))
        # country_code is 2-letter, we approximate by first 2 of ISO3 (not ISO2, but keeps the column non-null)
        code2 = iso3[:2]
        rows.append(
            f"  ({sql_str(code2)}, {sql_str(name_en)}, {sql_str(iso3)}, {sql_str(name_es)})"
        )
    lines.append(",\n".join(rows))
    lines.append("ON CONFLICT (country_code) DO UPDATE SET")
    lines.append("  country_iso3 = EXCLUDED.country_iso3,")
    lines.append("  country_name_es = EXCLUDED.country_name_es;")
    path.write_text("\n".join(lines))
    print(f"wrote {path}: {len(observed)} countries")


def fraudscheme_examples():
    """Pick 5 representative press articles per FraudScheme."""
    inp = ROOT / "data" / "processed" / "press_cases.jsonl"
    cases = []
    with inp.open() as f:
        for line in f:
            cases.append(json.loads(line))

    # detector already available in generate_seed_from_press.py but duplicated here for independence
    def detect_scheme(rec):
        exps = set(rec.get("exploitation_types", []))
        flags_b = set(rec.get("flags_credible_lethal", []))
        title_lower = (rec.get("title") or "").lower()
        if "forced_criminality" in exps:
            return "ForcedCriminalityScheme"
        if "organ_removal" in exps:
            return "DebtBondageTraffickingScheme"
        if any(k in title_lower for k in ("maquila", "maquiladora")):
            return "FakeMaquilaScheme"
        if any(k in title_lower for k in ("call center", "callcenter", "call-center")):
            return "CallCenterScamScheme"
        if any(k in title_lower for k in ("modela", "modelaje", "actriz")):
            return "ModelingAgencyScheme"
        if any(k in title_lower for k in ("crypto", "forex", "trader", "blockchain")):
            return "OnlineCryptoJobScheme"
        if any(k in title_lower for k in ("uber", "didi", "rappi", "conductor", "chofer")):
            return "GigEconomyFakeDriverScheme"
        if any(k in title_lower for k in ("multinivel", "mlm", "piramidal", "pirámide")):
            return "MLMHealthBeautyScheme"
        if any(k in title_lower for k in ("influencer", "community manager", "embajad")):
            return "OnlineInfluencerSalesScheme"
        if any(k in title_lower for k in ("maestr", "profesor", "teacher", "idioma", "inglés")):
            return "ForeignLanguageTeacherScheme"
        if any(k in title_lower for k in ("niñera", "au pair", "nanny", "cuidador")):
            return "VisaFraudScheme" if any(k in title_lower for k in ("canadá", "canada", "francia", "paris")) else "DomesticWorkerLockInScheme"
        if "solicita_ir_sola" in flags_b or "cita_edificio_multiusos" in flags_b:
            return "InPersonLureScheme"
        if "pago_adelantado" in rec.get("flags_classic", []):
            return "PayToWorkScheme"
        if "filtro_datos_personales" in flags_b:
            return "IdentityTheftScheme"
        return None

    by_scheme = defaultdict(list)
    for rec in cases:
        s = detect_scheme(rec)
        if s:
            by_scheme[s].append(rec)

    path = ROOT / "db" / "09_fraudscheme_examples.sql"
    lines = [
        "-- FraudScheme exemplars: up to 5 real press articles per scheme",
        f"-- Derived from {len(cases)} case-relevant classified press articles",
        "",
        "SET search_path TO ramona, public;",
        "",
        "-- Table to store examples with attribution",
        """CREATE TABLE IF NOT EXISTS fraudscheme_exemplars (
    exemplar_id   BIGSERIAL PRIMARY KEY,
    scheme_code   TEXT NOT NULL,
    example_rank  SMALLINT NOT NULL,
    title         TEXT NOT NULL,
    outlet        TEXT,
    url           TEXT,
    country       TEXT,
    exploit_hint  TEXT,
    UNIQUE (scheme_code, url)
);""",
        "",
        "INSERT INTO fraudscheme_exemplars (scheme_code, example_rank, title, outlet, url, country, exploit_hint) VALUES",
    ]
    insert_rows = []
    for scheme, recs in sorted(by_scheme.items()):
        # rank by: chars (longer article = more info), then by presence of B flags
        recs.sort(key=lambda r: -(r.get("chars", 0) + len(r.get("flags_credible_lethal", [])) * 1000))
        for rank, r in enumerate(recs[:5], start=1):
            title = (r.get("title") or "")[:300]
            outlet = r.get("outlet") or r.get("domain") or "unknown"
            url = r.get("final_url") or r.get("url") or ""
            country = (r.get("countries") or [None])[0] or None
            exp = (r.get("exploitation_types") or [None])[0] or None
            insert_rows.append(
                f"  ({sql_str(scheme)}, {rank}, {sql_str(title)}, {sql_str(outlet)}, "
                f"{sql_str(url)}, {sql_str(country) if country else 'NULL'}, "
                f"{sql_str(exp) if exp else 'NULL'})"
            )
    lines.append(",\n".join(insert_rows))
    lines.append("ON CONFLICT (scheme_code, url) DO NOTHING;")
    path.write_text("\n".join(lines))
    total = len(insert_rows)
    print(f"wrote {path}: {total} exemplars across {len(by_scheme)} schemes")


DEEP_PATTERNS = {
    # Additional Type B deep patterns (detected via fuller regex)
    "domicilio_en_vivo": r"envíen?|envía|manda|comparte.{0,30}ubicación\s+en\s+vivo",
    "adelanto_de_sueldo_primer_dia": r"adelanto.{0,20}(sueldo|salario)|anticipo.{0,20}primer\s+día",
    "fotografia_corporal": r"foto.{0,30}(cuerpo\s+completo|de\s+pie)|cuerpo\s+entero",
    "compra_de_producto_inicial": r"comprar\s+(un\s+)?kit|inventario\s+inicial|empezar\s+con\s+producto",
    "pide_firma_pagaré": r"pagar[eé]|recibo\s+en\s+blanco|firma.+en\s+blanco",
    "reclutador_insiste_urgente": r"es\s+urgente|no\s+puedo\s+esperar|pérdida\s+(del\s+)?cupo",
    "refiere_amigas_conocidas": r"refiere\s+amig|trae\s+a\s+alguien|referidas",
    "empresa_recien_creada": r"empresa\s+recién\s+(creada|abierta)|recién\s+(abrieron|fundada)",
    "sueldo_no_mencionado": r"hablamos\s+del\s+sueldo\s+después|dependiendo\s+de\s+tu\s+rendimiento",
    "horario_noche_exclusivo": r"solo\s+(de\s+)?noche|únicamente\s+(turno|horario)\s+nocturno",
    "entrevista_por_videollamada_cerrada": r"videollamada.{0,40}(cámara\s+apagada|sin\s+cámara)",
    "pago_en_efectivo_exclusivo": r"solo\s+efectivo|únicamente\s+efectivo|sin\s+transferencia",
    "recibir_visitas_en_domicilio": r"visita.{0,20}domicilio|(te|me)\s+van\s+(a\s+)?pasar\s+a\s+buscar",
    "acceso_restringido_a_familia": r"no\s+puedes\s+ver\s+a\s+tu\s+familia|contacto\s+con\s+familia\s+restring",
    "internet_laboral_restringido": r"sin\s+internet\s+personal|(celular|teléfono)\s+(del\s+trabajo|de\s+la\s+empresa)",
    "cuarto\s+compartido\s+con\s+recruiter": r"cuarto\s+compartido|mismo\s+cuarto|dormir.{0,15}compañera",
    "traslado_nocturno": r"traslado\s+(de\s+)?noche|viaje\s+nocturno",
    "pasaporte\s+custodiado": r"guard(é|amos|ar)\s+(el\s+|tu\s+)?pasaporte|custodia\s+(del\s+)?pasaporte",
    "contrato_en_otro_idioma": r"contrato\s+en\s+(inglés|otro\s+idioma)|no\s+entend\s+el\s+contrato",
    "recorrer_ruta_de_prueba": r"recorrer\s+(la\s+)?ruta|ruta\s+de\s+prueba",
    "oferta_por_influencer": r"influencer.+invitó|bajo\s+recomendación\s+de\s+influencer",
    "exigencia_de_cambio_nombre": r"cambi(ar|ó|a)\s+(tu\s+)?nombre|nombre\s+artístico",
    "menciona_deuda_traslado": r"debe(s|rás)?\s+el\s+traslado|deuda\s+del\s+traslado",
    "uso_de_whatsapp_business_falso": r"whatsapp\s+business.+sin\s+verificaci|cuenta\s+business\s+nueva",
    "publicidad_solo_imagenes": r"solo\s+imágenes|publicidad\s+visual\s+sin\s+texto",
    "ubicacion_zona_fronteriza": r"zona\s+frontera|frontera\s+norte|frontera\s+sur",
    "promesa_visa_humanitaria": r"visa\s+humanitaria|asilo\s+con\s+(trabajo|oferta)",
    "oferta_con_acoso_sexual_temprano": r"propuesta\s+indec|comentario\s+sexual|piropo\s+subido",
    "amenaza_con_deportar": r"deport(ar|ación).+amenaz|te\s+denuncio\s+a\s+migración",
    "eliminacion_de_contacto_post_aceptar": r"bloqueo\s+post\s+aceptar|desaparec(e|ió)\s+después\s+de\s+aceptar",
    "usa_nombre_celebridad": r"dicen?\s+ser\s+de\s+(Televisa|Tv\s+Azteca|Netflix|Google)|se\s+hac(en|ía)\s+pasar\s+por",
    "rechaza_videollamada": r"rechaz(a|aron)\s+videollamada|no\s+hace(n)?\s+videollamada",
    "menciona_sueldo_en_dolares_sin_justificar": r"sueldo\s+en\s+(dólares|USD|dollars).+sin\s+razón",
    "pide_cambio_de_ciudad_rapido": r"vente\s+(mañana|ya|en\s+dos\s+días)\s+a\s+otra\s+ciudad",
    "menciona_familiar_del_empleador": r"mi\s+(sobrino|tío|primo).+necesita",
    "promete_vuelos_pagados": r"vuelo.{0,30}(pagado|cubierto)|boleto\s+de\s+avión\s+incluido",
    "menciona_iglesia_o_grupo_religioso": r"grupo\s+(religioso|de\s+iglesia)|comunidad\s+de\s+fe",
    "presión_emocional_madre_sola": r"sé\s+que\s+eres\s+madre\s+sola|ideal\s+para\s+madre\s+soltera",
    "agencia_con_pagina_reciente": r"página\s+(recién\s+)?creada|dominio\s+nuevo",
    "solicita_referencia_no_verificable": r"referencia.{0,20}(whatsapp|teléfono\s+solo)|referencia.+sin\s+empleo\s+formal",
    "reunion_en_hotel": r"reunión\s+en\s+(el\s+)?hotel|cita\s+en\s+hotel",
    "reclutador_habla_como_amigo_cercano": r"(corazón|mi\s+reina|mi\s+vida).{0,20}(oportunidad|oferta)",
    "solicita_fotografía_intima": r"foto\s+íntima|foto\s+en\s+bikini|foto\s+provocat",
    "menciona_posible_esquema_comisiones_exagerado": r"comisión\s+del\s+[789]\d\s*%|comisión\s+de\s+90",
    "ofrece_alojamiento_compartido_con_desconocidos": r"compartir\s+alojamiento|dormir\s+con\s+(otras|otros)\s+chicas",
    "requisito_estar_soltera": r"(solo\s+)?solteras|preferible.+soltera",
    "requisito_ser_menor_de_25": r"menores\s+de\s+25|máximo\s+25\s+años",
    "oferta_con_promesa_de_romance": r"posible\s+(novio|pareja)|romance\s+incluido",
    "contratacion_sin_entrevista": r"contratación\s+sin\s+entrevista|aceptad(a|o)\s+sin\s+entrevista",
    "mencion_explicita_de_trata": r"podría\s+ser\s+trata|similar\s+a\s+trata",
}


def deep_patterns():
    inp = ROOT / "data" / "processed" / "press_cases.jsonl"
    compiled = {k: re.compile(v, re.IGNORECASE) for k, v in DEEP_PATTERNS.items()}
    # also need the raw text — which lives in data/raw/press.jsonl
    raw = ROOT / "data" / "raw" / "press.jsonl"
    # build lookup id -> text
    id_to_text = {}
    with raw.open() as f:
        for line in f:
            r = json.loads(line)
            id_to_text[r.get("id")] = (r.get("text") or "") + " " + (r.get("title") or "")
    counter = {k: 0 for k in compiled}
    total = 0
    with inp.open() as f:
        for line in f:
            r = json.loads(line)
            total += 1
            text = id_to_text.get(r.get("id"), "") or ""
            for name, rx in compiled.items():
                if rx.search(text):
                    counter[name] += 1
    path = ROOT / "db" / "10_deep_patterns.sql"
    lines = [
        "-- Deep regex patterns (v1.4)",
        f"-- Extracted from full text of {total} case-relevant press articles",
        "",
        "SET search_path TO ramona, public;",
        "",
        "INSERT INTO survivor_patterns (pattern_name, pattern_description, pattern_kind, observed_count, dominance_bucket, evidence_source) VALUES",
    ]
    rows = []
    for name, count in sorted(counter.items(), key=lambda kv: -kv[1]):
        pct = count / total * 100
        bucket = "hot" if pct >= 5 else ("warm" if pct >= 1 else "cold")
        desc = f"Patrón narrativo profundo detectado por análisis textual: {name.replace('_', ' ')}."
        rows.append(f"  ('{name}', {sql_str(desc)}, 'deep_textual', {count}, '{bucket}', NULL)")
    lines.append(",\n".join(rows))
    lines.append("ON CONFLICT (pattern_name) DO UPDATE SET")
    lines.append("  pattern_description = EXCLUDED.pattern_description,")
    lines.append("  observed_count = EXCLUDED.observed_count,")
    lines.append("  dominance_bucket = EXCLUDED.dominance_bucket;")
    path.write_text("\n".join(lines))
    detected = sum(1 for v in counter.values() if v > 0)
    print(f"wrote {path}: {len(counter)} deep patterns, {detected} with matches")


if __name__ == "__main__":
    print("=== countries ==="); enrich_countries()
    print("=== fraudscheme exemplars ==="); fraudscheme_examples()
    print("=== deep patterns ==="); deep_patterns()
