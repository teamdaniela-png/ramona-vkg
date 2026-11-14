# RATR-O v1.11.0: the Ontop demonstrator

The virtual knowledge graph runs on the stack of `docker-compose.yml`: PostgreSQL 16 loaded with
`db/01` to `db/16`, and Ontop 5.5.0 with `ontology/ratr-o.ttl` and `mappings/ramona.obda`, serving
SPARQL at `http://localhost:8080/sparql`. The PostgreSQL JDBC driver is 42.7.4. No triple is stored:
Ontop rewrites each query into SQL over the tables.

Three data states:

- **Seeds**: what `docker compose up -d` loads on a fresh volume.
- **Sample**: the seeds plus one CTDC victim in forty, 6,449 records, and the 11,596 UNODC figures of
  the Americas. It is the state of the offline validation.
- **Full**: the seeds plus the 257,969 victim records of the CTDC Global Synthetic Dataset v2025 and
  the 65,398 figures of the UNODC data portal on trafficking in persons, release of 28 October 2025.

## Checks

| Check | How | Result |
| --- | --- | --- |
| Seed files in PostgreSQL | `db/01` to `db/16` run in order by the database on first start, foreign keys enforced | All load: 43 tables, 1,379 offers |
| Mapping file in Ontop | `mappings/ramona.obda` parsed against the database metadata | The 206 assertions load |
| Reference queries, seeds | `scripts/ontop/run_queries.py` | 44 of 44 execute, 23 with rows, the row counts of the offline validation |
| Answers, seeds | `run_queries.py --dump` of the endpoint and of the offline runner, compared row by row with `scripts/ontop/compare_answers.py` | The 44 queries return the same rows from Ontop and from the offline runner |
| Graph served, seeds | `ontop materialize`, compared with the offline ABox closed under the ontology by `scripts/ontop/compare_with_offline.py` | The same 89,121 triples: the 75,675 asserted and 13,446 entailed by subclass, subproperty, inverse, domain and range axioms |
| CTDC load | `scripts/ingest_ctdc.py` over the 257,969 records of the release | Loads in under a minute, foreign keys enforced |
| UNODC load | `scripts/ingest_unodc.py` over the 65,398 figures of the release | Loads in under a minute, foreign keys enforced |
| Reference queries, sample | `run_queries.py --state sample` | 44 of 44 execute, 33 with rows, the row counts of the offline validation |
| Answers, sample | as for the seeds | The 44 queries return the same rows from Ontop and from the offline runner |
| Reference queries, full | `run_queries.py --state full` | 44 of 44 execute, 33 with rows, 8.9 seconds for the 44 together, the slowest 2.59 seconds |

`scripts/ontop/run_all.sh` runs the seed checks in one command.

## Row counts

Seconds are for the full state, on a laptop with an Apple M2 processor and 4 GB given to Docker.

| Query | Seeds | Sample | Full | Seconds |
| --- | ---: | ---: | ---: | ---: |
| `Q1_highrisk_by_platform` | 4 | 4 | 4 | 0.13 |
| `Q2_multicountry_recruiters` | 1 | 1 | 1 | 0.33 |
| `Q3_pattern_matches` | 54 | 54 | 54 | 0.40 |
| `Q4_route_unclassified` | 0 | 0 | 0 | 0.11 |
| `Q5_cjng_salary_pattern` | 6 | 6 | 6 | 0.07 |
| `Q6_edith_pattern_bundle` | 2 | 2 | 2 | 0.02 |
| `Q7_messenger_whatsapp_funnel` | 2 | 2 | 2 | 0.03 |
| `Q8_fraudulent_counts_by_country` | 5 | 5 | 5 | 0.04 |
| `Q9_ctdc_exploitation_by_country` | 0 | 100 | 100 | 0.78 |
| `Q10_type_b_only_cases` | 39 | 39 | 39 | 0.24 |
| `Q11_recruitment_channels_distribution` | 0 | 0 | 0 | 0.06 |
| `Q12_cross_source_age_gender` | 0 | 94 | 165 | 2.59 |
| `Q13_means_of_control_stack` | 0 | 69 | 72 | 0.73 |
| `Q14_mexico_press_vs_ctdc` | 0 | 1 | 1 | 0.02 |
| `Q15_fraudscheme_by_country` | 33 | 33 | 33 | 0.03 |
| `Q16_palermo_triad_coverage` | 0 | 0 | 0 | 0.01 |
| `Q17_scheme_vs_tool_heatmap` | 0 | 0 | 0 | 0.02 |
| `Q18_age_gender_per_scheme` | 0 | 0 | 0 | 0.00 |
| `Q19_outlets_by_scheme` | 129 | 129 | 129 | 0.09 |
| `Q20_type_b_over_a_by_country` | 3 | 3 | 3 | 0.02 |
| `Q21_pattern_cooccurrence` | 0 | 0 | 0 | 0.02 |
| `Q22_recruitment_x_exploitation` | 0 | 23 | 36 | 0.40 |
| `Q23_whatsapp_funnel_schemes` | 0 | 0 | 0 | 0.02 |
| `Q24_new_routes_from_press` | 0 | 0 | 0 | 0.01 |
| `Q25_trend_by_year` | 0 | 22 | 22 | 0.12 |
| `Q26_means_of_control_network` | 0 | 25 | 28 | 0.98 |
| `Q27_vulnerability_x_exploitation` | 0 | 0 | 0 | 0.36 |
| `Q28_crossborder_with_press` | 0 | 0 | 0 | 0.02 |
| `Q29_edith_cohort` | 0 | 0 | 0 | 0.02 |
| `Q30_schemes_in_both_sources` | 15 | 15 | 15 | 0.04 |
| `Q31_tiktok_dm_plus_group_code` | 283 | 283 | 283 | 0.36 |
| `Q32_minor_self_application` | 11 | 11 | 11 | 0.05 |
| `Q33_existential_forced_criminality` | 1 | 1 | 1 | 0.05 |
| `Q34_recruitment_stories` | 3 | 3 | 3 | 0.03 |
| `Q35_lexicon_false_positive_rate` | 13 | 13 | 13 | 0.03 |
| `Q36_who_is_targeted_mx` | 7 | 7 | 7 | 0.03 |
| `Q37_where_offers_mx` | 9 | 9 | 9 | 0.03 |
| `Q38_verbatim_wording` | 39 | 39 | 39 | 0.07 |
| `Q39_type_a_vs_type_b_real` | 3 | 3 | 3 | 0.04 |
| `Q40_criminal_recruitment_channels` | 3 | 3 | 3 | 0.01 |
| `Q41_flags_verified_employers_vs_press` | 15 | 15 | 15 | 0.03 |
| `Q42_unodc_detected_victims_mx` | 0 | 15 | 15 | 0.02 |
| `Q43_unodc_form_of_exploitation_mx` | 0 | 47 | 47 | 0.03 |
| `Q44_unodc_vs_ctdc_by_country` | 0 | 5 | 66 | 0.38 |

The 11 queries without rows in the full state ask for combinations that the loaded data do not
contain; `QUERY_EXECUTION_REPORT.md` says for each which data it needs.

## Reproduce

```bash
mkdir -p jdbc
curl -L -o jdbc/postgresql-42.7.4.jar \
  https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar
docker compose up -d
scripts/ontop/run_all.sh

python scripts/ingest_ctdc.py --csv /path/to/CTDC_global_synthetic_data_v2025.csv
python scripts/ingest_unodc.py --xlsx /path/to/data_glotip.xlsx
python3 scripts/ontop/run_queries.py --state full
```
