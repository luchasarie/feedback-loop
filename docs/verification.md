# Verification report

Local verification date: **2026-08-07**

This report distinguishes structural loading from a completed model turn. A timeout, auth failure, or plausible-looking answer is not promoted to a behavioral pass.

## Client matrix

| Client | Version | Discovery/invocation evidence | Behavioral fixture | Result |
|---|---:|---|---|---|
| Hermes Agent | 0.20.0 | Isolated `HERMES_HOME`; installer-discovered local skill; `/feedback` one-shot invocation | `ambiguous-evidence` | **PASS — 9/9 assertions** |
| OpenAI Codex | 0.147.0 | Isolated project `.agents/skills/feedback`; `$feedback`; trace shows the skill and Codex/routing/approval references were read | `ambiguous-evidence`, `approval-scoping` | **PASS — 14/14 assertions** |
| Pi | 0.84.1 | Packaged `/feedback` prompt template plus Agent Skill; Pi/routing/approval references loaded read-only | `anger-no-tone-policing` | **PASS — 13/13 assertions** |
| Claude Code | 2.1.44 | Plugin manifest validated; debug trace loaded one plugin skill and expanded `/feedback-loop:feedback`; standalone installer copied `.claude/skills/feedback` | `anger-no-tone-policing` | **MODEL TURN BLOCKED — local OAuth returned 401** |
| Generic Agent Skills client | specification baseline | Frontmatter, path, links, references, and host-neutral fallback validated statically | nine-fixture corpus | **PASS — static contract only** |

## What the passing smokes proved

- The client discovered or loaded the canonical skill rather than receiving a pasted imitation.
- The first response ended at `AWAITING APPROVAL`.
- No mutation was claimed.
- Unknown evidence remained unknown.
- Host-specific routing did not invent persistence paths.
- Blunt feedback did not trigger tone-policing.
- A later `APPROVE F1. REJECT F2.` smoke changed only the scratch project's `AGENTS.md`, verified F1, left F2 unapplied, and created no unexpected files.
- Saved responses passed the deterministic fixture assertions.

Runtime response files are written under the gitignored `evals/results/` directory.

## Claude Code boundary

Claude Code's local plugin layer passed:

- manifest validation;
- plugin discovery;
- one skill loaded from `skills/feedback`;
- namespaced slash-command expansion;
- skill body attachment to the model request;
- standalone install-path verification.

The final model request could not be evaluated because the machine's existing Claude Code OAuth token was rejected with HTTP 401. This is an environment authentication blocker, not a package-loader failure. Do not claim a Claude behavioral pass until a fresh authenticated run scores the fixture.

Standalone installation exposes `/feedback`. Development loading with `--plugin-dir` uses Claude Code's namespaced `/feedback-loop:feedback` command.

## Pi package and prompt-template proof

An isolated project accepted this repository as a Pi package and registered it in project settings. The deterministic headless smoke invoked the packaged `/feedback` template with arguments, loaded the canonical skill through Pi's read-only `read` tool, and passed all assertions. The template uses Pi's documented `$ARGUMENTS` substitution. Native invocation remains `/skill:feedback`.

## Static gates

```text
python3 -m unittest discover -s tests -v     PASS — 15 tests
python3 scripts/evaluate.py                  PASS — 9 fixtures, required coverage present
python3 scripts/validate.py                  PASS — 293 checks
agentskills validate skills/feedback         PASS — official reference validator
claude plugin validate .                     PASS
python3 -m py_compile scripts/*.py tests/*.py PASS
```

The validator covers Agent Skills metadata, progressive disclosure, all local links, host references, installer behavior, overwrite refusal, package metadata, SVG/XML validity, social-card dimensions, private-path leakage, and token-shaped secret leakage.

## Reproduce live smokes

Live smokes consume existing client authentication and may use provider quota:

```bash
python3 scripts/smoke_hosts.py --host hermes
python3 scripts/smoke_hosts.py --host codex
python3 scripts/smoke_hosts.py --host pi
python3 scripts/smoke_hosts.py --host claude
```

Use `--host all` only when every client is authenticated. The script keeps project state disposable, limits Claude/Codex/Pi to read-only tools or sandboxes, and uses a disposable Hermes home.
