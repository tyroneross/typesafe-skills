# Evaluation playbook

Run this before replacing anything in production. Each rung exists because
skipping it produced a wrong conclusion in a real evaluation.

## 1. Fix the answer key first

- Two labelers on at least an overlap sample; report a chance-corrected agreement
  figure (Krippendorff's alpha is the safe default).
- Adjudicate disagreements and write the rule that settled each one into the
  definitions.
- A key that contradicts itself caps every system at the same ceiling. In one run,
  9 of 64 rows were wrong for every arm and 28 right for every arm, so only 27
  rows could separate anything.

## 2. Freeze definitions before reading the test labels

Definitions written after inspecting the answers inflate whichever side receives
them; the effect has a name, adaptive overfitting, and no fixed size. Use a
dev split for iteration and keep the test split sealed.

## 3. Give both systems the same definitions

Otherwise the comparison measures wording. Measured: the same model scored 38 and
46 on one test purely from a definition rewrite.

## 4. Size the sample to the effect

At 64 items a 95% Wilson interval is about ±11 points; roughly 250 to 300 items
are needed to resolve a 7-point difference. Report the interval beside every
accuracy figure.

## 5. Test paired, not side by side

Both systems answer the same items, so use McNemar's exact test on the discordant
pairs. Fewer than 6 disagreements cannot reach significance in any direction.

## 6. Measure operations honestly

- Latency: serial, warm, repeated, reported as p50 and p95, with the eval host idle.
- Cost: report tokens per item as well as dollars, since rate cards change.
- Count failures and retries; a fallback that rescues a failed call still cost a
  round trip.

## 7. Prefer selective accuracy to calibration error

Report accuracy at a fixed coverage, such as "97.6% on the 53% of items above 0.9
confidence". Expected calibration error is binning-dependent and biased at small
sample sizes; if you report it, bootstrap an interval.

## 8. Have someone else reproduce it

Two independent reviewers reading the raw logs found that a reported 7-item
accuracy gain disappeared once the control arm received the same definitions.
Publish the logs, not the summary.
