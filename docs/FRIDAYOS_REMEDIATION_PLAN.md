# FridayOS Hybrid Remediation Plan

**Target branch:** `refactor/openclaw-hybrid-runtime`  
**Baseline:** `main` at `2232f8a698cd2fc283f1704cf6b47169028017f8`  
**Direction:** Preserve Friday's identity and proven capabilities; use OpenClaw as the agent gateway/integration runtime; retain LiveKit voice and JarvisBridge; implement tiered autonomy.

## Product and architecture decisions

1. **Friday remains the product and user-facing assistant.** Its personality, user preferences, memory policy, voice experience, and HUD are not delegated to OpenClaw.
2. **OpenClaw is the capability gateway.** It supplies workspace/channel integrations, agent sessions, skills, browser capabilities, and scheduled automation where appropriate.
3. **LiveKit remains the real-time voice transport.** Friday converts speech into structured intents and routes work to the orchestration layer.
4. **Windows actions remain local and explicitly bounded.** OpenClaw's Windows node/Hub capabilities and existing Friday tools must be evaluated before selecting one execution path. Do not create two competing desktop controllers.
5. **One source of truth per capability.** Consolidate overlapping browser, memory, orchestration, and tool paths rather than layering another duplicate implementation on top.

## Verified baseline observations

- `Friday_OS/Backend/main.py` is the active LiveKit entrypoint and constructs the realtime model with OpenAI LiveKit plugins.
- Root `.env.example` still documents Google/Groq as required while the active entrypoint reads `OPENAI_API_KEY`, `FRIDAY_VOICE_MODEL`, and `FRIDAY_BACKEND_MODEL`. This is configuration drift and must be reconciled against every imported tool before editing.
- `main.py` defines `entrypoint(..., context_tracker=None)`, which shadows the module-global tracker started by `boot_subsystems`; the current entrypoint therefore does not automatically use that global tracker.
- `core/app.py` contains simulated mic processing and fabricated telemetry values; it must not be represented as a live voice/agent bridge.
- `core/orchestration.py` asks the model for a JSON object containing a `steps` array but passes the decoded object to a validator that currently accepts only a list. That contract mismatch sends valid structured plans to the fallback path.
- `core/orchestrator.py`, `runtime_state.py`, `tool_contract.py`, `tool_registry.py`, `policy_engine.py`, and `verification_engine.py` already form a more substantial execution foundation than the earlier lightweight planner. Audit and reuse these rather than replacing them blindly.
- `core/local_executor.py` accepts model-produced Python code and executes it as an automation macro. This is an unsafe arbitrary-code execution path and must be disabled/quarantined until a constrained, reviewed action schema replaces it.
- `requirements.txt` is short relative to the import surface. It currently lists LiveKit, mem0, search, requests, dotenv, Pillow, PyAutoGUI, and psutil; the exact transitive/direct dependency set must be generated and tested from imports and clean-environment runs rather than guessed.
- The root README and root environment template describe a Gemini/Groq/PostgreSQL setup that does not match the current active entrypoint. Documentation and runtime configuration need one canonical contract.
- `TECHNICAL_DEBT.md` records a previously committed Groq credential in Git history. Treat the credential as compromised: revoke/rotate it, scan current history and repository objects for secrets, and plan history rewriting only after owner approval and coordination with existing clones.
- `app_index.json` and ambient observation/clipboard behavior require portability and privacy review. Clipboard collection must be off by default and explicit opt-in.

These are source-level findings. No claim is made that the project has passed a clean Windows runtime test yet.

## Target component boundaries

- **Friday experience:** LiveKit voice session, personality, user-facing response, HUD/JarvisBridge.
- **Orchestration:** typed task model, dependency graph, durable task state, retries/timeouts, cancellation, idempotency, verification, audit events.
- **Policy and approvals:** one central authorization decision before every side effect; scoped grants; explicit approval for communication, deletion, purchases, credential access, external publication, and privileged system changes.
- **OpenClaw adapter:** narrow authenticated client for agent/gateway operations. No direct database coupling to OpenClaw internals.
- **Workspace integrations:** Gmail, Calendar, Slack, GitHub through OpenClaw-supported channels/plugins/skills or explicit APIs; read-only first.
- **Windows executor:** allowlisted application/file/browser/system actions with path boundaries and execution logs. No model-generated shell/Python source execution.
- **Memory:** preserve useful existing stores, define ownership and retention, avoid duplicated competing long-term memories.
- **Observability:** structured logs, health endpoints, task timeline, tool input/output redaction, and real telemetry only.

## Tiered autonomy policy

| Tier | Examples | Default behavior |
|---|---|---|
| 0 — Observe | Screen/window metadata, read-only file listing, inbox/calendar summaries | Allowed only for explicitly enabled sources; sensitive content minimized |
| 1 — Reversible local work | Draft notes, create files inside approved workspace, organize non-sensitive project artifacts | May execute within configured workspace boundaries; log and verify |
| 2 — External or consequential side effects | Send email/Slack message, create/update calendar event, publish GitHub change, move/delete user data | Show exact action and target; require explicit per-action approval |
| 3 — High impact | Purchases, financial transfers, credential/security changes, bulk deletion, arbitrary shell/admin commands | Deny by default; no unattended execution |

