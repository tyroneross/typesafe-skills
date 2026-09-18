# Measured evidence behind this skill

Two head-to-head evaluations, run 17-18 September 2026. Both paired on the same
items, both scored by exact string match against a pre-existing answer key.

## Article subcategory, 77 articles, 12 labels

| Arm | Correct | p50 | Cost / 1k | Calibration error | At confidence >= 0.9 |
|---|---|---|---|---|---|
| Regex ladder (live in production) | 26 | ~0 ms | $0 | 0.104 | never reaches 0.9 |
| gpt-5.6-luna (shipped, switched off) | 65 | 1,323 ms | $0.182 | 0.130 | 88.7% on 80.5% |
| jev-1.13.0 | 66 | 136 ms | $0.037 | 0.050 | 97.6% on 53.2% |

McNemar exact between the two models: p = 1.00. Source: atomize-ai
`docs/10-reports/2026-09-17-classifier-bakeoff.html`, commit a2ff5053c.

## Search query intent, 64 queries, 16 labels

| Arm | Correct | p50 | Cost / 1k |
|---|---|---|---|
| Regex tier alone | 38 | ~0 ms | $0 |
| gpt-oss-20b, incumbent prompt (9 of 16 labels described) | 39 | 424 ms | $0.167 |
| gpt-oss-20b, shared definitions (all 16 described) | 46 | 496 ms | $0.227 |
| jev-1.13.0, same shared definitions | 46 | 121 ms | $0.066 |

Paired tests: incumbent prompt vs Jev, 13 to 6, p = 0.17. Shared definitions vs
Jev, 4 to 4, p = 1.00. Only 27 of the 64 rows discriminated between arms; 28 were
answered by every arm and 9 by none.

## Short candidate tests, 12 to 16 items each

| Stage | Shape used | Result |
|---|---|---|
| Event typing | Choice over 8 types | 15/16, including 8/8 on the repo's own test labels |
| Entity resolution | Score whose levels are merge / curator / separate | 13/16; all three misses were parent-vs-subsidiary pairs where the label is arguable |
| Retrieved-passage gate | 3 Nouls per passage in one request | relevance 12/12, contradiction 11/12, both planted prompt injections caught |
| Citation verification | Choice over supports / contradicts / says nothing | 12/12, mean confidence 0.98 |

Labels for all but the event rows were written by the same agent that ran the
test, so these show the question design works, not production accuracy.

## Question shape, measured on the same 64 queries

| Shape | Correct |
|---|---|
| v1: one-line string descriptions | 45 |
| v2: `means` / `not` objects | 46 |
| v3: `what` / `not_for` / `examples`, an `unclear` escape option, plus three facet Nouls in the same call | 47 |

v2 versus v3 paired: 2 to 3, exact p = 1.00, so the gain is within noise on this
sample. What the v3 shape adds beyond the count: the three extra questions cost
one shared request, and `needs_clarification` correctly ranked the empty string
(0.97) and the single stopword (0.96) at the top.

## Multi-label shape, 16 headlines

One Noul per event type instead of one Choice. The expected label fired on 16 of
16, and 4 headlines carried a defensible second label that a single Choice had to
discard, including the case that motivated the change:

- "Chrome ships an on-device AI model without asking users": incident_risk_event
  0.92 and model_release 0.71. The single-Choice version returned product_release
  at 0.91 and no way to say both.
- "A bank deploys an AI copilot in production": deployment_adoption 0.95 and
  product_release 0.95.

## What the numbers support

- Speed and cost differences are large and repeatable.
- Accuracy differences between a current-generation LLM and Jev were not
  detectable on either task once both received the same definitions.
- Confidence is usable as a gate with Jev and is not with a self-reported score.
- Both evaluations were reviewed independently by Claude Opus 5 and Claude Fable
  5.1; both reproduced every figure from raw logs and both rejected an
  accuracy-based adoption claim.
