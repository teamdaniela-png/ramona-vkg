-- Ramona VKG — schema extension v1.0
-- Adds victim-centric tables aligned to CTDC Global Synthetic Dataset (IOM, 2025)
-- and to the HUTRO-aligned fragment of RATR-O v1.0.
--
-- Designed to be idempotent: uses CREATE TABLE IF NOT EXISTS.

BEGIN;

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
    hutro_close_match        TEXT
);

INSERT INTO recruitment_method (recruitment_method_code, recruitment_method_label, hutro_close_match) VALUES
    ('intimate_partner',     'Recruited by intimate partner',  'hutro:recruitment_method'),
    ('friend',               'Recruited by friend',            'hutro:recruitment_method'),
    ('family',               'Recruited by family member',     'hutro:recruitment_method'),
    ('labour_broker',        'Recruited by labour broker',     'hutro:recruitment_method'),
    ('social_media',         'Contacted via social media',     'hutro:recruitment_method'),
    ('classifieds',          'Contacted via online classifieds', 'hutro:recruitment_method'),
    ('in_person_street',     'Recruited in person on street',  'hutro:recruitment_method'),
    ('false_job_offer',      'False job offer',                'hutro:recruitment_method'),
    ('abduction',            'Abduction / forced recruitment', 'hutro:recruitment_method'),
    ('sale_by_family',       'Sale by family',                 'hutro:recruitment_method'),
    ('debt_bondage_entry',   'Debt bondage from entry',        'hutro:recruitment_method'),
    ('other',                'Other',                          'hutro:recruitment_method'),
    ('unknown',              'Unknown',                        NULL)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS exploitation_type (
    exploitation_type_code   TEXT PRIMARY KEY,
    exploitation_type_label  TEXT NOT NULL,
    hutro_close_match        TEXT
);

INSERT INTO exploitation_type (exploitation_type_code, exploitation_type_label, hutro_close_match) VALUES
    ('labour_agriculture',    'Forced labour: agriculture',            'hutro:type_of_exploitation'),
    ('labour_construction',   'Forced labour: construction',           'hutro:type_of_exploitation'),
    ('labour_domestic',       'Forced labour: domestic work',          'hutro:type_of_exploitation'),
    ('labour_hospitality',    'Forced labour: hospitality',            'hutro:type_of_exploitation'),
    ('labour_other',          'Forced labour: other',                  'hutro:type_of_exploitation'),
    ('sex_prostitution',      'Sexual exploitation: prostitution',     'hutro:type_of_exploitation'),
    ('sex_pornography',       'Sexual exploitation: pornography',      'hutro:type_of_exploitation'),
    ('forced_marriage',       'Forced marriage',                       'hutro:type_of_exploitation'),
    ('forced_criminality',    'Forced criminality',                    'hutro:type_of_exploitation'),
    ('organ_removal',         'Organ removal',                         'hutro:type_of_exploitation'),
    ('other',                 'Other exploitation',                    'hutro:type_of_exploitation'),
    ('unknown',               'Unknown',                               NULL)
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
    hutro_close_match    TEXT
);

INSERT INTO vulnerability_factor (vulnerability_code, vulnerability_label, hutro_close_match) VALUES
    ('economic',           'Economic precarity',               'hutro:vulnerability_factor'),
    ('migrant_status',     'Migrant or irregular status',      'hutro:vulnerability_factor'),
    ('minor',              'Minor (under 18)',                 'hutro:vulnerability_factor'),
    ('prior_abuse',        'Prior history of abuse',           'hutro:vulnerability_factor'),
    ('low_education',      'Low formal education',             'hutro:vulnerability_factor'),
    ('single_parent',      'Single parent / caregiver',        'hutro:vulnerability_factor'),
    ('displaced',          'Internally displaced or refugee',  'hutro:vulnerability_factor'),
    ('indigenous',         'Indigenous community member',      'hutro:vulnerability_factor'),
    ('disability',         'Disability',                       'hutro:vulnerability_factor'),
    ('other',              'Other',                            'hutro:vulnerability_factor')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS communication_tool (
    tool_code   TEXT PRIMARY KEY,
    tool_label  TEXT NOT NULL,
    hutro_close_match TEXT
);

INSERT INTO communication_tool (tool_code, tool_label, hutro_close_match) VALUES
    ('whatsapp',    'WhatsApp',        'hutro:smuggler_and_trafficker_communication_tools'),
    ('messenger',   'Facebook Messenger', 'hutro:smuggler_and_trafficker_communication_tools'),
    ('telegram',    'Telegram',        'hutro:smuggler_and_trafficker_communication_tools'),
    ('sms',         'SMS',             'hutro:smuggler_and_trafficker_communication_tools'),
    ('voice_call',  'Voice call',      'hutro:smuggler_and_trafficker_communication_tools'),
    ('in_person',   'In person',       'hutro:smuggler_and_trafficker_communication_tools'),
    ('email',       'Email',           'hutro:smuggler_and_trafficker_communication_tools'),
    ('other',       'Other',           'hutro:smuggler_and_trafficker_communication_tools')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS transportation_means (
    tm_code   TEXT PRIMARY KEY,
    tm_label  TEXT NOT NULL,
    hutro_close_match TEXT
);

INSERT INTO transportation_means (tm_code, tm_label, hutro_close_match) VALUES
    ('bus',     'Bus',     'hutro:transportation_means'),
    ('car',     'Car',     'hutro:transportation_means'),
    ('foot',    'On foot', 'hutro:transportation_means'),
    ('boat',    'Boat',    'hutro:transportation_means'),
    ('air',     'Air',     'hutro:transportation_means'),
    ('train',   'Train',   'hutro:transportation_means'),
    ('truck',   'Truck',   'hutro:transportation_means'),
    ('mixed',   'Mixed',   'hutro:transportation_means'),
    ('unknown', 'Unknown', NULL)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS documentation_type (
    doc_code   TEXT PRIMARY KEY,
    doc_label  TEXT NOT NULL,
    is_false   BOOLEAN NOT NULL DEFAULT FALSE,
    hutro_close_match TEXT
);

INSERT INTO documentation_type (doc_code, doc_label, is_false, hutro_close_match) VALUES
    ('national_id', 'National ID',  FALSE, 'hutro:documentation_type'),
    ('passport',    'Passport',     FALSE, 'hutro:documentation_type'),
    ('visa',        'Visa',         FALSE, 'hutro:documentation_type'),
    ('work_permit', 'Work permit',  FALSE, 'hutro:documentation_type'),
    ('none',        'None',         FALSE, 'hutro:documentation_type'),
    ('confiscated', 'Confiscated',  FALSE, 'hutro:documentation_type'),
    ('false_document', 'False documentation', TRUE, 'hutro:false_documentation')
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
