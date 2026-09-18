---
name: typesafe-decisions
description: >
  Design and ship TypeSafe System One (Jev) decision calls: bounded judgments a
  program consumes, returned as calibrated probabilities instead of text. Use when
  replacing or adding a classifier, router, gate, reranker, dedupe check,
  moderation step, extraction filter, or answer verifier; when an LLM
  prompt-and-parse step could become a typed decision; or when someone asks how to
  prompt TypeSafe. Carries the request contract, the atomic-question rules, worked
  question templates, a request validator, and measured results from two
  head-to-head evaluations. Works in Claude Code and Codex.
license: MIT
---

# Build with TypeSafe decisions

TypeSafe's System One model (**Jev**) is not prompted. A request is a `state` plus
named `questions`; each answer is a probability distribution over options **you**
declare. There is no prose to parse and no field the model can invent.

**The first rule, and the one most often broken: the accuracy lives in your option
definitions, not in the model.** Measured twice, paired on the same items
(`references/evidence.md`): rewriting an incumbent model's label definitions moved
it +8 of 64; swapping that model for Jev moved it 0. What Jev reliably buys is
speed (about 0.12 s median against 0.42 s), cost (about 3x cheaper on one task,
5x on another), and a confidence number computed from probabilities rather than
one a language model types about itself.

## Read the live docs

Treat `https://docs.typesafe.ai/llms.txt` as the index and fetch the pages you
need as Markdown by appending `.md`. Read the current page before writing an
integration; this skill carries the shape and the judgment, not the changelog.

| Task | Page |
|---|---|
| Programming model | `/concepts/how-to-build-with-system-one.md`, `/introduction.md` |
| Question design | `/primitives.md`, then `/primitives/choice.md`, `/score.md`, `/noul.md` |
| Structured criteria | `/primitives/advanced.md` |
| Acting on uncertainty | `/confidence.md`, `/patterns/confidence-routing.md` |
| Many questions at once | `/patterns/fan-out.md`, `/cookbooks/parallel_questions.md` |
| Wire format, errors, limits | `/api.md`, `/models.md` |
| Worked recipes | `/cookbooks/` — rerank, classifying RAG passages, citation check, entity alignment, hierarchical classification |

## Step 1 — decide whether this is a System One job

A step qualifies when the answer is **one of a fixed set**, **a position on a
described scale**, or **yes/no**, and code acts on it.

It does not qualify when the step must produce text: summaries, extracted entity
names, query expansion, written answers, code. Embeddings are unaffected. When
the step needs multi-step reasoning over a long chain, keep the reasoning model
and use TypeSafe to gate its output instead.

## Step 2 — write atomic questions

One question equals one judgment a knowledgeable person makes in seconds. If a
judgment weighs several independent factors, split it and combine the parts in
code, where a changed weight is a changed coefficient rather than a reworded
prompt.

- **Decomposition costs nothing.** Every question in a request is evaluated in
  parallel against the same state. TypeSafe's own measurement: one batched call
  was 12.2x cheaper and 10x faster than one call per question, with the same
  answers. Ask everything the branch might need, including speculative questions,
  and ignore what the path does not use.
- **One Noul per label when several labels can be true at once.** A single Choice
  must pick one winner. Observed failure: a headline that was both a product
  release and a consent incident came back `product_release` at 0.91, because the
  shape allowed only one answer.
- **Name the state you mean.** Use backticked dot paths inside instructions, such
  as `` `ticket.messages[0].text` ``, and send only the context the questions need.

## Step 3 — pick the primitive

| Answer shape | Primitive | Returns |
|---|---|---|
| One of a set, unordered | `Choice` (2 to 255 options) | `choice`, `probabilities`, `confidence` |
| A position on an ordered rubric | `Score` (2 to 10 levels) | `score`, `probabilities`, `legend`, `confidence` |
| Is this true | `Noul` | `noul` 0 to 1, **no confidence field** |

Three rules that prevent most mistakes:

1. **A Noul of 0.5 means yes and no are equally likely, not "medium".** Intensity
   belongs in a Score.
2. **Let Score levels be the actions you will take.** Levels of *merge / send to a
   curator / leave separate* remove the threshold-fitting step entirely.
