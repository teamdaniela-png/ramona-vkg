-- Ramona VKG — schema extension v1.0
-- Adds victim-centric tables aligned to CTDC Global Synthetic Dataset (IOM, 2025)
-- and to the HUTRO-aligned fragment of RATR-O v1.0.
--
-- Designed to be idempotent: uses CREATE TABLE IF NOT EXISTS.
--
-- hutro_concept_label holds the preferred label of the HUTRO concept that each controlled
-- vocabulary is conceptually close to; hutro_concept_iri holds that concept's IRI.
--
-- HUTRO's BioPortal submission metadata declares the placeholder namespace
-- http://www.example.com, but BioPortal reports and resolves each concept under
-- https://bioportal.bioontology.org/ontologies/HUTRO with the local name appended directly,
-- with no separating slash or hash. Each of the IRIs below was checked one by one in the
-- BioPortal concept browser on 10 November 2026 and resolved to the expected preferred label.
-- Two local names differ from the obvious spelling: HUTRO writes 'recuritment_method', which
-- is misspelt at the source, and 'smuggler_trafficker_communication_tools', without the
-- conjunction. Up to v1.10 this file used the corrected spellings, which do not resolve.

BEGIN;
-- These tables live in the public schema, not in ramona, and mappings/ramona.obda reads
-- them as public.<table>. The search_path has to be set explicitly. Postgres's default is
-- "$user", public, and under docker-compose the database user is ramona and db/01 creates a
-- schema of that same name, so without this line every table below would be created in
-- ramona and the 26 mappings that read public.<table> would find nothing.
SET search_path TO public;


-- =========================================================================
-- Operational-schema extensions (additive, non-breaking)
-- =========================================================================

-- Add pattern tag to evidence_sources so a source can be tagged with the
-- named FraudScheme (or 'general') it documents. Used by seed v1.2 onward.
ALTER TABLE ramona.evidence_sources
    ADD COLUMN IF NOT EXISTS source_pattern TEXT;

COMMENT ON COLUMN ramona.evidence_sources.source_pattern IS
'Named FraudScheme tag from RATR-O (IdentityTheftScheme, PyramidScheme, etc.) or ''general'' when no single scheme applies.';

-- =========================================================================
-- Demographics and victim-centric tables
-- =========================================================================

CREATE TABLE IF NOT EXISTS age_group (
    age_group_code  TEXT PRIMARY KEY,
    age_group_label TEXT NOT NULL
);

INSERT INTO age_group (age_group_code, age_group_label) VALUES
    ('0-8',   '0 to 8 years'),
    ('9-17',  '9 to 17 years'),
    ('18-20', '18 to 20 years'),
    ('21-23', '21 to 23 years'),
    ('24-26', '24 to 26 years'),
    ('27-29', '27 to 29 years'),
    ('30-38', '30 to 38 years'),
    ('39-47', '39 to 47 years'),
    ('48+',   '48 years and older')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS gender (
    gender_code  TEXT PRIMARY KEY,
    gender_label TEXT NOT NULL
);

INSERT INTO gender (gender_code, gender_label) VALUES
    ('female',      'Woman'),
    ('male',        'Man'),
    ('trans_nc',    'Trans / Transgender / Non-Conforming'),
    ('unknown',     'Unknown')
ON CONFLICT DO NOTHING;

-- =========================================================================
-- HUTRO-aligned reference vocabularies
-- =========================================================================

CREATE TABLE IF NOT EXISTS recruitment_method (
    recruitment_method_code  TEXT PRIMARY KEY,
    recruitment_method_label TEXT NOT NULL,
    hutro_concept_label        TEXT,
    hutro_concept_iri          TEXT
);

