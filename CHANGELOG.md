# Changelog

All notable changes to Feedback Loop are documented here.

The project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.0] - 2026-10-20

### Added

- Privacy policy, [PRIVACY.md](PRIVACY.md), linked from the README and from the plugin manifest's `privacyPolicyUrl`. The manifest also links GitHub issues as `supportUrl`.
- Plugin directory icon, `.claude-plugin/icon.png`: the loop mark rendered at 1024 × 1024 on its own dark background. The validator checks its size.

### Fixed

- The loop mark's glow filter no longer clips into visible squares around the spark and check mark.

## [1.0.0] - 2026-08-07

### Added

- Standards-first `feedback` Agent Skill.
- Host adapters for Hermes Agent, Claude Code, OpenAI Codex, Pi, and unknown clients.
- Evidence-first, plan-only feedback workflow with explicit approval IDs.
- Persistence routing, privacy boundaries, and a collaboration-contract lane.
- Pi `/feedback` prompt-template shim.
- Cross-platform installer, static validator, behavioral evaluation fixtures, and rollback fault-injection tests covering files, directories, valid symlinks, dangling symlinks, and backup-name collisions.
- Versioned live compatibility receipts for Hermes, Codex, Pi, and Claude Code's loader boundary.
- Public README, workflow graphics, social preview, CI, issue forms, and publication checklist.
