"""Todo manager for executing query tasks with parallel support."""

import asyncio
import logging
from typing import Any

from finagent.agents.ui_callback import UICallback
from finagent.models.todo_item import TodoItem

logger = logging.getLogger(__name__)


class TodoManager:
    """
    Manages execution of todo items with dependency resolution and parallelization.

    Features:
    - Executes tasks in dependency order
    - Runs parallel-capable tasks concurrently
    - Provides progress updates via UI callbacks
    - Handles task failures gracefully
    """

    def __init__(self, ui_callback: UICallback):
        """
        Initialize todo manager.

        Args:
            ui_callback: UI callback for progress updates
        """
        self.ui_callback = ui_callback

    async def execute_todos(
        self, todos: list[TodoItem], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute todo list with parallel execution where possible.

        Args:
            todos: List of todo items to execute
            context: Execution context (query, retriever, etc.)

        Returns:
            Dictionary of results keyed by todo ID
        """
        results = {}
        completed = set()
        failed = set()

        logger.info(f"Starting execution of {len(todos)} tasks")

        while len(completed) + len(failed) < len(todos):
            # Find tasks ready to execute (dependencies met, not started)
            ready_tasks = [
                todo
                for todo in todos
                if todo.is_ready_to_execute(completed)
                and todo.id not in failed
            ]

            if not ready_tasks:
                # No more tasks can be executed
                remaining = len(todos) - len(completed) - len(failed)
                if remaining > 0:
                    logger.warning(
                        f"Execution blocked: {remaining} tasks have unmet dependencies"
                    )
                break

            # Group by parallelization capability
            parallel_tasks = [t for t in ready_tasks if t.can_parallel]
            sequential_tasks = [t for t in ready_tasks if not t.can_parallel]

            # Execute parallel tasks concurrently
            if parallel_tasks:
                logger.info(
                    f"Executing {len(parallel_tasks)} tasks in parallel: "
                    f"{[t.content for t in parallel_tasks]}"
                )

                parallel_results = await asyncio.gather(
                    *[
                        self._execute_single_todo(todo, context)
                        for todo in parallel_tasks
                    ],
                    return_exceptions=True,
                )

                for todo, result in zip(parallel_tasks, parallel_results):
                    if isinstance(result, Exception):
                        logger.error(f"Task {todo.id} failed: {result}")
                        failed.add(todo.id)
                        await self.ui_callback.on_todo_failed(todo, str(result))
                    else:
                        results[todo.id] = result
                        completed.add(todo.id)
                        logger.info(f"Task {todo.id} completed successfully")

            # Execute sequential tasks one by one
            for todo in sequential_tasks:
                logger.info(f"Executing sequential task: {todo.content}")

                try:
                    result = await self._execute_single_todo(todo, context)
                    results[todo.id] = result
                    completed.add(todo.id)
                    logger.info(f"Task {todo.id} completed successfully")

                except Exception as e:
                    logger.error(f"Task {todo.id} failed: {e}", exc_info=True)
                    failed.add(todo.id)
                    await self.ui_callback.on_todo_failed(todo, str(e))
                    # Continue with other tasks

        logger.info(
            f"Execution complete: {len(completed)} completed, {len(failed)} failed"
        )

        return results

    async def _execute_single_todo(
        self, todo: TodoItem, context: dict[str, Any]
    ) -> Any:
        """
        Execute a single todo item.

        Args:
            todo: Todo item to execute
            context: Execution context

        Returns:
            Task result

        Raises:
            Exception: If task execution fails
        """
        # Mark as started
        todo.mark_started()
        await self.ui_callback.on_todo_started(todo)

        try:
            # Execute based on category
            if todo.category == "analysis":
                result = await self._execute_analysis_task(todo, context)
            elif todo.category == "retrieval":
                result = await self._execute_retrieval_task(todo, context)
            elif todo.category == "validation":
                result = await self._execute_validation_task(todo, context)
            elif todo.category == "synthesis":
                result = await self._execute_synthesis_task(todo, context)
            else:
                raise ValueError(f"Unknown task category: {todo.category}")

            # Mark as completed
            todo.mark_completed(result)
            await self.ui_callback.on_todo_completed(todo)

            return result

        except Exception as e:
            # Mark as failed
            todo.mark_failed(str(e))
            raise

    async def _execute_analysis_task(
        self, todo: TodoItem, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute query analysis task.

        Args:
            todo: Analysis todo item
            context: Execution context

        Returns:
            Analysis results
        """
        # Check if analysis is already provided in context
        if "analysis" in context:
            await self.ui_callback.on_todo_progress(todo, 100, "Using provided analysis")
            return {
                "analysis": context["analysis"],
                "needs_clarification": context["analysis"].get("needs_clarification", False),
            }

        # Otherwise, perform basic analysis
        query = context["query"]

        # Update progress
        await self.ui_callback.on_todo_progress(todo, 50, "Analyzing query")

        # Basic analysis (could be replaced with LLM call)
        analysis_result = {
            "intent": f"Search for: {query.text}",
            "entities": [],
            "complexity": "moderate",
            "needs_clarification": False,
        }

        # Update progress
        await self.ui_callback.on_todo_progress(todo, 100, "Analysis complete")

        return {
            "analysis": analysis_result,
            "needs_clarification": False,
        }

    async def _execute_retrieval_task(
        self, todo: TodoItem, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute retrieval task (vector or concept search).

        Args:
            todo: Retrieval todo item
            context: Execution context

        Returns:
            Retrieval results with chunks and metadata
        """
        query = context["query"]
        retriever = context.get("retriever")
        strategy = todo.substeps[0] if todo.substeps else "vector"

        if not retriever:
            raise ValueError("Retriever not provided in context")

        # Update progress
        await self.ui_callback.on_todo_progress(
            todo, 30, f"Searching via {strategy} strategy"
        )

        # Execute retrieval based on strategy
        if strategy == "vector":
            chunks = retriever.retrieve(query.text, n_results=10)
        elif strategy == "concept":
            chunks = await self._retrieve_via_concepts(query, context)
        elif strategy == "parallel":
            # Parallel concept + vector retrieval
            chunks = await self._retrieve_parallel(query, context)
        else:
            chunks = retriever.retrieve(query.text, n_results=10)

        # Update progress
        await self.ui_callback.on_todo_progress(
            todo, 80, f"Found {len(chunks)} chunks"
        )

        # Notify UI of retrieval result
        doc_ids = set(chunk.metadata.get("doc_id") for chunk in chunks)
        await self.ui_callback.on_retrieval_result(strategy, len(doc_ids), len(chunks))

        await self.ui_callback.on_todo_progress(todo, 100, "Retrieval complete")

        return {"chunks": chunks, "strategy": strategy, "count": len(chunks)}

    async def _retrieve_via_concepts(
        self, query, context: dict[str, Any]
    ) -> list[Any]:
        """
        Retrieve documents via semantic concept analysis.

        Args:
            query: User query
            context: Execution context

        Returns:
            List of retrieved chunks
        """
        # For now, use vector retrieval with concept filtering
        # TODO: Implement true concept-based retrieval
        retriever = context.get("retriever")

        # Simulate some processing time
        await asyncio.sleep(0.3)

        # Use concept filtering if available
        if hasattr(retriever, 'retrieve_with_concept_filtering'):
            chunks = retriever.retrieve_with_concept_filtering(query.text, n_results=10)
        else:
            # Fall back to regular vector retrieval
            chunks = retriever.retrieve(query.text, n_results=10)

        return chunks

    async def _retrieve_parallel(self, query, context: dict[str, Any]) -> list[Any]:
        """
        Execute parallel concept + vector retrieval.

        Args:
            query: User query
            context: Execution context

        Returns:
            Merged and deduplicated chunks
        """
        retriever = context.get("retriever")

        # Run concept and vector retrieval in parallel
        concept_results, vector_results = await asyncio.gather(
            self._retrieve_via_concepts(query, context),
            asyncio.to_thread(retriever.retrieve, query.text, 10),
        )

        # Merge and deduplicate results
        seen_ids = set()
        merged_chunks = []

        for chunk in concept_results + vector_results:
            chunk_id = f"{chunk.metadata.get('doc_id')}_{chunk.metadata.get('chunk_id')}"
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                merged_chunks.append(chunk)

        logger.info(
            f"Parallel retrieval: {len(concept_results)} concept + "
            f"{len(vector_results)} vector = {len(merged_chunks)} merged"
        )

        return merged_chunks

    async def _execute_validation_task(
        self, todo: TodoItem, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute validation task.

        Args:
            todo: Validation todo item
            context: Execution context

        Returns:
            Validation results
        """
        # Get all retrieval results from context
        retrieval_results = context.get("retrieval_results", {})

        # Update progress
        await self.ui_callback.on_todo_progress(
            todo, 50, "Validating retrieval results"
        )

        # Simulate validation (basic check)
        total_chunks = sum(
            len(result.get("chunks", []))
            for result in retrieval_results.values()
            if isinstance(result, dict)
        )

        await asyncio.sleep(0.5)  # Simulate processing

        await self.ui_callback.on_todo_progress(todo, 100, "Validation complete")

        return {
            "validation_passed": total_chunks > 0,
            "total_chunks": total_chunks,
            "issues": [] if total_chunks > 0 else ["No chunks retrieved"],
        }

    async def _execute_synthesis_task(
        self, todo: TodoItem, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute answer synthesis task.

        Args:
            todo: Synthesis todo item
            context: Execution context

        Returns:
            Generated answer
        """
        query = context["query"]

        # Update progress
        await self.ui_callback.on_todo_progress(todo, 20, "Preparing context")
        await self.ui_callback.on_answer_generation_start()

        # Update progress
        await self.ui_callback.on_todo_progress(
            todo, 60, "Generating answer"
        )

        # Simulate answer generation
        await asyncio.sleep(1.0)

        # Create mock answer
        from finagent.models.answers import LegalAnswer
        from finagent.models.citations import LegalCitation, CitationType, CitationAuthority

        answer = LegalAnswer(
            query=query,
            executive_summary=f"根據查詢「{query.text}」的分析結果...",
            key_findings=["發現 1", "發現 2"],
            detailed_analysis="詳細分析內容",
            confidence_score="高",  # ConfidenceLevel enum: "高", "中", "低"
            confidence_explanation="基於充分的資料來源",
            citations=[
                LegalCitation(
                    id=1,
                    type=CitationType.ENFORCEMENT_DOCUMENT,
                    authority=CitationAuthority.PRIMARY,
                    title="測試文件",
                    formatted_citation="測試文件（民國110年）",
                )
            ],
        )

        # Update progress
        await self.ui_callback.on_todo_progress(todo, 90, "Formatting citations")

        # Format citations
        if answer.citations:
            await self.ui_callback.on_citations_formatted(answer.citations)

        await self.ui_callback.on_todo_progress(todo, 100, "Answer complete")

        return {"answer": answer}
