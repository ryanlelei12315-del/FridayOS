"""
FridayOS Main Entrypoint
LiveKit + Ambient Context + Automation Layer
"""

import asyncio
import json
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    function_tool,
    room_io,
)
from livekit.plugins import noise_cancellation, openai

from core.automation import FridayAutomationManager
from core.friday_rag import ingest_local_document, query_desktop_knowledge
from core.tracker import AmbientContextTracker
from memory import initialize_memory

from prompts import (
    FRIDAY_BEHAVIOR,
    FRIDAY_SYSTEM_PROMPT,
    USER_UNDERSTANDING_LAYER,
    WELCOME_MESSAGE,
)

from tools.home_assistant_tools import (
    get_device_state,
    toggle_device,
    turn_off_device,
    turn_on_device,
)

from tools.tools import (
    get_weather,
    search_web,
    send_email,
    structural_automation_worker,
)

from tools.tools_apps import (
    close_application,
    is_app_running,
    list_running_apps,
    open_application,
    refresh_app_index,
)

from tools.tools_browser import (
    google_search,
    open_website,
    read_website,
)

from tools.tools_files import (
    create_file,
    delete_file,
    find_file,
    list_files,
    move_file,
    read_file,
)

from tools.tools_memory import recall_memory
from tools.tools_vision import capture_active_screen
from core.orchestration import TaskOrchestrator
from jarvis_bridge_client import jarvis_say, jarvis_state


# ==========================================================
# PATH AND ENVIRONMENT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FRIDAY_VOICE_MODEL = os.getenv("FRIDAY_VOICE_MODEL", "gpt-live-1")
FRIDAY_BACKEND_MODEL = os.getenv("FRIDAY_BACKEND_MODEL", "gpt-5.6-luna")

if not OPENAI_API_KEY:
    print("[Warning] OPENAI_API_KEY not found in environment variables.")


# ==========================================================
# MODEL ORCHESTRATION
# ==========================================================

def create_model():
    """
    Build the real-time ChatGPT orchestration loop.

    Voice mode:
      GPT-Live handles low-latency speech and delegates reasoning/tool work
      to a separate OpenAI Responses model.

    Console mode:
      Use the same backend frontier model through the Responses API.
    """
    if "console" in sys.argv:
        print("[FridayOS] Console mode detected.")
        print(f"[FridayOS] Using OpenAI Responses model: {FRIDAY_BACKEND_MODEL}.")
        return openai.responses.LLM(model=FRIDAY_BACKEND_MODEL)

    print("[FridayOS] Voice mode detected.")
    print(f"[FridayOS] Using GPT-Live voice model: {FRIDAY_VOICE_MODEL}.")
    print(f"[FridayOS] Delegating reasoning to: {FRIDAY_BACKEND_MODEL}.")

    return openai.realtime.GPTLiveModel(
        model=FRIDAY_VOICE_MODEL,
        voice="alloy",
        delegation="responses",
        responses_options={
            "model": FRIDAY_BACKEND_MODEL,
            "instructions": (
                "You are the reasoning and execution layer behind FRIDAY. "
                "Handle delegated requests with precision. Use the registered "
                "function tools whenever they are required to obtain current "
                "information or perform an action. Prefer direct tool execution "
                "over explaining how the user could do it manually. After tool "
                "execution, return a concise result suitable for FRIDAY to speak aloud."
            ),
            "parallel_tool_calls": True,
            "reasoning": {"effort": "medium"},
            "text": {"verbosity": "low"},
        },
    )


# ==========================================================
# TOOL REGISTRY
# ==========================================================
#
# The four orchestration-critical tools are intentionally kept
# together at the top of the runner array:
#
#   search_web
#   send_email
#   structural_automation_worker
#   recall_memory
#
# Existing desktop, browser, file, and home-assistant tools remain
# registered so the orchestration layer does not regress existing
# FridayOS capabilities.
#

ORCHESTRATION_TOOLS = [
    search_web,
    send_email,
    structural_automation_worker,
    recall_memory,
]

TOOLS = [
    *ORCHESTRATION_TOOLS,
    get_weather,
    list_files,
    find_file,
    create_file,
    read_file,
    move_file,
    delete_file,
    refresh_app_index,
    list_running_apps,
    open_application,
    close_application,
    is_app_running,
    open_website,
    google_search,
    read_website,
    turn_on_device,
    turn_off_device,
    toggle_device,
    get_device_state,
    capture_active_screen,
]


# ==========================================================
# RAG TOOLS
# ==========================================================

@function_tool(
    description=(
        "Indexes a local file, PDF, or code script into long term memory "
        "storage blocks for RAG query recall."
    )
)
def learn_local_document(file_path: str):
    print(
        f"[RAG Engine] Commencing ingestion procedure on targeted asset: {file_path}"
    )
    return ingest_local_document(file_path)


