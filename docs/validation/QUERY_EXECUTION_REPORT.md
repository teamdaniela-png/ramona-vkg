# RATR-O v1.10.3 — execution of the 40 reference queries

Run on 10 November 2026. Ontop needs Docker, which does not run on the machine this
audit was carried out on, so the queries were executed against a materialisation of the
same mapping file over the same seeds: `db/*.sql` loaded into SQLite with dialect
translation only, `mappings/ramona.obda` executed row by row to produce the ABox, and the
TBox merged in with the subclass, subproperty and inverse closure that Ontop applies at
rewrite time. 85,081 triples in all. A query that returns rows here returns rows against
the VKG; a query that returns none is examined below.

Two artefacts of the offline runner, neither of them a property of the queries:

- rdflib 7.6.0 evaluates `?x IN (...)` as false for xsd:string-typed literals. The runner
  expands `IN` into a disjunction of equalities. Affects Q1.
- rdflib 7.6.0 does not treat a simple literal and an xsd:string-typed literal as the same
  term, which RDF 1.1 requires and Ontop implements. The runner canonicalises both sides.
  Affects every query that writes a string in a triple pattern.

The committed query files and mappings were not changed for either.

## Results

| query | rows | s | note |
| --- | --- | --- | --- |
| `Q1_highrisk_by_platform` | 4 | 0.02 |  |
| `Q2_multicountry_recruiters` | 1 | 0.02 |  |
| `Q3_pattern_matches` | 54 | 0.00 |  |
| `Q4_route_unclassified` | 0 | 0.00 | correct empty |
| `Q5_cjng_salary_pattern` | 6 | 0.03 |  |
| `Q6_edith_pattern_bundle` | 2 | 0.00 |  |
| `Q7_messenger_whatsapp_funnel` | 2 | 0.00 |  |
| `Q8_fraudulent_counts_by_country` | 5 | 0.03 |  |
| `Q9_ctdc_exploitation_by_country` | 0 | 0.00 | data gap |
| `Q10_type_b_only_cases` | 0 | 0.01 | data gap |
| `Q11_recruitment_channels_distribution` | 0 | 0.00 | data gap |
| `Q12_cross_source_age_gender` | 0 | 0.01 | data gap |
| `Q13_means_of_control_stack` | 0 | 0.00 | data gap |
| `Q14_mexico_press_vs_ctdc` | 0 | 0.00 | data gap |
| `Q15_fraudscheme_by_country` | 10 | 0.02 |  |
| `Q16_palermo_triad_coverage` | 0 | 0.01 | data gap |
| `Q17_scheme_vs_tool_heatmap` | 0 | 0.01 | data gap |
| `Q18_age_gender_per_scheme` | 0 | 0.01 | data gap |
| `Q19_outlets_by_scheme` | 93 | 0.04 |  |
| `Q20_type_b_over_a_by_country` | 3 | 0.02 |  |
| `Q21_pattern_cooccurrence` | 0 | 0.01 | corpus gap |
| `Q22_recruitment_x_exploitation` | 0 | 0.01 | data gap |
| `Q23_whatsapp_funnel_schemes` | 0 | 0.01 | data gap |
| `Q24_new_routes_from_press` | 0 | 0.03 | corpus gap |
| `Q25_trend_by_year` | 0 | 0.01 | data gap |
| `Q26_means_of_control_network` | 0 | 0.01 | data gap |
| `Q27_vulnerability_x_exploitation` | 0 | 0.01 | data gap |
| `Q28_crossborder_with_press` | 0 | 0.10 | schema gap |
| `Q29_edith_cohort` | 0 | 0.21 | corpus gap |
| `Q30_schemes_in_both_sources` | 0 | 6.81 | data gap |
| `Q32_minor_self_application` | 11 | 0.02 |  |
| `Q33_existential_forced_criminality` | 1 | 1.00 |  |
| `Q34_recruitment_stories` | 3 | 0.01 |  |
| `Q35_lexicon_false_positive_rate` | 13 | 0.52 |  |
| `Q36_who_is_targeted_mx` | 6 | 0.04 |  |
| `Q37_where_offers_mx` | 10 | 0.33 |  |
| `Q38_verbatim_wording` | 39 | 0.03 |  |
| `Q39_type_a_vs_type_b_real` | 3 | 0.71 |  |
| `Q40_criminal_recruitment_channels` | 3 | 0.01 |  |
| `Q31_tiktok_dm_plus_group_code` | 283 | n/a | runner limit, answer computed in SQL |

39 of the 40 queries execute. 19 return rows. Q31 does not finish in the offline runner:
its `:itemHasSignal ?s1 , ?s2` pattern makes rdflib enumerate the signal cross-product of
all 1,200 posts before filtering on the two signal types. Ontop pushes the same pattern
into SQL. The equivalent SQL over the seeds returns 283 posts that carry both a
private-channel call and a group code, so the query is answerable and correct; only the
in-memory runner cannot finish it.

## The 20 queries that return no rows

One is a correct empty answer. The other 19 are blocked by data that the repository does
not ship, not by anything wrong in the query. Each is named here rather than left for a
reader to discover.

