"""Deep Agent module for FinAgent.

This module provides a Deep Agent implementation using the deepagents library,
offering Claude Code-like capabilities including:
- Task planning with TodoListMiddleware
- Sub-agent delegation with SubAgentMiddleware
- Context management with SummarizationMiddleware
"""

from finagent.agents.deep_agent.financial_agent import (
    FinAgentDeepAgent,
    create_finagent_deep_agent,
)
from finagent.agents.deep_agent.tools import (
    hybrid_search,
    keyword_search,
    semantic_search,
)

__all__ = [
    "create_finagent_deep_agent",
    "FinAgentDeepAgent",
    "semantic_search",
    "keyword_search",
    "hybrid_search",
]
