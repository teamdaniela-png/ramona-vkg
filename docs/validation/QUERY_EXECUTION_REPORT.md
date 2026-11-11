# RATR-O v1.10.6: execution of the 41 reference queries

The queries were run with `scripts/offline_vkg/`: the seed files in `db/` are loaded into SQLite,
`mappings/ramona.obda` is executed to produce the graph the VKG exposes, and the queries are evaluated
over that graph together with the subclass, subproperty and inverse closure of the ontology, which is
what Ontop applies when it rewrites a query. `mappings/ramona.r2rml.ttl` was executed the same way and
gives the same graph, triple for triple.

Two data states:

- **Seeds**: what a clone of the repository loads. 75,675 ABox triples, 88,926 with the TBox.
- **Seeds plus CTDC**: the same after `scripts/ingest_ctdc.py` has loaded the CTDC Global Synthetic
  Dataset v2025, 257,969 victim records. The queries ran over one victim in forty, 6,449 records:
  142,629 ABox triples, 168,325 with the TBox. Row counts in that column are over the sample.

Both graphs are consistent with the ontology under HermiT.

## Results

| Query | Seeds | Seeds plus CTDC |
| --- | ---: | ---: |
| `Q1_highrisk_by_platform` | 4 | 4 |
| `Q2_multicountry_recruiters` | 1 | 1 |
| `Q3_pattern_matches` | 54 | 54 |
| `Q4_route_unclassified` | 0 | 0 |
| `Q5_cjng_salary_pattern` | 6 | 6 |
| `Q6_edith_pattern_bundle` | 2 | 2 |
| `Q7_messenger_whatsapp_funnel` | 2 | 2 |
| `Q8_fraudulent_counts_by_country` | 5 | 5 |
| `Q9_ctdc_exploitation_by_country` | 0 | 100 |
| `Q10_type_b_only_cases` | 0 | 0 |
| `Q11_recruitment_channels_distribution` | 0 | 0 |
| `Q12_cross_source_age_gender` | 0 | 94 |
| `Q13_means_of_control_stack` | 0 | 69 |
| `Q14_mexico_press_vs_ctdc` | 0 | 1 |
| `Q15_fraudscheme_by_country` | 33 | 33 |
| `Q16_palermo_triad_coverage` | 0 | 0 |
| `Q17_scheme_vs_tool_heatmap` | 0 | 0 |
| `Q18_age_gender_per_scheme` | 0 | 0 |
| `Q19_outlets_by_scheme` | 129 | 129 |
| `Q20_type_b_over_a_by_country` | 3 | 3 |
| `Q21_pattern_cooccurrence` | 0 | 0 |
| `Q22_recruitment_x_exploitation` | 0 | 23 |
| `Q23_whatsapp_funnel_schemes` | 0 | 0 |
| `Q24_new_routes_from_press` | 0 | 0 |
| `Q25_trend_by_year` | 0 | 22 |
| `Q26_means_of_control_network` | 0 | 25 |
| `Q27_vulnerability_x_exploitation` | 0 | 0 |
| `Q28_crossborder_with_press` | 0 | 0 |
| `Q29_edith_cohort` | 0 | 0 |
| `Q30_schemes_in_both_sources` | 15 | 15 |
| `Q31_tiktok_dm_plus_group_code` | 283 | 283 |
| `Q32_minor_self_application` | 11 | 11 |
| `Q33_existential_forced_criminality` | 1 | 1 |
| `Q34_recruitment_stories` | 3 | 3 |
| `Q35_lexicon_false_positive_rate` | 13 | 13 |
| `Q36_who_is_targeted_mx` | 6 | 6 |
| `Q37_where_offers_mx` | 10 | 10 |
| `Q38_verbatim_wording` | 39 | 39 |
| `Q39_type_a_vs_type_b_real` | 3 | 3 |
| `Q40_criminal_recruitment_channels` | 3 | 3 |
| `Q41_flags_verified_employers_vs_press` | 15 | 15 |

All 41 queries execute. 22 return rows over the seeds and 29 once the CTDC release is loaded.

## Queries that return no rows in either state

Each of these reads data that the demonstrator's seeds do not carry. The queries are kept because the
competency questions they answer are part of what the ontology is meant to cover.

- **`Q4_route_unclassified`**: The answer is the empty set: every offer on a documented route carries a classification.
- **`Q10_type_b_only_cases`**: Reads victim records derived from press articles. `scripts/ingest_press.py` writes them from the press corpus, which is not redistributed.
- **`Q11_recruitment_channels_distribution`**: Reads `:contactedThrough` on victims. CTDC has no communication-tool variable; press-derived victim records carry it.
- **`Q16_palermo_triad_coverage`**: Reads `:TIPEvent`. The demonstrator schema has no TIP-event table (see `docs/MAPPING_COVERAGE.md`).
- **`Q17_scheme_vs_tool_heatmap`**: Reads `:victimOfFraudScheme`. The demonstrator schema has no column linking a victim record to a fraud scheme.
- **`Q18_age_gender_per_scheme`**: Reads `:victimOfFraudScheme`, as Q17.
- **`Q21_pattern_cooccurrence`**: Joins `:matchesPattern` and `:offerDocumentedIn` on the same offer. In the seeds, pattern matches are on the 47 hand-curated offers and source links on the press-synthesised ones.
- **`Q23_whatsapp_funnel_schemes`**: Reads `:victimOfFraudScheme` and `:contactedThrough`, as Q17 and Q11.
- **`Q24_new_routes_from_press`**: Joins `:associatedWithRoute` and `:offerDocumentedIn` on the same offer; as Q21, the seeds carry them on different offers.
- **`Q27_vulnerability_x_exploitation`**: Reads `:hasVulnerabilityFactor`. CTDC has no vulnerability variable; press-derived victim records carry it.
- **`Q28_crossborder_with_press`**: Same join as Q24.
- **`Q29_edith_cohort`**: Same join as Q21.

## Reproduce

```bash
scripts/offline_vkg/run_all.sh
```

`scripts/offline_vkg/README.md` describes each step and how to add the CTDC records.