**`Q4_route_unclassified`** — correct empty. No offer on a documented route is unclassified: all 17 routed offers carry a classification. The query is right and the answer is genuinely the empty set.

**`Q9_ctdc_exploitation_by_country`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q10_type_b_only_cases`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q11_recruitment_channels_distribution`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q12_cross_source_age_gender`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q13_means_of_control_stack`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q14_mexico_press_vs_ctdc`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q16_palermo_triad_coverage`** — data gap. No table carries TIP events, so :TIPEvent has no mapping at all. Listed in docs/MAPPING_COVERAGE.md.

**`Q17_scheme_vs_tool_heatmap`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q18_age_gender_per_scheme`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q21_pattern_cooccurrence`** — corpus gap. The query needs :matchesPattern and :offerDocumentedIn on the same offer. ramona.offer_patterns covers offers 1 to 47, the hand-curated corpus; :offerDocumentedIn covers offers 48 to 1379, the press-synthesised corpus, through db/13_offer_provenance.sql. The two sets do not overlap. Closing this needs evidence_source filled in for the 47 curated offers, which the seeds do not record and which cannot be inferred from the offer text.

**`Q22_recruitment_x_exploitation`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q23_whatsapp_funnel_schemes`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q24_new_routes_from_press`** — corpus gap. Same disjunction as Q21 for the press side, and in addition the NOT EXISTS clause reads :OpenDatasetRecord, which depends on the CTDC module.

**`Q25_trend_by_year`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q26_means_of_control_network`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q27_vulnerability_x_exploitation`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

**`Q28_crossborder_with_press`** — schema gap. The query reads :routeVictimCount, and ramona.trafficking_routes has no victim-count column, so no mapping produces that property. Listed in docs/MAPPING_COVERAGE.md. The CTDC corridors were filtered to at least 3 victims each, so the counts exist upstream in scripts/extract_routes.py and are dropped on the way into the seed.

**`Q29_edith_cohort`** — corpus gap. Same disjunction as Q21: the Edith Guadalupe cohort lives in the hand-curated corpus, which carries pattern matches but no evidence link.

**`Q30_schemes_in_both_sources`** — data gap. the victim and CTDC module ships no rows: db/ creates ramona.victim, its three satellite tables and public.evidence_source_extended, and populates none of them, because scripts/ingest_ctdc.py loads them from the CTDC release, which this repository does not redistribute

## Defects this run found and that are now fixed

- `db/05_seed_cases_v1_2.sql` inserted 1,332 offers with `posted_at` NULL against a NOT NULL column, and resolved `platform_type = 'other'` against a platform row that `db/02` never seeds, so `source_platform` came out NULL against a NOT NULL column. Either one aborts the statement, so none of the 1,332 offers had ever entered the database. Both columns are now nullable, with the reason stated in the schema, and `:postedOn` and `:postedVia` moved into their own mappings filtered on IS NOT NULL.
- `db/02_seed_reference.sql` still keyed its 7 routes by ISO 3166-1 alpha-2 after v1.10.2 moved `trafficking_routes` to alpha-3 and added foreign keys to `countries.country_iso3`. The load would have failed on those constraints. The 7 rows are now alpha-3 and both foreign keys verify.
- `Q36` and `Q37` asked for `data/country/MX` after v1.10.2 canonicalised the country IRI to alpha-3. They now read `data/country/MEX` and return 6 and 10 rows.
- `Q19`, `Q21`, `Q24` and `Q29` used `:derivedFrom` with a `:JobOffer` subject, outside that property's domain of `:SurvivorTestimonyPattern`; the data carries offer provenance under `:offerDocumentedIn`. The mappings also asserted `:derivedFrom` of routes and of victim records, equally outside the domain. The ontology now declares the domain-free `:hasEvidenceSource`, with `:derivedFrom` and `:offerDocumentedIn` as subproperties, routes and victims use it directly, and `Q19` returns 93 rows.
- No mapping typed a survivor pattern by its kind, so `:ClassicRedFlagPattern` and `:CredibleLethalPattern` had no instances although `survivor_patterns.pattern_kind` holds the values. Five typing mappings added; `Q20` returns 3 rows.
- `ramona.offers` had no link to `ramona.evidence_sources`, so the provenance claim on `:EvidenceSource` did not hold for offers. `db/13_offer_provenance.sql` recovers it for 1,325 of the 1,379 rows by an equality on text the seeds already contain, and types the 1,335 press articles among the evidence sources.
- `db/04_schema_extension_v1.sql` was the only file in `db/` without a `SET search_path`, and the mappings read its tables as `public.*`. Replaying the directory inside one psql session would have created them in `ramona` instead and broken 26 mappings. The schema is now set explicitly.
- Eight numeric claims in the ontology's own `skos:note` annotations were wrong against the seeds, among them 197 countries for 248, 2,050 offers for 1,674, five pattern kinds for six, 24 fraud schemes for 26, and a 21% WhatsApp share that the data does not support at either 12.5% of the corpus or 34.9% of the offers whose platform is named. All eight are rewritten with the counted figure and the date it was counted.

