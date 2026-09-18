#!/usr/bin/env python3
"""Check a TypeSafe /v1/systemone request before it is sent. No network, stdlib only.

Catches the mistakes that cost a round trip or a wrong answer: the retired preview
shape, out-of-range option and level counts, a Choice with no escape option, a Noul
whose wording asks for intensity, criteria that describe an option without saying
what it excludes, and a state field no question refers to.

Usage:
  python3 validate_request.py request.json [--strict]
  cat request.json | python3 validate_request.py -
Exit codes: 0 clean or warnings only, 1 errors (or warnings with --strict), 2 usage.
"""

from __future__ import annotations

import json
import re
import sys

PREVIEW_KEYS = {"document": "state", "prompts": "questions", "options": "criteria", "levels": "criteria"}
INTENSITY = re.compile(r"\bhow (much|many|severe|strong|good|bad|likely|well|important)\b", re.I)
ESCAPES = {"other", "none", "none_of_the_above", "unknown", "unclear", "not_applicable", "na"}


def text_of(value) -> str:
    """Flatten a string / object / array criterion into searchable text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(text_of(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(text_of(v) for v in value)
    return str(value)


def validate(req: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for old, new in PREVIEW_KEYS.items():
        if old in req:
            errors.append(f"top level uses the retired preview field '{old}'; v1 expects '{new}'")

    if "state" not in req:
        errors.append("missing 'state'")
    elif not isinstance(req["state"], (str, dict, list)):
        errors.append("'state' must be a string, object or array of text")

    model = req.get("model")
    if not model:
        errors.append("missing 'model'")
    elif model in {"jev-latest", "jev-preview"}:
        warnings.append(f"'{model}' is an alias that moves; pin a version such as jev-1.13.0 so thresholds stay valid")

    questions = req.get("questions")
    if not isinstance(questions, dict) or not questions:
        errors.append("'questions' must be a non-empty map of question id to question")
        return errors, warnings

    state_text = text_of(req.get("state"))
    referenced: set[str] = set()

    for qid, q in questions.items():
        where = f"questions.{qid}"
        if not isinstance(q, dict):
            errors.append(f"{where}: must be an object")
            continue
        qtype = q.get("type")
        instructions = q.get("instructions")
        criteria = q.get("criteria")
        referenced.update(re.findall(r"`([A-Za-z_][\w.\[\]]*)`", text_of(instructions)))

        if qtype not in {"choice", "score", "noul"}:
            errors.append(f"{where}: type must be choice, score or noul (got {qtype!r})")
            continue
        if not instructions:
            (errors if qtype != "noul" else warnings).append(f"{where}: instructions is empty")

        if qtype == "choice":
            if not isinstance(criteria, dict):
                errors.append(f"{where}: choice criteria must be a map of option to description")
                continue
            n = len(criteria)
            if n < 2:
                errors.append(f"{where}: a choice needs at least 2 options (got {n})")
            if n > 255:
                errors.append(f"{where}: a choice takes at most 255 options (got {n})")
            if not ESCAPES & {k.lower().replace(" ", "_") for k in criteria}:
                warnings.append(f"{where}: no escape option (other / none); the model cannot decline")
            described = [k for k, v in criteria.items() if v]
            if described and len(described) < n:
                warnings.append(f"{where}: {n - len(described)} of {n} options have no description")
            boundaries = [k for k, v in criteria.items()
                          if isinstance(v, dict) and not ({"not", "not_for", "excludes"} & set(v))]
            if boundaries and len(boundaries) == n:
                warnings.append(f"{where}: no option says what belongs in a neighbouring option instead")

        elif qtype == "score":
            if not isinstance(criteria, list):
                errors.append(f"{where}: score criteria must be an ordered array of level descriptions")
                continue
            if not 2 <= len(criteria) <= 10:
                errors.append(f"{where}: a score takes 2 to 10 levels (got {len(criteria)})")

        else:  # noul
            if criteria is not None:
                if not isinstance(criteria, dict) or not {"true", "false"} >= set(criteria) - set():
                    if not isinstance(criteria, dict) or not set(criteria) <= {"true", "false"}:
                        errors.append(f"{where}: noul criteria may only carry 'true' and 'false'")
            if INTENSITY.search(text_of(instructions)):
                warnings.append(f"{where}: reads as an intensity question; a noul answers yes/no, use a score for degree")

    if len(questions) == 1:
        warnings.append("only one question in this request; questions run in parallel, so ask everything the branch may need")

    if isinstance(req.get("state"), dict):
        missing = {p.split(".")[0].split("[")[0] for p in referenced} - set(req["state"])
        for name in sorted(missing):
            warnings.append(f"instructions reference `{name}`, which is not a field of state")
        unused = set(req["state"]) - {p.split(".")[0].split("[")[0] for p in referenced}
        for name in sorted(unused):
            warnings.append(f"state field '{name}' is never referenced by a question; send only what the questions need")
    elif state_text and not referenced:
        warnings.append("no question points at the state with a backticked path")

    return errors, warnings


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    strict = "--strict" in sys.argv
    path = sys.argv[1]
    raw = sys.stdin.read() if path == "-" else open(path).read()
    try:
        req = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: not valid JSON: {e}")
        return 1

    errors, warnings = validate(req)
    for e in errors:
        print(f"error   {e}")
    for w in warnings:
        print(f"warning {w}")
    if not errors and not warnings:
        print("clean: request matches the v1 contract")
    return 1 if errors or (strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
