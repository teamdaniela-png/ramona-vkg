# Expert rules with exceptions and rules learned with Popper

Working note, 25 November 2026. It describes the rules for job offers given by the domain expert, the rules
that Popper learns from the same signals, the steps from an offer to an alert, and the data used to evaluate both.

The rules and the programs are in the repository. The collected offers, the cases and the expert's labels are not
published, so the programs that read them do not run from a clone.

| What | Where |
|---|---|
| Expert rules, version 2 (22 rules) | `scripts/rule_learning/asp/expert_rules.lp` |
| The same rules with every exception written in the body | `scripts/rule_learning/asp/expert_rules_long.lp` |
| Check that the two files give the same alerts (0 differences over the 813 offers and cases collected) | `scripts/rule_learning/asp/check_long_rules.py` |
| From a collected offer to ASP facts | `scripts/rule_learning/asp/build_posting_facts.py` |
| Clingo, Popper, Clingo | `scripts/rule_learning/popper/run_pipeline.py` |
| Rules learned by Popper, versions 1 to 3 | `scripts/rule_learning/popper/learned/` |

The ASP programs need the clingo Python package (tested with 5.8.3). Popper is run from its own checkout with
`popper.py <task> --max-vars 1 --max-body 8 --timeout 900`.

## 1. The expert's rules

Twenty-two rules, given by the domain expert and written in answer set programming. A rule holds by default and
stops holding when one of its exceptions applies (`ab_cN`). `not` is negation as failure.

Definitions used by the rules:

- **Verified employer**: the posting comes from an employer verified in public sources, or the post on a social
  network carries one strong validation signal or two weak ones. A recruitment agency that exists counts as
  verified even when it does not name its client. It is not enough that a company exists when the account that
  publishes is not the company's.
- **High pay**: 20,000 MXN a month or more, with weekly, fortnightly and daily pay converted to a month. The
  threshold was set by the expert.

| No. | The rule holds when | Unless | Level |
|---|---|---|---|
| 1 | High pay | The employer is verified and the offer asks for experience, or is a sales job not reached through a personal channel, or is a specialised post, or is a security post | verifica |
| 2 | Urgent hiring | Seasonal sales job at a large verified employer; operational post, internship or security post at a verified employer; the only urgency is the badge of a job board | verifica |
| 3 | Urgent hiring with no experience needed | An exception of rule 2 applies; entry-level post or internship at a verified employer | verifica |
| 4 | The offer arrives by WhatsApp or e-mail without the person having looked for a job | The channel was agreed with the recruiter; the recruiter is verifiable (profile with followers, with activity and related to the vacancy) | verifica |
| 5 | The only way in is a personal channel (a WhatsApp number, a private message, a phone number, a Hotmail or Gmail address) | The employer is verified | verifica |
| 6 | The person has to put up money to work | No exception | alerta |
| 7 | The offer does not say what the job is | The recruiter is verifiable | verifica |
| 8 | The offer uses the name or logo of a brand or public body that is not the one publishing it | No exception | alerta |
| 9 | The job is in another state or the transport is paid for | The employer is verified | alerta |
| 10 | The real job is not the one advertised (known only after contact) | No exception | escalar |
| 11 | The job is one reported as a false offer used to hook trafficking victims (waitress, receptionist, masseuse, maid, domestic service, care work, adult entertainment) | The employer is verified | verifica |
| 12 | Security post (guard, escort, bodyguard driver) | The employer is verified | verifica |
| 13 | It asks for "good presentation" and does not say what the job is | No exception | alerta |
| 14 | It asks for personal documents or bank details before any interview | No exception | alerta |
| 15 | It asks to download or install something, or to do a job test | The employer is verified | verifica |
| 16 | The person is told to come to a place that is not an established workplace (bus terminal, ranch, house, hotel, car park, fast-food restaurant) | No exception | alerta |
| 17 | The offer is addressed only to women or to an age range | The employer is verified | alerta |
| 18 | It asks for a photo of the person | The employer is verified | alerta |
| 19 | It uses the codes or emojis of criminal groups | No exception | alerta |
| 20 | The employer is never named and the offer circulates on a social network, a personal channel or a direct message | No exception | alerta |
| 21 | High pay together with no employer named, no experience needed or no job described | No exception | alerta |
| 22 | A job that appears as bait in the press cases (security, waiting and bar work, events, field work, construction, kitchen, domestic work, cleaning, call centre, driver) | The employer is verified | verifica |

