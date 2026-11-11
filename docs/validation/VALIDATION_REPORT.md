# RATR-O v1.10.6: validation

Tools: ROBOT 1.9.11 (the OWL API profile checker and the HermiT reasoner) on OpenJDK, rdflib 7.6, and
the scripts in `scripts/`.

## The ontology

| Check | How | Result |
| --- | --- | --- |
| OWL 2 QL profile, Turtle | `robot validate-profile --profile QL` | In profile (`robot_profile_QL.txt`) |
| OWL 2 QL profile, RDF/XML | same | In profile |
| Consistency | `robot reason --reasoner hermit` | Consistent |
| Unsatisfiable classes | HermiT, `--dump-unsatisfiable` | None |
| Labels | every class and property | An English and a Spanish `rdfs:label` on all 286 terms |
| Definitions | every class and property | An `rdfs:comment` on all 286 terms |
| Domains and ranges | every property | A range on all 172 properties; a domain on 171. `:hasEvidenceSource` has none by design |
| Structure, naming, vocabulary closure, datatypes | `scripts/audit_o1.py` | No findings (`../AUDIT_O1.md`) |
| Serialisations | `ratr-o.ttl`, `.rdf`, `.jsonld`, `.nt` | Isomorphic, 1,722 triples each |

Size: 114 classes, 69 object properties, 103 datatype properties, one named individual.

`robot report` applies the conventions of the OBO Foundry, which RATR-O does not follow in two respects:
it gives every term two `rdfs:label` values, one per language, where OBO expects one, and it writes
definitions as `rdfs:comment` where OBO expects `IAO:0000115`.

## The ontology with data

| Check | How | Result |
| --- | --- | --- |
| Seed files | `db/01` to `db/14` loaded in order | All load |
| Mappings | 173 assertions in `mappings/ramona.obda` executed | 75,259 triples over the seeds |
| R2RML | `mappings/ramona.r2rml.ttl` executed following the W3C recommendation | The same 75,259 triples |
| Consistency with the seeds | TBox and ABox merged, HermiT | Consistent, 88,488 triples |
| CTDC load | `scripts/ingest_ctdc.py` over the 257,969 records of the release | Loads with foreign keys enforced |
| Consistency with CTDC victims | seeds plus one victim in forty (6,449), HermiT | Consistent, 167,887 triples |
| R2RML with CTDC victims | as above | The same 142,213 ABox triples as the native mapping |
| Domain and range typing | `scripts/offline_vkg/check_domain_range.py`, both data states | No individual is typed outside the hierarchy of its asserted class |
| Reference queries | 40 queries, both data states | All execute; see `QUERY_EXECUTION_REPORT.md` |

## Alignments and citations

- The eight `skos:closeMatch` alignments to HUTRO point at the concept IRIs BioPortal reports, each
  opened in the BioPortal concept browser on 10 November 2026 and found under the expected preferred
  label. See `../HUTRO_vs_RATRO_comparison.md`.
- The external documents the ontology cites were requested on 10 November 2026. Two pages of Mexican
  state governments were unavailable that day and are cited together with their Internet Archive
  snapshots.

## Publication

- `https://w3id.org/ratr-o` redirects to the Turtle for `Accept: text/turtle` and to the HTML
  documentation otherwise. A change to the redirect rules that also serves RDF/XML, JSON-LD and
  N-Triples by content negotiation is submitted to w3id.org (perma-id/w3id.org#7140). The four files
  are at `https://teamdaniela-png.github.io/ramona-vkg/ontology/`.
- `https://w3id.org/ratr-o/<version>` resolves to the Turtle of that version.

## Reproduce

```bash
ROBOT="java -jar robot.jar"
$ROBOT validate-profile --profile QL --input ontology/ratr-o.ttl --output docs/validation/robot_profile_QL.txt
$ROBOT reason --reasoner hermit --input ontology/ratr-o.ttl --dump-unsatisfiable unsat.txt --output /tmp/r.ttl
python scripts/audit_o1.py
scripts/offline_vkg/run_all.sh /tmp/vkg
$ROBOT merge --input ontology/ratr-o.ttl --input /tmp/vkg/abox_obda.ttl reason --reasoner hermit --output /tmp/merged.ttl
```

## Scope

Objective 1 is the ontology. Two things belong to the later objectives and are stated here so that
nobody looks for them in this delivery:

- The Docker stack that serves the VKG through Ontop (Objective 3) is configured in
  `docker-compose.yml` and has not been run as part of this validation. What it would serve was
  validated with `scripts/offline_vkg/`.
- The CTDC Global Synthetic Dataset is not redistributed in the repository. `db/` creates the victim
  tables and `scripts/ingest_ctdc.py` fills them from a downloaded copy.
