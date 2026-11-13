# RATR-O: social-media criminal-recruitment module

## Source

Arias Vásquez, A. (coord.), Peña González, R. (dir.) and Aguayo Quezada, S. (coord. gral.) (2025).
*Del scroll al "jale": cómo se recluta en TikTok*. Seminario sobre Violencia y Paz, El Colegio de México.
Corpus of 100 TikTok videos collected 15 March to 31 August 2025, analysed with crisp-set
Qualitative Comparative Analysis (QCA).

The report defines four dichotomous conditions observed in each video:

| Code | Condition | RATR-O class |
|---|---|---|
| NR | Direct recruitment narrative | `:DirectRecruitmentPost` |
| ECC | Exaltation of criminal culture | `:CriminalCultureExaltationPost` |
| AVC | Aspiration to criminal life | `:CriminalLifeAspirationPost` |
| A | Acoustic framing (music, gunfire, radio) | `:AcousticFramingPost` |

and three sufficient configurations ("recruitment stories"):

| Story | Configuration | RATR-O class |
|---|---|---|
| Enrolarse en lo criminal | NR * ECC | `:EnrolInCrimeStoryPost` |
| Conexión emocional | NR * A | `:EmotionalConnectionStoryPost` |
| Bélicos | ECC * A * AVC | `:BelicoStoryPost` |

The words and symbols used in the posts and comments (79 lexicon terms, 71 verbatim with page
and image reference) are in `data/lexicon/tiktok_reclutamiento_lexicon.csv` and are loaded as
`:LexiconTerm` instances documented in `:ColmexScrollAlJale2025`.

## Class structure

```
SocialMediaItem
├── SocialMediaPost                       (disjoint with SocialMediaComment)
│   ├── DirectRecruitmentPost  ⊑ JobOffer, ∃exhibitsFraudScheme.ForcedCriminalityScheme
│   │   ├── EnrolInCrimeStoryPost        ⊑ CriminalCultureExaltationPost
│   │   └── EmotionalConnectionStoryPost ⊑ AcousticFramingPost
│   ├── CriminalCultureExaltationPost
│   ├── CriminalLifeAspirationPost
│   ├── AcousticFramingPost
│   └── BelicoStoryPost ⊑ ECC, A, AVC
└── SocialMediaComment
    ├── SelfApplicationComment
    └── RecruiterReplyComment

RedFlag
└── SocialMediaRecruitmentSignal
    ├── GroupCodeSignal, GroupEmojiSignal, PrivateChannelCallSignal, HighWeeklyPaySignal,
    ├── FamilyAppealSignal, MinorAgeMentionSignal, WomenInvitationSignal,
    └── NationalReachSignal, RecruitmentHashtagSignal, FatalismSignal

EvidenceSource
└── ResearchReport  (individual :ColmexScrollAlJale2025)

LexiconTerm
```

## Where OWL 2 QL draws the line, and where we put what does not fit

**1. QCA configurations are conjunctions; OWL 2 QL cannot use a conjunction as a sufficient condition.**
The source states that NR and ECC together are *sufficient* for the story "enrolarse en lo criminal":

    DirectRecruitmentPost ⊓ CriminalCultureExaltationPost ⊑ EnrolInCrimeStoryPost

OWL 2 QL admits only atomic classes or unqualified existentials on the left-hand side of a
subclass axiom, so this axiom is outside the profile. What *is* in the profile is the
necessary direction (the story implies each condition), written as two axioms:

    EnrolInCrimeStoryPost ⊑ DirectRecruitmentPost
    EnrolInCrimeStoryPost ⊑ CriminalCultureExaltationPost

The sufficient direction is moved to the mapping layer: `M-Social-Story-Enrol` in
`mappings/ramona.obda` populates `:EnrolInCrimeStoryPost` with
`SELECT ... WHERE cond_nr AND cond_ecc`. The same holds for the other two stories.
Consequence: the classification is correct for data that comes through the mapping, but a
post asserted directly in RDF as NR and ECC would not be inferred to belong to the story.
This is the standard OBDA trade-off: query rewriting stays in AC0 (first-order rewritable)
and the non-QL part of the domain knowledge is compiled into SQL.

**2. Counting thresholds are not expressible.**
A rule such as "two or more signals make a post critical" needs qualified number restrictions,
which are outside OWL 2 QL. It belongs to the classifier (`:RiskClassification` produced by the
pipeline) or to a SPARQL aggregate, not to the TBox.

**3. Existentials on the right-hand side are expressible and useful.**

    DirectRecruitmentPost ⊑ ∃exhibitsFraudScheme.ForcedCriminalityScheme

No database row links a TikTok post to a scheme, yet every direct recruitment post is a certain
answer to "which offers exhibit some forced-criminality scheme", with an anonymous scheme as
witness. The demonstrator runs Ontop with its default settings, which do not apply existential
reasoning, so `Q33` states the rewriting under the axiom as a union: the offers with a recorded
forced-criminality scheme, the direct recruitment posts and the criminal-recruitment offers.
It counts 698 offers; the recorded links alone give 92.

**4. Datatypes outside the QL datatype map.**
`xsd:date`, `xsd:gYear` and `xsd:boolean` are not in the OWL 2 QL datatype map. Ranges using them
are declared `rdfs:Literal` in the TBox and the mapping emits the concrete type
(`docs/validation/VALIDATION_REPORT.md`).

**5. Negation is not in the TBox.**
`Q35` ("which keywords fire on non-recruitment posts") uses `FILTER NOT EXISTS`, evaluated by
the SPARQL endpoint under closed-world semantics. It is a query-level operation, not an
ontological claim.

## Data

`db/11_social_media_module.sql` (generated by `scripts/build_social_module.py`) creates
`lexicon_terms`, `social_items`, `social_item_signals` and `social_item_terms`, and loads the
79 lexicon terms and the 1,500 synthetic items from `data/synthetic/`. All items carry
`:itemIsSynthetic true`. Nothing in this module is empirical prevalence: see
`data/synthetic/README.md`.

## Regenerate

```bash
python3 scripts/build_tiktok_synthetic.py --seed 2026
python3 scripts/build_social_module.py
python3 scripts/obda_to_r2rml.py
```

## Status

- Ontology: in OWL 2 QL under the OWL API checker (ROBOT 1.9.11), consistent under HermiT with the 1,500 synthetic items (`docs/validation/VALIDATION_REPORT.md`).
- Mappings: Ontop native and R2RML, which produce the same graph.
- Queries Q31 to Q35 execute through Ontop and over the materialised mappings, and return rows (`docs/validation/QUERY_EXECUTION_REPORT.md`).