Rules 1 to 17 are version 1. Rules 18 to 22 and the levels are version 2, written on 24 November 2026 after the
second blind test.

Three levels:

```
strong(6;8;9;13;14;16;17;18;19;20;21).
weak(1;2;3;4;5;7;11;12;15;22).
alerta(O)   :- holds(O, N), strong(N).
verifica(O) :- holds(O, N), weak(N), not alerta(O).
escalar(O)  :- holds(O, 10).
```

- `alerta`: at least one strong rule holds.
- `verifica`: only weak rules hold. The person should check the employer before going on. These jobs are not to
  be stigmatised.
- `escalar`: rule 10. It does not warn about an offer: the person is already in it and has to be referred.

A rule with its exceptions:

```
c2(O)    :- has(O, contratacion_urgente), not ab_c2(O).
ab_c2(O) :- sales(O), seasonal(O), large_verified_employer(O).
ab_c2(O) :- operational_role(O), verified_employer(O).
ab_c2(O) :- internship(O), verified_employer(O).
ab_c2(O) :- security(O), verified_employer(O).
ab_c2(O) :- portal_badge_only(O).
```

## 2. The rules Popper learns

### What Popper receives

Clingo derives the signals of every example from its facts and from the expert's definitions (verified employer,
high pay, relocation, personal channel). Popper receives, for version 3:

- `exs.pl`: 227 positive examples, `pos(alert(o))`, and 242 negative ones, `neg(alert(o))`. The labels are the
  expert's.
- `bk.pl`: 15,775 facts. Each signal of each example is given as true, `signal(o)`, or as false, `not_signal(o)`,
  so that Popper can learn rules with negation. The three channel signals (`social_network`, `formal_portal`,
  `direct_message`) are given as false only when the channel of the offer is known.
- `bias.pl`: head `alert/1`, 68 body predicates (34 signals and their complements), and the constraints on rules
  that use the channel, below.

The 34 signals: `appearance_required`, `asks_for_documents`, `asks_for_money`, `asks_for_photo`,
`asks_to_download`, `borrowed_name`, `bus_terminal`, `coded_language`, `direct_message`, `employer_never_named`,
`entry_level`, `formal_portal`, `high_pay`, `intermediary`, `internship`, `no_experience`, `no_job_described`,
`operational_role`, `personal_contact`, `recruitment_role`, `relocation`, `requires_experience`, `sales`,
`seasonal`, `security`, `social_network`, `specialised_role`, `trafficking_risk_role`, `transport_sent`,
`unestablished_meeting_place`, `unsolicited_contact`, `urgent`, `verified`, `women_or_age_targeted`.

Popper does not see the expert's rules. It sees the signals and the labels. One exception of the expert is already inside a signal: `urgent` leaves out the urgency badge that job boards put on a posting, which is an exception of rule 2.

### Three versions

| | Version 1 | Version 2 | Version 3 |
|---|---|---|---|
| Date | 23 November | 24 November | 24 November |
| Positive examples | 170 | 210 | 227 |
| Negative examples | 227 | 242 | 242 |
| Signals | 28 | 32 | 34 |
| Rules learned | 10 | 7 | 9 |
| Positives covered, training | 164 of 170 | 205 of 210 | 221 of 227 |
| Negatives covered, training | 0 of 227 | 0 of 242 | 0 of 242 |
| Use | Sat the second blind test | Intermediate | Frozen for the third round |

