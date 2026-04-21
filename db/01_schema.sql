-- Ramona AI demo schema
-- Postgres 16
-- All tables are demo-only. No PII. Contact fields are SHA-256 hashes.

CREATE SCHEMA IF NOT EXISTS ramona;
SET search_path TO ramona, public;

-- Reference tables ------------------------------------------------------------

CREATE TABLE countries (
    country_code     CHAR(2) PRIMARY KEY,  -- ISO 3166-1 alpha-2
    country_name     TEXT NOT NULL
);

CREATE TABLE languages (
    language_code    CHAR(2) PRIMARY KEY,  -- ISO 639-1
    language_name    TEXT NOT NULL
);

CREATE TABLE platforms (
    platform_id      SERIAL PRIMARY KEY,
    platform_name    TEXT NOT NULL UNIQUE,
    platform_type    TEXT NOT NULL,        -- whatsapp | telegram | messenger | sms | facebook | tiktok | classifieds | other
    platform_country CHAR(2) REFERENCES countries(country_code)
);

CREATE TABLE evidence_sources (
    source_id        SERIAL PRIMARY KEY,
    source_title     TEXT NOT NULL,
    source_outlet    TEXT NOT NULL,
    source_url       TEXT,
    source_date      DATE
);

CREATE TABLE trafficking_routes (
    route_id         SERIAL PRIMARY KEY,
    route_name       TEXT NOT NULL,
    origin_country   CHAR(2) NOT NULL REFERENCES countries(country_code),
    destination_country CHAR(2) NOT NULL REFERENCES countries(country_code),
    known_since      DATE,
    evidence_source  INTEGER REFERENCES evidence_sources(source_id)
);

CREATE TABLE survivor_patterns (
    pattern_id       SERIAL PRIMARY KEY,
    pattern_name     TEXT NOT NULL UNIQUE,
    pattern_description TEXT NOT NULL,
    evidence_source  INTEGER REFERENCES evidence_sources(source_id)
);

-- Core operational tables -----------------------------------------------------

CREATE TABLE employers (
    employer_id      SERIAL PRIMARY KEY,
    employer_name    TEXT,
    has_verified_identity BOOLEAN NOT NULL DEFAULT FALSE,
    tax_id_hash      TEXT,
    historical_offer_count INTEGER NOT NULL DEFAULT 0,
    historical_flag_count  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE recruiters (
    recruiter_id     SERIAL PRIMARY KEY,
    contact_hash     TEXT UNIQUE,
    agent_name       TEXT,
    recruiter_country CHAR(2) REFERENCES countries(country_code),
    first_seen_at    DATE,
    historical_offer_count INTEGER NOT NULL DEFAULT 0,
    historical_flag_count  INTEGER NOT NULL DEFAULT 0,
    associated_employer INTEGER REFERENCES employers(employer_id)
);

CREATE TABLE candidates (
    candidate_id     SERIAL PRIMARY KEY,
    candidate_id_hash TEXT UNIQUE,
    candidate_country CHAR(2) REFERENCES countries(country_code)
);

CREATE TABLE classifications (
    classification_id   SERIAL PRIMARY KEY,
    risk_level          TEXT NOT NULL CHECK (risk_level IN ('safe','suspicious','high-risk','fraudulent')),
    explanation_text    TEXT,
    classified_at       DATE NOT NULL,
    classifier_version  TEXT NOT NULL DEFAULT 'ramona-v0.9'
);

CREATE TABLE offers (
    offer_id         SERIAL PRIMARY KEY,
    raw_text         TEXT NOT NULL,
    offered_role     TEXT,
    offered_location TEXT,
    offered_salary_mxn NUMERIC(10,2),
    posted_at        DATE NOT NULL,
    source_platform  INTEGER NOT NULL REFERENCES platforms(platform_id),
    country_code     CHAR(2) NOT NULL REFERENCES countries(country_code),
    language_code    CHAR(2) NOT NULL REFERENCES languages(language_code),
    recruiter_id     INTEGER REFERENCES recruiters(recruiter_id),
    employer_id      INTEGER REFERENCES employers(employer_id),
    classification_id INTEGER REFERENCES classifications(classification_id),
    risk_score       NUMERIC(3,2)
);

CREATE TABLE red_flags (
    flag_id          SERIAL PRIMARY KEY,
    offer_id         INTEGER NOT NULL REFERENCES offers(offer_id),
    flag_type        TEXT NOT NULL CHECK (flag_type IN (
        'sueldo_alto',
        'horarios_flexibles',
        'sin_experiencia',
        'pago_adelantado',
        'aceptacion_urgente',
        'entrevista_lejana_traslado',
        'empleo_fuera_estado'
    )),
    flag_confidence  NUMERIC(3,2) NOT NULL CHECK (flag_confidence BETWEEN 0 AND 1),
    detected_by      TEXT NOT NULL CHECK (detected_by IN ('rule','nlp','human'))
);

CREATE TABLE offer_patterns (
    offer_id         INTEGER NOT NULL REFERENCES offers(offer_id),
    pattern_id       INTEGER NOT NULL REFERENCES survivor_patterns(pattern_id),
    PRIMARY KEY (offer_id, pattern_id)
);

CREATE TABLE offer_routes (
    offer_id         INTEGER NOT NULL REFERENCES offers(offer_id),
    route_id         INTEGER NOT NULL REFERENCES trafficking_routes(route_id),
    PRIMARY KEY (offer_id, route_id)
);

CREATE TABLE submissions (
    submission_id    SERIAL PRIMARY KEY,
    candidate_id     INTEGER NOT NULL REFERENCES candidates(candidate_id),
    offer_id         INTEGER NOT NULL REFERENCES offers(offer_id),
    submitted_at     DATE NOT NULL
);

CREATE INDEX idx_offers_posted_at ON offers(posted_at);
CREATE INDEX idx_offers_country ON offers(country_code);
CREATE INDEX idx_offers_platform ON offers(source_platform);
CREATE INDEX idx_red_flags_offer ON red_flags(offer_id);
CREATE INDEX idx_red_flags_type ON red_flags(flag_type);
