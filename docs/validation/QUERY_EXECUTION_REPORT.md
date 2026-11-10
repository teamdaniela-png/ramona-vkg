# RATR-O v1.10.5 — execution of the 40 reference queries

Run on 10 November 2026. Ontop needs Docker, which does not run on the machine this audit was
carried out on, so the queries were executed against a materialisation of the same mapping file:
`db/*.sql` loaded into SQLite with dialect translation only, `mappings/ramona.obda` executed row by
row to produce the ABox, and the TBox merged in with the subclass, subproperty and inverse closure
that Ontop applies at rewrite time. The published `mappings/ramona.r2rml.ttl` was executed the same
way and gives the identical graph.

Two data states were run:

- **Seeds only**: what a clone of the repository loads. 75,259 ABox triples, 88,488 with the TBox.
- **Seeds plus CTDC**: the same, after `scripts/ingest_ctdc.py` loaded the CTDC Global Synthetic
  Dataset v2025 (257,969 victim records, with foreign keys enforced). The queries ran over a
  1-in-40 systematic sample of the victims, 6,449 records, because the in-memory runner does not
  hold the full load: 142,213 ABox triples, 167,887 with the TBox, consistent under HermiT. Row
  counts in that column are over the sample; whether a query returns rows at all is not.

Three artefacts of the offline runner (rdflib 7.6.0), none of them a property of the queries:

- `?x IN (...)` evaluates to false for xsd:string-typed literals. The runner expands it. Affects Q1.
- A simple literal and an xsd:string-typed literal are not treated as the same term, which RDF 1.1
  requires and Ontop implements. The runner canonicalises both sides.
- A join with an empty subquery returns rows with the subquery's variables unbound, and
  `FILTER EXISTS` and a two-object pattern over all posts do not finish. Affects Q28, Q10 and Q31,
  whose answers were established in SQL instead and are the ones shown.

The committed queries and mappings were not changed for any of these.

## Results

| query | seeds only | seeds plus CTDC | note |
| --- | ---: | ---: | --- |
| `Q1_highrisk_by_platform` | 4 | 4 |  |
| `Q2_multicountry_recruiters` | 1 | 1 |  |
| `Q3_pattern_matches` | 54 | 54 |  |
| `Q4_route_unclassified` | 0 | 0 | see below |
| `Q5_cjng_salary_pattern` | 6 | 6 |  |
| `Q6_edith_pattern_bundle` | 2 | 2 |  |
| `Q7_messenger_whatsapp_funnel` | 2 | 2 |  |
| `Q8_fraudulent_counts_by_country` | 5 | 5 |  |
| `Q9_ctdc_exploitation_by_country` | 0 | 100 | needs the CTDC load |
| `Q10_type_b_only_cases` | 0 | 0 | see below |
| `Q11_recruitment_channels_distribution` | 0 | 0 | see below |
| `Q12_cross_source_age_gender` | 0 | 94 | needs the CTDC load |
| `Q13_means_of_control_stack` | 0 | 69 | needs the CTDC load |
| `Q14_mexico_press_vs_ctdc` | 0 | 1 | needs the CTDC load |
| `Q15_fraudscheme_by_country` | 33 | 33 |  |
| `Q16_palermo_triad_coverage` | 0 | 0 | see below |
| `Q17_scheme_vs_tool_heatmap` | 0 | 0 | see below |
| `Q18_age_gender_per_scheme` | 0 | 0 | see below |
| `Q19_outlets_by_scheme` | 129 | 129 |  |
| `Q20_type_b_over_a_by_country` | 3 | 3 |  |
| `Q21_pattern_cooccurrence` | 0 | 0 | see below |
| `Q22_recruitment_x_exploitation` | 0 | 23 | needs the CTDC load |
| `Q23_whatsapp_funnel_schemes` | 0 | 0 | see below |
| `Q24_new_routes_from_press` | 0 | 0 | see below |
| `Q25_trend_by_year` | 0 | 22 | needs the CTDC load |
| `Q26_means_of_control_network` | 0 | 25 | needs the CTDC load |
| `Q27_vulnerability_x_exploitation` | 0 | 0 | see below |
| `Q28_crossborder_with_press` | 0 | 0 | see below |
| `Q29_edith_cohort` | 0 | 0 | see below |
| `Q30_schemes_in_both_sources` | 15 | 15 |  |
| `Q31_tiktok_dm_plus_group_code` | 283 | 283 | computed in SQL |
| `Q32_minor_self_application` | 11 | 11 |  |
| `Q33_existential_forced_criminality` | 1 | 1 |  |
| `Q34_recruitment_stories` | 3 | 3 |  |
| `Q35_lexicon_false_positive_rate` | 13 | 13 |  |
| `Q36_who_is_targeted_mx` | 6 | 6 |  |
| `Q37_where_offers_mx` | 10 | 10 |  |
| `Q38_verbatim_wording` | 39 | 39 |  |
| `Q39_type_a_vs_type_b_real` | 3 | 3 |  |
| `Q40_criminal_recruitment_channels` | 3 | 3 |  |

**21 of the 40 queries return rows over the seeds alone, and 28 once the CTDC release is loaded.**
Of the 12 that return none in either state, one is a correct empty answer and the rest are named
below with what each one lacks.

