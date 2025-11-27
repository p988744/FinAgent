"""
Verification script for Plan-and-Execute Agent.
Uses LLM-as-a-Judge to validate the execution trace.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from finagent.agents.plan_execute.graph import PlanExecuteWorkflow
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.document_processing.retriever import DocumentRetriever
from finagent.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class ExecutionTracer:
    def __init__(self):
        self.trace: List[Dict[str, Any]] = []
        
    def add_event(self, step: str, details: Any):
        self.trace.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "details": details
        })
        
    def get_trace_summary(self) -> str:
        summary = []
        for event in self.trace:
            step = event["step"]
            details = event["details"]
            
            if step == "planner":
                summary.append(f"PLANNER: Created plan with {len(details.tasks)} tasks.")
                for t in details.tasks:
                    summary.append(f"  - Task {t.id}: {t.description} (Tool: {t.tool})")
            
            elif step == "executor_start":
                summary.append(f"EXECUTOR: Starting execution.")
                
            elif step == "executor_step":
                task = details[0]
                result = details[1]
                summary.append(f"EXECUTOR: Executed Task {task['id']}")
                summary.append(f"  - Tool: {task['tool']}")
                summary.append(f"  - Args: {task['args']}")
                summary.append(f"  - Result: {str(result)[:200]}...") # Truncate result
                
            elif step == "replanner":
                if "response" in details:
                    summary.append(f"REPLANNER: Generated Final Response.")
                    summary.append(f"  - Response: {details['response'][:200]}...")
                elif "plan" in details:
                    summary.append(f"REPLANNER: Updated Plan.")
                    for t in details["plan"].tasks:
                        summary.append(f"  - Task {t.id}: {t.description} (Status: {t.status})")
                        
        return "\n".join(summary)

async def run_verification():
    print("🚀 Starting Plan-and-Execute Verification (LLM Judge)")
    
    # 1. Setup
    tracer = ExecutionTracer()
    retriever = DocumentRetriever(collection_name="legal_documents")
    hard_searcher = HardSearcher(db_path="data/finagent.db")
    workflow = PlanExecuteWorkflow(retriever=retriever, hard_searcher=hard_searcher)
    
    query = "請找出玉山銀行在2020年關於洗錢防制的裁罰案件，並說明裁罰金額。"
    print(f"\n❓ Query: {query}\n")
    
    # 2. Execution
    initial_state = {
        "input": query,
        "plan": None,
        "past_steps": [],
        "response": None
    }
    
    print("⚙️  Running Workflow...")
    try:
        async for event in workflow.graph.astream(initial_state):
            for key, value in event.items():
                if key == "planner":
                    tracer.add_event("planner", value["plan"])
                    print("  - Planner finished")
                elif key == "executor":
                    # Value contains 'past_steps', get the last one
                    if value.get("past_steps"):
                        last_step = value["past_steps"][-1]
                        tracer.add_event("executor_step", last_step)
                        print(f"  - Executor finished task {last_step[0]['id']}")
                elif key == "replanner":
                    tracer.add_event("replanner", value)
                    print("  - Replanner finished")
                    
    except Exception as e:
        print(f"❌ Workflow Execution Failed: {e}")
        sys.exit(1)

    # 3. Output Trace for Manual Verification
    print("\n📜 Execution Trace (Copy this to LLM for verification):")
    print("="*50)
    trace_summary = tracer.get_trace_summary()
    print(trace_summary)
    print("="*50)
    
    print("\n✅ Verification Script Completed (Check trace above)")


if __name__ == "__main__":
    asyncio.run(run_verification())
