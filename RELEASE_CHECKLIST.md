# v1.0.0 publication checklist

This is the final external-action gate. Completing the local build does not authorize public repository creation, push, release, marketplace submission, or social posting.

## Current local candidate

- [x] Canonical Agent Skills package
- [x] Hermes, Claude Code, Codex, Pi, and generic adapters
- [x] Safe installer with overwrite refusal, timestamped backups, and rollback tests
- [x] Pi package metadata and `/feedback` prompt template
- [x] README, visual identity, social card, security/contribution materials
- [x] Nine behavioral fixtures and deterministic evaluator
- [x] Hermes behavioral smoke
- [x] Codex behavioral smoke
- [x] Pi package/prompt behavioral smoke
- [x] Claude Code manifest, plugin loader, slash expansion, and installer smoke
- [ ] Claude Code authenticated behavioral fixture — blocked locally by expired OAuth
- [x] Private-path and token-shape scan
- [x] Official-source architecture note passes strict citation verification

## Required final local gates

```bash
python3 -m unittest discover -s tests -v
python3 scripts/evaluate.py
python3 scripts/validate.py
uvx --from skills-ref==0.1.1 agentskills validate skills/feedback
uvx ruff==0.16.2 check scripts tests
uvx codespell==2.4.3 README.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md CHANGELOG.md RELEASE_CHECKLIST.md docs skills prompts scripts tests evals/fixtures .github --skip='*.png,__pycache__/*' --ignore-words-list='nd,te'
claude plugin validate .
git diff --check
```

Record the exact candidate commit and clean-worktree fingerprint after the final local commit. A late edit invalidates the gate packet.

## Proposed GitHub settings

| Setting | Value |
|---|---|
| Owner/repository | `luchasarie/feedback-loop` |
| Visibility | Public |
| Description | Turn blunt AI-agent feedback into evidence, scoped improvements, explicit approval, and verified learning. |
| Website | `https://agentskills.io/` |
| Default branch | `main` |
| Issues | Enabled |
| Discussions | Disabled for V1 |
| Wiki | Disabled |
| Social preview | `assets/social-card.png` |
| License | MIT |

Proposed topics:

```text
agent-skills ai-agents claude-code codex pi hermes-agent developer-tools prompt-engineering
```

## Publication sequence — requires explicit approval

1. Create the public repository without an auto-generated README, license, or `.gitignore`.
2. Add the approved remote and push the exact reviewed `main` commit.
3. Apply description, website, topics, issue settings, and social preview.
4. Confirm the public tree and rendered README match the local commit.
5. Confirm GitHub Actions passes on the public commit.
6. Create annotated tag `v1.0.0` and a GitHub release from `CHANGELOG.md`.
7. Re-run install commands from the public URL in isolated homes/projects.
8. Publish no marketplace listing until post-release host evidence warrants it.

## Stop conditions

Do not publish if the candidate is dirty, any static/unit gate is red, a private-leak scan is red, remote links other than the intentionally nonexistent pre-publication repository URL fail, or the final public action has not been explicitly approved.