Popper stopped at the time limit (900 seconds) in the three versions. The rules are the best hypothesis found in
that time; it is not shown to be optimal.

Version 2 adds to the training the offers of the second blind test (40 positive, 15 negative; the 4 doubtful ones
and one offer whose label the expert withdrew are left out) and four signals: photo, coded language, job used as
bait, verified employer. Version 3 adds the 17 field cases as positives and two signals Popper did not receive: an
appointment at a place that is not a workplace, and offers addressed to women or an age range. The more specific
signal `bus_terminal` was given to Popper from version 1.

### Version 1, the ten rules that sat the blind test

```
 1. alert(O) :- offer(O), employer_never_named(O).
 2. alert(O) :- offer(O), asks_for_documents(O).
 3. alert(O) :- offer(O), no_job_described(O).
 4. alert(O) :- offer(O), borrowed_name(O).
 5. alert(O) :- offer(O), unsolicited_contact(O).
 6. alert(O) :- offer(O), channel_known(O), not formal_portal(O), not social_network(O).
 7. alert(O) :- offer(O), channel_known(O), not formal_portal(O), pay_high(O).
 8. alert(O) :- offer(O), moves_person(O), not requires_experience(O).
 9. alert(O) :- offer(O), channel_known(O), not formal_portal(O), security(O), not personal_channel(O).
10. alert(O) :- offer(O), operational_role(O), not sales(O), not requires_experience(O),
                trafficking_risk_role(O), not personal_channel(O).
```

### Version 2, the seven rules of the intermediate version

```
1. alert(O) :- offer(O), no_job_described(O).
2. alert(O) :- offer(O), borrowed_name(O).
3. alert(O) :- offer(O), employer_never_named(O).
4. alert(O) :- offer(O), asks_to_download(O).
5. alert(O) :- offer(O), channel_known(O), not formal_portal(O), not verified_employer(O).
6. alert(O) :- offer(O), not requires_experience(O), not security(O), moves_person(O).
7. alert(O) :- offer(O), not requires_experience(O), operational_role(O), trafficking_risk_role(O), not personal_channel(O), not sales(O).
```

### Version 3, the nine current rules

```
1. alert(O) :- offer(O), unestablished_meeting_place(O).
2. alert(O) :- offer(O), no_job_described(O).
3. alert(O) :- offer(O), asks_for_money(O).
4. alert(O) :- offer(O), asks_for_documents(O).
5. alert(O) :- offer(O), employer_never_named(O).
6. alert(O) :- offer(O), channel_known(O), not formal_portal(O), not verified_employer(O).
7. alert(O) :- offer(O), pay_high(O), has(O, sin_experiencia).
8. alert(O) :- offer(O), not women_or_age_targeted(O), not requires_experience(O), moves_person(O).
9. alert(O) :- offer(O), not sales(O), not personal_channel(O), trafficking_risk_role(O),
               not requires_experience(O), operational_role(O).
```

### The constraint added by the expert

In the second blind test, rule 6 of version 1 (the channel is known, it is not a job board and it is not a social
network) held in the five false alarms of Popper, and in one of them it was the only rule. Four were vacancies of
a real security company published on its own page. In the training of version 1 nearly all the legitimate offers
came from job boards.

For versions 2 and 3 the language bias carries these constraints: a rule that uses the channel must carry the
condition "employer not verified", and that condition may only appear together with the channel.

```
chan(R) :- body_literal(R,social_network,_,_).
chan(R) :- body_literal(R,formal_portal,_,_).
chan(R) :- body_literal(R,direct_message,_,_).
chan(R) :- body_literal(R,not_social_network,_,_).
chan(R) :- body_literal(R,not_formal_portal,_,_).
chan(R) :- body_literal(R,not_direct_message,_,_).
:- chan(R), not body_literal(R,not_verified,_,_).
:- body_literal(R,not_verified,_,_), not chan(R).
:- body_literal(_,verified,_,_).
```

So the form of rule 6 of version 3 was not found by Popper: it is the expert's knowledge placed in the search
space.

