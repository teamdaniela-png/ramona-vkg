# RATR-O validation with standard tools (v1.10.1, 10 Nov 2026)

Tools: ROBOT 1.9.11 (OWL API profile checker, HermiT reasoner, ROBOT report) on OpenJDK 27.0.1,
plus the repository audit script `scripts/audit_o1.py`.

## Results

| Check | Tool | Result |
|---|---|---|
| OWL 2 QL profile | `robot validate-profile --profile QL` | **In profile** (`robot_profile_QL.txt`) |
| TBox consistency | `robot reason --reasoner hermit` | **Consistent** |
| Unsatisfiable classes | HermiT, `--dump-unsatisfiable` | **None** (no dump file produced) |
| TBox (1,582 triples) + 1,500 synthetic social items (24,037 triples) | `robot merge` + HermiT | **Consistent** |
| TBox + synthetic items + 295 verified real offers (4,919 triples), 35,670 triples in all | `robot merge` + HermiT | **Consistent** |
| Repository audit (profile, coverage, provenance, naming, definitions, vocabulary closure, datatypes) | `scripts/audit_o1.py` | **0 blockers, 0 SHOULD** (`../AUDIT_O1.md`) |
| Quality report | `robot report` | OBO-convention findings only (see below) |

## What the standard profile checker found in v1.9

The first run of the OWL API checker on v1.9 reported the ontology **not in OWL 2 QL**:

1. **16 data-property ranges outside the OWL 2 QL datatype map**: `xsd:date` (6), `xsd:gYear` (4),
   `xsd:boolean` (6). OWL 2 QL admits a restricted datatype map (OWL 2 Profiles, section 3.2) that
   includes `xsd:dateTime`, `xsd:integer`, `xsd:decimal`, `xsd:string` and `xsd:anyURI`, but not
   these three.
   **Fix:** ranges set to `rdfs:Literal`, each property annotated with its intended datatype;
   the mapping layer keeps emitting `xsd:date`, `xsd:gYear` and `xsd:boolean` literals.
   This is the same design rule as the QCA conjunctions (`../MODULE_SOCIAL_RECRUITMENT.md`):
   what the profile cannot express is enforced in the mapping, not dropped.
2. **Undeclared annotation properties** (`dc:title`, `dc:creator`, `dct:*`, `skos:note`,
   `skos:closeMatch`). No logical effect. **Fix:** declared as `owl:AnnotationProperty`.

## What the v1.10.1 audit found in v1.10

The audit that preceded the delivery of O1 found five defects that the earlier checks had missed,
because the earlier checks never read the queries and the mappings together with the TBox, and
never reasoned over the real-offer ABox and the synthetic ABox in the same graph.

1. **Mapping and queries used a term the ontology does not declare.** `:hasMeansOfControl` is
   asserted by `mappings/ramona.obda` and `mappings/ramona.r2rml.ttl` and queried by
   `queries/Q13` and `queries/Q26`, but it was never declared in the TBox, so those two queries
   were not answerable over the published vocabulary. **Fix:** declared as a datatype property
   with domain `:Victim` and range `xsd:string`, and distinguished in its definition from
   `:PalermoMeans` (means used to obtain the person, as against means used to keep them).
2. **A mapping emitted a datatype that clashes with the declared range, making the merged graph
   inconsistent.** `:sourceUrl` has range `xsd:anyURI`, but the press module added in v1.10
   (`M-Press-*`, and `scripts/materialize_press_abox.py`) emitted `xsd:string`. HermiT reports
   `owl:Thing ⊑ owl:Nothing` on the merged graph. The defect was invisible while the two ABoxes
   were reasoned separately. **Fix:** the three producers now emit `xsd:anyURI`. The claim that
   the real-offer graph is consistent only holds from v1.10.1 on; for v1.10 it was wrong.
3. **158 of 281 classes and properties had no definition**, only labels. For a published
   vocabulary this is a documentation defect, not a logical one. **Fix:** every class, object
   property and datatype property now carries an `rdfs:comment`. The Palermo subclasses quote the
   fragment of Article 3(a) they stand for.
