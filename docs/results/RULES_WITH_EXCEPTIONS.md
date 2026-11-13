# Rules with exceptions over the documented offers: three examples

Working note. Everything below runs from the repository:

```
python3 scripts/rule_learning/learn_rules.py              # example table
python3 scripts/rule_learning/asp/build_facts.py          # offers as ASP facts
python3 scripts/rule_learning/asp/evaluate.py             # the three examples, with clingo
python3 scripts/rule_learning/asp/learn_exceptions.py     # learning defaults with exceptions, with clingo
```

The ASP scripts need the clingo Python package (`pip install clingo`, tested with 5.8.3).

Scope: 167 press-documented offers in Mexico (audit status *verificada*) and 37 postings of verified employers.
Of the 167, 93 are documented as criminal recruitment.

## The kind of rule we have in mind

Exceptions by specificity: a general rule holds unless a more specific rule blocks it. Written with negation as
failure in `scripts/rule_learning/asp/rules_with_exceptions.lp`.

### Example 1. Is this offer an alert?

```
alert_pay(O)  :- high_pay(O), not ab_pay(O).
ab_pay(O)     :- high_pay(O), driver(O), requirements(O), not ab_driver(O).
ab_driver(O)  :- has(O, sin_experiencia).
```

Weekly pay more than 1.5 times the median of the verified postings is an alert, unless the post is a driver job
that states its requirements, unless it also says that no experience is needed.

| | Fires on | Documented offers | Verified postings |
|---|---|---|---|
| General rule alone | 22 | 20 | 2 |
| With the exceptions | 20 | 20 | 0 |

The two verified postings that the exception blocks are an executive-protection driver and a guest transportation
driver, both with detailed requirements. One documented offer ("guards or drivers", 12,000 MXN a week, no experience
needed) meets the exception to the exception and stays an alert.

### Example 2. What kind of trap does a promise of high pay point to?

```
kind_pay(O, criminal) :- has(O, sueldo_alto), not ab_kind_pay(O).
kind_pay(O, fraud)    :- has(O, sueldo_alto), has(O, pago_adelantado).
ab_kind_pay(O)        :- has(O, pago_adelantado).
ab_kind_pay(O)        :- target(O, women).
```

| | Concludes on | Correct |
|---|---|---|
| General rule alone | 49 | 31 (63%) |
| With the exceptions | 39 | 31 (79%): criminal recruitment 28 of 36, fraud 3 of 3 |

The rule stays silent on the 10 offers aimed at women: 3 sexual exploitation, 3 criminal recruitment, 4 other.
Across the 167 offers, none of the 16 that ask for an advance payment is criminal recruitment.

### Example 3. What kind of trap does an ordinary-sounding job point to?

```
kind_role(O, criminal) :- has(O, rol_plausible_gancho), not ab_kind_role(O).
kind_role(O, sexual)   :- has(O, rol_plausible_gancho), target(O, women).
ab_kind_role(O)        :- target(O, women).
```

| | Concludes on | Correct |
|---|---|---|
| General rule alone | 28 | 14 (50%) |
| With the exception | 28 | 20 (71%): criminal recruitment 14 of 20, sexual exploitation 6 of 8 |

None of the 8 offers aimed at women is criminal recruitment.

## Can the exceptions be learned?

`learn_exceptions.lp` states the search as an ASP program: clingo chooses up to two default rules and up to two
exceptions per default, minimising misclassified examples plus a cost of 2 per rule kept. Scored by 5-fold
stratified cross-validation repeated 10 times.

| Task | Hypothesis learned on all examples | Precision | Recall | Balanced accuracy |
|---|---|---|---|---|
| A. Criminal recruitment vs other documented offers, defaults only | `security`; `minors` | 0.82 ± 0.02 | 0.63 ± 0.01 | 0.73 ± 0.02 |
| A. With exceptions | `security`; `young` unless `women` | 0.82 ± 0.03 | 0.63 ± 0.02 | 0.73 ± 0.01 |
| B. Documented offers vs verified postings, defaults only | `sueldo_alto`; `empleo_fuera_estado` | 1.00 ± 0.00 | 0.37 ± 0.02 | 0.68 ± 0.01 |
| B. With exceptions | same hypothesis, no exception kept | 1.00 ± 0.00 | 0.37 ± 0.02 | 0.68 ± 0.01 |

Reading: with these data the learner keeps at most one exception, and it does not improve the held-out score.
The exceptions of the three examples are real but each rests on 2 to 10 offers, which is below what the search
can separate from noise. On the present sample the task behaves as a predictive one; the exception structure is
visible by hand and not yet learnable.

## Open questions

1. Is the target predictive (flag an offer) or inferential (conclude what kind of trap it is and why)? Examples 2
   and 3 are the inferential reading and are where the exceptions carry weight.
2. How many examples per exception would ILASP or Popper need? Not run yet.
3. `rol_plausible_gancho` is defined by the outcome (a credible role *used as a hook*), so it cannot hold of a
   verified posting. It is usable to tell kinds of trap apart (Example 3) but not to tell traps from postings.
4. A documented offer is known through what the press reported: an absent flag means *not reported*. Negation as
   failure over these facts reads "not reported" as "false".
5. Rules with `not` are outside OWL 2 QL. They would sit on top of the ontology, over the answers of the
   virtual knowledge graph.

## Limits

37 verified postings, all from formal job boards and four job categories. Press coverage over-represents heavily
reported cases. Counts are of documented offers, not prevalence.
