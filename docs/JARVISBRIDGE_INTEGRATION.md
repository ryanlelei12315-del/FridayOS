# JarvisBridge integration

JarvisBridge is an optional local desktop-wallpaper companion for FRIDAY OS. It is not a replacement for LiveKit, FRIDAY's model, or FRIDAY's existing text-to-speech.

## Architecture

- JarvisBridge Node server: `http://127.0.0.1:3000`
- Wallpaper connection: WebSocket to the JarvisBridge server
- FRIDAY adapter: `jarvis_bridge_client.py` (Python standard library only)
- FRIDAY voice output remains authoritative. Use `jarvis_say(reply, speak=False)` to animate/show the reply without triggering a second voice.

## Start the bridge

In a terminal opened in the JarvisBridge checkout:

```powershell
npm install
node servers.js
```

Keep the wallpaper application running and connected. The server exposes `GET /health`, `POST /state`, and `POST /alert` on loopback port 3000.

## Use from FRIDAY

The adapter is deliberately best-effort and uses a short timeout. If the bridge is not running, FRIDAY continues normally.

```python
from jarvis_bridge_client import jarvis_say, jarvis_state, jarvis_health

jarvis_state("listening")
jarvis_state("thinking")
# reply = await FRIDAY's existing request/response pipeline
jarvis_say(reply, speak=False)  # avoid duplicate speech from the wallpaper
jarvis_state("speaking")        # while FRIDAY's own TTS is playing
jarvis_state("idle")            # when FRIDAY finishes speaking
```

Do not call these functions on every streamed audio chunk. Publish state transitions only. If calling from an asyncio event loop, use `await asyncio.to_thread(jarvis_state, "thinking")` for network calls so even the short HTTP timeout cannot stall audio processing.

## Configuration

Set `JARVIS_BRIDGE_URL` only if the local bridge uses a different URL. The default is loopback-only at `http://127.0.0.1:3000`; do not expose this unauthenticated control endpoint to the public internet.

## Integration boundary

This commit adds the reusable adapter and integration guide. FRIDAY's LiveKit event hooks should be wired against the exact event API used by the installed LiveKit Agents version, and validated with the project test suite before enabling automatic state transitions. The adapter itself does not start the Node bridge or wallpaper process.
