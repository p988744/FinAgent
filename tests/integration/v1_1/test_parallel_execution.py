"""Integration test for parallel task execution."""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from finagent.agents.plan_execute.executor import ExecutorAgent
from finagent.agents.plan_execute.models import Plan, PlanTask, PlanExecuteState
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run the parallel execution test."""
    print("🚀 Starting Parallel Execution Test")
    
    # Initialize dependencies
    retriever = DocumentRetriever(collection_name="legal_documents")
    hard_searcher = HardSearcher(db_path="data/finagent.db")
    executor = ExecutorAgent(retriever=retriever, hard_searcher=hard_searcher)
    
    # Create a plan with 2 independent tasks
    task1 = PlanTask(
        id=1,
        description="Search for AML regulations",
        tool="retriever",
        args={"query": "AML regulations"},
        status="pending"
    )
    task2 = PlanTask(
        id=2,
        description="Search for KYC requirements",
        tool="retriever",
        args={"query": "KYC requirements"},
        status="pending"
    )
    
    plan = Plan(tasks=[task1, task2])
    state = {
        "input": "test",
        "plan": plan,
        "past_steps": [],
        "response": None
    }
    
    print("\n📋 Testing Dependency Detection...")
    deps = executor.detect_dependencies(plan.tasks)
    print(f"Dependencies: {deps}")
    if deps[1] == [] and deps[2] == []:
        print("✅ Correctly detected no dependencies.")
    else:
        print("❌ Failed to detect independence.")
        
    print("\n⚙️ Testing Task Routing...")
    routes = executor.route_tasks(state)
    print(f"Routes generated: {len(routes)}")
    if len(routes) == 2:
        print("✅ Correctly routed 2 tasks for parallel execution.")
    else:
        print(f"❌ Expected 2 routes, got {len(routes)}.")

    print("\n🏃 Testing Parallel Execution Speed...")
    # We can't easily mock the tool delay here without modifying the tool code,
    # but we can measure if they run.
    
    start_time = time.time()
    
    # Simulate parallel execution using asyncio.gather
    # In the real graph, LangGraph handles this
    tasks = []
    for route in routes:
        # route is a Send object. In a real graph, we'd let the graph handle it.
        # Here we manually call execute_task. Send object has .arg attribute (not .args)
        tasks.append(executor.execute_task(route.arg))
        
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Execution took {duration:.2f} seconds")
    print(f"Results count: {len(results)}")
    
    if len(results) == 2:
        print("✅ Successfully executed 2 tasks.")
    else:
        print("❌ Failed to execute all tasks.")

if __name__ == "__main__":
    asyncio.run(main())
