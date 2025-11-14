"""Reference Guard Agent - Decides if re-search is needed based on validation results."""

import logging

from finagent.agents.state import AgentState

logger = logging.getLogger(__name__)


class ReferenceGuard:
    """
    Reference Guard evaluates validation results and decides if re-search is needed.

    Responsibilities:
    - Evaluate validation issue severity
    - Decide whether to trigger re-search
    - Increment search iteration counter
    - Prevent infinite loops with max iteration limit
    """

    def __init__(self, max_iterations: int = 2):
        """
        Initialize reference guard.

        Args:
            max_iterations: Maximum number of re-search iterations allowed (default: 2)
        """
        self.max_iterations = max_iterations

    def evaluate(self, state: AgentState) -> AgentState:
        """
        Evaluate validation results and update state.

        Args:
            state: Current agent state with validation results

        Returns:
            Updated state with re-search decision
        """
        current_iteration = state.get("search_iteration", 0)
        validation_passed = state.get("validation_passed", True)
        validation_issues = state.get("validation_issues", [])
        retrieved_chunks = state.get("retrieved_chunks", [])

        logger.info(
            f"Reference guard evaluating: iteration={current_iteration}, "
            f"validation_passed={validation_passed}, "
            f"issues={len(validation_issues)}"
        )

        # Check if re-search should be performed
        should_research = self._should_research(
            current_iteration=current_iteration,
            validation_passed=validation_passed,
            validation_issues=validation_issues,
            has_documents=len(retrieved_chunks) > 0,
        )

        if should_research:
            # Increment iteration for next search
            state["search_iteration"] = current_iteration + 1

            # Update strategy for next iteration
            state["search_strategy"] = self._get_strategy(state["search_iteration"])

            state["processing_steps"].append(
                f"參考守衛：檢測到關鍵問題，啟動第 {state['search_iteration'] + 1} 次搜索"
                f"（策略：{state['search_strategy']}）"
            )

            logger.info(
                f"Re-search triggered: iteration {state['search_iteration']}, "
                f"strategy={state['search_strategy']}"
            )
        else:
            state["processing_steps"].append(
                f"參考守衛：驗證{'通過' if validation_passed else '未通過'}，"
                f"{'繼續生成答案' if not should_research else '已達最大搜索次數'}"
            )

            logger.info("No re-search needed, proceeding to answer")

        return state

    def _should_research(
        self,
        current_iteration: int,
        validation_passed: bool,
        validation_issues: list[str],
        has_documents: bool,
    ) -> bool:
        """
        Decide if re-search is needed.

        Args:
            current_iteration: Current search iteration
            validation_passed: Whether validation passed
            validation_issues: List of validation issues
            has_documents: Whether any documents were retrieved

        Returns:
            True if re-search should be performed, False otherwise
        """
        # Don't re-search if already at max iterations
        if current_iteration >= self.max_iterations:
            logger.info(f"Max iterations reached ({self.max_iterations}), no re-search")
            return False

        # Don't re-search if validation passed
        if validation_passed:
            logger.info("Validation passed, no re-search needed")
            return False

        # Don't re-search if no documents found (won't help)
        if not has_documents:
            logger.info("No documents found, re-search unlikely to help")
            return False

        # Check if issues are critical enough to warrant re-search
        has_critical_issue = self._has_critical_issues(validation_issues)

        if not has_critical_issue:
            logger.info("No critical issues detected, proceeding without re-search")
            return False

        logger.info("Critical issues detected, re-search warranted")
        return True

    def _has_critical_issues(self, validation_issues: list[str]) -> bool:
        """
        Check if validation issues are critical enough to warrant re-search.

        Args:
            validation_issues: List of validation issue messages

        Returns:
            True if critical issues found, False otherwise
        """
        # Define critical issue keywords
        critical_keywords = [
            "關鍵字檢查失敗",  # Missing required keywords
            "實體類型不符",  # Entity type mismatch
        ]

        # Check if any issue contains critical keywords
        for issue in validation_issues:
            if any(keyword in issue for keyword in critical_keywords):
                logger.info(f"Critical issue found: {issue[:100]}...")
                return True

        return False

    def _get_strategy(self, iteration: int) -> str:
        """
        Get search strategy name for given iteration.

        Args:
            iteration: Search iteration number

        Returns:
            Strategy name: "strict", "relaxed", or "broad"
        """
        strategies = {
            0: "strict",
            1: "relaxed",
            2: "broad",
        }

        return strategies.get(iteration, "broad")


def get_search_params(iteration: int) -> dict:
    """
    Get search parameters based on iteration.

    Args:
        iteration: Search iteration number (0 = first search, 1-2 = re-search)

    Returns:
        Dict with search parameters: threshold, max_results, strategy
    """
    strategies = {
        0: {  # First search - strict
            "strategy": "strict",
            "threshold": 0.8,
            "max_results": 5,
        },
        1: {  # First re-search - relaxed
            "strategy": "relaxed",
            "threshold": 0.9,
            "max_results": 10,
        },
        2: {  # Second re-search - broad
            "strategy": "broad",
            "threshold": 1.0,
            "max_results": 15,
        },
    }

    # Default to broad strategy if iteration exceeds defined strategies
    return strategies.get(iteration, strategies[2])
