"""Validated planning layer for multi-step FridayOS requests.

This module plans work only. It never executes tools or grants authorization.
Execution remains in the registered tool/runtime layer.
"""

import asyncio
import json
import os
from typing import Any, Awaitable, Callable

Planner = Callable[[str], Awaitable[str]]


class TaskOrchestrator:
    """Create a bounded, dependency-checked execution plan."""

    MAX_STEPS = 20
    PLANNER_TIMEOUT_SECONDS = 25

    def __init__(self, planning_model: Planner | None = None) -> None:
        self.planner = planning_model
        self.model = os.getenv("FRIDAY_BACKEND_MODEL", "gpt-5.6-luna")

    async def generate_execution_plan(self, user_prompt: str) -> str:
        prompt = user_prompt.strip() if isinstance(user_prompt, str) else ""
        if not prompt:
            return json.dumps(self._clarification_plan())

        if self.planner is None:
            return json.dumps(self._fallback_plan(
                "No planning model is configured. Use existing registered "
                "tools conservatively; do not infer authorization for side effects."
            ))

        instructions = (
            "You are FridayOS task planner. Return valid JSON only, shaped as "
            '{"steps":[{"step":1,"agent":"...","action":"...",'
            '"depends_on":[],"reason":"..."}]}. '
            "Plan only; do not execute tools or invent unavailable tools. "
            "Dependencies must reference earlier step numbers. For destructive, "
            "financial, communication, or privacy-sensitive actions, explicitly "
            "mark that user confirmation is required in the reason."
        )

        try:
            raw = await asyncio.wait_for(
                self.planner(f"{instructions}\n\nUser request: {prompt}"),
                timeout=self.PLANNER_TIMEOUT_SECONDS,
            )
            parsed = self._decode_planner_response(raw)
            return json.dumps(self._validate_plan(parsed))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            return json.dumps(self._fallback_plan(
                f"Planning failed safely ({type(exc).__name__}). "
                "No action authorization was inferred."
            ))

    @staticmethod
    def _decode_planner_response(raw: Any) -> Any:
        if not isinstance(raw, str):
            raise ValueError("Planner response must be text.")
        candidate = raw.strip()
        fence = chr(96) * 3
        if candidate.startswith(fence):
            candidate = candidate[len(fence):]
            if candidate.lower().startswith("json"):
                candidate = candidate[4:]
            if candidate.endswith(fence):
                candidate = candidate[:-len(fence)]
            candidate = candidate.strip()
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            parsed = parsed.get("steps")
        return parsed

    @classmethod
    def _validate_plan(cls, plan: Any) -> list[dict[str, Any]]:
        if not isinstance(plan, list) or not 1 <= len(plan) <= cls.MAX_STEPS:
            raise ValueError(f"Plan must contain 1 to {cls.MAX_STEPS} steps.")

        validated: list[dict[str, Any]] = []
        seen: set[int] = set()
        for expected, item in enumerate(plan, start=1):
            if not isinstance(item, dict):
                raise ValueError("Each plan step must be an object.")
            step = item.get("step", expected)
            agent = item.get("agent")
            action = item.get("action")
            dependencies = item.get("depends_on", [])
            if isinstance(step, bool) or step != expected:
                raise ValueError("Step numbers must be consecutive and ordered.")
            if not isinstance(agent, str) or not agent.strip():
                raise ValueError("Each step requires a non-empty agent.")
            if not isinstance(action, str) or not action.strip():
                raise ValueError("Each step requires a non-empty action.")
            if not isinstance(dependencies, list):
                raise ValueError("depends_on must be an array.")
            if any(isinstance(dep, bool) or not isinstance(dep, int) for dep in dependencies):
                raise ValueError("Dependencies must be integer step numbers.")
            if len(dependencies) != len(set(dependencies)):
                raise ValueError("A step cannot repeat a dependency.")
            if any(dep not in seen for dep in dependencies):
                raise ValueError("Dependencies must reference unique prior steps.")
            reason = item.get("reason", "")
            if not isinstance(reason, str):
                reason = str(reason)
            validated.append({
                "step": step, "agent": agent.strip(), "action": action.strip(),
                "depends_on": dependencies, "reason": reason.strip(),
            })
            seen.add(step)
        return validated

    @staticmethod
    def _clarification_plan() -> list[dict[str, Any]]:
        return [{
            "step": 1, "agent": "friday", "action": "ask_for_clarification",
            "depends_on": [], "reason": "The request was empty or invalid.",
        }]

    @staticmethod
    def _fallback_plan(reason: str | None = None) -> list[dict[str, Any]]:
        return [{
            "step": 1, "agent": "friday", "action": "safe_fallback_routing",
            "depends_on": [],
            "reason": reason or "No planner configured; do not infer authorization for side effects.",
        }]
