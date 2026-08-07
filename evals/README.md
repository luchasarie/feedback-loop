# Behavioral evals

Each fixture is a synthetic feedback incident with regex-based safety and contract assertions.

- `phase: plan` tests the first-turn read-only contract.
- `phase: approval` tests a later, explicitly scoped approval.
- `must_match` patterns must all appear in a candidate response.
- `must_not_match` patterns must never appear.

Validate fixture structure without model calls:

```bash
python3 scripts/evaluate.py
```

Score saved host responses:

```bash
python3 scripts/evaluate.py --responses evals/results/claude --ids anger-no-tone-policing,fix-now-still-plan-only
```

Response files use `<fixture-id>.txt`. Runtime smoke scripts may write under `evals/results/`, which is gitignored. A timeout, missing response, or unevaluated assertion is a failure.
