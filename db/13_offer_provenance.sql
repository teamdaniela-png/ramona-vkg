-- Ramona VKG — offer provenance and evidence-source kind
--
-- 1. Links each offer in ramona.offers to the evidence source it was synthesised from. The
--    raw_text of a synthesised offer is exactly
--    '[Sintetizado desde articulo de prensa: ' || source_title || ']', so the join below is
--    an equality on text the seeds already contain. 1,325 of the 1,332 synthesised offers
--    match a source; where two rows duplicate the same article, MIN(source_id) picks one
--    deterministically; 7 match none and stay NULL. The 47 offers written for the demonstrator in db/03
--    carry no source.
--
-- 2. Records the kind of each evidence source, from how the row entered the database:
--    db/05 inserts 1,332 rows scraped from the press corpus, whose source_title ends in
--    ' - ' || source_outlet, and db/02 inserts 5 reference rows, each named below.
--    mappings/ramona.obda types the press articles as :PressArticle from this column.
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

-- The five reference rows of db/02, by title.
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
