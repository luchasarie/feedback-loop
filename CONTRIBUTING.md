# Contributing

Feedback Loop should stay small, portable, and honest.

## Useful contributions

- A verified host adapter based on current primary documentation.
- A fixture that catches a real behavioral regression.
- Clearer wording that reduces blame, apology theater, or over-correction.
- A portability fix that keeps the canonical skill host-neutral.
- Accessibility or rendering improvements to the public assets.

## Ground rules

1. Open an issue before adding a runtime, persistence class, or executable dependency.
2. Keep host-specific paths and commands in `skills/feedback/references/hosts/`.
3. Do not add telemetry, network calls, or automatic self-modification.
4. Do not weaken the first-turn plan-only gate.
5. Do not require users to sanitize anger before feedback can be processed.
6. Add or update a fixture for every behavioral change.

## Local checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
python3 scripts/evaluate.py
uvx --from skills-ref==0.1.1 agentskills validate skills/feedback
uvx ruff==0.16.2 check scripts tests
uvx codespell==2.4.3 README.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md CHANGELOG.md RELEASE_CHECKLIST.md docs skills prompts scripts tests evals/fixtures .github --skip='*.png,__pycache__/*' --ignore-words-list='nd,te'
```

For runtime adapters, include the exact client version, invocation, isolated fixture, and redacted output used for verification.

## Pull requests

Describe the failure mode, smallest contract change, affected hosts, checks run, and remaining limitations. By contributing, you agree that your contribution is licensed under the MIT License.