@function_tool(
    description=(
        "Queries the long term desktop vector knowledge index database "
        "to search for specific project facts or information."
    )
)
def query_long_term_memory(question: str):
    print(
        f"[RAG Engine] Performing semantic lookups for question: '{question}'"
    )
    return query_desktop_knowledge(question)


TOOLS += [
    learn_local_document,
    query_long_term_memory,
]


@function_tool(
    description=(
        "Creates a sequential execution plan for a complex or multi-step request. "
        "Call this before performing multi-step external actions."
    )
)
async def plan_complex_task(user_prompt: str) -> str:
    return await TaskOrchestrator().generate_execution_plan(user_prompt)


TOOLS.append(plan_complex_task)


# ==========================================================
# JARVISBRIDGE WALLPAPER INTEGRATION
# ==========================================================

BRIDGE_STATES = {"idle", "listening", "thinking", "speaking"}


def attach_jarvisbridge_hooks(session: AgentSession) -> tuple[asyncio.Queue, asyncio.Task]:
    """Mirror LiveKit state transitions and assistant text to the local wallpaper."""
    events: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

    async def publish_events() -> None:
        while True:
            kind, value = await events.get()
            try:
                if kind == "state":
                    await asyncio.to_thread(jarvis_state, value)
                elif kind == "alert":
                    # FRIDAY owns speech output; the wallpaper must remain silent.
                    await asyncio.to_thread(jarvis_say, value, speak=False)
            except Exception as exc:
                # The wallpaper is optional and must never take down the agent.
                print(f"[JarvisBridge] Non-fatal publish error: {exc}")
            finally:
                events.task_done()

    @session.on("agent_state_changed")
    def on_agent_state_changed(event) -> None:
        state = str(getattr(event, "new_state", "idle")).lower()
        if state == "initializing":
            state = "idle"
        if state in BRIDGE_STATES:
            events.put_nowait(("state", state))

    @session.on("conversation_item_added")
    def on_conversation_item_added(event) -> None:
        item = getattr(event, "item", None)
        if item is None:
            return

        role = str(getattr(item, "role", "")).lower()
        if not role.endswith("assistant"):
            return

        text_content = getattr(item, "text_content", "")
        if callable(text_content):
            try:
                text_content = text_content()
            except Exception:
                return

        if isinstance(text_content, str) and text_content.strip():
            events.put_nowait(("alert", text_content.strip()[:500]))

    return events, asyncio.create_task(publish_events(), name="jarvisbridge-publisher")

# ==========================================================
# AGENT
# ==========================================================

class FridayAgent(Agent):
    def __init__(self) -> None:
        initialize_memory()

        voice_instructions = (
            f"{FRIDAY_SYSTEM_PROMPT}\n\n"
            f"{USER_UNDERSTANDING_LAYER}\n\n"
            f"{FRIDAY_BEHAVIOR}\n\n"
            "Delegation rule: answer simple conversational requests directly. "
            "For requests requiring web research, memory lookup, email, desktop "
            "automation, file operations, application control, or other external "
            "actions, delegate the work to the reasoning layer and keep the user "
            "informed briefly while it executes. For multi-step requests, use "
            "plan_complex_task to create an ordered dependency plan before executing "
            "the required registered tools."
        )

        super().__init__(
            instructions=voice_instructions,
            llm=create_model(),
            tools=TOOLS,
        )


# ==========================================================
# LIVEKIT SERVER
# ==========================================================

server = AgentServer()


# ==========================================================
# SUBSYSTEM BOOT
# ==========================================================

def boot_subsystems(proc=None):
    """
    Called once by LiveKit when a worker process starts.
    """
    global context_tracker
    global automation_manager

    print("====================================")
    print("         FRIDAY OS BOOT")
    print("====================================")

    if context_tracker is None:
        context_tracker = AmbientContextTracker()
        context_tracker.start()
        print("[Boot] Ambient context tracker started.")

    if automation_manager is None:
        automation_manager = FridayAutomationManager()
        automation_manager.start()
        print("[Boot] Automation manager started.")

    print("[Boot] All subsystems online and mapped to Agent module state.")


# ==========================================================
# SUBSYSTEM SHUTDOWN
# ==========================================================

def shutdown_subsystems():
    """
    Gracefully shuts down background services.
    """
    global context_tracker
    global automation_manager

    print("\n====================================")
    print("       FRIDAY OS SHUTDOWN")
    print("====================================")

    try:
        if automation_manager:
            automation_manager.stop()
            automation_manager = None
            print("[Shutdown] Automation manager stopped.")

        if context_tracker:
            context_tracker.stop()
            context_tracker = None
            print("[Shutdown] Context tracker stopped.")

    except Exception as e:
        print(f"[Shutdown Error] {e}")

    print("[Shutdown] FridayOS safely offline.")


# ==========================================================
# GLOBAL REFERENCES
# ==========================================================

context_tracker: AmbientContextTracker | None = None
automation_manager: FridayAutomationManager | None = None


