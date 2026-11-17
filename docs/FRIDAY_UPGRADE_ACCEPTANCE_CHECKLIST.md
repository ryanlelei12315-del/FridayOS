# FridayOS Upgrade Acceptance Checklist

This checklist is the release source of truth. A feature is not complete because code exists.
Mark PASS only when its acceptance test/evidence passes. Use PARTIAL, FAIL, or NOT STARTED otherwise.
Never mark a hardware-dependent workflow PASS from source inspection alone.

## Status definitions
- [ ] PASS — implementation exists and its acceptance test/evidence passes.
- [ ] PARTIAL — implementation exists but evidence or edge cases are incomplete.
- [ ] FAIL — acceptance test fails or a regression is confirmed.
- [ ] NOT STARTED — not implemented.

## 0. Baseline and change control
- [ ] Record baseline commit and clean/dirty working-tree state.
- [ ] Preserve user changes; never reset or overwrite an unreviewed working tree.
- [ ] Keep upgrades on a feature branch and merge only after regression checks.
- [ ] Record Python, OS, LiveKit Agents, and plugin versions.
- [ ] Record test command, result, and date for each release candidate.

## 1. Agent session lifecycle
- [ ] LiveKit room connection succeeds and failures are reported.
- [ ] One AgentSession is created per room/job.
- [ ] Agent starts exactly once per session.
- [ ] Voice mode configures audio input and noise cancellation.
- [ ] Console mode disables audio output.
- [ ] Greeting uses the same ambient context snapshot as the session.
- [ ] Room shutdown/cancellation exits cleanly.
- [ ] Ambient monitor task is cancelled and awaited.
- [ ] JarvisBridge publisher is drained, cancelled, and awaited.
- [ ] Optional JarvisBridge failures never crash the LiveKit session.
- [ ] Concurrent room sessions do not share session-local tasks or queues.
- [ ] Repeated connect/disconnect cycles do not leak tasks or threads.

## 2. Intelligence and orchestration
- [ ] Voice and text sessions use consistent identity, tools, and context policy.
- [ ] Model configuration is validated at startup.
- [ ] Provider errors and timeouts have safe, observable fallbacks.
- [ ] Planner output supports the documented JSON schema.
- [ ] Plans are bounded, ordered, and dependency-validated.
- [ ] Invalid plans never trigger tools.
- [ ] Cancellation propagates instead of being swallowed.
- [ ] Tool execution is separate from planning and requires authorization.
- [ ] Multi-step progress and final results reflect actual tool outcomes.

## 3. Background task engine
- [ ] Persistent task queue and task identifiers.
- [ ] Pending/running/succeeded/failed/cancelled states.
- [ ] Restart recovery and idempotent task claiming.
- [ ] Retry policy with bounded attempts and backoff.
- [ ] Timeouts, cancellation, and dead-letter handling.
- [ ] Task history and structured audit events.
- [ ] Background work does not block realtime audio.

## 4. Skills and integrations
- [ ] Skill manifest/schema and versioning.
- [ ] Discovery and explicit installation workflow.
- [ ] Per-skill permission declarations.
- [ ] Approval before enabling sensitive capabilities.
- [ ] Tool allowlist and runtime permission enforcement.
- [ ] Plugin errors are isolated and logged.
- [ ] Disable/uninstall workflow and dependency checks.

## 5. Memory
- [ ] PostgreSQL configuration is validated without exposing credentials.
- [ ] Memory schema and migrations are deterministic.
- [ ] Conversation memory persists across restarts.
- [ ] Semantic retrieval returns source/provenance metadata.
- [ ] Duplicate and stale memory handling.
- [ ] User correction and deletion workflows.
- [ ] Sensitive clipboard or screen data is not stored by default.
- [ ] Memory failures degrade gracefully without breaking voice.

## 6. Desktop intelligence
- [ ] Screen capture permission and error handling.
- [ ] Screen interpretation is grounded in current captures.
- [ ] Active application/process context is available.
- [ ] Mouse and keyboard actions are allowlisted.
- [ ] Destructive actions require confirmation.
- [ ] Actions are verified against resulting UI state.
- [ ] Undo/compensation exists where technically possible.
- [ ] Windows 11 compatibility is manually verified.

## 7. Friday interface
- [ ] HUD listening/thinking/speaking/idle/error states.
- [ ] Voice activity visualization.
- [ ] Task monitor with status and progress.
- [ ] Notifications and actionable errors.
- [ ] Memory inspection and correction UI.
- [ ] Skill and permission management UI.
- [ ] Settings and diagnostics panel.
- [ ] Keyboard accessibility and responsive desktop layout.

## 8. Security and reliability
- [ ] Secrets are loaded from environment/secret manager and never logged.
- [ ] Clipboard and screen context follow least-privilege rules.
- [ ] Email, file deletion, financial, and external communication actions require approval.
- [ ] Tool inputs are validated and bounded.
- [ ] Audit log records actor, action, timestamp, and outcome without secret payloads.
- [ ] Graceful shutdown closes owned resources.
- [ ] Structured logs and actionable error reporting.
- [ ] Unit, integration, and regression tests pass.
- [ ] Dependency/security review completed.

## 9. Release gates
- [ ] Gate 1 — architecture and dependency baseline recorded.
- [ ] Gate 2 — unit tests pass.
- [ ] Gate 3 — integration tests pass.
- [ ] Gate 4 — Windows 11 voice, console, and desktop workflows manually verified.
- [ ] Gate 5 — permission and security tests pass.
- [ ] Gate 6 — full regression suite passes.
- [ ] Gate 7 — documentation, known limitations, and release notes complete.

## Implementation log
| Date | Area | Status | Evidence / commit |
|---|---|---|---|
| 2026-11-17 | Agent session lifecycle foundation | PARTIAL | feat/friday-runtime-foundation; local LiveKit runtime tests required |
| 2026-11-17 | Planner schema validation | PARTIAL | Unit tests added; execute locally before PASS |
