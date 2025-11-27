"""
LangGraph visualization of the new UI-driven query flow.

This module creates a visual flowchart showing the execution flow
with parallel execution, dependency management, and UI callbacks.
"""

from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class QueryFlowState(TypedDict):
    """State for the query flow graph."""

    # Input
    query: str

    # Analysis stage
    analysis: dict | None
    needs_clarification: bool

    # Planning stage
    resolution_plan: dict | None
    todo_list: list[dict] | None

    # Retrieval stage (parallel)
    concept_results: list | None
    vector_results: list | None
    merged_chunks: list | None

    # Validation stage
    validation_passed: bool
    validation_issues: list[str]

    # Synthesis stage
    final_answer: dict | None
    citations: list | None

    # UI updates
    messages: Annotated[list, add_messages]


def create_query_flow_graph():
    """
    Create a LangGraph visualization of the new query flow.

    Shows:
    - Sequential stages (analysis → planning → retrieval → validation → synthesis)
    - Parallel execution (concept + vector retrieval)
    - Conditional paths (clarification, deep search)
    - UI callback points

    Returns:
        Compiled LangGraph
    """

    # Define node functions
    def analyze_query(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 1: Analyze query intent and complexity.

        UI Callbacks:
        - on_analysis_start()
        - on_analysis_complete()
        """
        return {
            **state,
            "analysis": {"intent": "...", "complexity": "moderate", "entities": []},
            "needs_clarification": False,
            "messages": [{"role": "system", "content": "🔍 Analysis complete"}],
        }

    def request_clarification(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 2 (Optional): Request user clarification.

        UI Callbacks:
        - on_clarification_requested()
        """
        return {
            **state,
            "messages": [{"role": "system", "content": "❓ Clarification needed"}],
        }

    def create_resolution_plan(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 3: Create execution plan based on complexity.

        Strategies:
        - Simple: Vector search only (15s)
        - Complex: Parallel concept + vector (25s)
        - Deep Search: Full document reading (45s)

        UI Callbacks:
        - on_plan_created()
        - on_todo_list_created()
        """
        return {
            **state,
            "resolution_plan": {"strategy": "complex", "parallel_capable": True},
            "todo_list": [
                {"id": "analysis", "status": "completed"},
                {"id": "retrieval_concept", "status": "pending", "can_parallel": True},
                {"id": "retrieval_vector", "status": "pending", "can_parallel": True},
                {"id": "validation", "status": "pending"},
                {"id": "synthesis", "status": "pending"},
            ],
            "messages": [{"role": "system", "content": "📋 Plan: Complex (parallel retrieval)"}],
        }

    def retrieve_via_concept(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 4a: Concept-based retrieval (parallel).

        UI Callbacks:
        - on_todo_started(concept_task)
        - on_todo_progress(concept_task, percentage, message)
        - on_retrieval_result("concept", doc_count, chunk_count)
        - on_todo_completed(concept_task)
        """
        return {
            **state,
            "concept_results": ["chunk1", "chunk2", "chunk3"],
            "messages": [{"role": "system", "content": "✓ Concept retrieval: 3 docs"}],
        }

    def retrieve_via_vector(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 4b: Vector similarity retrieval (parallel with 4a).

        UI Callbacks:
        - on_todo_started(vector_task)
        - on_todo_progress(vector_task, percentage, message)
        - on_retrieval_result("vector", doc_count, chunk_count)
        - on_todo_completed(vector_task)
        """
        return {
            **state,
            "vector_results": ["chunk4", "chunk5", "chunk6"],
            "messages": [{"role": "system", "content": "✓ Vector retrieval: 5 docs"}],
        }

    def merge_results(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 5: Merge and deduplicate parallel retrieval results.
        """
        concept = state.get("concept_results", [])
        vector = state.get("vector_results", [])
        return {
            **state,
            "merged_chunks": concept + vector,
            "messages": [{"role": "system", "content": f"Merged: {len(concept) + len(vector)} chunks"}],
        }

    def validate_results(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 6: Validate citation integrity and coverage.

        UI Callbacks:
        - on_todo_started(validation_task)
        - on_todo_progress(validation_task, percentage, message)
        - on_todo_completed(validation_task)
        """
        chunks = state.get("merged_chunks", [])
        return {
            **state,
            "validation_passed": len(chunks) > 0,
            "validation_issues": [] if len(chunks) > 0 else ["No chunks found"],
            "messages": [{"role": "system", "content": "✓ Validation passed"}],
        }

    def perform_deep_search(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 7 (Optional): Read full documents for deep analysis.

        Triggered when:
        - Query complexity is high
        - Initial results are insufficient
        - User explicitly requests detailed analysis

        UI Callbacks:
        - on_todo_started(deep_search_task)
        - on_todo_progress(deep_search_task, percentage, message)
        """
        return {
            **state,
            "messages": [{"role": "system", "content": "🔬 Deep search complete"}],
        }

    def synthesize_answer(state: QueryFlowState) -> QueryFlowState:
        """
        Stage 8: Generate final answer with LLM synthesis.

        UI Callbacks:
        - on_todo_started(synthesis_task)
        - on_answer_generation_start()
        - on_todo_progress(synthesis_task, percentage, message)
        - on_citations_formatted(citations)
        - on_todo_completed(synthesis_task)
        - on_answer_complete(answer)
        """
        return {
            **state,
            "final_answer": {"executive_summary": "...", "key_findings": []},
            "citations": [{"id": 1, "title": "Source 1"}],
            "messages": [{"role": "system", "content": "✨ Answer complete"}],
        }

    # Conditional routing functions
    def should_clarify(state: QueryFlowState) -> str:
        """Route to clarification if needed."""
        if state.get("needs_clarification", False):
            return "clarify"
        return "plan"

    def should_deep_search(state: QueryFlowState) -> str:
        """Route to deep search if validation fails or complexity is high."""
        plan = state.get("resolution_plan", {})
        validation_passed = state.get("validation_passed", True)

        if plan.get("strategy") == "deep_search" or not validation_passed:
            return "deep_search"
        return "synthesize"

    # Build the graph
    workflow = StateGraph(QueryFlowState)

    # Add nodes
    workflow.add_node("analyze", analyze_query)
    workflow.add_node("clarify", request_clarification)
    workflow.add_node("plan", create_resolution_plan)
    workflow.add_node("retrieve_concept", retrieve_via_concept)
    workflow.add_node("retrieve_vector", retrieve_via_vector)
    workflow.add_node("merge", merge_results)
    workflow.add_node("validate", validate_results)
    workflow.add_node("deep_search", perform_deep_search)
    workflow.add_node("synthesize", synthesize_answer)

    # Add edges
    # Sequential flow
    workflow.add_edge(START, "analyze")
    workflow.add_conditional_edges(
        "analyze",
        should_clarify,
        {
            "clarify": "clarify",
            "plan": "plan",
        }
    )
    workflow.add_edge("clarify", "plan")

    # Parallel retrieval
    workflow.add_edge("plan", "retrieve_concept")
    workflow.add_edge("plan", "retrieve_vector")

    # Merge after parallel completion
    workflow.add_edge("retrieve_concept", "merge")
    workflow.add_edge("retrieve_vector", "merge")

    # Validation
    workflow.add_edge("merge", "validate")

    # Conditional deep search
    workflow.add_conditional_edges(
        "validate",
        should_deep_search,
        {
            "deep_search": "deep_search",
            "synthesize": "synthesize",
        }
    )
    workflow.add_edge("deep_search", "synthesize")

    # End
    workflow.add_edge("synthesize", END)

    # Compile
    app = workflow.compile()

    return app


def visualize_query_flow(output_path: str = "query_flow_graph.png"):
    """
    Generate and save a visual diagram of the query flow.

    Args:
        output_path: Path to save the PNG diagram

    Returns:
        Path to the generated diagram
    """
    graph = create_query_flow_graph()

    # Generate Mermaid diagram
    try:
        from IPython.display import Image, display

        # Get the graph visualization
        img_data = graph.get_graph().draw_mermaid_png()

        # Save to file
        with open(output_path, "wb") as f:
            f.write(img_data)

        print(f"✅ Graph saved to: {output_path}")
        return output_path

    except ImportError:
        print("⚠️  IPython not available. Generating Mermaid source instead.")

        # Generate Mermaid source code
        mermaid_code = graph.get_graph().draw_mermaid()

        mermaid_path = output_path.replace(".png", ".mmd")
        with open(mermaid_path, "w") as f:
            f.write(mermaid_code)

        print(f"✅ Mermaid source saved to: {mermaid_path}")
        print("\nTo visualize, paste the content into: https://mermaid.live/")

        return mermaid_path


def print_ascii_flow():
    """
    Print ASCII art representation of the query flow.

    This provides a quick visual reference without dependencies.
    """
    flow = """
╔══════════════════════════════════════════════════════════════════════╗
║                    FinAgent Query Flow (LangGraph)                   ║
╚══════════════════════════════════════════════════════════════════════╝

                              ┌─────────┐
                              │  START  │
                              └────┬────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │ 🔍 Analyze      │
                         │    Query        │
                         └────┬────────────┘
                              │
                         ┌────┴────┐
                         │ Need    │
                         │ Clarify?│
                         └─┬────┬──┘
                    Yes    │    │    No
                      ┌────┘    └────┐
                      ▼              ▼
              ┌───────────┐    ┌────────────┐
              │ ❓ Request │    │ 📋 Create  │
              │ Clarify   │    │    Plan    │
              └─────┬─────┘    └─────┬──────┘
                    │                │
                    └────────┬───────┘
                             ▼
                    ┌────────────────┐
                    │  Parallel      │
                    │  Retrieval     │
                    └────┬──────┬────┘
                         │      │
                    ┌────┘      └────┐
                    ▼                ▼
          ┌──────────────┐  ┌──────────────┐
          │ 🔤 Concept   │  │ 🎯 Vector    │
          │   Retrieval  │  │   Retrieval  │
          └──────┬───────┘  └──────┬───────┘
                 │                 │
                 └────────┬────────┘
                          ▼
                 ┌────────────────┐
                 │ Merge Results  │
                 └────────┬───────┘
                          ▼
                 ┌────────────────┐
                 │ ✓ Validate     │
                 │   Citations    │
                 └────┬───────────┘
                      │
                 ┌────┴─────┐
                 │ Deep     │
                 │ Search?  │
                 └─┬─────┬──┘
            Yes    │     │    No
              ┌────┘     └────┐
              ▼               ▼
      ┌──────────────┐  ┌────────────────┐
      │ 🔬 Deep      │  │ 🤖 Synthesize  │
      │    Search    │  │    Answer      │
      └──────┬───────┘  └────────┬───────┘
             │                   │
             └─────────┬─────────┘
                       ▼
              ┌────────────────┐
              │ 📚 Show        │
              │    Citations   │
              └────────┬───────┘
                       ▼
              ┌────────────────┐
              │  ✨ Final      │
              │     Answer     │
              └────────┬───────┘
                       ▼
                  ┌────────┐
                  │  END   │
                  └────────┘

╔══════════════════════════════════════════════════════════════════════╗
║  Legend:                                                             ║
║  🔍 Analysis   📋 Planning    🔤 Concept Search   🎯 Vector Search   ║
║  ✓ Validation  🔬 Deep Search 🤖 LLM Synthesis   📚 Citations       ║
║  ✨ Final      ❓ Clarification                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Key Features:
  • Parallel Execution: Concept + Vector retrieval run simultaneously
  • Conditional Routing: Clarification and deep search when needed
  • UI Callbacks: 14 callback points for real-time updates
  • Error Handling: Graceful failures with detailed error messages
  • Progress Tracking: 0-100% progress for each task

Performance:
  • Simple Plan: ~15s (vector only)
  • Complex Plan: ~25s (parallel retrieval)
  • Deep Search Plan: ~45s (full document reading)
  • Parallel Speedup: 40-50% faster than sequential

"""
    print(flow)


if __name__ == "__main__":
    import sys

    print("🚀 FinAgent Query Flow - LangGraph Visualization\n")

    # Print ASCII flow
    print_ascii_flow()

    # Generate graph visualization
    print("\n" + "="*70)
    print("Generating LangGraph diagram...")
    print("="*70 + "\n")

    try:
        output_path = visualize_query_flow("query_flow_graph.png")
        print(f"\n✅ Success! Graph diagram available at: {output_path}")
    except Exception as e:
        print(f"\n⚠️  Error generating graph: {e}")
        print("ASCII flow diagram shown above is still available.")

    sys.exit(0)
