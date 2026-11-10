-- Ramona VKG — offer provenance and evidence-source kind
--
-- Two gaps found while executing the 40 reference queries against the seeds:
--
-- 1. ramona.offers had no link to ramona.evidence_sources, so the 1,332 offers that
--    db/05_seed_cases_v1_2.sql synthesises from press articles carried no provenance, and
--    :EvidenceSource's claim that every observatory fact traces to a source did not hold
--    for offers. The link is recovered, not invented: each synthesised offer's raw_text is
--    exactly '[Sintetizado desde articulo de prensa: ' || source_title || ']', so the join
--    below is an equality on text the seeds already contain. 1,325 of the 1,332 match a
--    single source; 6 match two rows that duplicate the same article, and MIN(source_id)
--    picks one deterministically; 7 find no match and stay NULL.
--
-- 2. ramona.evidence_sources had no kind, so no source could be typed as a press article
--    and queries asking for ?s a :PressArticle over this registry returned nothing. The
--    kind is derived from how each row entered the database: db/05 inserts 1,332 rows
--    scraped from the press corpus, whose source_title ends in ' - ' || source_outlet,
--    and db/02 inserts 5 hand-curated rows, each named explicitly below.
--
-- Idempotent: re-running it recomputes the same values.

SET search_path TO ramona, public;

BEGIN;

ALTER TABLE ramona.offers
  ADD COLUMN IF NOT EXISTS evidence_source INTEGER REFERENCES ramona.evidence_sources(source_id);

UPDATE ramona.offers
   SET evidence_source = (
         SELECT MIN(e.source_id)
           FROM ramona.evidence_sources e
          WHERE ramona.offers.raw_text
                = '[Sintetizado desde artículo de prensa: ' || e.source_title || ']')
 WHERE ramona.offers.raw_text LIKE '[Sintetizado desde art%';

ALTER TABLE ramona.evidence_sources
  ADD COLUMN IF NOT EXISTS source_kind TEXT;

-- The press corpus: every row db/05 inserted.
UPDATE ramona.evidence_sources
   SET source_kind = 'press_article'
 WHERE source_title LIKE '% - ' || source_outlet;

-- The five hand-curated rows of db/02, by title.
UPDATE ramona.evidence_sources SET source_kind = 'press_article'
 WHERE source_title IN (
   '"Pedian Ir Sola": Narran Como Eran Citas de Trabajo en Edificio Donde Hallaron a Edith Guadalupe',
   'Grupos delictivos refinan reclutamiento en redes sociales tras caso del Rancho Izaguirre',
   'Alerta de seguridad: Rancho Izaguirre y reclutamiento forzado CJNG');

UPDATE ramona.evidence_sources SET source_kind = 'organisation_material'
 WHERE source_title = 'Como detectar las ofertas de trabajo falsas (infografia Ramona AI)';

UPDATE ramona.evidence_sources SET source_kind = 'statistics_report'
 WHERE source_title = 'Estadisticas de victimas de ofertas falsas: Consejo Ciudadano CDMX';

COMMIT;
