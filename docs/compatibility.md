# Compatibility model

Feedback Loop uses the Agent Skills format as its portable core and keeps host-specific behavior in reference adapters.

## Support levels

| Host | Discovery | Invocation | Persistence-aware | Local verification |
|---|---|---|---|---|
| Hermes Agent | Native skill directory | `/feedback` | Yes | Behavioral pass |
| Claude Code | `.claude/skills` or plugin | `/feedback` standalone; `/feedback-loop:feedback` as plugin | Yes | Loader pass; model turn auth-blocked |
| OpenAI Codex | `.agents/skills` | `$feedback` | Yes | Behavioral pass |
| Pi | package or Agent Skills directories | `/skill:feedback` or packaged `/feedback` template | Yes | Behavioral pass |
| Generic Agent Skills client | Standard `SKILL.md` | Host-specific | Safe fallback | Static contract pass |

“Persistence-aware” means the skill knows where a change may belong. It does not mean the feedback turn writes there.

## Versioned verification

Compatibility claims should record client and version, discovery method, invocation, isolated fixture, evidence the skill loaded, first-turn immutability, routing correctness, and later scoped-approval behavior. A timeout or plausible-looking answer is not a pass.

See the dated [verification report](verification.md) for exact versions, assertions, evidence boundaries, and reproduction commands.

## Shared installation

Codex and Pi both discover standard skills from `~/.agents/skills`. Installing there reduces duplicate copies. Claude Code uses its own skill directory or plugin mechanism. Hermes discovers skills from its configured profile skill library.

The included installer copies rather than symlinks for predictable behavior across operating systems. It refuses to overwrite by default.

## Known command differences

- Hermes and standalone Claude Code installs: slash command by skill name.
- Claude Code plugin loading: namespaced `/feedback-loop:feedback` command.
- Codex: dollar-prefixed explicit skill mention.
- Pi: `/skill:<name>` for skills; a packaged prompt template provides `/feedback` as a convenience shim.

The canonical skill never hard-codes its invocation into the diagnosis workflow.
