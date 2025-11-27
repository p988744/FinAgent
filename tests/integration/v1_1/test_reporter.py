"""Integration test for ReporterAgent."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from finagent.agents.plan_execute.reporter import ReporterAgent
from finagent.agents.plan_execute.models import PlanExecuteState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run the reporter test."""
    print("🚀 Starting ReporterAgent Test")
    
    agent = ReporterAgent()
    
    # Mock state
    state = {
        "input": "What is the penalty for money laundering?",
        "plan": None,
        "past_steps": [
            ({"description": "Search for AML penalty"}, "The penalty is up to 5 million NTD."),
            ({"description": "Check recent cases"}, "Case A: Fined 2 million. Case B: Fined 4 million.")
        ],
        "response": None,
        "scratchpad": []
    }
    
    print("\n📝 Generating Report...")
    result = await agent.report(state)
    
    print("\n✨ Final Report:")
    print(result["response"])
    
    # Check for Chinese headers (since we requested Traditional Chinese)
    # The LLM might use "執行摘要" or "Executive Summary" depending on interpretation,
    # but usually it translates headers if the content is Chinese.
    # Based on previous run, it used "**執行摘要**".
    
    if ("執行摘要" in result["response"] or "Executive Summary" in result["response"]) and \
       ("關鍵發現" in result["response"] or "Key Findings" in result["response"]):
        print("\n✅ Report structure verified.")
    else:
        print("\n❌ Report structure missing required sections.")

if __name__ == "__main__":
    asyncio.run(main())