### Next to the expert's rules

- Both have: asks for money (expert rule 6), asks for documents (14), appointment at a place that is not a
  workplace (16), no job described (7), high pay with no experience (part of 21).
- "The employer is never named" was rule 1 of Popper version 1 before the expert had it. The expert added it in
  version 2 as rule 20, limited to social networks, personal channels and direct messages. The signal was among
  those given to Popper; the rule was formed by Popper.
- Given by the expert and not received by Popper version 1: coded language, the signal for an appointment at a
  place that is not a workplace, and that an account bearing the name of a company is not enough to verify it.
  Popper version 1 did receive `bus_terminal`: it is true in 29 of its 170 positive examples and in none of the
  227 negative ones, but the final hypothesis has no rule with it.
- Rules 6, 8 and 9 of version 3 use negation, as the expert's exceptions do.

## 3. The steps

| Step | In | What is done | Out |
|---|---|---|---|
| 1. Capture | The offer: text, screenshot or press note | One row per offer: employer, job, pay, channel, contact, what it asks for, verification of the employer | A CSV row |
| 2. Facts | The CSV row | `build_posting_facts.py` writes the ASP facts of the offer | `offer(o). coded_language(o).` |
| 3. Signals | Facts and the expert's definitions | Clingo derives the signals | 34 signals per offer |
| 4. Learning | Signals and the expert's labels | Popper searches for rules that cover the positives and no negative | Rules `alert(O) :- ...` |
| 5. Evaluation | Expert rules, Popper rules and offers | The rules of Popper are rewritten in ASP with negation as failure and Clingo evaluates the two rule bases | Per offer: alerta, verifica or escalar |

Blind-test protocol:

- The rules, the fact generator and the rules of Popper are frozen before the offers are searched. Their SHA-256
  digests are kept and the run checks them.
- The offers are new: they are in no earlier round and not in the training.
- Each offer is put on a card with the same fields and the same tone, without its source, so that the format does
  not give away where it comes from.
- The expert labels from the card, without seeing the result of the rules and without the source of the offers
  she did not bring herself: legitima, dudosa, fraude or peligro.
- The signals of an offer include what the poster did after contact (asked for money, asked for documents, set the
  appointment at the bus terminal). They do not include the outcome.
- It is run once. After the result no rule of that version is changed: changes go to a new version, tested on new
  offers.

## 4. The data evaluated

### Training data of Popper version 3

| Group | Examples | Source |
|---|---:|---|
| **Positives (fraude or peligro)** | **227** | |
| Press cases | 136 | Individual cases documented in press notes. The notes were read by a language model; the expert labelled each case (134 peligro, 2 fraude) |
| Cases of the expert | 34 | Screenshots and messages collected and labelled by the expert |
| Second blind test | 40 | Its 17 fraude and 23 peligro offers, after the test was scored |
| Field cases | 17 | 10 interviews and 7 cases of users of Ramona |
| **Negatives (legitima)** | **242** | |
| Indeed | 153 | Employer verified in public sources |
| Postings captured by hand | 37 | `data/real/legit_offers.csv`: LinkedIn 25, Talenteca 8, OCC 3, Computrabajo 1; verified employer |
| Computrabajo | 22 | Employer verified in public sources |
| Facebook | 14 | Employer validated with the expert's signals |
| Second blind test | 15 | The offers labelled legitima, less the one whose label was withdrawn |
| Servicio Nacional de Empleo | 1 | Verified employer |

On these data the expert's rules, version 2, give: of the 227 positives, 209 alerta, 13 verifica, 1 escalar only
and 4 with no rule; of the 242 legitimate offers, 0 alerta and 12 verifica. Popper version 3 covers 221 of 227
and 0 of 242. None of these figures is a test: both rule bases have seen these data.

### Second blind test: 60 new offers

