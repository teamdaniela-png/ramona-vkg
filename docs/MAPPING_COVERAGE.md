# Mapping coverage of the declared vocabulary

State on 10 November 2026, RATR-O v1.10.4, `mappings/ramona.obda` with 168 mappings. The published
`mappings/ramona.r2rml.ttl` was executed against the same seeds and produces the same 71,963 triples,
triple for triple.
Generated from `scripts/audit_o1.py` section 10, which reports the same counts as a NOTE.

| | Declared | Produced by a mapping | Not produced |
|---|---:|---:|---:|
| Classes | 114 | 70 | 44 |
| Object properties | 67 | 31 | 36 |
| Datatype properties | 101 | 69 | 32 |

The ontology is deliberately larger than the current mapping. A reviewer should be able to tell at
a glance which part of it the demonstrator actually populates, which is what this file is for.

## Why a term is not produced by a mapping

**1. It is an abstract superclass.** Its subclasses or instances are what the data carries.
Examples: `:Agent`, `:FraudScheme`, `:PalermoAction`, `:PalermoMeans`, `:PalermoPurpose`,
`:SocialMediaItem`, `:RiskClassification` subtrees.

**2. It is a controlled value loaded directly by a `db/` seed.** The named FraudScheme classes
are the main case: their exemplars live in `db/09_fraudscheme_examples.sql` (101 rows) and are
attached to offers there, not minted by a mapping assertion.

**3. The demonstrator database has no column for it.** These are the real gaps, and they are
honest ones: the ontology models more than Ramona's current schema records.

- `:TIPEvent` and all five `:tipEvent*` properties. ICS-TIP's central unit is modelled but there
  is no TIP-event table, so nothing populates it.
- The Palermo triad links on offers and schemes (`:exhibitsAction`, `:exhibitsMeans`,
  `:exhibitsPurpose`, `:schemePalermo*`). Asserting a Palermo element for a given offer is an
  interpretive step and the schema has no column that records that judgement.
- Route metadata beyond origin, destination and `known_since`: `:routeVictimCount`,
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

## Fixed on 10 November 2026

Five properties were declared and mappable from columns that already existed, and had simply never
been wired. They are mapped now: `:observedCount`, `:patternHasKind`, `:dominanceBucketValue`,
`:sourceAuthor`, `:datasetRecordId`. `:DominanceBucket` was an unconnected class (OOPS! P04); it is
now the range of the new `:hasDominanceBucket` and is minted by `M-DominanceBucket`.

## Full list of terms not produced by a mapping

Classes (44):

```
:Agent
:BeggingRingScheme
:ClassicRedFlagPattern
:CommunicationPattern
:CredibleLethalPattern
:DemographicProfile
:ExploitationPattern
:ExploitationRisk
:FalseDocumentation
:FishingVesselLabourScheme
:ForcedChildMarriageScheme
:FraudRisk
:FraudScheme
:GangRecruitmentSchoolsScheme
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
:OrganRemovalRecruitmentScheme
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
:RecruitmentPattern
:ResearchReport
:SocialMediaItem
:SocialMediaRecruitmentSignal
:SportsTalentScheme
:TIPEvent
:TraffickingRisk
:Transfer
:Transportation
```

Properties (68):

```
:candidateDefraudedBy
:commentsOn
:containsRedFlag
:evidenceAccessedOnline
:evidenceArchivedUrl
:evidenceFor
:evidenceStrength
:evidencedByPressArticle
:exhibitsAction
:exhibitsMeans
:exhibitsPurpose
:flagKeywordPattern
:hasDemographicProfile
:hasRecruitmentMethod
:hasTitle
:hostsOffer
:leadsToExploitation
:observedInCountry
:offerClassifierConfidence
:offerFirstContactAt
:offerIsActive
:offerLanguage
:offerScreenshotUrl
:offers
:operatesIn
:patternRegex
:pctOfCases
:platformModeratedBy
:recruitsFor
:riskExplanationEn
:riskExplanationEs
:routeDominantExploitation
:routeEarliestYear
:routeIsTransnational
:routeLatestYear
:routeStopoverCountries
:routeUpdatedAt
:routeVictimCount
:schemeExploitationType
:schemeFirstAttestedYear
:schemeJurisdictionScope
:schemeNamedAfterCase
:schemePalermoAction
:schemePalermoMeans
:schemePalermoPurpose
:schemePreferredTool
:schemeTargetsAgeGroup
:schemeTargetsGender
:schemeTypicalRoute
:sourceAccessedAt
:sourceLanguage
:tipEventHappenedIn
:tipEventHasAction
:tipEventHasMeans
:tipEventHasPurpose
:tipEventInvolves
:tipEventRegisteredBy
:transportedBy
:travelledWith
:victimCaseClosedAt
:victimCaseOpenedAt
:victimEducationLevel
:victimHasChildrenCount
:victimMaritalStatus
:victimOfFraudScheme
:victimOfOffer
:victimPriorEmployment
:victimReferralSource
```

## Mapped but with no rows in the shipped seeds

Separate from coverage: 18 mappings are correct and execute, and return nothing, because the
tables they read are created by `db/` and populated by no seed file.

- `ramona.victim` and its satellites `victim_exploitation`, `victim_means_of_control`,
  `victim_vulnerability`: loaded by `scripts/ingest_ctdc.py` from the CTDC v2025 release,
  which this repository does not redistribute. 15 mappings.
- `public.evidence_source_extended`: author, dataset-record and kind annotations over
  evidence sources, and the `:OpenDatasetRecord` registry. 3 mappings, including the one
  that types `:PressArticle` over that registry; `db/13_offer_provenance.sql` now types the
  press articles over `ramona.evidence_sources` instead, so `:PressArticle` is populated.

Five further mappings, `M-Press-Scheme-*` and `M-Press-SchemeType-*` for
`CallCenterScamScheme`, `GigEconomyFakeDriverScheme`, `ForeignLanguageTeacherScheme`,
`CentralAmericanMigrantLabourScheme` and `ConstructionLabourBondageScheme`, name real
classes and match no row: 15 of the 26 fraud schemes are attested in the verified press
corpus and these five are not among them.

`docs/validation/QUERY_EXECUTION_REPORT.md` lists which of the 40 reference queries each of
these gaps blocks.