async def start_ambient_trigger_loop(session: AgentSession) -> None:
    """Monitor host CPU periodically and speak only on sustained high load."""
    import psutil

    consecutive_high_samples = 0
    try:
        while True:
            await asyncio.sleep(120)
            try:
                cpu_usage = await asyncio.to_thread(psutil.cpu_percent, 1.0)
                consecutive_high_samples = consecutive_high_samples + 1 if cpu_usage > 90.0 else 0
                if consecutive_high_samples >= 2:
                    await session.generate_reply(
                        instructions=(
                            f"Ambient diagnostic alert: CPU usage remains high "
                            f"({cpu_usage:.1f}%). Briefly notify the user calmly. "
                            "Do not claim an unverified cause."
                        )
                    )
                    consecutive_high_samples = 0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"[Ambient Trigger Error] {exc}")
    except asyncio.CancelledError:
        print("[Ambient] Trigger loop cancelled.")
        raise


# ==========================================================
# RTC SESSION
# ==========================================================

@server.rtc_session()
async def entrypoint(ctx: JobContext, context_tracker=None):
    """
    Own one LiveKit room lifecycle.

    The optional context_tracker argument is retained for compatibility with
    LiveKit dependency injection. When it is not injected, use the worker-level
    tracker started by boot_subsystems().
    """
    print("[Agent] Initializing room session...")
    await ctx.connect()
    print("[Agent] Connected to room.")

    active_tracker = context_tracker or globals().get("context_tracker")
    desktop_context = "You are FridayOS."

    if active_tracker is not None:
        try:
            current = active_tracker.current_context or {}
            active_window = current.get("active_window_title", "Unknown")
            active_process = current.get("active_process_name", "Unknown")
            # Clipboard data is deliberately excluded from the default prompt.
            # It may contain passwords, tokens, or private messages.
            desktop_context = (
                "You are FridayOS, an ambient operating system intelligence.\n"
                f"Active Window: {active_window}\n"
                f"Process Name: {active_process}"
            )
            print(f"[Agent] Active Window: {active_window}")
        except Exception as exc:
            print(f"[Context Error] Unable to read ambient context: {exc}")

    session = AgentSession()
    bridge_events, bridge_task = attach_jarvisbridge_hooks(session)
    ambient_task: asyncio.Task | None = None

    async def stop_bridge() -> None:
        """Flush the final idle state and stop the optional wallpaper worker."""
        if bridge_task.done():
            return
        try:
            bridge_events.put_nowait(("state", "idle"))
        except asyncio.QueueFull:
            pass
        try:
            await asyncio.wait_for(bridge_events.join(), timeout=2.0)
        except asyncio.TimeoutError:
            print("[JarvisBridge] Timed out flushing final events.")
        bridge_task.cancel()
        try:
            await bridge_task
        except asyncio.CancelledError:
            pass

    try:
        is_console = "console" in sys.argv
        agent = FridayAgent()

        if is_console:
            print("[Agent] Starting console session...")
            await session.start(room=ctx.room, agent=agent)

            # Console mode must never publish generated audio.
            session.output.set_audio_enabled(False)
            print("[Safety] Audio output disabled for console mode.")

            try:
                await session.generate_reply(
                    instructions=f"{desktop_context}\n\n{WELCOME_MESSAGE}"
                )
            except Exception as exc:
                print(f"[Greeting Error] {exc}")

            print("[Agent] Console session ready.")
            await session.wait_for_shutdown()
            return

        print("[Agent] Starting voice session...")
        await session.start(
            room=ctx.room,
            agent=agent,
            room_options=room_io.RoomOptions(
                video_input=room_io.VideoInputOptions(),
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            ),
        )

        ambient_task = asyncio.create_task(
            start_ambient_trigger_loop(session),
            name="friday-ambient-monitor",
        )

        await session.generate_reply(
            instructions=f"{desktop_context}\n\n{WELCOME_MESSAGE}"
        )
        print("[Agent] Voice session ready.")
        await session.wait_for_shutdown()

    except asyncio.CancelledError:
        print("[Agent] Room session cancelled.")
        raise
    except Exception as exc:
        print(f"[Session Error] {type(exc).__name__}: {exc}")
        raise
    finally:
        if ambient_task is not None:
            ambient_task.cancel()
            try:
                await ambient_task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                print(f"[Ambient Shutdown Error] {exc}")

        await stop_bridge()
        print("[Agent] Room session resources released.")


# ==========================================================
# SIGNAL HANDLING
# ==========================================================

def handle_exit(signum, frame):
    """
    Handles Ctrl+C and process termination.
    """
    print(f"\n[Signal] Received signal {signum}")
    shutdown_subsystems()
    sys.exit(0)


# ==========================================================
# MAIN
# ==========================================================

def main():
    if sys.platform != "win32":
        print("FridayOS requires Windows.")
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_exit)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_exit)

    server.setup_fnc = boot_subsystems

    print("[Boot] Handing execution to LiveKit Agent Server...")

    try:
        cli.run_app(server)
    finally:
        shutdown_subsystems()


if __name__ == "__main__":
    main()