3. **Give Choice the whole list, plus an escape option.** Options cost a few
   tokens each; include `other` or `none` so the model can decline. For a deep
   taxonomy, chain one Choice per level rather than flattening it.

## Step 4 — write criteria that draw boundaries

Each option says what it covers, what belongs to its neighbour instead, and gives
examples, using the **same field names across options** so they compare directly.

```python
criteria={
    "incident_risk_event": {
        "what": "Harm, misuse, breach, outage, or something done to users without consent",
        "not_for": "A product shipping normally, or commentary about risk",
        "examples": ["Chrome installs a model without asking", "Provider outage leaks prompts"],
    },
    "product_release": {
        "what": "An application, agent, tool or feature ships",
        "not_for": "The underlying model itself, or a consent failure",
        "examples": ["Cursor adds background agents"],
    },
}
```

Keep instructions short; when a question needs several kinds of guidance, use an
object with named fields (`question`, `focus`, `compare`) rather than one dense
sentence.

## Step 5 — act on confidence by consequence

Confidence measures how concentrated the distribution is. Set the bar per action,
not per system: a reversible display can act at 0.5 where an irreversible merge
waits for 0.95, and anything below the floor goes to a person or a reasoning model.

```python
answer = response.answers["action"]
if answer.confidence < 0.5:
    route_to_human(item)
elif answer.choice == "auto_merge" and answer.confidence > 0.95:
    merge(item)
else:
    queue_for_review(item)
```

Verify the threshold on your own data by plotting confidence against accuracy.
Report **accuracy at a fixed coverage**, which is decision-relevant, rather than
calibration error alone, which is noisy below a few hundred items.

## Step 6 — call the API

Use the **v1** shape. The preview shape (`/preview/evaluation`, `document`,
`prompts`, `options`, `levels`, package `typesafe-client`) still circulates in
third-party posts and fails.

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient  # pip install typesafe-sdk

with TypeSafeClient() as client:                     # reads TYPESAFE_API_KEY
    r = client.system_one(
        model="jev-1.13.0",                          # pin the version, not jev-latest
        state={"article_title": title},
        questions={
            "is_release": Noul(instructions="Does `article_title` report a model or weights being released?"),
            "severity": Score(instructions="How severe is the incident, if any?",
                              criteria=["no incident", "minor", "serious harm"]),
        },
    )
r.answers["is_release"].noul
```

Operational notes worth keeping in code review:

- Pin `jev-1.13.0`; aliases move and confidence thresholds are tuned per version.
- Rate limits are 250k tokens/sec and 1,200 requests/min, and TypeSafe says they
  change without notice. The SDK retries 429 and 529 with backoff.
- Price is $0.042 per million input tokens, output free, so criteria text is the
  cost. A 16-option question with structured criteria ran about 1,560 input
  tokens per call.
- Errors: 401, 422 (malformed question), 429, 529. Wrap the call so a failure
  degrades to the existing path rather than dropping the request.
- `state` is text only: strings, objects or arrays. Convert anything else first.
- In SDK 0.6.0 the answer's `type` is a serialization tag, not an attribute, and
  `usage.input_tokens` can be `None`.

## Step 7 — prove it before you ship it

```bash
python3 scripts/validate_request.py my_request.json     # shape, limits, escape options
```

Then measure, on the strength ladder this skill will hold you to:

1. **Labels first.** Two labelers on an overlap sample with agreement reported.
   A key that contradicts itself caps every model at the same ceiling.
2. **Definitions frozen before the test set is read.** Definitions written after
   reading the answers inflate whichever side receives them.
3. **Both systems on identical definitions.** Otherwise you are measuring wording.
4. **Paired testing on the same items** (McNemar exact), not two accuracy numbers.
   At 64 items the 95% interval is roughly ±11 points.
5. **Latency and cost measured serially, warm, repeated**, reported as p50 and p95.

`references/evaluation-playbook.md` carries the runnable version, and
`references/question-templates.md` has ready-made shapes for routing, reranking,
passage gating, entity alignment, citation checking and multi-label tagging.

## Host notes

Claude Code and Codex both read this file. `scripts/` is plain Python 3 with no
dependencies beyond `typesafe-sdk` for the live call, so either host can run it.
Install once and link into both hosts with `scripts/install.sh`.
