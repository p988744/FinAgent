import sys
import inspect
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

def verify_phase_1():
    print("🔍 Verifying Phase 1: Tool Infrastructure...")
    
    errors = []
    
    # 1. Check Directory and Files
    tools_dir = Path(__file__).parent.parent / "src/finagent/tools"
    if not tools_dir.exists():
        errors.append("❌ Directory 'src/finagent/tools' does not exist.")
    else:
        print("  - Directory 'src/finagent/tools': OK")
        
    files = ["retriever.py", "search.py", "__init__.py"]
    for f in files:
        if not (tools_dir / f).exists():
            errors.append(f"❌ File 'src/finagent/tools/{f}' missing.")
        else:
            print(f"  - File '{f}': OK")

    # 2. Check Imports in Executor
    try:
        from finagent.agents.plan_execute.executor import ExecutorAgent
        # Inspect the source to see imports (static analysis might be better but let's check if it runs)
        # We can check if the tools attribute of an instance has the right class
        # But better to check if we can import the tools from the new location
        from finagent.tools import RetrieverTool, HardSearchTool
        print("  - Import 'finagent.tools': OK")
        
        # Check if Executor uses them? 
        # Let's inspect the executor.py file content for the import string
        executor_path = Path(__file__).parent.parent / "src/finagent/agents/plan_execute/executor.py"
        with open(executor_path, "r") as f:
            content = f.read()
            if "from finagent.tools import HardSearchTool, RetrieverTool" in content or \
               "from finagent.tools import RetrieverTool, HardSearchTool" in content:
                print("  - Executor imports from shared tools: OK")
            else:
                errors.append("❌ ExecutorAgent does not import from 'finagent.tools'.")
                
    except ImportError as e:
        errors.append(f"❌ ImportError: {e}")

    # 3. Check Async Support (_arun)
    try:
        from finagent.tools import RetrieverTool, HardSearchTool
        
        if hasattr(RetrieverTool, "_arun") and inspect.iscoroutinefunction(RetrieverTool._arun):
            print("  - RetrieverTool._arun (async): OK")
        else:
            errors.append("❌ RetrieverTool missing async '_arun' method.")
            
        if hasattr(HardSearchTool, "_arun") and inspect.iscoroutinefunction(HardSearchTool._arun):
            print("  - HardSearchTool._arun (async): OK")
        else:
            errors.append("❌ HardSearchTool missing async '_arun' method.")
            
    except Exception as e:
        errors.append(f"❌ Error checking tool methods: {e}")

    # Result
    if errors:
        print("\n❌ Phase 1 Verification FAILED:")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("\n✅ Phase 1 Verification PASSED")
        sys.exit(0)

if __name__ == "__main__":
    verify_phase_1()