## The queries that return no rows in either state

**`Q4_route_unclassified`** — Correct empty answer. All 17 offers on a documented route carry a classification.

**`Q10_type_b_only_cases`** — Needs victim records derived from press articles, which `scripts/ingest_press.py` writes and no seed ships. The CTDC load does not supply them: no CTDC victim has a press source. The offline runner does not finish its `FILTER EXISTS`; the answer was confirmed in SQL.

**`Q11_recruitment_channels_distribution`** — Reads `:contactedThrough`. CTDC has no communication-tool variable, so `victim.communication_tool_code` is empty after the CTDC load; only press-derived victim records would fill it.

**`Q16_palermo_triad_coverage`** — No table carries TIP events, so `:TIPEvent` and the `:tipEvent*` properties have no mapping. Listed in docs/MAPPING_COVERAGE.md.

**`Q17_scheme_vs_tool_heatmap`** — Reads `:victimOfFraudScheme`, which no mapping produces: the schema has no column linking a victim record to a fraud scheme. Also `:contactedThrough`, as Q11.

**`Q18_age_gender_per_scheme`** — Reads `:victimOfFraudScheme`, as Q17.

**`Q21_pattern_cooccurrence`** — Corpus gap. Needs `:matchesPattern` and `:offerDocumentedIn` on the same offer. Pattern matches cover offers 1 to 47, the hand-curated corpus; provenance covers offers 48 to 1379, the press-synthesised corpus. Closing it needs `evidence_source` filled in for the 47 curated offers, which the seeds do not record and which cannot be inferred from the offer text.

**`Q23_whatsapp_funnel_schemes`** — Reads `:victimOfFraudScheme` and `:contactedThrough`, as Q17.

**`Q24_new_routes_from_press`** — Corpus gap, as Q21: route associations and press provenance never meet on one offer.

**`Q27_vulnerability_x_exploitation`** — Reads `:hasVulnerabilityFactor`. CTDC has no vulnerability variable, so `victim_vulnerability` is empty after the CTDC load.

**`Q28_crossborder_with_press`** — Corpus gap, as Q21, in its subquery. The outer part works now that `:routeVictimCount` is populated. rdflib returns 50 rows here with an unbound `?pressArticles`, which is wrong: the subquery is empty, so the join is empty.

**`Q29_edith_cohort`** — Corpus gap, as Q21: the cohort lives in the hand-curated corpus, which has pattern matches and no evidence link.

## What loading the victim module for the first time found

The fifth pass ran `scripts/ingest_ctdc.py` for the first time, unchanged, through a sqlite-backed
stand-in for psycopg with foreign keys enforced, and then executed the 18 victim mappings and the
queries that depend on them. None of this had ever run. It found:

- **The ingest aborted.** CTDC writes the 9 to 17 age band as `09--17`; the script knew `9--17`. The
  26,004 records of minors in that band violated the foreign key to `age_group` and took the batch
  with them.
- **58,397 victims of sexual exploitation lost their exploitation type.** The script gave forced labour
  without a subtype the bucket `labour_other` and did nothing for `isSexualExploit` without a subtype,
  although its own header said it did. The vocabulary gains `sex_other` and the script emits it.
- **Every run added a second dataset row.** The `ON CONFLICT DO NOTHING` on `evidence_source_extended`
  never fired, because the unique constraint includes a column that is NULL here.
- **The TBox entailed that victims were job offers.** The mappings stated a victim's country of
  exploitation with `:inCountry`, whose domain is `:JobOffer`: 5,066 of the 6,449 sampled victims were
  entailed to be job offers, and a query for `?x a :JobOffer` over the VKG would have returned them.
  New property `:exploitedInCountry`, domain `:Victim`.
- **The TBox entailed that victims were demographic profiles.** `:hasAgeGroup`, `:hasGender`,
  `:hasNationality` and `:hasVulnerabilityFactor` have domain `:DemographicProfile`, and the mappings
  asserted them on the victim. The mappings now mint the profile the TBox always required, and Q12
  reads through it as Q18 and Q27 already did.
- **The TBox entailed that every source with a kind was an open-dataset record.** The kind was stated
  with `:datasetName`, whose domain is `:OpenDatasetRecord`. New property `:sourceKind`.
- **Seven queries still used `:derivedFrom` on a victim or an offer**, among them four that the third
  pass could not test for lack of data and one it missed because the pattern ran over two lines.
- **Nine code bindings returned the empty string.** `STRAFTER(STR(?x), "#")` was applied to instance
  IRIs, which have no fragment, so every group collapsed into one. Scheme occurrences now carry
  `:schemeCode`, and method, exploitation and vulnerability codes are taken from the last path segment.
  Q15 went from 10 rows to 33 and Q19 from 93 to 129, which is the grouping finally working.
- **`:routeVictimCount` had no data.** `db/14_route_victim_counts.sql` supplies the counts for the 1,771
  corridors, recomputed from the release and checked to be exactly the set `db/06_ctdc_routes.sql` loads.

After these, a check that types every individual by the domain and range axioms of the properties it
takes part in, over all 142,213 triples, finds no individual entailed into a class outside the tree of
its asserted type.

