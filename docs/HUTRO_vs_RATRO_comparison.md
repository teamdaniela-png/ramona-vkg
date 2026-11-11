# RATR-O vs HUTRO — Formal comparative analysis

**Prepared for:** the Dialogue Residency at the Institute of Logic and Computation, TU Wien.
**RATR-O version:** 1.10.6 (11 November 2026).
**HUTRO version reviewed:** as published on BioPortal, upload date 22 April 2025, author Danial Zemchal Tesfahans, status Alpha.

An ontology for human trafficking already exists on BioPortal: HUTRO. This document says what RATR-O reuses from it, what it adds, and why it was not built as an extension of it.

---

## Executive summary

HUTRO and RATR-O are complementary, not overlapping. HUTRO covers a very specific corridor (Eritrean refugees trafficked into Ethiopia) with a thin SKOS vocabulary and no reasoning layer. RATR-O covers labour-recruitment fraud and trafficking in Latin America, uses the OWL 2 QL fragment, is bound to operational data via OBDA / R2RML, and ships with an audit trail, a demonstrator, and a dataset of 259k records. Eight generalisable concepts of HUTRO are reused in RATR-O through `skos:closeMatch`. All other concepts in RATR-O are new contributions.

## Side-by-side comparison

| Dimension | HUTRO | RATR-O v1.6.1 |
|---|---|---|
| **Author** | Danial Zemchal Tesfahans, Addis Ababa (Ethiopia) | Daniela Camberos, Ramona AI (Mexico), with Magdalena Ortiz TU Wien as proposed co-author |
| **Upload / version date** | 22 April 2025 | 22 April 2026 |
| **Status declared on BioPortal** | Alpha | Not applicable (this is the ontology's own repository); self-audited twice, the second time before delivery, with zero blockers and zero SHOULD-grade findings remaining |
| **Purpose declared** | "to investigate the trend of human trafficking of Eritrean refugees in Ethiopia" | "detection of fraudulent job offers, labour-recruitment fraud, and human-trafficking recruitment patterns in Latin America" |
| **Geographic scope** | Horn of Africa (Eritrea to Ethiopia corridor, with ransom-transaction focus) | Latin America, with specific attention to Mexico; alignment to the global ISO 3166-1 catalogue (248 countries, keyed on the alpha-3 code, which is the canonical country key of the VKG) |
| **Formal language** | SKOS ConceptScheme | OWL 2 QL (DL-Lite fragment, Calvanese et al. 2007) |
| **Reasoning layer** | None (SKOS does not provide logical inference) | Query rewriting under DL-Lite guarantees (Xiao et al. 2019) |
| **Profile validation** | Not applicable | Validated (no disallowed axioms in the OWL 2 QL profile) |
| **Classes / top-level concepts** | not re-verified: BioPortal is served behind a bot challenge, so the metrics page could not be opened on 10 November 2026. The first version of this document recorded 37 SKOS concepts | 114 OWL classes |
| **Object properties** | Default SKOS (broader, narrower, related) | 66 domain-specific object properties |
| **Datatype properties** | None (SKOS conceptScheme) | 101 domain-specific datatype properties |
| **Named subclasses of "trafficking recruitment scheme"** | 0 (HUTRO does not factor recruitment into named schemes) | 26 FraudSchemes with official-source citations |
| **Alignment with Palermo Protocol** | Not formalised | `:PalermoAction`, `:PalermoMeans`, `:PalermoPurpose` with verbatim sub-concepts |
| **Alignment with ICS-TIP** | Not formalised | `rdfs:seeAlso` to ICS-TIP v4 PDF and `:TIPEvent` central unit. `:TIPEvent` is conceptual only: the demonstrator database has no TIP-event table, so no mapping populates it |
| **Alignment with UNODC GLOTIP** | Not formalised | `rdfs:seeAlso` on `:Victim` |
| **Operational database binding (OBDA or R2RML)** | None | Ontop OBDA mapping + W3C R2RML mapping both shipped |
| **Connected SPARQL demonstrator** | None | Dockerised Ontop stack and 40 reference queries answering 36 competency questions |
| **Connected open dataset** | None | 257,969 CTDC records, 2,379 case-relevant press articles, and 295 verified real offer descriptions |
| **Provenance mechanism for each domain claim** | `inScheme` only | `:hasEvidenceSource :EvidenceSource`, with `:derivedFrom` for patterns and `:offerDocumentedIn` for offers |
| **Documentation** | BioPortal class tree | HTML docs (100+ KB), dataset statistics, audit report, rigor statement, comparison table, competency questions, GitHub Pages |
| **Reproducibility** | Not applicable (static vocabulary) | Every statistic reproducible by running committed scripts |
| **Licence** | Not explicitly stated | CC BY 4.0 (ontology), Apache 2.0 (code) |

## Conceptual reuse from HUTRO to RATR-O

RATR-O records a close match to eight HUTRO concepts. "Close match" is the right relation when two
concepts are similar enough to be interoperable in many applications but are not identical in scope.

**How the alignment is recorded.** Each of the eight is asserted as `skos:closeMatch` against the
concept IRI BioPortal reports for it: `https://bioportal.bioontology.org/ontologies/HUTRO` followed
directly by the concept's local name, with no separating slash or hash. HUTRO's submission metadata
declares the namespace `http://www.example.com`; the concatenated form is the one BioPortal serves and
resolves, so it is the one used. Each IRI was opened in the BioPortal concept browser on 10 November
2026 and found under the expected preferred label. Two local names are reproduced exactly as HUTRO
writes them: `recuritment_method` and `smuggler_trafficker_communication_tools`.

HUTRO's concepts are `skos:Concept` instances that also carry `owl:NamedIndividual`, so each match is
an annotation assertion on the RATR-O class rather than an OWL object-property assertion, which keeps
the file inside the OWL 2 QL profile. The reference tables in `db/04_schema_extension_v1.sql` carry
both the label, in `hutro_concept_label`, and the IRI, in `hutro_concept_iri`.

For each:

| RATR-O class | HUTRO concept (label) | What is reused | What differs |
|---|---|---|---|
| `:RecruitmentMethod` | "recruitment method" | the notion of categorising how a victim is initially approached | RATR-O uses 13 controlled values (social_media, classifieds, in_person_street, labour_broker, etc.), covering the online-recruitment context that HUTRO does not represent |
| `:TypeOfExploitation` | "type of exploitation" | the broad distinction between labour, sexual, and other exploitation | RATR-O adds ISIC-aligned labour subtypes (agriculture, construction, hospitality, domestic) and explicit `:forced_criminality`, `:organ_removal` |
| `:VulnerabilityFactor` | "vulnerability factor" | the idea that a victim's socioeconomic context increases exposure | RATR-O uses ten codes including `migrant_status`, `minor`, `indigenous`, `single_parent` that reflect Latin-American victimology literature |
| `:TransportationMeans` | "transportation means" | the notion that trafficking routes use attested transport modes | RATR-O uses eight codes plus `unknown`; matches the CTDC vocabulary |
| `:CommunicationTool` | "smuggler and trafficker communication tools" | that first-contact tool is a first-class entity | RATR-O adds `whatsapp`, `messenger`, `telegram` as primary categories because those are the dominant tools in the Latin-American online-recruitment context |
| `:DocumentationType` | "documentation type" | types of identity and travel documents demanded or withheld | RATR-O adds `:FalseDocumentation` as an explicit subclass and aligns with Palermo `:MeansFraud` |
| `:FalseDocumentation` | "false documentation" | identical conceptually | same semantic, adopted verbatim |
| `:TraffickingRoute` | "trafficking transit places" | the notion of routes with transit stages | RATR-O structures routes with explicit origin and destination countries, victim counts, year ranges |

## What RATR-O introduces that HUTRO does not have

The following are original contributions of RATR-O with no counterpart in HUTRO. Each is either a Ramona-specific operational class, a Latin-America-specific cultural pattern, or a general advance that HUTRO's SKOS scope cannot express.

### Operational layer (Ramona product data)
- `:JobOffer`, `:Submission`, `:Candidate`, `:OnlineRecruitmentChannel`.
- `:RiskClassification` with three risk axes (`:FraudRisk`, `:ExploitationRisk`, `:TraffickingRisk`).
- `:RedFlag` with the seven canonical Ramona flags and the dual detection-track classification (Type A / Type B).

### Cultural-context layer (Latin American recruitment)
- `:SurvivorTestimonyPattern` and five subclasses (ClassicRedFlagPattern, CredibleLethalPattern, CommunicationPattern, RecruitmentPattern, ExploitationPattern).
- 24 `:FraudScheme` subclasses named after attested operational patterns, each with at least one authoritative citation. The nine most specifically Latin-American are InPersonLureScheme (Edith Guadalupe archetype), ForcedCriminalityScheme (CJNG Rancho-Izaguirre archetype), VisaFraudScheme (nanny-to-Canada archetype), ModelingAgencyScheme (Mexico-Colombia corridor), CallCenterScamScheme (Mexico-Costa Rica corridor), FakeMaquilaScheme (border-Mexico archetype), GigEconomyFakeDriverScheme, OnlineInfluencerSalesScheme, CentralAmericanMigrantLabourScheme.

### Formal-reasoning and framework-alignment layer
- Palermo Protocol Article 3 triad as OWL classes (`:PalermoAction`, `:PalermoMeans`, `:PalermoPurpose`) with verbatim sub-concepts.
- ICS-TIP's `:TIPEvent` as the central unit of classification.
- UNODC GLOTIP cross-reference for macro statistics.

### Data-engineering layer (not present in any SKOS vocabulary)
- Observatory measurement properties: `:observedCount`, `:pctOfCases`, `:dominanceBucketValue`, `:routeVictimCount`, `:routeEarliestYear`, `:routeLatestYear`.
- Provenance properties: `:hasEvidenceSource`, `:derivedFrom`, `:offerDocumentedIn`, `:evidenceFor`, `:evidenceStrength`, `:evidenceArchivedUrl`.
- Evidence-source hierarchy: `:EvidenceSource`, `:PressArticle`, `:OpenDatasetRecord`.

## What the two ontologies mean to say, in one sentence each

**HUTRO says:** "Eritrean refugees trafficked into Ethiopia are held for ransom paid through these channels, and this is the vocabulary for describing the ransom event."

**RATR-O says:** "In Latin America, recruitment-based fraud and trafficking take these 24 named operational forms; this is a Virtual Knowledge Graph that makes every fact about an offer or victim traceable to its public source, auditable in DL-Lite, and queryable at scale via SPARQL over 259,000 records."

## Why RATR-O did not simply extend HUTRO

Three reasons:

1. **Domain fit.** HUTRO's domain is abduction-with-ransom in the Horn of Africa. RATR-O's domain is online recruitment fraud in Latin America. Extending HUTRO would have forced RATR-O into a SKOS vocabulary that cannot express the things Ramona needs to say (risk classification, survivor-testimony patterns, operational data binding).

2. **Formal expressiveness.** SKOS does not offer subclass reasoning, domain and range axioms, or compatibility with OBDA tooling like Ontop. OWL 2 QL does. Since the project requires a Virtual Knowledge Graph running SPARQL over Postgres, OWL 2 QL is the right choice per Xiao, Ding, Cogrel and Calvanese (2019).

3. **Respect for the source.** Overwriting HUTRO as a de-facto replacement would have been uncollegial toward the HUTRO author. A close match is the canonical way to acknowledge conceptual kinship without claiming authority over the other author's vocabulary.

## References

Calvanese, D., De Giacomo, G., Lembo, D., Lenzerini, M. and Rosati, R. (2007). Tractable Reasoning and Efficient Query Answering in Description Logics: The DL-Lite Family. *Journal of Automated Reasoning*, 39(3), 385-429.

Tesfahans, D. Z. (2025). *Human Trafficking Ontology (HUTRO).* BioPortal, 22 April 2025. URL: https://bioportal.bioontology.org/ontologies/HUTRO

Xiao, G., Ding, L., Cogrel, B. and Calvanese, D. (2019). Virtual Knowledge Graphs: An Overview of Systems and Use Cases. *Data Intelligence*, 1(3), 201-223.

---

Last updated: 22 April 2026.
