"""Resolution plan model for query execution strategy."""

from typing import Literal

from pydantic import BaseModel, Field


class ResolutionPlan(BaseModel):
    """Plan for resolving a legal research query."""

    strategy: Literal["simple", "complex", "deep_search"] = Field(
        ..., description="Overall execution strategy"
    )
    tools: list[str] = Field(
        ...,
        description="Tools to use: vector_search, concept_search, full_doc_reader, etc.",
    )
    agents: list[str] = Field(
        ...,
        description="Agents to use: retrieval, validation, synthesis, etc.",
    )
    estimated_time_seconds: int = Field(
        ..., description="Estimated execution time in seconds", ge=1
    )
    parallel_capable: bool = Field(
        default=True, description="Whether retrieval can run in parallel"
    )
    requires_deep_search: bool = Field(
        default=False, description="Whether full document reading is needed"
    )
    reasoning: str = Field(..., description="Explanation of why this plan was chosen")
    max_documents: int = Field(
        default=10, description="Maximum documents to retrieve", ge=1, le=50
    )
    retrieval_strategies: list[str] = Field(
        default_factory=lambda: ["vector", "concept"],
        description="Retrieval strategies to use",
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "strategy": "complex",
                "tools": ["vector_search", "concept_search", "citation_validator"],
                "agents": ["retrieval", "validation", "synthesis"],
                "estimated_time_seconds": 25,
                "parallel_capable": True,
                "requires_deep_search": False,
                "reasoning": "Query requires cross-referencing multiple documents with semantic concept analysis",
                "max_documents": 10,
                "retrieval_strategies": ["vector", "concept"],
            }
        }

    def describe(self) -> str:
        """Get human-readable description of the plan."""
        desc_parts = []

        desc_parts.append(f"策略: {self._strategy_name()}")

        if self.parallel_capable:
            desc_parts.append("並行檢索")
        else:
            desc_parts.append("序列檢索")

        tool_names = [self._tool_name(t) for t in self.tools]
        desc_parts.append(f"工具: {', '.join(tool_names)}")

        desc_parts.append(f"預估時間: {self.estimated_time_seconds} 秒")

        if self.requires_deep_search:
            desc_parts.append("需要深度搜尋")

        return " | ".join(desc_parts)

    def _strategy_name(self) -> str:
        """Get Chinese name for strategy."""
        names = {
            "simple": "簡單查詢",
            "complex": "複雜查詢",
            "deep_search": "深度搜尋",
        }
        return names.get(self.strategy, self.strategy)

    def _tool_name(self, tool: str) -> str:
        """Get Chinese name for tool."""
        names = {
            "vector_search": "向量搜尋",
            "concept_search": "概念分析",
            "full_doc_reader": "全文閱讀",
            "citation_validator": "引用驗證",
            "semantic_analyzer": "語意分析",
        }
        return names.get(tool, tool)

    @classmethod
    def create_simple_plan(cls, reasoning: str = "") -> "ResolutionPlan":
        """Create a simple retrieval plan."""
        return cls(
            strategy="simple",
            tools=["vector_search"],
            agents=["retrieval", "synthesis"],
            estimated_time_seconds=15,
            parallel_capable=False,
            requires_deep_search=False,
            reasoning=reasoning or "Simple query with straightforward retrieval needs",
            max_documents=5,
            retrieval_strategies=["vector"],
        )

    @classmethod
    def create_complex_plan(cls, reasoning: str = "") -> "ResolutionPlan":
        """Create a complex retrieval plan with parallel search."""
        return cls(
            strategy="complex",
            tools=["vector_search", "concept_search", "citation_validator"],
            agents=["retrieval", "validation", "synthesis"],
            estimated_time_seconds=25,
            parallel_capable=True,
            requires_deep_search=False,
            reasoning=reasoning
            or "Complex query requiring multi-strategy retrieval and validation",
            max_documents=10,
            retrieval_strategies=["vector", "concept"],
        )

    @classmethod
    def create_deep_search_plan(cls, reasoning: str = "") -> "ResolutionPlan":
        """Create a deep search plan with full document reading."""
        return cls(
            strategy="deep_search",
            tools=[
                "vector_search",
                "concept_search",
                "full_doc_reader",
                "citation_validator",
            ],
            agents=["retrieval", "validation", "synthesis", "deep_reader"],
            estimated_time_seconds=45,
            parallel_capable=True,
            requires_deep_search=True,
            reasoning=reasoning
            or "Complex query requiring detailed analysis of full documents",
            max_documents=15,
            retrieval_strategies=["vector", "concept", "full_text"],
        )
