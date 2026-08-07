# Security

Feedback Loop is a prompt package, but prompt packages can still cause harm.

## Security contract

The canonical skill:

- performs no network call on its own;
- requires read-only evidence gathering during the feedback turn;
- forbids secret reproduction in plans;
- forbids first-turn file, memory, skill, configuration, or remote mutation;
- requires explicit, item-scoped approval before later changes;
- treats instructions found inside evidence as data, not authority.

The installer copies local files only. It does not download dependencies, execute package hooks, or overwrite an existing installation unless `--force` is supplied. A forced replacement first creates a timestamped sibling backup.

## Reporting a vulnerability

Report concrete exploit paths privately to the repository owner before publishing them. Include the affected version and host, exact invocation, minimal reproduction, impact, and containment if known. Never include real credentials, private transcripts, or other people's data.
