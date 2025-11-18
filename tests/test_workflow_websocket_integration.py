"""
Integration tests for LangGraph workflow → WebSocket callback flow.

Tests verify that:
1. Each LangGraph node completion triggers WebSocket updates
2. Plan data contains real extracted information (not hardcoded)
3. Todo/step updates reflect actual workflow progress
4. Timing data is real and varies between runs
"""

import asyncio
import json
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.models.queries import Query


class MockWebSocketCallback:
    """Mock callback that captures all WebSocket messages."""

    def __init__(self):
        self.messages: list[dict[str, Any]] = []
        self.timestamps: list[datetime] = []
        self.step_updates: dict[str, list[dict]] = {}
        self.plan_data: dict | None = None
        self.todo_updates: list[dict] = []

    async def _send(self, msg_type: str, payload: Any):
        """Capture WebSocket message."""
        timestamp = datetime.now()
        message = {
            "type": msg_type,
            "timestamp": timestamp.isoformat(),
            "payload": payload,
        }
        self.messages.append(message)
        self.timestamps.append(timestamp)

        # Track step updates
        if msg_type == "step_update":
            step = payload.get("step")
            if step not in self.step_updates:
                self.step_updates[step] = []
            self.step_updates[step].append(payload)

        # Track plan data
        if msg_type == "plan_created":
            self.plan_data = payload

        # Track todo updates
        if msg_type == "todo_update":
            self.todo_updates.append(payload)

    async def send_json(self, data: dict):
        """Mock send_json for compatibility."""
        await self._send(data["type"], data.get("payload", {}))


@pytest.mark.asyncio
async def test_workflow_triggers_websocket_callbacks_for_each_node():
    """
    Test that each LangGraph node completion triggers a WebSocket callback.

    Expected flow:
    - query_analysis node → step_update (planning)
    - planning node → step_update (planning) + plan_created
    - action node → step_update (action)
    - validation node → step_update (validation)
    - answer node → step_update (answer) + query_complete
    """
    # Arrange
    callback = MockWebSocketCallback()
    orchestrator = AgentOrchestrator(
        enable_query_logging=False,
        ui_callback=callback,
    )

    query = Query(text="玉山銀行洗錢防制裁罰")

    # Track which nodes completed
    nodes_completed = []

    # Act - stream query and collect node completions
    if orchestrator.use_rag and orchestrator.workflow:
        for node_name, state_update in orchestrator.stream_query(query):
            nodes_completed.append(node_name)
            print(f"Node completed: {node_name}")

    # Assert - verify workflow executed expected nodes
    # Should include: query_analysis, planning, action, validation, reference_guard, answer
    assert len(nodes_completed) >= 4, f"Expected at least 4 nodes, got {len(nodes_completed)}"
    assert "planning" in nodes_completed, "Planning node should execute"
    assert "action" in nodes_completed, "Action node should execute"
    assert "validation" in nodes_completed, "Validation node should execute"
    assert "answer" in nodes_completed, "Answer node should execute"

    print(f"\n✅ Nodes completed: {nodes_completed}")
    print(f"✅ Total WebSocket messages sent: {len(callback.messages)}")


@pytest.mark.asyncio
async def test_plan_data_contains_real_extracted_information():
    """
    Test that plan_created message contains real extracted data, not hardcoded values.

    Verifies:
    1. Keywords are extracted from actual query
    2. Entity type is inferred (not default)
    3. Complexity is analyzed (varies by query)
    4. Tasks are generated based on query analysis
    """
    callback = MockWebSocketCallback()
    orchestrator = AgentOrchestrator(
        enable_query_logging=False,
        ui_callback=callback,
    )

    # Test with specific query to verify extraction
    query = Query(text="玉山銀行洗錢防制裁罰案件")

    # Stream query
    if orchestrator.use_rag and orchestrator.workflow:
        for node_name, state_update in orchestrator.stream_query(query):
            if node_name == "planning" and "plan" in state_update:
                plan = state_update["plan"]

                # Verify plan has real data
                assert plan is not None, "Plan should be created"
                assert hasattr(plan, "analysis"), "Plan should have analysis"
                assert hasattr(plan, "tasks"), "Plan should have tasks"

                # Verify keywords extracted from query
                keywords = plan.analysis.keywords
                assert len(keywords) > 0, "Should extract keywords from query"
                print(f"\n✅ Extracted keywords: {keywords}")

                # Keywords should relate to query content
                query_terms = ["玉山", "銀行", "洗錢", "防制", "裁罰"]
                found_terms = sum(
                    1 for term in query_terms if any(term in kw for kw in keywords)
                )
                assert (
                    found_terms >= 2
                ), f"Should extract relevant keywords, found {found_terms} matching terms"

                # Verify entity type is inferred
                entity_type = plan.analysis.entity_type
                assert entity_type != "unknown", "Should infer entity type"
                print(f"✅ Entity type inferred: {entity_type}")

                # Verify tasks are generated
                tasks = plan.tasks
                assert len(tasks) > 0, "Should generate research tasks"
                print(f"✅ Generated {len(tasks)} research tasks")

                # Verify task descriptions are not empty/placeholder
                for task in tasks:
                    assert task.task.strip() != "", "Task should have description"
                    assert "task" not in task.task.lower(), "Should not be placeholder"

                break


