# RATR-O — Competency Questions

**Methodology:** Competency questions (CQs) are the standard instrument for ontology requirements and evaluation in knowledge engineering. The approach was formalised by Uschold and Gruninger (*Ontologies: Principles, Methods and Applications*, Knowledge Engineering Review, 1996) and is now canonical in any serious OWL or DL-Lite deployment. Each CQ is a natural-language question that the domain expert (here: Ramona AI) explicitly wants the ontology to answer. A SPARQL query over the Virtual Knowledge Graph must materialise the answer for the ontology to claim coverage of the CQ.

This document lists 26 competency questions covering RATR-O v1.6.1 and maps each to the SPARQL query (`queries/Q1..Q30`) that answers it.

---

## Group A — Operational questions (Ramona AI product)

These are the questions Ramona's analysts work on day to day. The VKG must answer them in real time over the operational Postgres.

### CQ1. Which platforms host the most high-risk offers this quarter?
**Answers:** `Q1_highrisk_by_platform.rq`.
**Why it matters:** platform-level intervention. If Marketplace hosts 60% of fraudulent offers, Ramona prioritises monitoring there.
**Ontology machinery exercised:** `:JobOffer :postedVia :Platform`, `:JobOffer :hasRiskClassification`.

### CQ2. Which recruiters post offers in multiple countries?
**Answers:** `Q2_multicountry_recruiters.rq`.
**Why it matters:** cross-border operations are a strong signal of organised trafficking rather than local fraud.
**Ontology machinery exercised:** `:Recruiter :recruiterCountry :Country`, `:JobOffer :offeredByRecruiter`.

### CQ3. Which offers match at least one documented survivor-testimony pattern?
**Answers:** `Q3_pattern_matches.rq`.
**Why it matters:** bridges operational data to documented public cases.
**Ontology machinery exercised:** `:JobOffer :matchesPattern :SurvivorTestimonyPattern :derivedFrom :EvidenceSource`.

### CQ4. Which offers lie on a known trafficking route but have not been classified?
**Answers:** `Q4_route_unclassified.rq`.
**Why it matters:** queues cases for analyst review.
**Ontology machinery exercised:** `:JobOffer :associatedWithRoute`, absence of `:hasRiskClassification`.

### CQ5. Which offers match the CJNG post-Rancho-Izaguirre pattern?
**Answers:** `Q5_cjng_salary_pattern.rq`.
**Why it matters:** immediate alert on a specific documented recruitment scheme.
**Ontology machinery exercised:** `:JobOffer :offeredSalaryMXN`, `:JobOffer :offeredRole`.

### CQ6. Which offers bundle the Edith Guadalupe patterns (come alone, no ID, multi-use building)?
**Answers:** `Q6_edith_pattern_bundle.rq`.
**Why it matters:** the central Type-B cohort and the canonical credible-lethal signal.
**Ontology machinery exercised:** multiple `:matchesPattern` on the same offer, `:CredibleLethalPattern` subclass.

### CQ7. How does the Messenger-to-WhatsApp funnel correlate with personal-data filtering?
**Answers:** `Q7_messenger_whatsapp_funnel.rq`.
**Why it matters:** policy signal for platform cooperation.
**Ontology machinery exercised:** conjunction of two patterns on one offer.

### CQ8. How many confirmed-fraudulent offers exist per country, and what is the average risk score?
**Answers:** `Q8_fraudulent_counts_by_country.rq`.
**Why it matters:** country-level dashboard.
**Ontology machinery exercised:** `:RiskClassification :riskLevel "fraudulent"`, `:JobOffer :inCountry`.

## Group B — Observatory questions (cross-source statistics)

These exercise the VKG over the three data sources: Ramona operational + CTDC synthetic + press observatory. The same SPARQL query runs transparently over all three.