Single run of 24 November 2026 with the expert's rules version 1 (17 rules) and Popper version 1 (10 rules),
frozen on 23 November. Version 1 had no levels: an alert means that at least one rule holds. The expert labelled
17 offers fraude, 23 peligro, 16 legitima and 4 dudosa.

| | Expert rules, version 1 | Popper, version 1 |
|---|---|---|
| Fraude with an alert (17) | 17 (100.0%) | 17 (100.0%) |
| Peligro with an alert (23) | 21 (91.3%) | 23 (100.0%) |
| Fraude and peligro with an alert (40) | 38 (95.0%) | 40 (100.0%) |
| Legitima with an alert, false alarms (16) | 3 (18.8%) | 5 (31.3%) |
| Correct alerts among the alerts on offers with a firm label | 38 of 41 (92.7%) | 40 of 45 (88.9%) |
| Correct over the 56 offers with a firm label | 51 (91.1%) | 51 (91.1%) |
| Dudosa with an alert (4) | 3 | 2 |

The errors:

- Expert rules, peligro with no alert (2): a driver offer written with the code "pollitos", and a call-centre
  offer from a personal profile that never names the employer. Version 1 had no rule for either.
- Expert rules, false alarms (3): an events hostess asked for a photo (rule 14 counted the photo as a document);
  a driver offer whose contact is a message to a phone number and whose publishing account is not the company's
  (rule 5); an urgent warehouse post published by an agency (rules 2 and 3).
- Popper, false alarms (5): four vacancies of a security company on its own page (rule 6 in the four; rules 8 and
  9 also in some) and the events hostess (rules 2 and 6).

After the test the expert withdrew her label legitima for the driver offer. The published result keeps the
original label. With that offer left out of the legitimate ones, the false alarms are 2 of 15 for the expert
rules and 5 of 15 for Popper.

### Field cases: 17

Ten interviews and seven cases of users of Ramona, labelled by the expert on 24 November, after version 2 of her
rules was written: 15 peligro and 2 fraude. They were not used to train Popper versions 1 and 2; they are in the
training of Popper version 3. The expert already knew these cases, so for her rules they are not a blind test.

| | Expert v1 | Popper v1 | Expert v2 | Popper v2 |
|---|---|---|---|---|
| Interviews (10) | 9 | 4 | 8 alerta, 1 verifica | 8 |
| User cases (7) | 7 | 5 | 6 alerta, 1 verifica | 4 |
| Total (17) | 16 (94.1%) | 9 (52.9%) | 14 alerta, 2 verifica | 12 (70.6%) |

Seven of the ten interviews include an appointment at a place that is not a workplace (rule 16); in five of them
it is the bus terminal. Popper version 1 did not receive the signal for such an appointment. It did receive
`bus_terminal`, present in those five cases, but had no rule that used it. One interview meets none of the
expert's rules in either version.

### First blind test

19 November 2026, 43 offers, the expert's first 10 rules frozen on 18 November: 7 of 7 fraude with an alert and
16 of 23 legitima with no alert. The other 13 were labelled dudosa (7 with an alert). It had no peligro offers. Those 43 offers are no longer a blind test for later
versions.

### Limits

- One person labelled: the expert.
- The 17 field cases are interviews and cases of Ramona that the expert already knew. They measure Popper
  versions 1 and 2 on data they had not seen; for the expert's rules they are not a blind test.
- Of the 60 offers of the second blind test, 49 were labelled without their source. The other 11 are screenshots
  brought by the expert, who therefore knew where they came from. The two peligro offers the expert's rules missed
  are among those 11.
- The second blind test measured version 1 of the expert's rules and of Popper. The expert's rules version 2 and
  Popper version 3 have no blind test yet: it is the third round, with new offers, the same protocol and the versions already frozen.
- The press cases were read by a language model. Their labels are the expert's.
- Two legitimate postings share one identifier, so one negative example carries the signals of two postings (both
  legitimate and verified): 243 postings in 242 examples. It is corrected in the next version.
- The four offers labelled dudosa count neither as correct nor as an error.
