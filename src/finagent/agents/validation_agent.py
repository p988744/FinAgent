"""Validation Agent - Validates citations and fact coverage."""

import logging

from finagent.agents.state import AgentState

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

    def __init__(self, min_citations: int = 1):
        """
        Initialize validation agent.

        Args:
            min_citations: Minimum number of citations required
        """
        self.min_citations = min_citations

    def validate(self, state: AgentState) -> AgentState:
        """
        Validate retrieved documents and citations.

        Args:
            state: Current agent state with retrieved chunks and citations

        Returns:
            Updated state with validation results
        """
        logger.info("Validation agent checking citation integrity")

        citations = state.get("citations", [])
        retrieved_chunks = state.get("retrieved_chunks", [])
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

        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            state["errors"].append(f"驗證失敗：{str(e)}")
            state["validation_passed"] = False
            state["validation_issues"] = [f"驗證過程錯誤：{str(e)}"]

        return state