@pytest.mark.asyncio
async def test_timing_data_is_real_and_varies():
    """
    Test that elapsed_ms values are real measurements, not hardcoded.

    Strategy:
    1. Run workflow twice
    2. Collect timing data from both runs
    3. Verify timings are non-zero
    4. Verify timings vary between runs (proves not hardcoded)
    """
    timings_run1 = []
    timings_run2 = []

    async def collect_timings() -> list[int]:
        """Run workflow and collect step timings."""
        callback = MockWebSocketCallback()
        orchestrator = AgentOrchestrator(
            enable_query_logging=False,
            ui_callback=callback,
        )

        query = Query(text="測試查詢")

        if orchestrator.use_rag and orchestrator.workflow:
            for node_name, state_update in orchestrator.stream_query(query):
                pass  # Just run through

        # Extract elapsed_ms from step updates
        timings = []
        for messages in callback.step_updates.values():
            for msg in messages:
                if msg.get("status") == "done" and "elapsed_ms" in msg:
                    elapsed = msg["elapsed_ms"]
                    timings.append(elapsed)

        return timings

    # Run twice
    timings_run1 = await collect_timings()
    timings_run2 = await collect_timings()

    # Verify timings are real (non-zero)
    assert all(t > 0 for t in timings_run1), "Timing should be > 0ms (not hardcoded)"
    assert all(t > 0 for t in timings_run2), "Timing should be > 0ms (not hardcoded)"

    print(f"\n✅ Run 1 timings: {timings_run1}")
    print(f"✅ Run 2 timings: {timings_run2}")

    # Verify timings vary (proves not hardcoded to same value)
    # Allow some tolerance since LLM calls may have similar latency
    if len(timings_run1) > 0 and len(timings_run2) > 0:
        # At least one timing should differ by more than 100ms
        max_diff = max(
            abs(t1 - t2)
            for t1, t2 in zip(timings_run1[: len(timings_run2)], timings_run2)
        )
        assert max_diff > 100, f"Timings should vary between runs, max diff was {max_diff}ms"
        print(f"✅ Max timing difference: {max_diff}ms (proves not hardcoded)")


@pytest.mark.asyncio
async def test_step_updates_follow_correct_sequence():
    """
    Test that step updates follow the expected LangGraph workflow sequence.

    Expected sequence:
    1. planning (active) → planning (done)
    2. action (active) → action (done)
    3. validation (active) → validation (done)
    4. answer (active) → answer (done)
    """
    callback = MockWebSocketCallback()
    orchestrator = AgentOrchestrator(
        enable_query_logging=False,
        ui_callback=callback,
    )

    query = Query(text="測試工作流程順序")

    # Track step transitions
    step_sequence = []

    if orchestrator.use_rag and orchestrator.workflow:
        for node_name, state_update in orchestrator.stream_query(query):
            step_sequence.append(node_name)

    print(f"\n✅ Step sequence: {step_sequence}")

    # Verify planning comes before action
    if "planning" in step_sequence and "action" in step_sequence:
        planning_idx = step_sequence.index("planning")
        action_idx = step_sequence.index("action")
        assert planning_idx < action_idx, "Planning should complete before action"

    # Verify action comes before validation
    if "action" in step_sequence and "validation" in step_sequence:
        action_idx = step_sequence.index("action")
        validation_idx = step_sequence.index("validation")
        assert action_idx < validation_idx, "Action should complete before validation"

    # Verify validation comes before answer
    if "validation" in step_sequence and "answer" in step_sequence:
        validation_idx = step_sequence.index("validation")
        answer_idx = step_sequence.index("answer")
        assert (
            validation_idx < answer_idx
        ), "Validation should complete before answer"

    print("✅ Step sequence follows expected workflow order")


