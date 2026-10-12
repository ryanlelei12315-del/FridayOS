"""Validated planning layer for multi-step FridayOS requests."""

import json
from typing import Any, Awaitable, Callable

Planner = Callable[[str], Awaitable[str]]


class TaskOrchestrator:
    """Build ordered plans through an injected async planner or safe fallback."""

    def __init__(self, planning_model: Planner | None = None) -> None:
        self.planner = planning_model

    async def generate_execution_plan(self, user_prompt: str) -> str:
        prompt = user_prompt.strip()
        if not prompt:
            return json.dumps([{
                "step": 1, "agent": "monolith", "action": "ask_for_clarification",
                "depends_on": [], "reason": "The request was empty."
            }])
        if self.planner is None:
            return json.dumps(self._fallback_plan())
        instructions = (
            "You are FridayOS's task planner. Return a valid JSON array only. Each item "
            "must contain step (integer), agent (string), action (string), depends_on "
            "(array of prior step integers), and reason (string). Plan only; do not "
            "execute tools or invent unavailable tools. For destructive, financial, "
            "communication, or privacy-sensitive actions, require user confirmation."
        )
        try:
            parsed = json.loads(await self.planner(f"{instructions}\n\nUser request: {prompt}"))
            return json.dumps(self._validate_plan(parsed))
        except Exception:
            return json.dumps(self._fallback_plan())

    @staticmethod
    def _validate_plan(plan: Any) -> list[dict[str, Any]]:
        if not isinstance(plan, list) or not plan or len(plan) > 20:
            raise ValueError("Plan must contain 1 to 20 steps.")
        validated: list[dict[str, Any]] = []
        seen: set[int] = set()
        for expected, item in enumerate(plan, start=1):
            if not isinstance(item, dict):
                raise ValueError("Each step must be an object.")
            step, agent, action = item.get("step", expected), item.get("agent"), item.get("action")
            dependencies = item.get("depends_on", [])
            if step != expected or not isinstance(agent, str) or not agent.strip():
                raise ValueError("Steps must be ordered and include an agent.")
            if not isinstance(action, str) or not action.strip():
                raise ValueError("Each step requires an action.")
            if not isinstance(dependencies, list) or any(
                not isinstance(dep, int) or dep not in seen for dep in dependencies
            ):
                raise ValueError("Dependencies must reference prior steps only.")
            validated.append({
                "step": step, "agent": agent.strip(), "action": action.strip(),
                "depends_on": dependencies, "reason": str(item.get("reason", ""))
            })
            seen.add(step)
        return validated

    @staticmethod
    def _fallback_plan() -> list[dict[str, Any]]:
        return [{
            "step": 1, "agent": "monolith", "action": "fallback_routing",
            "depends_on": [],
            "reason": "No planning model was configured or structured planning failed. "
                      "Use existing registered tools and do not infer authorization for side effects."
        }]
