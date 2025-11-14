"""Validation Agent - Validates citations and fact coverage."""

import logging

from finagent.agents.state import AgentState
from finagent.utils.keyword_extraction import (
    extract_critical_keywords,
    extract_must_have_keywords,
    identify_entity_type,
    validate_keyword_presence,
    validate_entity_type_match,
)

logger = logging.getLogger(__name__)


class ValidationAgent:
    """
    Validation Agent ensures citation integrity and fact coverage.

    Responsibilities:
    - Verify all retrieved chunks have valid citations
    - Check citation format compliance (Taiwan legal format)
    - Ensure sufficient source coverage
    - Flag potential issues for review
    """

    def __init__(self, min_citations: int = 1, ui_callback=None):
        """
        Initialize validation agent.

        Args:
            min_citations: Minimum number of citations required
            ui_callback: Optional UICallback for progress updates
        """
        self.min_citations = min_citations
        self.ui_callback = ui_callback

    def validate(self, state: AgentState) -> AgentState:
        """
        Validate retrieved documents and citations.

        Args:
            state: Current agent state with retrieved chunks and citations

        Returns:
            Updated state with validation results
        """
        logger.info("Validation agent checking citation integrity")

        # Phase 5: Find and mark validation todo as in_progress
        todos = state.get("todos", [])
        validation_todo = next((t for t in todos if t.category == "validation"), None)

        if validation_todo and validation_todo.status == "pending":
            validation_todo.mark_started()
            if self.ui_callback:
                import asyncio
                try:
                    asyncio.create_task(self.ui_callback.on_todo_started(validation_todo))
                except RuntimeError:
                    pass

        # Emit validation start callback
        if self.ui_callback:
            import asyncio
            try:
                asyncio.create_task(self.ui_callback.on_validation_start())
            except RuntimeError:
                pass

        citations = state.get("citations", [])
        retrieved_chunks = state.get("retrieved_chunks", [])
        query = state.get("query")
        query_text = query.text if query else ""
        issues = []

        try:
            # Check 1: Minimum citations
            if len(citations) < self.min_citations:
                issues.append(
                    f"引用來源不足：僅有 {len(citations)} 個引用，建議至少 {self.min_citations} 個"
                )

            # Check 2: All chunks have valid metadata
            for idx, chunk in enumerate(retrieved_chunks, 1):
                if not chunk.metadata:
                    issues.append(f"文件片段 {idx} 缺少元數據")
                elif not chunk.metadata.get("filename"):
                    issues.append(f"文件片段 {idx} 缺少檔名資訊")

            # Check 3: Citation format validation (basic check)
            for citation in citations:
                if not citation.title or citation.title == "未知文件":
                    issues.append(f"引用 {citation.id} 缺少標題")
                if not citation.issuing_authority:
                    issues.append(f"引用 {citation.id} 缺少發布機關")

            # Check 4: Keyword validation (NEW - CRITICAL)
            if query_text and retrieved_chunks:
                # Extract critical keywords from query
                critical_keywords = extract_critical_keywords(query_text)
                must_have_keywords = extract_must_have_keywords(query_text)

                logger.info(f"Critical keywords for validation: {critical_keywords}")
                logger.info(f"Must-have keywords: {must_have_keywords}")

                if must_have_keywords:
                    # Check if AT LEAST ONE chunk contains the must-have keywords
                    chunks_with_keywords = []

                    for chunk in retrieved_chunks:
                        chunk_text = chunk.page_content if hasattr(chunk, 'page_content') else str(chunk)
                        has_all_keywords, missing = validate_keyword_presence(must_have_keywords, chunk_text)

                        if not missing:  # All must-have keywords present
                            chunks_with_keywords.append(chunk)

                    if not chunks_with_keywords:
                        # CRITICAL: No chunks contain must-have keywords
                        issues.append(
                            f"⚠️ 關鍵字檢查失敗：所有引用文件都缺少必要關鍵字 {must_have_keywords}。"
                            f"這些文件可能與查詢主題不符。"
                        )
                        logger.warning(f"Keyword validation failed: No chunks contain {must_have_keywords}")

            # Check 5: Entity type validation (NEW)
            if query_text and retrieved_chunks:
                query_entity_type = identify_entity_type(query_text)

                if query_entity_type != "unknown":
                    # Query specifies an entity type - validate chunks match
                    mismatched_chunks = []

                    for idx, chunk in enumerate(retrieved_chunks):
                        chunk_text = chunk.page_content if hasattr(chunk, 'page_content') else str(chunk)
                        chunk_entity_type = identify_entity_type(chunk_text)

                        if chunk_entity_type != "unknown" and chunk_entity_type != query_entity_type:
                            mismatched_chunks.append((idx + 1, chunk_entity_type))

                    if mismatched_chunks:
                        mismatch_details = ", ".join([f"文件{idx}({etype})" for idx, etype in mismatched_chunks])
                        issues.append(
                            f"⚠️ 實體類型不符：查詢要求 {query_entity_type}，"
                            f"但以下文件類型不符：{mismatch_details}"
                        )
                        logger.warning(f"Entity type mismatch: Query={query_entity_type}, Mismatches={mismatched_chunks}")

            # Determine validation result
            validation_passed = len(issues) == 0

            # Update state
            state["validation_passed"] = validation_passed
            state["validation_issues"] = issues

            if validation_passed:
                state["processing_steps"].append("驗證代理：所有引用通過驗證")
                logger.info("Validation passed")
            else:
                state["processing_steps"].append(f"驗證代理：發現 {len(issues)} 個潛在問題")
                logger.warning(f"Validation found {len(issues)} issues: {issues}")

            # Phase 5: Mark validation todo as completed (always mark as completed, even with warnings)
            if validation_todo:
                validation_todo.mark_completed(result={"passed": validation_passed, "issues": len(issues)})
                if self.ui_callback:
                    import asyncio
                    try:
                        asyncio.create_task(self.ui_callback.on_todo_completed(validation_todo))
                    except RuntimeError:
                        pass

            # Update state with todos
            state["todos"] = todos

            # Emit validation complete callback
            if self.ui_callback:
                import asyncio
                try:
                    asyncio.create_task(
                        self.ui_callback.on_validation_complete(
                            passed=validation_passed,
                            issues=issues
                        )
                    )
                except RuntimeError:
                    pass

        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            state["errors"].append(f"驗證失敗：{str(e)}")
            state["validation_passed"] = False
            state["validation_issues"] = [f"驗證過程錯誤：{str(e)}"]

            # Phase 5: Mark validation todo as failed
            todos = state.get("todos", [])
            validation_todo = next((t for t in todos if t.category == "validation"), None)
            if validation_todo:
                validation_todo.mark_failed(error=str(e))
                if self.ui_callback:
                    import asyncio
                    try:
                        asyncio.create_task(self.ui_callback.on_todo_failed(validation_todo, str(e)))
                    except RuntimeError:
                        pass
            state["todos"] = todos

        return state
