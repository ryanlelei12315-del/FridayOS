# FridayOS — Open-Source Real-Time Voice AI Assistant

**FridayOS** is a Python-powered, real-time **voice and visual AI assistant** built with **LiveKit Agents, WebRTC, Google Gemini, and retrieval-augmented generation (RAG)**. It is designed as a personal AI operating-system layer: talk naturally to an AI agent, invoke tools, search the web, work with files, recall project knowledge, and connect supported automation services.

If you're exploring an **open-source voice assistant**, a **LiveKit AI agent**, a **Python conversational AI project**, or an assistant with **long-term memory and tool calling**, FridayOS is a practical codebase to study and extend.

> Project status: active development. Capabilities depend on the configured providers, credentials, installed dependencies, and the current implementation in the repository.

## What FridayOS is built to do

- **Real-time voice conversations** using LiveKit Agents and WebRTC.
- **LLM-powered responses** with Google Gemini; optional Groq-backed automation is documented where supported.
- **Tool calling** for supported web, browser, file, email, application, and automation workflows.
- **Knowledge retrieval (RAG)** using ChromaDB so local documents can be indexed and queried semantically.
- **Conversation and project memory** with the repository's memory components and optional PostgreSQL persistence.
- **Ambient context and automation foundations** for building a more proactive desktop assistant.
- **Expo-based mobile/web interface** in the companion frontend project.

## Technology stack

| Area | Technologies |
| --- | --- |
| AI agent and backend | Python, LiveKit Agents |
| Real-time communications | LiveKit, WebRTC |
| Language model | Google Gemini |
| Optional automation model | Groq |
| Retrieval-augmented generation | ChromaDB, embeddings / vector search |
| Memory persistence | PostgreSQL (optional, based on configuration) |
| Frontend | React Native, Expo, TypeScript |
| Testing | pytest |

## Architecture

```text
Expo / React Native frontend
  ├── Dashboard and assistant controls
  └── LiveKit room connection
            │ WebRTC
            ▼
Python LiveKit agent backend
  ├── Gemini conversation model
  ├── Registered function tools
  ├── Document retrieval (ChromaDB / RAG)
  ├── Memory and context components
  └── Optional external integrations
```

## Repository layout

The backend lives under `Friday_OS/Backend/`. The companion frontend has been developed in the separate [FridayOS_Frontend repository](https://github.com/ryanlelei12315-del/FridayOS_Frontend); follow that repository's current setup instructions unless its code has been moved into this repository.

Typical backend areas include:

- `main.py` — primary agent entry point.
- `tools/` — function tools for supported integrations and actions.
- `core/` — retrieval, automation, and context components.
- `memory.py` — memory initialization.
- `prompts.py` — assistant instructions and prompt configuration.
- `tests/` — automated tests, where available.

## Getting started

### Requirements

- Python 3.12 recommended (check dependency and deployment configuration for the exact supported version).
- A [LiveKit Cloud](https://cloud.livekit.io/) project and credentials.
- A [Google AI API key](https://ai.google.dev/).
- Optional [Groq API key](https://console.groq.com/) for supported automation workflows.
- Optional PostgreSQL and any credentials required by the integrations you enable.

### Configure environment variables

Copy the repository's `.env.example` to `.env` if present, then fill in the credentials required by your selected features. Common variables include:

| Variable | Purpose |
| --- | --- |
| `LIVEKIT_URL` | LiveKit WebSocket URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `GROQ_API_KEY` | Optional Groq integration |
| `GMAIL_USER` / `GMAIL_APP_PASSWORD` | Optional email integration |
| `HOME_ASSISTANT_URL` / `HOME_ASSISTANT_TOKEN` | Optional Home Assistant integration |
| `POSTGRES_*` | Optional PostgreSQL configuration |

**Security:** never commit real API keys, access tokens, passwords, or populated `.env` files. Use local environment variables or your deployment platform's secret manager.

### Run the backend

From the repository root, inspect the current backend directory and its dependency file, then run:

```bash
cd Friday_OS/Backend
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS / Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

If the installed entry point supports console mode, run `python main.py console` for text interaction. Run `python main.py` for the LiveKit voice workflow after configuring the required credentials. Check the current code and provider documentation if command options have changed.

### Run the frontend

The frontend setup is documented in the [FridayOS_Frontend repository](https://github.com/ryanlelei12315-del/FridayOS_Frontend). In a local clone, install its dependencies and follow its Expo scripts. A LiveKit room and a valid token/configuration are required for connected voice sessions.

## Tool calling and integrations

FridayOS uses LiveKit-compatible function tools for supported actions. Tool availability depends on the current source code and environment configuration. The repository documents tool areas such as:

- Web search and browser actions
- File creation, reading, searching, moving, and deletion
- Application control
- Email sending
- Home Assistant smart-home actions
- Memory recall and document retrieval
- Automation helpers

Review the implementation before enabling tools that can modify files, send messages, or control external systems. Grant only the permissions needed for your use case.

## Retrieval-augmented generation (RAG) and memory

The RAG components use a ChromaDB vector store to retrieve relevant content from ingested documents. This pattern helps a conversational assistant answer questions grounded in personal notes, project documentation, and other local knowledge.

Example requests, when the relevant tools are configured:

- “Learn from my project documentation.”
- “Find the notes related to my current project.”
- “What did my documentation say about this feature?”

Ingestion and retrieval behavior depends on the implementation, supported file formats, and configured embedding/model providers.

## Testing

Where the repository's test suite is configured, install the backend dependencies and run pytest from the appropriate project directory. For example:

```bash
python -m pytest tests/ -v
```

Check test paths against the current checkout before running; repository layout may change as the backend and frontend are consolidated.

## Contributing

Issues, bug reports, documentation improvements, and focused pull requests are welcome. When reporting a problem, include your operating system, Python version, the relevant sanitized logs, and steps to reproduce it. **Do not include API keys, passwords, access tokens, or private conversation data.**

## Related project

- **Frontend:** [ryanlelei12315-del/FridayOS_Frontend](https://github.com/ryanlelei12315-del/FridayOS_Frontend)

## License

Check the license file in this repository and the companion frontend repository for the terms that apply to each codebase.
