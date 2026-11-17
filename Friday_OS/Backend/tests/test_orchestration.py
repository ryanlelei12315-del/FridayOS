import asyncio
import json

import pytest

from core.orchestration import TaskOrchestrator


def test_empty_request_returns_clarification_plan():
    plan = json.loads(asyncio.run(TaskOrchestrator().generate_execution_plan("   ")))
    assert plan[0]["action"] == "ask_for_clarification"


def test_missing_planner_uses_safe_fallback():
    plan = json.loads(asyncio.run(TaskOrchestrator().generate_execution_plan("organize my files")))
    assert plan[0]["action"] == "safe_fallback_routing"
    assert "authorization" in plan[0]["reason"]


def test_validate_accepts_ordered_dependencies():
    plan = [
        {"step": 1, "agent": "research", "action": "search", "depends_on": []},
        {"step": 2, "agent": "writer", "action": "summarize", "depends_on": [1]},
    ]
    assert TaskOrchestrator._validate_plan(plan)[1]["depends_on"] == [1]


@pytest.mark.parametrize("dependencies", [[2], [1, 1], [True], ["1"]])
def test_validate_rejects_invalid_dependencies(dependencies):
    plan = [{"step": 1, "agent": "research", "action": "search", "depends_on": dependencies}]
    with pytest.raises(ValueError):
        TaskOrchestrator._validate_plan(plan)


def test_decode_accepts_documented_steps_object():
    raw = '{"steps":[{"step":1,"agent":"research","action":"search","depends_on":[]}]}'
    decoded = TaskOrchestrator._decode_planner_response(raw)
    assert decoded[0]["action"] == "search"


def test_invalid_planner_output_falls_back_without_authorizing_actions():
    async def planner(_prompt: str) -> str:
        return "not-json"
    plan = json.loads(asyncio.run(TaskOrchestrator(planner).generate_execution_plan("send an email")))
    assert plan[0]["action"] == "safe_fallback_routing"
    assert "authorization" in plan[0]["reason"]


def test_validate_rejects_non_integer_step_number():
    plan = [{"step": 1.0, "agent": "research", "action": "search", "depends_on": []}]
    with pytest.raises(ValueError):
        TaskOrchestrator._validate_plan(plan)
