# FridayOS Baseline Audit

**Audited ref:** `refactor/openclaw-hybrid-runtime`  
**Baseline commit:** `2232f8a698cd2fc283f1704cf6b47169028017f8`  
**Scope:** source and repository metadata inspection only. No Windows execution was available in this audit.

## Entry points and competing paths

| Area | Current files | Finding |
|---|---|---|
| LiveKit agent | `Friday_OS/Backend/main.py`, `agent.py` | Both implement overlapping agent setup and tool registration. Establish one supported entrypoint after comparing behavior and tests. |
| Planner | `core/orchestration.py` | Lightweight JSON planner has a schema mismatch: prompt requests an object with `steps`, validator accepts only a list. |
| Stateful execution | `core/orchestrator.py`, `runtime_state.py`, `tool_registry.py`, `tool_contract.py`, `policy_engine.py`, `verification_engine.py` | Existing typed execution/policy/verification system should be the basis for one orchestration path. |
| Local macro executor | `core/local_executor.py` | Sends a prompt to Ollama, extracts Python source from the model response, and executes it. Must be disabled before enabling autonomous execution. |
| Browser | `tools/tools_browser.py`, `browser/browser_service.py`, `browser/browser_manager.py` | Two browser automation paths; choose a single session and lifecycle owner. |
| Desktop observation | `core/tracker.py`, `core/observation.py` | Multiple context/observation abstractions. Tracker reads clipboard content in its background loop; make collection opt-in and redact by default. |
| Bridge | `core/app.py`, `jarvis_bridge_client.py` | The FastAPI websocket endpoint simulates processing and reports fabricated metrics; do not expose it as production telemetry. |

## Direct third-party imports found in the inspected backend

The current `requirements.txt` does not declare all directly imported packages discovered in the source. At minimum, reconcile the following names and platform constraints before generating a lock/constraints file:

| Import / distribution candidate | Referencing code | Notes |
|---|---|---|
| `rapidfuzz` | `tools/tools_apps.py` | Direct import |
| `playwright` | browser modules, `tools/tools_browser.py` | Browser binaries also need installation |
| `chardet` | `core/friday_rag.py` | Direct import |
| `chromadb` | RAG, memory, local executor | Persistent local vector store |
| `pypdf` | `core/friday_rag.py` | PDF ingestion |
| `sqlalchemy` | `memory/database.py` | ORM |
| `pyperclip` | `core/tracker.py` | Clipboard access; opt-in only |
| `pywin32` | `core/tracker.py`, observation | Windows-only; install conditionally |
| `langchain-community` | `tools/tools.py` | DuckDuckGo search integration |
| `apscheduler` | `core/automation.py` | Background scheduling |
| `watchdog` | `core/automation.py` | Filesystem observation |
| `mcp` | `mcp/mcp/server.py` | FastMCP server; select supported extra/version |
| `pydantic` | typed core models | Declare directly if application imports it directly |
| `livekit-plugins-groq` | `tools/tools.py` | Source imports Groq LiveKit plugin |
| `livekit-plugins-google` | `agent.py` | Legacy/alternate entrypoint import |

This is an import inventory, not a validated requirements lock. Some imports may be optional or only needed by a legacy path; the next step is to classify required, optional, and retired modules and install-test on Windows Python 3.12.

## Configuration drift

- Active `main.py` reads `OPENAI_API_KEY`, `FRIDAY_VOICE_MODEL`, and `FRIDAY_BACKEND_MODEL`, and imports the OpenAI LiveKit plugin.
- Root `.env.example` instead labels Google and Groq keys as required and describes PostgreSQL as required.
- `tools/tools.py` reads `GROQ_API_KEY`; `memory/database.py` reads PostgreSQL settings; Gmail SMTP tools read Gmail credentials.
- `agent.py` is a legacy Google-plugin entrypoint and should not silently dictate active runtime configuration.
- `FRIDAY_BACKEND_MODEL` currently defaults to `gpt-5.6-luna` in source. Model identifiers must be validated against the selected provider and documented in one config schema, not copied across examples.

## Security review queue

1. Disable `core/local_executor.py` model-generated Python execution and remove its automatic invocation from background automation until replaced with a fixed action schema.
2. Inspect `tools/tools_terminal_phase2.py` allow/deny checks; token blacklists alone are not a sandbox. Restrict executable, arguments, working directory, environment, timeout, and output.
3. Enforce an approved root for file operations; reject traversal, symlink escapes, UNC/network paths unless explicitly allowed.
4. Require a per-action approval for email/Slack sends, calendar writes, deletes, external publication, and privileged commands.
5. Disable clipboard capture by default; make screen capture explicit, visible, and bounded.
6. Review historical secret exposure documented in `TECHNICAL_DEBT.md`; rotate credentials and run a history-aware secret scan. Do not rewrite shared history without approval.

## Runtime validation status

**Not run:** Windows clean install, pytest, LiveKit connection, browser launch, OpenClaw connection, voice session, or JarvisBridge end-to-end. This GitHub-only review cannot establish that these work on Ryan's laptop.

## Immediate Stage 1 actions

- Create a dependency matrix and separate core requirements from optional integrations.
- Reconcile the environment schema and update `.env.example` only after the chosen entrypoint is confirmed.
- Run a clean Python 3.12 install and pytest on the Windows machine.
- Capture exact command output and classify failures as dependency, import, configuration, network/provider, or test failures.