INSERT INTO recruitment_method (recruitment_method_code, recruitment_method_label, hutro_concept_label, hutro_concept_iri) VALUES
    ('intimate_partner',     'Recruited by intimate partner',  'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('friend',               'Recruited by friend',            'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('family',               'Recruited by family member',     'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('labour_broker',        'Recruited by labour broker',     'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('social_media',         'Contacted via social media',     'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('classifieds',          'Contacted via online classifieds', 'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('in_person_street',     'Recruited in person on street',  'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('false_job_offer',      'False job offer',                'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('abduction',            'Abduction / forced recruitment', 'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('sale_by_family',       'Sale by family',                 'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('debt_bondage_entry',   'Debt bondage from entry',        'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('other',                'Other',                          'recruitment method', 'https://bioportal.bioontology.org/ontologies/HUTROrecuritment_method'),
    ('unknown',              'Unknown',                        NULL, NULL)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS exploitation_type (
    exploitation_type_code   TEXT PRIMARY KEY,
    exploitation_type_label  TEXT NOT NULL,
    hutro_concept_label        TEXT,
    hutro_concept_iri          TEXT
);

INSERT INTO exploitation_type (exploitation_type_code, exploitation_type_label, hutro_concept_label, hutro_concept_iri) VALUES
    ('labour_agriculture',    'Forced labour: agriculture',            'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('labour_construction',   'Forced labour: construction',           'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('labour_domestic',       'Forced labour: domestic work',          'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('labour_hospitality',    'Forced labour: hospitality',            'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('labour_other',          'Forced labour: other',                  'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('sex_prostitution',      'Sexual exploitation: prostitution',     'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('sex_pornography',       'Sexual exploitation: pornography',      'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('sex_other',             'Sexual exploitation: other',            'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('forced_marriage',       'Forced marriage',                       'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('forced_criminality',    'Forced criminality',                    'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('organ_removal',         'Organ removal',                         'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('other',                 'Other exploitation',                    'type of exploitation', 'https://bioportal.bioontology.org/ontologies/HUTROtype_of_exploitation'),
    ('unknown',               'Unknown',                               NULL, NULL)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS means_of_control (
    means_code    TEXT PRIMARY KEY,
    means_label   TEXT NOT NULL,
    ctdc_variable TEXT
);

INSERT INTO means_of_control (means_code, means_label, ctdc_variable) VALUES
    ('debt_bondage_earnings',  'Debt bondage and/or withholding of earnings', 'meansDebtBondageEarnings'),
    ('threats',                'Threats to individual and/or family',         'meansThreats'),
    ('abuse_psy_phy_sex',      'Psychological, physical and/or sexual abuse', 'meansAbusePsyPhySex'),
    ('false_promises',         'False promises',                              'meansFalsePromises'),
    ('drugs_alcohol',          'Psychoactive substances',                     'meansDrugsAlcohol'),
    ('deny_basic_needs',       'Restricts finance, movement, medical care or necessities', 'meansDenyBasicNeeds'),
    ('excessive_work_hours',   'Excessive working hours',                     'meansExcessiveWorkHours'),
    ('withhold_docs',          'Withholding of documents',                    'meansWithholdDocs')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS vulnerability_factor (
    vulnerability_code   TEXT PRIMARY KEY,
    vulnerability_label  TEXT NOT NULL,
    hutro_concept_label    TEXT,
    hutro_concept_iri          TEXT
);

INSERT INTO vulnerability_factor (vulnerability_code, vulnerability_label, hutro_concept_label, hutro_concept_iri) VALUES
    ('economic',           'Economic precarity',               'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('migrant_status',     'Migrant or irregular status',      'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('minor',              'Minor (under 18)',                 'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('prior_abuse',        'Prior history of abuse',           'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('low_education',      'Low formal education',             'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('single_parent',      'Single parent / caregiver',        'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('displaced',          'Internally displaced or refugee',  'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('indigenous',         'Indigenous community member',      'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('disability',         'Disability',                       'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor'),
    ('other',              'Other',                            'vulnerability factor', 'https://bioportal.bioontology.org/ontologies/HUTROvulnerability_factor')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS communication_tool (
    tool_code   TEXT PRIMARY KEY,
    tool_label  TEXT NOT NULL,
    hutro_concept_label TEXT,
    hutro_concept_iri          TEXT
);

INSERT INTO communication_tool (tool_code, tool_label, hutro_concept_label, hutro_concept_iri) VALUES
    ('whatsapp',    'WhatsApp',        'smuggler and trafficker communication tools', 'https://bioportal.bioontology.org/ontologies/HUTROsmuggler_trafficker_communication_tools'),
    ('messenger',   'Facebook Messenger', 'smuggler and trafficker communication tools', 'https://bioportal.bioontology.org/ontologies/HUTROsmuggler_trafficker_communication_tools'),
    ('telegram',    'Telegram',        'smuggler and trafficker communication tools', 'https://bioportal.bioontology.org/ontologies/HUTROsmuggler_trafficker_communication_tools'),
    ('sms',         'SMS',             'smuggler and trafficker communication tools', 'https://bioportal.bioontology.org/ontologies/HUTROsmuggler_trafficker_communication_tools'),
    ('voice_call',  'Voice call',      'smuggler and trafficker communication tools', 'https://bioportal.bioontology.org/ontologies/HUTROsmuggler_trafficker_communication_tools'),
    ('in_person',   'In person',       'smuggler and trafficker communication tools', 'https://bioportal.bioontology.org/ontologies/HUTROsmuggler_trafficker_communication_tools'),
    ('email',       'Email',           'smuggler and trafficker communication tools', 'https://bioportal.bioontology.org/ontologies/HUTROsmuggler_trafficker_communication_tools'),
    ('other',       'Other',           'smuggler and trafficker communication tools', 'https://bioportal.bioontology.org/ontologies/HUTROsmuggler_trafficker_communication_tools')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS transportation_means (
    tm_code   TEXT PRIMARY KEY,
    tm_label  TEXT NOT NULL,
    hutro_concept_label TEXT,
    hutro_concept_iri          TEXT
);

INSERT INTO transportation_means (tm_code, tm_label, hutro_concept_label, hutro_concept_iri) VALUES
    ('bus',     'Bus',     'transportation means', 'https://bioportal.bioontology.org/ontologies/HUTROtransportation_means'),
    ('car',     'Car',     'transportation means', 'https://bioportal.bioontology.org/ontologies/HUTROtransportation_means'),
    ('foot',    'On foot', 'transportation means', 'https://bioportal.bioontology.org/ontologies/HUTROtransportation_means'),
    ('boat',    'Boat',    'transportation means', 'https://bioportal.bioontology.org/ontologies/HUTROtransportation_means'),
    ('air',     'Air',     'transportation means', 'https://bioportal.bioontology.org/ontologies/HUTROtransportation_means'),
    ('train',   'Train',   'transportation means', 'https://bioportal.bioontology.org/ontologies/HUTROtransportation_means'),
    ('truck',   'Truck',   'transportation means', 'https://bioportal.bioontology.org/ontologies/HUTROtransportation_means'),
    ('mixed',   'Mixed',   'transportation means', 'https://bioportal.bioontology.org/ontologies/HUTROtransportation_means'),
    ('unknown', 'Unknown', NULL, NULL)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS documentation_type (
    doc_code   TEXT PRIMARY KEY,
    doc_label  TEXT NOT NULL,
    is_false   BOOLEAN NOT NULL DEFAULT FALSE,
    hutro_concept_label TEXT,
    hutro_concept_iri          TEXT
);

INSERT INTO documentation_type (doc_code, doc_label, is_false, hutro_concept_label, hutro_concept_iri) VALUES
    ('national_id', 'National ID',  FALSE, 'documentation type', 'https://bioportal.bioontology.org/ontologies/HUTROdocumentation_type'),
    ('passport',    'Passport',     FALSE, 'documentation type', 'https://bioportal.bioontology.org/ontologies/HUTROdocumentation_type'),
    ('visa',        'Visa',         FALSE, 'documentation type', 'https://bioportal.bioontology.org/ontologies/HUTROdocumentation_type'),
    ('work_permit', 'Work permit',  FALSE, 'documentation type', 'https://bioportal.bioontology.org/ontologies/HUTROdocumentation_type'),
    ('none',        'None',         FALSE, 'documentation type', 'https://bioportal.bioontology.org/ontologies/HUTROdocumentation_type'),
    ('confiscated', 'Confiscated',  FALSE, 'documentation type', 'https://bioportal.bioontology.org/ontologies/HUTROdocumentation_type'),
    ('false_document', 'False documentation', TRUE, 'false documentation', 'https://bioportal.bioontology.org/ontologies/HUTROfalse_documentation')
ON CONFLICT DO NOTHING;

-- =========================================================================
-- Victim table (anonymised case records)
-- =========================================================================

CREATE TABLE IF NOT EXISTS evidence_source_extended (
    source_id          BIGSERIAL PRIMARY KEY,
    source_kind        TEXT NOT NULL,       -- 'press', 'ctdc', 'unodc', 'rnpdno', 'ramona_internal'
    dataset_name       TEXT,
    dataset_record_id  TEXT,
    outlet             TEXT,
    title              TEXT,
    url                TEXT,
    author             TEXT,
    published_at       DATE,
    raw_text           TEXT,
    ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_kind, dataset_record_id, url)
);

CREATE TABLE IF NOT EXISTS victim (
    victim_id                BIGSERIAL PRIMARY KEY,
    external_id              TEXT NOT NULL,
    source_kind              TEXT NOT NULL,
    source_id                BIGINT REFERENCES evidence_source_extended(source_id),
    year_of_registration     SMALLINT,
    age_group_code           TEXT REFERENCES age_group(age_group_code),
    gender_code              TEXT REFERENCES gender(gender_code),
    citizenship_iso3         TEXT,
    country_of_exploitation_iso3 TEXT,
    traffick_duration_band   TEXT,
    recruitment_method_code  TEXT REFERENCES recruitment_method(recruitment_method_code),
    communication_tool_code  TEXT REFERENCES communication_tool(tool_code),
    transportation_code      TEXT REFERENCES transportation_means(tm_code),
    documentation_code       TEXT REFERENCES documentation_type(doc_code),
    loaded_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_kind, external_id)
);

-- Multi-valued flags (a single victim can have multiple exploitation types,
-- multiple means of control, multiple vulnerability factors).

CREATE TABLE IF NOT EXISTS victim_exploitation (
    victim_id              BIGINT NOT NULL REFERENCES victim(victim_id) ON DELETE CASCADE,
    exploitation_type_code TEXT NOT NULL REFERENCES exploitation_type(exploitation_type_code),
    PRIMARY KEY (victim_id, exploitation_type_code)
);

CREATE TABLE IF NOT EXISTS victim_means_of_control (
    victim_id   BIGINT NOT NULL REFERENCES victim(victim_id) ON DELETE CASCADE,
    means_code  TEXT NOT NULL REFERENCES means_of_control(means_code),
    PRIMARY KEY (victim_id, means_code)
);

CREATE TABLE IF NOT EXISTS victim_vulnerability (
    victim_id           BIGINT NOT NULL REFERENCES victim(victim_id) ON DELETE CASCADE,
    vulnerability_code  TEXT NOT NULL REFERENCES vulnerability_factor(vulnerability_code),
    PRIMARY KEY (victim_id, vulnerability_code)
);

-- =========================================================================
-- Dual-track classification (Tipo A / Tipo B) for offers and victims
-- =========================================================================

CREATE TABLE IF NOT EXISTS offer_detection_track (
    offer_id                  BIGINT PRIMARY KEY,
    has_classic_red_flags     BOOLEAN NOT NULL DEFAULT FALSE,
    classic_flag_count        SMALLINT NOT NULL DEFAULT 0,
    has_credible_lethal_pattern BOOLEAN NOT NULL DEFAULT FALSE,
    credible_pattern_count    SMALLINT NOT NULL DEFAULT 0,
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    comment                   TEXT
);

COMMENT ON TABLE offer_detection_track IS
'Dual-track classification. Type A (classic) = obvious red flags from Ramona''s 7-flag taxonomy. Type B (credible-lethal) = subtle patterns of the Edith Guadalupe kind (no logo, ven sola, sin identificación, edificio multiusos, sueldo creíble). A case can be in both, neither, or only one. The observatory publishes the distribution of B-only cases as the central "nobody is exempt" statistic.';

-- =========================================================================
-- Useful indices
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_victim_source_kind       ON victim(source_kind);
CREATE INDEX IF NOT EXISTS idx_victim_year              ON victim(year_of_registration);
CREATE INDEX IF NOT EXISTS idx_victim_coe               ON victim(country_of_exploitation_iso3);
CREATE INDEX IF NOT EXISTS idx_victim_citizen           ON victim(citizenship_iso3);
CREATE INDEX IF NOT EXISTS idx_victim_age_gender        ON victim(age_group_code, gender_code);
CREATE INDEX IF NOT EXISTS idx_vexp_type                ON victim_exploitation(exploitation_type_code);
CREATE INDEX IF NOT EXISTS idx_vmoc_code                ON victim_means_of_control(means_code);
CREATE INDEX IF NOT EXISTS idx_evsrc_kind               ON evidence_source_extended(source_kind);

COMMIT;