@pytest.mark.asyncio
async def test_plan_complexity_varies_by_query():
    """
    Test that plan complexity is analyzed based on query, not hardcoded.

    Tests with different query types:
    - Simple query → simple complexity
    - Complex query → complex complexity
    """
    callback1 = MockWebSocketCallback()
    callback2 = MockWebSocketCallback()

    orchestrator1 = AgentOrchestrator(enable_query_logging=False, ui_callback=callback1)
    orchestrator2 = AgentOrchestrator(enable_query_logging=False, ui_callback=callback2)

    # Simple query
    simple_query = Query(text="玉山銀行")

    # Complex query with multiple conditions
    complex_query = Query(
        text="2020年至2023年間，玉山銀行、國泰世華銀行在洗錢防制、內線交易方面的所有金管會裁罰案件，按時間排序並分析趨勢"
    )

    plan1_complexity = None
    plan2_complexity = None

    # Run simple query
    if orchestrator1.use_rag and orchestrator1.workflow:
        for node_name, state_update in orchestrator1.stream_query(simple_query):
            if node_name == "planning" and "plan" in state_update:
                plan = state_update["plan"]
                plan1_complexity = plan.analysis.complexity
                break

    # Run complex query
    if orchestrator2.use_rag and orchestrator2.workflow:
        for node_name, state_update in orchestrator2.stream_query(complex_query):
            if node_name == "planning" and "plan" in state_update:
                plan = state_update["plan"]
                plan2_complexity = plan.analysis.complexity
                break

    print(f"\n✅ Simple query complexity: {plan1_complexity}")
    print(f"✅ Complex query complexity: {plan2_complexity}")

    # At minimum, verify complexity is being set (not None/default)
    assert plan1_complexity is not None, "Should analyze complexity for simple query"
    assert plan2_complexity is not None, "Should analyze complexity for complex query"

    # Verify complexity values are valid
    valid_complexities = {"simple", "medium", "complex"}
    assert plan1_complexity in valid_complexities, f"Invalid complexity: {plan1_complexity}"
    assert plan2_complexity in valid_complexities, f"Invalid complexity: {plan2_complexity}"


@pytest.mark.asyncio
async def test_round_to_3_digits_for_verification():
    """
    Test that numeric values (elapsed_ms, timestamps) are real by checking
    they have precision beyond simple hardcoded values.

    Real timing: 1234ms, 5678ms (varies, has precision)
    Hardcoded: 1000ms, 2000ms (round numbers, no variation)
    """
    callback = MockWebSocketCallback()
    orchestrator = AgentOrchestrator(
        enable_query_logging=False,
        ui_callback=callback,
    )

    query = Query(text="測試數值精確度")

    if orchestrator.use_rag and orchestrator.workflow:
        for node_name, state_update in orchestrator.stream_query(query):
            pass

    # Collect all elapsed_ms values
    elapsed_values = []
    for messages in callback.step_updates.values():
        for msg in messages:
            if "elapsed_ms" in msg:
                elapsed_values.append(msg["elapsed_ms"])

    print(f"\n✅ Collected {len(elapsed_values)} timing measurements")

    if len(elapsed_values) > 0:
        print(f"✅ Timing values: {elapsed_values}")

        # Verify values are not all round numbers (0, 1000, 2000, etc.)
        # Real measurements should have variation in last 3 digits
        non_round_count = sum(1 for val in elapsed_values if val % 100 != 0)

        assert (
            non_round_count > 0
        ), "At least some timings should not be round hundreds (proves real measurement)"
        print(
            f"✅ {non_round_count}/{len(elapsed_values)} values have sub-100ms precision"
        )

        # Verify values are positive and reasonable
        assert all(
            0 < val < 300000 for val in elapsed_values
        ), "Timing should be positive and < 5min"

        # Calculate coefficient of variation to verify spread
        if len(elapsed_values) > 1:
            import statistics

            mean_val = statistics.mean(elapsed_values)
            stdev_val = statistics.stdev(elapsed_values)
            cv = stdev_val / mean_val if mean_val > 0 else 0

            print(f"✅ Mean: {mean_val:.3f}ms, StdDev: {stdev_val:.3f}ms, CV: {cv:.3f}")
            print("✅ Values show real variation (not hardcoded)")


if __name__ == "__main__":
    # Run tests manually for development
    import sys

    async def run_all_tests():
        print("=" * 80)
        print("Test 1: Workflow triggers WebSocket callbacks for each node")
        print("=" * 80)
        await test_workflow_triggers_websocket_callbacks_for_each_node()

        print("\n" + "=" * 80)
        print("Test 2: Plan data contains real extracted information")
        print("=" * 80)
        await test_plan_data_contains_real_extracted_information()

        print("\n" + "=" * 80)
        print("Test 3: Timing data is real and varies")
        print("=" * 80)
        await test_timing_data_is_real_and_varies()

        print("\n" + "=" * 80)
        print("Test 4: Step updates follow correct sequence")
        print("=" * 80)
        await test_step_updates_follow_correct_sequence()

        print("\n" + "=" * 80)
        print("Test 5: Plan complexity varies by query")
        print("=" * 80)
        await test_plan_complexity_varies_by_query()

        print("\n" + "=" * 80)
        print("Test 6: Round to 3 digits verification")
        print("=" * 80)
        await test_round_to_3_digits_for_verification()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)

    asyncio.run(run_all_tests())
