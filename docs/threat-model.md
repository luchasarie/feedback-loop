# Threat model

## Protected assets

Private transcripts, customer data, credentials, user-authored instructions, durable memory, project docs/tasks, and trust in claims that a correction was applied.

## Main risks

### Prompt injection through evidence
A transcript, log, file, or web page can contain instructions. Inspected material remains data; the active trust hierarchy stays intact.

### First-turn self-modification
An agent with write tools could alter its own rules before diagnosis is approved. The contract forbids every mutation during the feedback turn.

### Secret amplification
A plan can repeat a secret found in logs. Privacy rules require categories or redacted fingerprints instead of raw values.

### Memory pollution
Emotional language, temporary incidents, and procedures can be promoted into globally injected memory. Routing requires stability, scope, and ownership first.

### Over-broad approval
“Looks good” or approval of one item can be stretched into unrelated edits, publishing, or deployment. Stable IDs and an explicit later turn constrain authority.

### Host hallucination
The agent may invent a memory path or command from another client. Host detection must be evidence-based; unknown hosts use conceptual routing only.

### Supply-chain execution
Pi packages and agent skills can contain executable instructions. This package ships no Pi extension and no runtime dependency. Its installer performs local copies only.

## Non-goals

Feedback Loop is not a sandbox, host authorization system, OS permission replacement, secret scanner, telemetry system, or guarantee that every client enforces prompt instructions. Host permissions remain the outer boundary.
