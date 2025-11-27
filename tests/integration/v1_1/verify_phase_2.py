import sys
import inspect
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

def verify_phase_2():
    print("🔍 Verifying Phase 2: Wiki Search Workflow...")
    
    errors = []
    
    # 1. Check Directory and Files
    agent_dir = Path(__file__).parent.parent / "src/finagent/agents/wiki_search"
    if not agent_dir.exists():
        errors.append("❌ Directory 'src/finagent/agents/wiki_search' does not exist.")
    else:
        print("  - Directory 'src/finagent/agents/wiki_search': OK")
        
    files = ["graph.py", "prompts.py", "__init__.py"]
    for f in files:
        if not (agent_dir / f).exists():
            errors.append(f"❌ File 'src/finagent/agents/wiki_search/{f}' missing.")
        else:
            print(f"  - File '{f}': OK")

    # 2. Check WikiSearchWorkflow Class
    try:
        from finagent.agents.wiki_search.graph import WikiSearchWorkflow
        
        # Check if it has a graph attribute (initialized in __init__)
        # We can't easily check instance attributes without instantiating, 
        # but we can check if the class exists and is importable.
        print("  - Import 'WikiSearchWorkflow': OK")
        
    except ImportError as e:
        errors.append(f"❌ ImportError: {e}")

    # 3. Check Orchestrator Integration
    try:
        from finagent.agents.orchestrator import AgentOrchestrator
        # Inspect source for use_wiki_search parameter
        orch_path = Path(__file__).parent.parent / "src/finagent/agents/orchestrator.py"
        with open(orch_path, "r") as f:
            content = f.read()
            if "use_wiki_search" in content:
                print("  - AgentOrchestrator supports 'use_wiki_search': OK")
            else:
                errors.append("❌ AgentOrchestrator missing 'use_wiki_search' parameter.")
                
            if "WikiSearchWorkflow" in content:
                 print("  - AgentOrchestrator imports 'WikiSearchWorkflow': OK")
            else:
                 errors.append("❌ AgentOrchestrator does not use 'WikiSearchWorkflow'.")

    except Exception as e:
        errors.append(f"❌ Error checking Orchestrator: {e}")

    # 4. Check WebSocket Integration
    try:
        ws_path = Path(__file__).parent.parent / "src/finagent/api/routes/websocket.py"
        with open(ws_path, "r") as f:
            content = f.read()
            if "use_wiki_search" in content:
                print("  - WebSocket API supports 'use_wiki_search': OK")
            else:
                errors.append("❌ WebSocket API missing 'use_wiki_search' handling.")
                
            if '"search": "action"' in content and '"synthesize": "answer"' in content:
                print("  - WebSocket API maps Wiki Search nodes: OK")
            else:
                errors.append("❌ WebSocket API missing node mapping for Wiki Search.")

    except Exception as e:
        errors.append(f"❌ Error checking WebSocket: {e}")

    # Result
    if errors:
        print("\n❌ Phase 2 Verification FAILED:")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("\n✅ Phase 2 Verification PASSED")
        sys.exit(0)

if __name__ == "__main__":
    verify_phase_2()
