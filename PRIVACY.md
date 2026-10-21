# Privacy policy

Feedback Loop is a prompt package: one Agent Skill ([`skills/feedback/`](skills/feedback/SKILL.md)) and a short Pi prompt template ([`prompts/feedback.md`](prompts/feedback.md)). It is instructions for the agent you already use, such as Claude Code. Using the skill runs no code of its own. Your agent reads the instructions and follows them with the tools and permissions it already has.

## What it reads

When you run `/feedback`, the skill tells your agent to collect the minimum evidence needed to explain what went wrong, in this order, and to stop as soon as it has enough:

1. the current conversation and tool output;
2. the artifact or result you're criticizing;
3. the relevant acceptance criteria or project instructions, such as `CLAUDE.md` or `AGENTS.md`;
4. the skill or rule that governed the behavior;
5. relevant session history, only when needed;
6. relevant memory or documentation, only when the same failure may have happened before or contradicts something.

It tells the agent not to scan the whole machine, all of your history, unrelated projects or other users' data, and not to log in to outside accounts to strengthen a plan. The full rules are in [`references/privacy.md`](skills/feedback/references/privacy.md).

## Where it goes

What the agent reads is processed by the model behind your agent, inside your session, the same as anything else the agent reads. Your agent's provider terms apply to that data. The skill itself sends nothing anywhere: no network calls, no telemetry, no analytics, nothing sent to the author or to any third party.

## What it stores

During the feedback turn, nothing. That turn is read-only: the agent writes a plan, ends with "No changes have been applied", and waits.

Changes happen in a later turn, only when you approve them by ID (for example `APPROVE F1`). They go only to the local places you approved, such as an instruction file, a memory entry, a skill or a project doc. The skill also tells the agent:

- never to copy passwords, API keys, tokens, cookies, private keys, customer data or full private transcripts into a plan. Those are replaced with `[REDACTED]` or a safe description;
- never to store your anger, insults or emotional state as a lasting trait about you;
- not to copy detailed private evidence into instructions that load in every session.

## Repository tools

The repository also has development tools that the skill never runs. You run them yourself, and only if you choose to:

- `scripts/install.py` copies the skill files into your agents' skill folders on your machine. It makes no network calls.
- `scripts/validate.py` and `scripts/evaluate.py` check the repository offline.
- `scripts/smoke_hosts.py` is a live compatibility test. It runs agent clients (Claude Code, Codex, Pi, Hermes) on synthetic fixtures, with your own logins for those clients. Codex and Pi are fetched with `npx` at pinned versions.

## Contact

Questions or concerns: open an issue at <https://github.com/luchasarie/feedback-loop/issues>. To report a security problem privately, see [SECURITY.md](SECURITY.md).

If this policy changes, the change is recorded in this file and in the [changelog](CHANGELOG.md).