4. **Dangling IRIs inside annotation text and 18 Spanish labels without accents.** Three comments
   referred to `:fraudAxis`, `:exploitationAxis` and `:traffickingAxis`, which are not declared
   (the dimensions are the subclasses `:FraudRisk`, `:ExploitationRisk`, `:TraffickingRisk`), and
   one referred to the CTDC value `:labour_agriculture` as if it were an ontology term.
   **Fix:** comments rewritten, labels corrected.

5. **The country catalogue corrupted itself on load.** `db/08_enriched_countries.sql` filled
   `country_code CHAR(2) PRIMARY KEY` with the first two letters of each alpha-3 code. Thirty-nine
   keys collided, so the `ON CONFLICT (country_code) DO UPDATE` upsert overwrote Colombia with
   Comoros, Spain with Estonia and Argentina with Armenia, and Mexico was never defined under `MX`.
   This is a defect of the demonstrator database rather than of the ontology, but every
   country-level answer the VKG gives depends on it. **Fix:** codes taken from the ISO 3166 tables
   in `pycountry` (added to `requirements.txt`); 248 rows, 248 distinct keys.

`scripts/audit_o1.py` now covers the first four classes of defect. Run against the v1.10 file it reports
4 blockers and 162 SHOULD-grade findings; against v1.10.1 it reports none.

## Reasoning with data

Materialised with `scripts/materialize_social_abox.py` and `scripts/materialize_press_abox.py`
(the same rules as the `M-Social-*` and `M-Press-*` mappings) and reasoned with HermiT
(`--include-indirect true`). Entailed class memberships that no data row asserts:

| Class | Synthetic items only | With the 295 verified real offers | Why |
|---|---:|---:|---|
| `:JobOffer` | 600 | 895 | `:DirectRecruitmentPost ⊑ :JobOffer`; the 295 real offers add directly |
| `:RedFlag` | 2,479 | 2,797 | every signal class ⊑ `:SocialMediaRecruitmentSignal` ⊑ `:RedFlag` |
| `:SocialMediaItem` | 1,500 | 1,500 | posts and comments ⊑ `:SocialMediaItem` |
| `:PressArticle` | 0 | 274 | `:PressArticle ⊑ :EvidenceSource`, one per documented article |

The existential axiom on `:DirectRecruitmentPost` (anonymous `:ForcedCriminalityScheme`
witness) is not visible as a class assertion; it is exercised by `queries/Q33` under Ontop.

## ROBOT report: why the remaining findings are not defects

`robot report` applies OBO Foundry conventions. Remaining items (`robot_report.tsv`):

- `multiple_labels` (398): every term has an English and a Spanish `rdfs:label`. Bilingual
  labels are intentional (Mexico and Latin America are the domain).
- `missing_definition` (281, that is every term): OBO expects `IAO:0000115`; RATR-O uses
  `rdfs:comment`, which every term now carries.
- `missing_superclass` (30, INFO): top-level classes by design.

Fixed from the report in earlier versions: missing ontology description (`dc:description` added)
and a stray untyped subject `:hutro` (removed; the HUTRO link remains on the ontology header).

## Reproduce

```bash
ROBOT="java -jar robot.jar"
$ROBOT validate-profile --profile QL --input ontology/ratr-o.ttl --output docs/validation/robot_profile_QL.txt
$ROBOT reason --reasoner hermit --input ontology/ratr-o.ttl --dump-unsatisfiable unsat.txt --output /tmp/r.ttl
.venv/bin/python scripts/materialize_social_abox.py /tmp/abox_social.ttl
.venv/bin/python scripts/materialize_press_abox.py /tmp/abox_press.ttl
$ROBOT merge --input ontology/ratr-o.ttl --input /tmp/abox_social.ttl --input /tmp/abox_press.ttl \
  reason --reasoner hermit --axiom-generators "ClassAssertion" --include-indirect true \
  --output /tmp/abox_inferred.ttl
$ROBOT report --input ontology/ratr-o.ttl --fail-on none --output docs/validation/robot_report.tsv
.venv/bin/python scripts/audit_o1.py
```

## Not yet done

- OOPS! (ontology pitfall scanner) and FOOPS! (FAIR assessment): web services, pending.
- Query answering under Ontop (O3): pending Docker.
- Zenodo DOI: `.zenodo.json` ready, not yet deposited.