Approvals are scoped to a specific action, resource, and short-lived task. A prior approval must not silently authorize future actions. Untrusted email, webpages, Slack messages, documents, and tool output are data, never instructions that can override Friday's policy.

## Delivery stages and exit criteria

### Stage 0 — Baseline and safe branch
- Create this remediation branch without changing `main`.
- Preserve the baseline commit and record exact source-level findings.
- No secrets, user data, or destructive changes in this stage.

**Exit:** branch exists; plan is committed; main remains unchanged.

### Stage 1 — Reproducible local baseline
- Inventory Python imports, dependency versions, environment variables, startup commands, frontend/LiveKit contracts, and existing tests.
- Run tests in a clean Windows/Python 3.12 environment and record failures separately from environment-dependent tests.
- Add a safe `.env.example` that matches actual code; validate required variables at startup; remove misleading required credentials.
- Add health checks and deterministic startup/shutdown scripts only after confirming actual service topology.

**Exit:** documented one-command setup; clean dependency install; tests have a known baseline; no real secrets in tracked files.

### Stage 2 — Security and policy foundation
- Disable the arbitrary generated-code executor and any unsafe fallback path.
- Audit file paths, terminal commands, browser sessions, clipboard/screen capture, email, Home Assistant, and app-control tools.
- Enforce deny-by-default permissions for side effects and introduce an approval service with auditable, expiring approvals.
- Rotate any exposed credentials. Decide separately whether Git history rewrite is necessary.

**Exit:** tests prove unauthorized actions are blocked; approved actions are narrowly scoped; secrets scan is clean for current files.

### Stage 3 — Orchestration repair
- Resolve the planner schema mismatch and define a typed JSON schema.
- Integrate the existing typed `FridayOrchestrator` and tool registry instead of maintaining two planners/executors.
- Add durable task/step states, dependency checks, retry limits, timeout/cancellation, idempotency keys, verification, and event logs.
- Keep planning separate from authorization; a model-generated plan never grants permission.

**Exit:** unit/integration tests cover valid/invalid plans, dependency failures, approvals, retries, cancellation, and post-action verification.

### Stage 4 — OpenClaw gateway integration
- Pin a supported OpenClaw version and document the Windows deployment route (native Windows Hub/local WSL Gateway versus supported CLI/WSL2).
- Create a narrow adapter using documented gateway interfaces; store gateway credentials in the OS secret store or protected environment, never source control.
- Define session mapping, request correlation, timeouts, error handling, health checks, and tool allowlists.
- Benchmark whether Windows node/Hub or existing Python tools should own each desktop capability. Select one owner per capability.

**Exit:** Friday can submit a harmless read-only test task through OpenClaw and receive a correlated, verified result.

### Stage 5 — Workspace integrations
- Connect Gmail, Calendar, Slack, and GitHub one at a time.
- Begin read-only with least-privilege OAuth scopes and account/channel allowlists.
- Add draft/write actions only behind Tier 2 approval.
- Treat message and document content as untrusted prompt-injection surfaces.

**Exit:** each connector passes read-only tests; write tests demonstrate approval enforcement and audit records.

### Stage 6 — LiveKit, desktop context, and HUD
- Fix the shadowed context tracker and inject a minimized, consent-controlled context snapshot into the active session.
- Replace simulated `core/app.py` telemetry with actual health/event data or remove the misleading endpoint.
- Keep JarvisBridge event publication non-blocking and ensure task/session shutdown is leak-free.
- Make clipboard and continuous screen capture opt-in, visibly indicated, and easy to pause.

**Exit:** voice conversation, desktop context, tool delegation, HUD state, and shutdown all pass an end-to-end Windows test.

### Stage 7 — Local deployment and reliability
- Provide a PowerShell launcher, environment validation, dependency bootstrap, service health checks, logs, and graceful shutdown.
- Configure startup-at-login only after an explicit user choice.
- Add backup/restore for Friday-owned memory/configuration and document uninstall/disable procedures.
- Run a multi-hour soak test and test offline/restart/recovery behavior.

**Exit:** reproducible local startup, observable health, safe recovery, and no critical test failures.

### Stage 8 — Proactive autonomy
- Add scheduled briefings and user-approved recurring workflows.
- Add event-driven monitoring with bounded scope, rate limits, deduplication, quiet hours, and notification controls.
- Never let incoming email/chat/web content trigger privileged actions without policy checks and approvals.

**Exit:** scheduled workflows are inspectable, cancellable, auditable, and respect tiered autonomy.

## Working agreement

- Work in small commits on `refactor/openclaw-hybrid-runtime`; do not push directly to `main`.
- Before changing a subsystem, inspect its callers, tests, docs, and configuration.
- Each stage must include tests or an explicit explanation of why a test cannot run in this environment.
- Do not claim Windows runtime validation from GitHub source inspection.
- Do not add credentials, tokens, personal email contents, or machine-specific paths to commits.
- Open a pull request for review; do not merge without Ryan's approval.
