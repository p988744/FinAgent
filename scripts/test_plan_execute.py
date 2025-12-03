"""Integration test for the Plan-and-Execute agent flow."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from finagent.agents.plan_execute.graph import PlanExecuteWorkflow
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever
from finagent.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run the integration test."""
    print("🚀 Starting Plan-and-Execute Agent Test")
    
    # Initialize dependencies
    # Note: Ensure you have data in your vector DB or this will return empty results
    retriever = DocumentRetriever(collection_name="legal_documents")
    hard_searcher = HardSearcher(db_path="data/finagent.db")
    
    # Initialize workflow
    workflow = PlanExecuteWorkflow(retriever=retriever, hard_searcher=hard_searcher)
    
    # Test query
    query = "請找出玉山銀行在2020年關於洗錢防制的裁罰案件，並說明裁罰金額。"
    print(f"\n❓ Query: {query}\n")
    
    # Run workflow
    initial_state = {
        "input": query,
        "plan": None,
        "past_steps": [],
        "response": None
    }
    
    try:
        # Stream the execution
        async for event in workflow.graph.astream(initial_state):
            for key, value in event.items():
                print(f"\n📍 Node: {key}")
                if key == "planner":
                    print("📋 Plan created:")
                    for task in value["plan"].tasks:
                        print(f"  - [{task.id}] {task.description} ({task.tool})")
                elif key == "executor":
                    print("⚙️  Executor updated state (past_steps updated)")
                elif key == "replanner":
                    if "response" in value:
                        print("\n✨ Final Response:")
                        print(value["response"])
                    elif "plan" in value:
                        print("🔄 Replanning... New tasks added.")
                        for task in value["plan"].tasks:
                            print(f"  - [{task.id}] {task.description} ({task.tool})")
                            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
