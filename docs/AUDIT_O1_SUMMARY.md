# RATR-O: validation summary

Objective 1 of the Dialogue Residency at TU Wien is a domain ontology in OWL 2 QL covering job offers,
employers, recruiters, candidates, trafficking red flags, geographic routes, platforms and risk
classifications. The current version is 1.10.6.

| | |
| --- | --- |
| Size | 114 classes, 69 object properties, 103 datatype properties |
| Profile | In OWL 2 QL under the OWL API checker (ROBOT 1.9.11), as Turtle and as RDF/XML |
| Consistency | Consistent under HermiT, alone and together with its data |
| Terms | An English and a Spanish label and a definition on every term |
| Mappings | 204 assertions, Ontop native and W3C R2RML, which produce the same graph |
| Queries | 41 reference queries for 37 competency questions; all execute |
| Alignments | HUTRO by verified concept IRI; Palermo Protocol, ICS-TIP, UNODC GLOTIP |

The full report, with how each check was run and how to reproduce it, is
[`validation/VALIDATION_REPORT.md`](validation/VALIDATION_REPORT.md). The execution of the queries is
[`validation/QUERY_EXECUTION_REPORT.md`](validation/QUERY_EXECUTION_REPORT.md), and the class diagrams
are in [`diagrams/`](diagrams/).
