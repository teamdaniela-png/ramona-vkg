# Mapping coverage of the declared vocabulary

State on 13 November 2026, RATR-O v1.10.7, `mappings/ramona.obda` with 204 mappings. The published
`mappings/ramona.r2rml.ttl` was executed against the same seeds and produces the same 75,675 triples,
triple for triple, and the same 142,629 over the seeds plus a 1-in-40 sample of the CTDC victim records.
`docs/MAPPING_SPEC.md` has the identifier templates and the foreign keys.

| | Declared | Produced by a mapping | Not produced |
|---|---:|---:|---:|
| Classes | 114 | 79 | 35 |
| Object properties | 69 | 37 | 32 |
| Datatype properties | 103 | 72 | 31 |

The ontology is deliberately larger than the current mapping. A reviewer should be able to tell at
a glance which part of it the demonstrator actually populates, which is what this file is for.

## Why a term is not produced by a mapping

**1. It is an abstract superclass.** Its subclasses or instances are what the data carries.
Examples: `:Agent`, `:FraudScheme`, `:PalermoAction`, `:PalermoMeans`, `:PalermoPurpose`,
`:SocialMediaItem`, `:RiskClassification` subtrees.

**2. It is a controlled value loaded directly by a `db/` seed.** The named FraudScheme classes
are the main case: their exemplars live in `db/09_fraudscheme_examples.sql` (101 rows) and are
attached to offers there, not minted by a mapping assertion.

**3. The demonstrator database has no column for it.** The ontology models more than the
demonstrator schema records.

- `:TIPEvent` and all five `:tipEvent*` properties. ICS-TIP's central unit is modelled but there
  is no TIP-event table, so nothing populates it.
- The Palermo triad links on offers and schemes (`:exhibitsAction`, `:exhibitsMeans`,
  `:exhibitsPurpose`, `:schemePalermo*`). Asserting a Palermo element for a given offer is an
  interpretive step and the schema has no column that records that judgement.
- Route metadata beyond origin, destination, `known_since` and the victim count:
  `:routeEarliestYear`, `:routeLatestYear`, `:routeStopoverCountries`, `:routeIsTransnational`,
  `:routeUpdatedAt`, `:routeDominantExploitation`.
- Victim case and life-history fields: `:victimCaseOpenedAt`, `:victimCaseClosedAt`,
  `:victimMaritalStatus`, `:victimEducationLevel`, `:victimHasChildrenCount`,
  `:victimReferralSource`, `:victimPriorEmployment`.
- Offer fields Ramona's production system has but this schema does not: `:hasTitle`,
  `:offerIsActive`, `:offerLanguage`, `:offerScreenshotUrl`, `:offerFirstContactAt`,
  `:offerClassifierConfidence`.
- Bilingual risk explanations `:riskExplanationEn` / `:riskExplanationEs` (the schema has a single
  `explanation_text`).

## Full list of terms not produced by a mapping

Generated from the ontology and `mappings/ramona.obda` on 13 November 2026.

### Classes (35)

:Agent
:BeggingRingScheme
:ExploitationRisk
:FalseDocumentation
:FishingVesselLabourScheme
:ForcedChildMarriageScheme
:FraudRisk
:FraudScheme
:Harbouring
:MeansAbduction
:MeansAbuseOfPower
:MeansAbuseOfVulnerability
:MeansCoercion
:MeansDeception
:MeansFraud
:MeansPaymentOrBenefit
:MeansThreatOfForce
:OnlineRecruitmentChannel
:PalermoAction
:PalermoMeans
:PalermoPurpose
:PurposeForcedLabour
:PurposeOrganRemoval
:PurposeServitude
:PurposeSexualExploitation
:PurposeSlavery
:Receipt
:Recruitment
:ResearchReport
:SocialMediaItem
:SocialMediaRecruitmentSignal
:TIPEvent
:TraffickingRisk
:Transfer
:Transportation

### Object properties (32)

:candidateDefraudedBy
:commentsOn
:containsRedFlag
:evidenceFor
:exhibitsAction
:exhibitsMeans
:exhibitsPurpose
:hasRecruitmentMethod
:hostsOffer
:leadsToExploitation
:observedInCountry
:offers
:operatesIn
:platformModeratedBy
:recruitsFor
:routeDominantExploitation
:schemeExploitationType
:schemePalermoAction
:schemePalermoMeans
:schemePalermoPurpose
:schemePreferredTool
:schemeTargetsAgeGroup
:schemeTargetsGender
:schemeTypicalRoute
:tipEventHappenedIn
:tipEventHasAction
:tipEventHasMeans
:tipEventHasPurpose
:tipEventInvolves
:tipEventRegisteredBy
:victimOfFraudScheme
:victimOfOffer

### Datatype properties (31)

:evidenceAccessedOnline
:evidenceArchivedUrl
:evidenceStrength
:flagKeywordPattern
:hasTitle
:offerClassifierConfidence
:offerFirstContactAt
:offerIsActive
:offerLanguage
:offerScreenshotUrl
:patternRegex
:pctOfCases
:riskExplanationEn
:riskExplanationEs
:routeEarliestYear
:routeIsTransnational
:routeLatestYear
:routeStopoverCountries
:routeUpdatedAt
:schemeFirstAttestedYear
:schemeJurisdictionScope
:schemeNamedAfterCase
:sourceAccessedAt
:sourceLanguage
:victimCaseClosedAt
:victimCaseOpenedAt
:victimEducationLevel
:victimHasChildrenCount
:victimMaritalStatus
:victimPriorEmployment
:victimReferralSource

## Mapped but with no rows in the shipped seeds

Separate from coverage: some mappings are correct and execute, and return nothing over a clone of
the repository, because the tables they read are created by `db/` and populated by no seed file.

- `public.victim`, `victim_exploitation` and `victim_means_of_control`: loaded by
  `scripts/ingest_ctdc.py` from the CTDC Global Synthetic Dataset v2025, which this repository does
  not redistribute. With the release downloaded, `python scripts/ingest_ctdc.py --csv <file>` loads
  257,969 victim records, 189,096 exploitation rows and 276,562 means-of-control rows.
  `docs/validation/QUERY_EXECUTION_REPORT.md` gives the query results with them loaded.
- `victim.communication_tool_code` and `public.victim_vulnerability`: CTDC has no variable for
  either, so `M-Victim-CommunicationTool` and `M-Victim-Vulnerability` stay empty after the CTDC load.
  Only victim records derived from press articles by `scripts/ingest_press.py` would fill them.
- `public.evidence_source_extended` beyond the one CTDC dataset row: author and dataset-record
  annotations, and press sources in that registry. `db/13_offer_provenance.sql` types the press
  articles over `ramona.evidence_sources`, so `:PressArticle` is populated either way.

Five further pairs of mappings, `M-Press-Scheme-*` and `M-Press-SchemeType-*` for
`CallCenterScamScheme`, `GigEconomyFakeDriverScheme`, `ForeignLanguageTeacherScheme`,
`CentralAmericanMigrantLabourScheme` and `ConstructionLabourBondageScheme`, name real classes and
match no row: 15 of the 26 fraud schemes are attested in the verified press corpus and these five
are not among them.
