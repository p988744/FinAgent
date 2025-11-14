"""Test TODO list display with live updates."""

import asyncio
import time

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.cli.formatters.todo_display import TodoListDisplay
from finagent.models.plan import PlanTask, QueryAnalysis, ResearchPlan
from finagent.models.queries import Query
from rich.console import Console

console = Console()


def create_sample_plan() -> ResearchPlan:
    """Create a sample research plan for testing."""
    analysis = QueryAnalysis(
        keywords=["創投公司", "創投"],
        must_have_keywords=["創投", "創業投資"],
        entity_type="venture_capital",
        jurisdiction="金管會",
        query_type="enforcement_search",
        complexity="complex",
    )

    tasks = [
        PlanTask(
            id=1,
            task="向量搜索：創投公司, 創投",
            status="pending",
            search_method="vector_search",
            estimated_time=10,
        ),
        PlanTask(
            id=2,
            task="深度搜索：grep 關鍵字「創投, 創業投資」",
            status="pending",
            search_method="hard_search",
            estimated_time=30,
        ),
        PlanTask(
            id=3,
            task="驗證引用完整性和關鍵字匹配",
            status="pending",
            search_method="vector_search",
            estimated_time=5,
        ),
        PlanTask(
            id=4,
            task="生成答案並格式化引用",
            status="pending",
            search_method="vector_search",
            estimated_time=15,
        ),
    ]

    return ResearchPlan(
        analysis=analysis,
        tasks=tasks,
        max_results=10,
        use_hard_search=True,
        estimated_total_time=60,
    )


async def test_static_display():
    """Test static (non-live) TODO list display."""
    console.print("\n[cyan]===== Test 1: Static Display =====[/cyan]\n")

    plan = create_sample_plan()
    display = TodoListDisplay(plan)

    # Show initial state
    console.print("[yellow]Initial state (all pending):[/yellow]")
    display.display_static()

    # Simulate task completion
    await asyncio.sleep(1)
    plan.tasks[0].status = "completed"
    plan.tasks[1].status = "in_progress"

    console.print("\n[yellow]After task 1 completes, task 2 in progress:[/yellow]")
    display = TodoListDisplay(plan)  # Create new display with updated plan
    display.display_static()

    # Complete all tasks
    await asyncio.sleep(1)
    plan.tasks[1].status = "completed"
    plan.tasks[2].status = "completed"
    plan.tasks[3].status = "completed"

    console.print("\n[yellow]All tasks completed:[/yellow]")
    display = TodoListDisplay(plan)
    display.display_static()


async def test_live_display():
    """Test live updating TODO list display."""
    console.print("\n[cyan]===== Test 2: Live Display =====[/cyan]\n")

    plan = create_sample_plan()
    display = TodoListDisplay(plan)

    # Start live display
    display.start()

    # Simulate task execution
    await asyncio.sleep(2)
    display.update_task_status(1, "in_progress")

    await asyncio.sleep(2)
    display.update_task_status(1, "completed")
    display.update_task_status(2, "in_progress")

    await asyncio.sleep(3)
    display.update_task_status(2, "completed")
    display.update_task_status(3, "in_progress")

    await asyncio.sleep(1)
    display.update_task_status(3, "completed")
    display.update_task_status(4, "in_progress")

    await asyncio.sleep(2)
    display.update_task_status(4, "completed")

    # Stop live display
    await asyncio.sleep(1)
    display.stop()

    # Show completion summary
    console.print()
    console.print(f"[green]{display.get_completion_summary()}[/green]")


async def test_with_real_query():
    """Test TODO display with real query execution."""
    console.print("\n[cyan]===== Test 3: Real Query with TODO Display =====[/cyan]\n")

    # Create orchestrator
    orchestrator = AgentOrchestrator()

    # Create query
    query = Query(text="金管會對創投公司的裁罰有哪些？")

    console.print(f"[cyan]處理查詢:[/cyan] {query.text}\n")

    # Execute query
    answer = await orchestrator.process_query(query)

    # Extract plan from processing_steps
    processing_steps = answer.processing_steps

    # Find planning analysis
    plan_found = False
    for step in processing_steps:
        if "📋 查詢分析" in step:
            console.print(f"[green]✓[/green] {step}")
            plan_found = True
        elif "📝 研究任務" in step:
            console.print(f"[green]✓[/green] {step}")

    if not plan_found:
        console.print("[yellow]Note: Plan not found in processing_steps[/yellow]")

    # For now, create a plan manually based on processing_steps
    # In production, we'd extract this from the actual workflow state
    console.print("\n[yellow]Task execution visualization:[/yellow]\n")

    # Create plan from analysis
    sample_plan = create_sample_plan()
    display = TodoListDisplay(sample_plan)

    # Map processing steps to task updates
    task_map = {
        "向量搜索": 1,
        "深度搜索": 2,
        "驗證": 3,
        "答案代理": 4,
    }

    current_task = None
    display.start()

    for step in processing_steps:
        # Update task based on step content
        for keyword, task_id in task_map.items():
            if keyword in step:
                if current_task and current_task != task_id:
                    display.update_task_status(current_task, "completed")
                if current_task != task_id:
                    display.update_task_status(task_id, "in_progress")
                    current_task = task_id
                await asyncio.sleep(0.5)  # Slow down for visualization
                break

    # Complete final task
    if current_task:
        display.update_task_status(current_task, "completed")

    await asyncio.sleep(1)
    display.stop()

    console.print()
    console.print(f"[green]{display.get_completion_summary()}[/green]")


async def main():
    """Run all TODO display tests."""
    await test_static_display()
    await test_live_display()
    await test_with_real_query()


if __name__ == "__main__":
    asyncio.run(main())
