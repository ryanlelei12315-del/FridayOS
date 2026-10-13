# JarvisBridge integration

JarvisBridge is an optional local desktop-wallpaper companion for FRIDAY OS. It is not a replacement for LiveKit, FRIDAY's model, or FRIDAY's existing text-to-speech.

## Architecture

- JarvisBridge Node server: `http://127.0.0.1:3000`
- Wallpaper connection: WebSocket to the JarvisBridge server
- FRIDAY adapter: `Friday_OS/Backend/jarvis_bridge_client.py` (Python standard library only)
- FRIDAY voice output remains authoritative. The wallpaper receives assistant text with `speak=False`, preventing duplicate speech.

## Start the bridge

In a terminal opened in the JarvisBridge checkout:

```powershell
npm install
node servers.js
```

Keep the wallpaper application running and connected. The server exposes `GET /health`, `POST /state`, and `POST /alert` on loopback port 3000.

## Automatic integration

The FRIDAY entrypoint (`Friday_OS/Backend/main.py`) subscribes to LiveKit's `agent_state_changed` and `conversation_item_added` events:

- `initializing` is normalized to `idle`; `idle`, `listening`, `thinking`, and `speaking` are sent to the wallpaper.
- Non-empty assistant text is sent to `POST /alert` with `speak=false`, so the wallpaper can display the reply without speaking over FRIDAY.
- Events are serialized through an async queue and HTTP requests run in `asyncio.to_thread`; realtime audio processing is not blocked by network I/O.
- Bridge errors are non-fatal. When FRIDAY's session ends, it publishes `idle` and shuts down the publisher task.

The integration is automatic once both processes are running. Start JarvisBridge separately using the steps above; FRIDAY does not spawn or manage the Node server or wallpaper process.

## Configuration and security

Set `JARVIS_BRIDGE_URL` only if the local bridge uses a different URL. The default is loopback-only at `http://127.0.0.1:3000`; do not expose this unauthenticated control endpoint to the public internet.

## Validation

A running end-to-end check requires Windows, the project's installed LiveKit Agents dependencies, a connected wallpaper WebSocket client, and both applications running together. Verify that the sphere follows listening/thinking/speaking/idle transitions and that assistant replies appear without a second voice. If the bridge is unavailable, FRIDAY should continue operating normally.