### CQ9. How many CTDC victims per country of exploitation and by exploitation type?
**Answers:** `Q9_ctdc_exploitation_by_country.rq`.
**Why it matters:** baseline global victim distribution.
**Ontology machinery exercised:** `:Victim :inCountry`, `:Victim :victimOfExploitation`.

### CQ10. Which press-documented cases show Type B patterns but no Type A flags?
**Answers:** `Q10_type_b_only_cases.rq`.
**Why it matters:** the central observatory statistic (9.9× ratio).
**Ontology machinery exercised:** `:CredibleLethalPattern` + `NOT EXISTS :ClassicRedFlagPattern`.

### CQ11. What is the distribution of first-contact communication tool across all sources?
**Answers:** `Q11_recruitment_channels_distribution.rq`.
**Why it matters:** tells us which messaging platforms are the dominant vector.
**Ontology machinery exercised:** `:Victim :contactedThrough :CommunicationTool`.

### CQ12. How are victims distributed across age group, gender and exploitation type?
**Answers:** `Q12_cross_source_age_gender.rq`.
**Why it matters:** demographic baseline for targeted intervention.
**Ontology machinery exercised:** three-way cross `:AgeGroup` × `:Gender` × `:TypeOfExploitation`.

### CQ13. Which means-of-control profile dominates each exploitation type?
**Answers:** `Q13_means_of_control_stack.rq`.
**Why it matters:** informs legal framing (e.g., whether a case fits Palermo's "means" element).
**Ontology machinery exercised:** `:Victim :hasMeansOfControl`.

### CQ14. In Mexico, how many victims are press-documented vs CTDC-registered?
**Answers:** `Q14_mexico_press_vs_ctdc.rq`.
**Why it matters:** measures visibility gap between official registration and public press. Policy-relevant.
**Ontology machinery exercised:** `:Victim :derivedFrom :EvidenceSource`, cross-datasource federation.

## Group C — FraudScheme questions (the v1.2-v1.6 taxonomy)

These only exist because RATR-O introduced a named FraudScheme taxonomy. They validate that the taxonomy generates actionable questions, not abstract categories.

### CQ15. In which countries is each FraudScheme attested?
**Answers:** `Q15_fraudscheme_by_country.rq`.
**Why it matters:** geographic map for each scheme. InPersonLureScheme clusters in MX-CDMX; OrganRemovalRecruitmentScheme has different geography.
**Ontology machinery exercised:** `:exhibitsFraudScheme`, `:inCountry`.

### CQ16. Do the TIP events we observe cover the three Palermo elements (Action × Means × Purpose)?
**Answers:** `Q16_palermo_triad_coverage.rq`.
**Why it matters:** compliance with Palermo Protocol legal framework.
**Ontology machinery exercised:** `:TIPEvent`, `:tipEventHasAction`, `:tipEventHasMeans`, `:tipEventHasPurpose`.

### CQ17. Which communication tool does each FraudScheme prefer?
**Answers:** `Q17_scheme_vs_tool_heatmap.rq`.
**Why it matters:** operational — if OrganRemoval uses mostly classifieds but MLM uses mostly Instagram, moderation priorities differ.
**Ontology machinery exercised:** `:victimOfFraudScheme` × `:contactedThrough`.

### CQ18. What age-gender profile is the most common target of each FraudScheme?
**Answers:** `Q18_age_gender_per_scheme.rq`.
**Why it matters:** personalised prevention messaging.
**Ontology machinery exercised:** three-way join across FraudScheme × AgeGroup × Gender.

### CQ19. Which press outlets most frequently document each FraudScheme?
**Answers:** `Q19_outlets_by_scheme.rq`.
**Why it matters:** media partnerships and validation cross-checks.
**Ontology machinery exercised:** `:evidencedByPressArticle`, `:sourceOutlet`.

### CQ20. In each country, what is the Type-B-only to Type-A-only ratio?
**Answers:** `Q20_type_b_over_a_by_country.rq`.
**Why it matters:** disaggregates the 9.9× global statistic.
**Ontology machinery exercised:** dual subclass filter and negation.

## Group D — Pattern-centric questions (network analytics)

### CQ21. Which pattern pairs co-occur in the same article?
**Answers:** `Q21_pattern_cooccurrence.rq`.
**Why it matters:** identifies pattern bundles that are the signature of specific schemes.
**Ontology machinery exercised:** two `:matchesPattern` on the same offer, with filter on ordering.

### CQ22. Does each CTDC recruitment-method class predict a dominant exploitation type?
**Answers:** `Q22_recruitment_x_exploitation.rq`.
**Why it matters:** tests correlations that the literature suggests (e.g., intimate-partner recruitment → sexual exploitation).
**Ontology machinery exercised:** CTDC-scoped join `:recruitedVia` × `:victimOfExploitation`.

### CQ23. Which FraudSchemes are attested to use WhatsApp as first contact?
**Answers:** `Q23_whatsapp_funnel_schemes.rq`.
**Why it matters:** feeds a Meta-platform-cooperation request.
**Ontology machinery exercised:** single-tool filter across all schemes.

### CQ24. Which trafficking routes have press attestation but no CTDC coverage yet?
**Answers:** `Q24_new_routes_from_press.rq`.
**Why it matters:** early-warning capability. A route that press documents but CTDC hasn't seen is a signal of an emerging or newly-surfacing corridor.
**Ontology machinery exercised:** `:associatedWithRoute` with `FILTER NOT EXISTS` against CTDC-derived routes.

### CQ25. What is the annual trend of victim registration in CTDC 2002-2023?
**Answers:** `Q25_trend_by_year.rq`.
**Why it matters:** macro trend for the Discussion section of the paper.
**Ontology machinery exercised:** `:yearOfRegistration` aggregation.

### CQ26. Which means-of-control pairs co-occur most often in CTDC victims?
**Answers:** `Q26_means_of_control_network.rq`.
**Why it matters:** input for a control-network visualization in the paper.
**Ontology machinery exercised:** self-join on `:hasMeansOfControl`.

## Coverage summary

| CQ group | Questions | Answered by |
|---|---:|---|
| A. Operational | 8 (CQ1-CQ8) | Q1-Q8 |
| B. Observatory | 6 (CQ9-CQ14) | Q9-Q14 |
| C. FraudScheme | 6 (CQ15-CQ20) | Q15-Q20 |
| D. Pattern and trend | 6 (CQ21-CQ26) | Q21-Q26 |
| **Total** | **26 CQs** | **26 SPARQL queries** |

Four additional SPARQL queries exist (`Q27` vulnerability × exploitation, `Q28` cross-border + press, `Q29` Edith cohort explicit, `Q30` schemes attested in both sources). They are not required to answer a pre-registered CQ but serve as internal validation and cross-checks. In total the repository ships 30 SPARQL queries against 26 competency questions, a 1.15× coverage ratio.

## What RATR-O cannot answer (honest boundary)

The ontology does not commit to answering:

- **Temporal causation.** "Did exposure to X precede Y?" requires an event calculus not present in DL-Lite.
- **Monetary amounts of illicit financial flows.** RATR-O models `offeredSalaryMXN` but not the financial flows of the traffickers themselves.
- **Real-time social-network graph.** The observatory snapshots the network; it does not compute live graph algorithms.
- **Identity of any individual victim, recruiter, or survivor.** By design, to preserve privacy.
- **Predictive forecasting.** The ontology is descriptive, not predictive. A companion ML pipeline could be layered on top but is out of scope for v1.6.1.

Stating these boundaries explicitly is itself a rigor signal — the ontology claims only what it delivers.

## Reference

Uschold, M. and Gruninger, M. (1996). Ontologies: Principles, Methods and Applications. *Knowledge Engineering Review*, 11(2), 93–136.
