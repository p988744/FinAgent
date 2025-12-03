#!/usr/bin/env python3
"""
CLI Retrieval Tool - Search and retrieve documents from the knowledge base.

This provides direct access to the three search tools:
- auto: Let the system choose the best tool (default)
- semantic: Semantic vector search (conceptual queries)
- keyword: Exact keyword matching (specific terms)
- hybrid: Combined BM25 + Vector search (recommended)

Usage:
    python scripts/cli_retrieval.py "search query"                    # Auto mode
    python scripts/cli_retrieval.py "search query" --tool hybrid      # Specify tool
    python scripts/cli_retrieval.py                                   # Interactive mode
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finagent.document_processing import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.tools import RetrieverTool, HardSearchTool, HybridRetrieverTool
from finagent.agents.plan_execute.query_analyzer import QueryAnalyzerAgent


def print_header():
    """Print CLI header."""
    print()
    print("=" * 80)
    print("  FinAgent Retrieval CLI")
    print("  Direct Knowledge Base Search")
    print("=" * 80)
    print()


def print_tool_info():
    """Print information about available tools."""
    print("Available Search Tools:")
    print("─" * 80)
    print()
    print("  🔍 semantic   - Semantic vector search")
    print("                 Best for: Conceptual/analytical queries")
    print("                 Example: '分析銀行業洗錢防制的主要問題'")
    print()
    print("  🔎 keyword    - Exact keyword matching (grep-style)")
    print("                 Best for: Finding specific terms (Boolean AND)")
    print("                 Example: '找出包含「金管會」和「裁罰」的文件'")
    print()
    print("  🔍🔎 hybrid   - Combined BM25 + Vector (60% semantic, 40% keyword)")
    print("                 Best for: Queries with both specific terms and concepts")
    print("                 Example: '2020年玉山銀行洗錢防制裁罰'")
    print()
    print("  🤖 auto       - Let the system choose (uses Query Analyzer)")
    print("                 Analyzes your query and selects the best tool")
    print()


async def auto_select_tool(query: str, retriever, hard_searcher):
    """
    Automatically select the best tool based on query analysis.

    Returns:
        tuple: (tool_name, tool_object)
    """
    print("🤖 Analyzing query to select best tool...")
    print()

    # Use query analyzer
    analyzer = QueryAnalyzerAgent()
    state = {"input": query, "query_insight": None, "plan": None, "past_steps": [], "response": None}

    result = await analyzer.analyze(state)
    insight = result["query_insight"]

    # Print analysis
    print("📊 Query Analysis:")
    print(f"   Type:       {insight.query_type}")
    print(f"   Strategy:   {insight.search_strategy}")
    print(f"   Complexity: {insight.complexity}")

    if insight.key_entities:
        entities_str = ", ".join(insight.key_entities[:5])
        if len(insight.key_entities) > 5:
            entities_str += f" (and {len(insight.key_entities) - 5} more)"
        print(f"   Entities:   {entities_str}")

    print()
    print(f"💡 {insight.reasoning}")
    print()

    # Map strategy to tool
    strategy_map = {
        "semantic": ("semantic", RetrieverTool(retriever=retriever)),
        "keyword": ("keyword", HardSearchTool(hard_searcher=hard_searcher)),
        "hybrid": ("hybrid", HybridRetrieverTool(retriever=retriever, semantic_weight=0.6, keyword_weight=0.4))
    }

    tool_name, tool = strategy_map.get(insight.search_strategy, ("hybrid", HybridRetrieverTool(retriever=retriever)))

    print(f"✅ Selected tool: {tool_name}")
    print()

    return tool_name, tool


def format_results(results: str, tool_name: str) -> str:
    """Format search results for display."""
    lines = results.split('\n')
    formatted_lines = []

    # Add header
    tool_icons = {
        "semantic": "🔍",
        "keyword": "🔎",
        "hybrid": "🔍🔎"
    }
    icon = tool_icons.get(tool_name, "🔍")

    formatted_lines.append(f"{icon} Search Results (Tool: {tool_name})")
    formatted_lines.append("─" * 80)
    formatted_lines.append("")

    # Format result lines
    for line in lines:
        formatted_lines.append(line)

    return "\n".join(formatted_lines)


async def retrieval_search(query: str, tool_choice: str = "auto", num_results: int = 5):
    """
    Execute a retrieval search.

    Args:
        query: Search query
        tool_choice: Tool to use (auto, semantic, keyword, hybrid)
        num_results: Number of results to return
    """
    # Initialize components
    print("Initializing knowledge base...")
    retriever = DocumentRetriever(collection_name="legal_documents")
    hard_searcher = HardSearcher(db_path="data/finagent.db")

    if not retriever.collection_exists():
        print("❌ Error: Document index not available.")
        print("   Please run indexing first: uv run finagent reindex")
        return

    print("✅ Ready")
    print()

    print(f"Query: {query}")
    print()

    # Select tool
    if tool_choice == "auto":
        tool_name, tool = await auto_select_tool(query, retriever, hard_searcher)
    else:
        # Manual tool selection
        tools = {
            "semantic": RetrieverTool(retriever=retriever),
            "keyword": HardSearchTool(hard_searcher=hard_searcher),
            "hybrid": HybridRetrieverTool(retriever=retriever, semantic_weight=0.6, keyword_weight=0.4)
        }

        tool = tools.get(tool_choice)
        if not tool:
            print(f"❌ Error: Unknown tool '{tool_choice}'")
            print("   Available: auto, semantic, keyword, hybrid")
            return

        tool_name = tool_choice
        print(f"Using tool: {tool_name}")
        print()

    # Execute search
    print("Searching...")
    print()

    try:
        if tool_name == "keyword":
            # For keyword search, we need to extract keywords
            # Simple approach: split query into words
            keywords = [word.strip() for word in query.split() if len(word.strip()) > 1]
            results = tool._run(keywords=keywords[:5])  # Limit to 5 keywords
        elif tool_name == "semantic":
            results = tool._run(query=query, n_results=num_results)
        else:  # hybrid
            results = tool._run(query=query, k=num_results)

        # Print results
        print(format_results(results, tool_name))
        print()

    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()


async def interactive_mode():
    """Interactive CLI mode."""
    print_header()
    print_tool_info()

    print("Interactive Retrieval Mode")
    print("─" * 80)
    print("Enter your search queries, or 'exit' to quit.")
    print()

    while True:
        try:
            query = input("\n🔍 Search query: ").strip()

            if not query:
                continue

            if query.lower() in ['exit', 'quit', 'q']:
                print("\nExiting...")
                break

            if query.lower() == 'help':
                print()
                print_tool_info()
                continue

            # Ask for tool choice
            tool_input = input("   Tool (auto/semantic/keyword/hybrid) [auto]: ").strip().lower()
            tool_choice = tool_input if tool_input in ['auto', 'semantic', 'keyword', 'hybrid'] else 'auto'

            # Ask for number of results
            num_input = input("   Number of results [5]: ").strip()
            try:
                num_results = int(num_input) if num_input else 5
            except ValueError:
                num_results = 5

            print()
            print("─" * 80)
            print()

            await retrieval_search(query, tool_choice, num_results)

            print()
            input("Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Command line mode
        query = ""
        tool_choice = "auto"
        num_results = 5

        # Parse arguments
        args = sys.argv[1:]
        i = 0
        while i < len(args):
            arg = args[i]

            if arg in ['--tool', '-t']:
                if i + 1 < len(args):
                    tool_choice = args[i + 1]
                    i += 2
                else:
                    print("Error: --tool requires a value")
                    sys.exit(1)
            elif arg in ['--num', '-n']:
                if i + 1 < len(args):
                    try:
                        num_results = int(args[i + 1])
                        i += 2
                    except ValueError:
                        print("Error: --num requires an integer")
                        sys.exit(1)
                else:
                    print("Error: --num requires a value")
                    sys.exit(1)
            elif arg in ['--help', '-h']:
                print_header()
                print("Usage:")
                print("  python scripts/cli_retrieval.py \"query\" [options]")
                print()
                print("Options:")
                print("  --tool, -t     Tool to use (auto, semantic, keyword, hybrid) [auto]")
                print("  --num, -n      Number of results [5]")
                print("  --help, -h     Show this help")
                print()
                print_tool_info()
                sys.exit(0)
            else:
                query += " " + arg
                i += 1

        query = query.strip()

        if not query:
            print("Error: No query provided")
            print("Usage: python scripts/cli_retrieval.py \"your query here\"")
            sys.exit(1)

        print_header()
        await retrieval_search(query, tool_choice, num_results)
    else:
        # Interactive mode
        await interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
