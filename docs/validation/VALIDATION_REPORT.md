# RATR-O validation with standard tools (v1.9.1, 3 Nov 2026)

Tools: ROBOT 1.9.11 (OWL API profile checker, HermiT reasoner, ROBOT report) on OpenJDK 27.0.1.
Before v1.9.1 the ontology was checked only by the repository script `scripts/audit_o1.py`.

## Results

| Check | Tool | Result |
|---|---|---|
| OWL 2 QL profile | `robot validate-profile --profile QL` | **In profile** (`robot_profile_QL.txt`) |
| TBox consistency | `robot reason --reasoner hermit` | **Consistent** |
| Unsatisfiable classes | HermiT, `--dump-unsatisfiable` | **None** (no dump file produced) |
| TBox + 1,500 synthetic items (24,037 triples) | `robot merge` + HermiT | **Consistent** |
| TBox v1.10 + 352 real offers + 1,500 synthetic items (50,600 triples) | `robot merge` + HermiT | **Consistent** |
| Quality report | `robot report` | OBO-convention findings only (see below) |

## What the standard profile checker found that our script missed

The first run of the OWL API checker on v1.9 reported the ontology **not in OWL 2 QL**:

1. **16 data-property ranges outside the OWL 2 QL datatype map**: `xsd:date` (6), `xsd:gYear` (4),
   `xsd:boolean` (6). OWL 2 QL admits a restricted datatype map (OWL 2 Profiles, section 3.2) that
   includes `xsd:dateTime`, `xsd:integer`, `xsd:decimal` and `xsd:string`, but not these three.
   **Fix:** ranges set to `rdfs:Literal`, each property annotated with its intended datatype;
   the mapping layer keeps emitting `xsd:date`, `xsd:gYear` and `xsd:boolean` literals.
   This is the same design rule as the QCA conjunctions (`docs/MODULE_SOCIAL_RECRUITMENT.md`):
   what the profile cannot express is enforced in the mapping, not dropped.
2. **Undeclared annotation properties** (`dc:title`, `dc:creator`, `dct:*`, `skos:note`,
   `skos:closeMatch`). No logical effect. **Fix:** declared as `owl:AnnotationProperty`.

`scripts/audit_o1.py` now includes the datatype-map check; run against the original v1.9 file
it detects the same 16 ranges.

## Reasoning with data

Materialised with `scripts/materialize_social_abox.py` (same rules as the `M-Social-*`
mappings) and reasoned with HermiT (`--include-indirect true`). Entailed class memberships that
no data row asserts:

| Class | Entailed members | Why |
|---|---:|---|
| `:JobOffer` | 600 | `:DirectRecruitmentPost ⊑ :JobOffer` |
| `:RedFlag` | 2,479 | every signal class ⊑ `:SocialMediaRecruitmentSignal` ⊑ `:RedFlag` |
| `:SocialMediaItem` | 1,500 | posts and comments ⊑ `:SocialMediaItem` |

The existential axiom on `:DirectRecruitmentPost` (anonymous `:ForcedCriminalityScheme`
witness) is not visible as a class assertion; it is exercised by `queries/Q33` under Ontop.

## ROBOT report: why the remaining findings are not defects

`robot report` applies OBO Foundry conventions. Remaining items (`robot_report.tsv`):

- `multiple_labels` (372): every term has an English and a Spanish `rdfs:label`. Bilingual
  labels are intentional (Mexico and Latin America are the domain).
- `missing_definition` (268): OBO expects `IAO:0000115`; RATR-O uses `rdfs:comment`.
- `missing_superclass` (30, INFO): top-level classes by design.

Fixed from the report: missing ontology description (`dc:description` added) and a stray
untyped subject `:hutro` (removed; the HUTRO link remains on the ontology header).

## Reproduce

```bash
ROBOT="java -jar robot.jar"
$ROBOT validate-profile --profile QL --input ontology/ratr-o.ttl --output docs/validation/robot_profile_QL.txt
$ROBOT reason --reasoner hermit --input ontology/ratr-o.ttl --dump-unsatisfiable unsat.txt --output /tmp/r.ttl
.venv/bin/python scripts/materialize_social_abox.py /tmp/abox.ttl
$ROBOT merge --input ontology/ratr-o.ttl --input /tmp/abox.ttl reason --reasoner hermit \
  --axiom-generators "ClassAssertion" --include-indirect true --output /tmp/abox_inferred.ttl
$ROBOT report --input ontology/ratr-o.ttl --fail-on none --output docs/validation/robot_report.tsv
```

## Not yet done

- OOPS! (ontology pitfall scanner) and FOOPS! (FAIR assessment): web services, pending.
- Query answering under Ontop (O3): pending Docker.
