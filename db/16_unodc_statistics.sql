-- Ramona VKG — official statistics of UNODC
--
-- One row per figure of the UNODC data portal on trafficking in persons: a country, a year, an
-- indicator, a breakdown and a count. The table is created empty. The release is not
-- redistributed here; scripts/ingest_unodc.py loads a downloaded copy.
-- stat_id is the position of the row in the release, so the same file gives the same identifiers.

SET search_path TO ramona, public;

CREATE TABLE IF NOT EXISTS unodc_statistics (
    stat_id             INTEGER PRIMARY KEY,
    source_id           INTEGER NOT NULL REFERENCES public.evidence_source_extended(source_id),
    country_iso3        TEXT NOT NULL REFERENCES ramona.countries(country_iso3),
    indicator           TEXT NOT NULL,
    dimension           TEXT NOT NULL,
    category            TEXT NOT NULL,
    sex                 TEXT NOT NULL,
    age                 TEXT NOT NULL,
    year                INTEGER NOT NULL,
    value               INTEGER,
    value_as_published  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_unodc_country_year ON unodc_statistics(country_iso3, year);
