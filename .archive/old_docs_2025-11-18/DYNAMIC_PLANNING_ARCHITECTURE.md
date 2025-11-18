# Dynamic Planning Agent & Tool Registry Architecture

**Version:** 1.0.0
**Date:** 2025-01-18
**Status:** Design Document
**Author:** Claude Code

## Executive Summary

This document outlines the architecture for transforming FinAgent's query system from a rigid vector-search-only approach to a dynamic, tool-based system capable of handling complex query types. The design addresses four critical query limitations and provides a scalable framework for future capability expansion.

## 1. Problem Statement

### Current Limitations

The existing system cannot process the following query types:

| Query Type | Example | Root Cause | Required Capability |
|------------|---------|------------|---------------------|
| **Temporal** | "玉山銀行最近一次的罰款紀錄" | No metadata-based filtering | Latest record retrieval by date |
| **Comprehensive** | "玉山銀行過去所有的裁罰紀錄" | Top-k vector search only | Full document listing + deep reading |
| **Specific File** | "「國泰世華銀行_內線交易_2021.txt」這個檔案的摘要" | No direct file access | Direct file loading |
| **Multi-Entity** | "玉山銀行與國泰世華銀行的裁罰紀錄比較" | Single entity focus | Parallel multi-entity search |

### Root Architectural Issues

1. **Planning Agent Rigidity**: Hardcoded to only use vector search
2. **No Tool Abstraction**: Retrieval logic tightly coupled to action agent
3. **Missing Metadata Layer**: Document metadata not queryable
4. **Single-Path Execution**: Cannot orchestrate multiple search strategies

## 2. Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Query                                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Enhanced Planning Agent                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Query Analyzer (LLM)                                    │    │
│  │ - Intent Classification                                 │    │
│  │ - Entity Extraction                                     │    │
│  │ - Temporal Detection                                    │    │
│  │ - Complexity Assessment                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Tool Selector (LLM)                                     │    │
│  │ - Tool Registry Lookup                                  │    │
│  │ - Capability Matching                                   │    │
│  │ - Task Sequencing                                       │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Tool Registry                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Vector  │  │ Metadata │  │   List   │  │   Read   │       │
│  │  Search  │  │  Search  │  │   Docs   │  │   File   │  ...  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Enhanced Action Agent                          │
│  - Tool Execution                                                │
│  - Result Aggregation                                            │
│  - Relevance Filtering                                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Validation Agent → Answer Agent                     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Tool Registry System**: Centralized tool management with pluggable architecture
2. **Enhanced Planning Agent**: LLM-driven query analysis and tool selection
3. **Tool Interface**: Standardized contract for all tools
4. **Enhanced Action Agent**: Multi-tool executor with aggregation logic
5. **Metadata Layer**: Document metadata indexing and querying

## 3. Tool Registry System

### 3.1 Tool Interface

All tools must implement the `BaseTool` interface:

```python
# src/finagent/tools/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel, Field

class ToolCapability(BaseModel):
    """Describes what a tool can do."""
    name: str = Field(..., description="Tool name (e.g., 'vector_search')")
    description: str = Field(..., description="What this tool does")

    # Query intent matching
    supported_intents: List[str] = Field(
        ...,
        description="Query intents this tool can handle (e.g., 'temporal', 'comparison', 'specific_file')"
    )

    # Required query features
    required_features: List[str] = Field(
        default_factory=list,
        description="Features needed in query (e.g., 'entity_name', 'date_range', 'filename')"
    )

    # Execution characteristics
    execution_time_estimate: str = Field(
        ...,
        description="Estimated execution time (e.g., 'fast', 'medium', 'slow')"
    )

    cost_estimate: str = Field(
        ...,
        description="Resource cost (e.g., 'low', 'medium', 'high')"
    )

    # Limitations
    limitations: List[str] = Field(
        default_factory=list,
        description="Known limitations of this tool"
    )

class ToolInput(BaseModel):
    """Standardized input for all tools."""
    query: str = Field(..., description="User query")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific parameters"
    )

class ToolOutput(BaseModel):
    """Standardized output from all tools."""
    success: bool = Field(..., description="Whether execution succeeded")
    results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved results (documents, metadata, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata (time, cost, etc.)"
    )
    error: str | None = Field(None, description="Error message if failed")

class BaseTool(ABC):
    """Base class for all tools."""

    @abstractmethod
    def get_capability(self) -> ToolCapability:
        """Return tool capability description."""
        pass

    @abstractmethod
    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """Execute the tool."""
        pass

    @abstractmethod
    def validate_input(self, tool_input: ToolInput) -> bool:
        """Validate input parameters."""
        pass
```

### 3.2 Tool Registry Implementation

```python
# src/finagent/tools/registry.py

from typing import Dict, List, Type
from finagent.tools.base import BaseTool, ToolCapability

class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._capabilities: Dict[str, ToolCapability] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new tool."""
        capability = tool.get_capability()
        self._tools[capability.name] = tool
        self._capabilities[capability.name] = capability
        logger.info(f"Registered tool: {capability.name}")

    def get_tool(self, name: str) -> BaseTool | None:
        """Get tool by name."""
        return self._tools.get(name)

    def get_all_capabilities(self) -> Dict[str, ToolCapability]:
        """Get all tool capabilities for planning."""
        return self._capabilities.copy()

    def find_tools_for_intent(self, intent: str) -> List[str]:
        """Find tools that support a given intent."""
        matching_tools = []
        for name, capability in self._capabilities.items():
            if intent in capability.supported_intents:
                matching_tools.append(name)
        return matching_tools

    def find_tools_for_query(self, query_features: Dict[str, Any]) -> List[str]:
        """Find tools that can handle query with given features."""
        matching_tools = []
        for name, capability in self._capabilities.items():
            # Check if all required features are present
            if all(
                feature in query_features
                for feature in capability.required_features
            ):
                matching_tools.append(name)
        return matching_tools

# Global registry instance
_registry = ToolRegistry()

def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry
```

### 3.3 Tool Registration at Startup

```python
# src/finagent/tools/__init__.py

from finagent.tools.registry import get_registry
from finagent.tools.vector_search import VectorSearchTool
from finagent.tools.metadata_search import MetadataSearchTool
from finagent.tools.list_documents import ListDocumentsTool
from finagent.tools.read_file import ReadFileTool
from finagent.tools.hybrid_search import HybridSearchTool
from finagent.tools.multi_entity_search import MultiEntitySearchTool

def initialize_tools():
    """Initialize and register all tools."""
    registry = get_registry()

    # Register all tools
    registry.register(VectorSearchTool())
    registry.register(MetadataSearchTool())
    registry.register(ListDocumentsTool())
    registry.register(ReadFileTool())
    registry.register(HybridSearchTool())
    registry.register(MultiEntitySearchTool())

    logger.info(f"Initialized {len(registry.get_all_capabilities())} tools")
```

## 4. Individual Tool Specifications

### 4.1 Vector Search Tool (Existing)

**Purpose:** Semantic similarity search using vector embeddings

```python
# src/finagent/tools/vector_search.py

from finagent.tools.base import BaseTool, ToolCapability, ToolInput, ToolOutput

class VectorSearchTool(BaseTool):
    """Semantic vector search using Chroma."""

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="vector_search",
            description="語義向量搜尋，適合一般性問題和關鍵字搜尋",
            supported_intents=[
                "general_search",
                "keyword_search",
                "semantic_search"
            ],
            required_features=["query"],
            execution_time_estimate="fast",  # ~2-5 seconds
            cost_estimate="low",  # Embedding API call only
            limitations=[
                "Cannot filter by date or metadata",
                "Top-k results only (not exhaustive)",
                "May miss exact filename matches"
            ]
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """Execute vector search."""
        try:
            # Get parameters
            top_k = tool_input.parameters.get("top_k", 10)
            relevance_threshold = tool_input.parameters.get("relevance_threshold", 0.8)

            # Execute search using existing retriever
            results = await self.retriever.retrieve(
                query=tool_input.query,
                top_k=top_k,
                relevance_threshold=relevance_threshold
            )

            return ToolOutput(
                success=True,
                results=[r.model_dump() for r in results],
                metadata={
                    "top_k": top_k,
                    "relevance_threshold": relevance_threshold,
                    "results_count": len(results)
                }
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                results=[],
                error=str(e)
            )

    def validate_input(self, tool_input: ToolInput) -> bool:
        """Validate input."""
        return bool(tool_input.query)
```

### 4.2 Metadata Search Tool (New)

**Purpose:** Filter documents by date, entity, jurisdiction, and other metadata

```python
# src/finagent/tools/metadata_search.py

class MetadataSearchTool(BaseTool):
    """Search documents by metadata filters."""

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="metadata_search",
            description="依據元資料篩選文件（日期、實體、裁罰類型等）",
            supported_intents=[
                "temporal",  # Latest, past records
                "entity_specific",
                "jurisdiction_filter",
                "penalty_type_filter"
            ],
            required_features=[],  # Optional filters
            execution_time_estimate="fast",  # Database query
            cost_estimate="low",
            limitations=[
                "Requires metadata to be indexed",
                "Cannot do semantic matching"
            ]
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """Execute metadata search."""
        try:
            # Build filter from parameters
            filters = {}

            # Entity filter
            if entity := tool_input.parameters.get("entity"):
                filters["entity"] = entity

            # Date range filter
            if date_from := tool_input.parameters.get("date_from"):
                filters["date_from"] = date_from
            if date_to := tool_input.parameters.get("date_to"):
                filters["date_to"] = date_to

            # Penalty type filter
            if penalty_type := tool_input.parameters.get("penalty_type"):
                filters["penalty_type"] = penalty_type

            # Jurisdiction filter
            if jurisdiction := tool_input.parameters.get("jurisdiction"):
                filters["jurisdiction"] = jurisdiction

            # Query metadata DB
            results = await self.metadata_db.search(filters)

            # For temporal queries, sort by date
            if "latest" in tool_input.query.lower() or "最近" in tool_input.query:
                results = sorted(results, key=lambda r: r.get("date", ""), reverse=True)

            return ToolOutput(
                success=True,
                results=results,
                metadata={
                    "filters": filters,
                    "results_count": len(results)
                }
            )
        except Exception as e:
            return ToolOutput(success=False, results=[], error=str(e))

    def validate_input(self, tool_input: ToolInput) -> bool:
        """Validate that at least one filter is provided."""
        return bool(tool_input.parameters)
```

### 4.3 List Documents Tool (New)

**Purpose:** List all documents matching criteria (exhaustive, not top-k)

```python
# src/finagent/tools/list_documents.py

class ListDocumentsTool(BaseTool):
    """List all documents matching criteria."""

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="list_documents",
            description="列出所有符合條件的文件（完整清單，非 top-k）",
            supported_intents=[
                "comprehensive_list",  # All records
                "inventory",
                "catalog"
            ],
            required_features=["entity"],  # At minimum, need entity or criteria
            execution_time_estimate="fast",
            cost_estimate="low",
            limitations=[
                "Returns metadata only (not full content)",
                "Requires subsequent deep reading for details"
            ]
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """List all matching documents."""
        try:
            entity = tool_input.parameters.get("entity")
            penalty_type = tool_input.parameters.get("penalty_type")

            # Query document DB for all matching files
            all_docs = await self.document_db.list_all(
                entity=entity,
                penalty_type=penalty_type
            )

            return ToolOutput(
                success=True,
                results=[
                    {
                        "filename": doc.filename,
                        "entity": doc.entity,
                        "penalty_type": doc.penalty_type,
                        "date": doc.date,
                        "jurisdiction": doc.jurisdiction,
                        "file_path": doc.file_path
                    }
                    for doc in all_docs
                ],
                metadata={
                    "total_count": len(all_docs),
                    "entity": entity,
                    "penalty_type": penalty_type
                }
            )
        except Exception as e:
            return ToolOutput(success=False, results=[], error=str(e))

    def validate_input(self, tool_input: ToolInput) -> bool:
        """Validate that entity is provided."""
        return "entity" in tool_input.parameters
```

### 4.4 Read File Tool (New)

**Purpose:** Load and read specific file by filename or path

```python
# src/finagent/tools/read_file.py

class ReadFileTool(BaseTool):
    """Read a specific file directly."""

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="read_file",
            description="直接讀取特定檔案（依檔名或路徑）",
            supported_intents=[
                "specific_file",  # Named file query
                "direct_access"
            ],
            required_features=["filename"],
            execution_time_estimate="fast",
            cost_estimate="low",
            limitations=[
                "Requires exact filename or path",
                "Cannot do semantic search"
            ]
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """Read file directly."""
        try:
            filename = tool_input.parameters.get("filename")

            # Find file path
            file_path = await self.document_db.get_file_path(filename)

            if not file_path:
                return ToolOutput(
                    success=False,
                    results=[],
                    error=f"File not found: {filename}"
                )

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Get metadata
            metadata = await self.document_db.get_metadata(filename)

            return ToolOutput(
                success=True,
                results=[{
                    "filename": filename,
                    "content": content,
                    "metadata": metadata
                }],
                metadata={
                    "file_path": file_path,
                    "content_length": len(content)
                }
            )
        except Exception as e:
            return ToolOutput(success=False, results=[], error=str(e))

    def validate_input(self, tool_input: ToolInput) -> bool:
        """Validate filename is provided."""
        return "filename" in tool_input.parameters
```

### 4.5 Hybrid Search Tool (New)

**Purpose:** Combine vector search with metadata filtering

```python
# src/finagent/tools/hybrid_search.py

class HybridSearchTool(BaseTool):
    """Hybrid search combining vector + metadata."""

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="hybrid_search",
            description="混合搜尋（語義向量 + 元資料篩選）",
            supported_intents=[
                "filtered_semantic_search",
                "temporal_with_keywords",
                "entity_with_semantic"
            ],
            required_features=["query"],  # Query + optional filters
            execution_time_estimate="medium",
            cost_estimate="medium",
            limitations=[
                "Slower than pure vector or metadata search",
                "Requires both vector index and metadata DB"
            ]
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """Execute hybrid search."""
        try:
            # Step 1: Metadata filtering
            metadata_filters = {
                k: v for k, v in tool_input.parameters.items()
                if k in ["entity", "date_from", "date_to", "penalty_type", "jurisdiction"]
            }

            if metadata_filters:
                # Get candidate documents from metadata
                candidates = await self.metadata_db.search(metadata_filters)
                candidate_ids = [c["id"] for c in candidates]
            else:
                candidate_ids = None

            # Step 2: Vector search within candidates
            vector_results = await self.retriever.retrieve(
                query=tool_input.query,
                top_k=tool_input.parameters.get("top_k", 10),
                relevance_threshold=tool_input.parameters.get("relevance_threshold", 0.8),
                filter_document_ids=candidate_ids  # Filter to candidates
            )

            return ToolOutput(
                success=True,
                results=[r.model_dump() for r in vector_results],
                metadata={
                    "metadata_filters": metadata_filters,
                    "candidate_count": len(candidate_ids) if candidate_ids else "all",
                    "results_count": len(vector_results)
                }
            )
        except Exception as e:
            return ToolOutput(success=False, results=[], error=str(e))

    def validate_input(self, tool_input: ToolInput) -> bool:
        """Validate query is provided."""
        return bool(tool_input.query)
```

### 4.6 Multi-Entity Search Tool (New)

**Purpose:** Parallel search for multiple entities (e.g., for comparison)

```python
# src/finagent/tools/multi_entity_search.py

class MultiEntitySearchTool(BaseTool):
    """Search multiple entities in parallel."""

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="multi_entity_search",
            description="並行搜尋多個實體（用於比較分析）",
            supported_intents=[
                "comparison",  # A vs B
                "multi_entity_analysis"
            ],
            required_features=["entities"],  # List of entities
            execution_time_estimate="medium",
            cost_estimate="high",  # Multiple searches
            limitations=[
                "Higher cost (multiple searches)",
                "Requires subsequent comparison logic"
            ]
        )

    async def execute(self, tool_input: ToolInput) -> ToolOutput:
        """Execute multi-entity search."""
        try:
            entities = tool_input.parameters.get("entities", [])

            if len(entities) < 2:
                return ToolOutput(
                    success=False,
                    results=[],
                    error="Multi-entity search requires at least 2 entities"
                )

            # Parallel search for each entity
            import asyncio

            async def search_entity(entity: str):
                """Search for single entity."""
                # Use hybrid search for each entity
                results = await self.hybrid_tool.execute(
                    ToolInput(
                        query=tool_input.query,
                        parameters={
                            "entity": entity,
                            "top_k": tool_input.parameters.get("top_k_per_entity", 5)
                        }
                    )
                )
                return {
                    "entity": entity,
                    "results": results.results
                }

            # Execute searches in parallel
            entity_results = await asyncio.gather(
                *[search_entity(entity) for entity in entities]
            )

            return ToolOutput(
                success=True,
                results=entity_results,
                metadata={
                    "entities": entities,
                    "entity_count": len(entities),
                    "total_results": sum(len(er["results"]) for er in entity_results)
                }
            )
        except Exception as e:
            return ToolOutput(success=False, results=[], error=str(e))

    def validate_input(self, tool_input: ToolInput) -> bool:
        """Validate entities list is provided."""
        entities = tool_input.parameters.get("entities", [])
        return isinstance(entities, list) and len(entities) >= 2
```

## 5. Enhanced Planning Agent

### 5.1 Query Analysis

The planning agent will use LLM to analyze the query and determine:

1. **Intent Classification**: What kind of query is this?
2. **Entity Extraction**: Which banks/entities are mentioned?
3. **Temporal Detection**: Is there a time constraint?
4. **Complexity Assessment**: Simple vs complex query

```python
# src/finagent/agents/query_analyzer.py

from pydantic import BaseModel, Field
from typing import List

class QueryIntent(str, Enum):
    """Query intent types."""
    GENERAL_SEARCH = "general_search"  # 一般搜尋
    TEMPORAL = "temporal"  # 時間相關（最近、過去）
    COMPREHENSIVE = "comprehensive"  # 完整清單（所有）
    SPECIFIC_FILE = "specific_file"  # 特定檔案
    COMPARISON = "comparison"  # 比較分析
    ENTITY_SPECIFIC = "entity_specific"  # 特定實體

class QueryAnalysis(BaseModel):
    """Structured query analysis result."""

    # Intent
    intent: QueryIntent = Field(..., description="Primary query intent")
    secondary_intents: List[QueryIntent] = Field(
        default_factory=list,
        description="Secondary intents"
    )

    # Entity extraction
    entities: List[str] = Field(
        default_factory=list,
        description="Extracted entity names (banks, institutions)"
    )

    # Temporal features
    has_temporal_constraint: bool = Field(False, description="Has time constraint")
    temporal_type: str | None = Field(
        None,
        description="Type of temporal constraint (latest, past, specific_date)"
    )
    date_range: dict | None = Field(None, description="Extracted date range")

    # File reference
    has_file_reference: bool = Field(False, description="References specific file")
    filename: str | None = Field(None, description="Extracted filename")

    # Query characteristics
    complexity: str = Field(..., description="simple | medium | complex")
    requires_exhaustive_search: bool = Field(
        False,
        description="Requires all results (not top-k)"
    )
    requires_multi_entity: bool = Field(
        False,
        description="Requires multi-entity orchestration"
    )

    # Extracted parameters
    extracted_parameters: dict = Field(
        default_factory=dict,
        description="Additional extracted parameters"
    )

class QueryAnalyzer:
    """Analyzes user query to determine intent and features."""

    ANALYSIS_PROMPT = """你是一個專業的查詢分析助手。分析使用者的查詢，辨識意圖和特徵。

查詢意圖類型：
- general_search: 一般關鍵字搜尋
- temporal: 時間相關（最近、過去、特定日期）
- comprehensive: 要求完整清單（所有、全部）
- specific_file: 指定特定檔案名稱
- comparison: 比較分析（A vs B、比較）
- entity_specific: 特定實體的資訊

使用者查詢：{query}

請以 JSON 格式回答，包含以下欄位：
- intent: 主要意圖
- secondary_intents: 次要意圖（陣列）
- entities: 提及的實體名稱（陣列）
- has_temporal_constraint: 是否有時間限制（布林值）
- temporal_type: 時間限制類型（latest/past/specific_date）
- date_range: 日期範圍（字典，包含 from 和 to）
- has_file_reference: 是否指定檔案（布林值）
- filename: 檔案名稱
- complexity: 複雜度（simple/medium/complex）
- requires_exhaustive_search: 是否需要完整搜尋（布林值）
- requires_multi_entity: 是否需要多實體搜尋（布林值）
- extracted_parameters: 其他參數（字典）

範例：
查詢：「玉山銀行最近一次的罰款紀錄」
分析：
{{
  "intent": "temporal",
  "secondary_intents": ["entity_specific"],
  "entities": ["玉山銀行"],
  "has_temporal_constraint": true,
  "temporal_type": "latest",
  "date_range": null,
  "has_file_reference": false,
  "filename": null,
  "complexity": "medium",
  "requires_exhaustive_search": false,
  "requires_multi_entity": false,
  "extracted_parameters": {{"penalty_type": "罰款"}}
}}

請分析上述查詢。
"""

    async def analyze(self, query: str) -> QueryAnalysis:
        """Analyze query and return structured analysis."""
        # Use LLM to analyze query
        response = await self.llm.ainvoke(
            self.ANALYSIS_PROMPT.format(query=query)
        )

        # Parse JSON response
        analysis_dict = json.loads(response.content)

        return QueryAnalysis(**analysis_dict)
```

### 5.2 Tool Selection

Based on query analysis, select appropriate tools:

```python
# src/finagent/agents/tool_selector.py

class ToolSelector:
    """Selects appropriate tools based on query analysis."""

    SELECTION_PROMPT = """你是一個工具選擇專家。根據查詢分析結果，選擇最適合的工具來執行任務。

可用工具：
{tool_descriptions}

查詢分析：
{query_analysis}

請選擇最適合的工具組合，並說明原因。以 JSON 格式回答：
{{
  "selected_tools": [
    {{
      "tool_name": "工具名稱",
      "reason": "選擇原因",
      "parameters": {{"參數": "值"}},
      "execution_order": 1
    }}
  ],
  "execution_strategy": "sequential | parallel",
  "estimated_total_time": "估計總時間（秒）"
}}
"""

    async def select_tools(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> List[dict]:
        """Select tools based on query analysis."""

        # Get all tool capabilities
        registry = get_registry()
        capabilities = registry.get_all_capabilities()

        # Format tool descriptions for LLM
        tool_descriptions = "\n\n".join([
            f"**{cap.name}**\n"
            f"描述：{cap.description}\n"
            f"支援意圖：{', '.join(cap.supported_intents)}\n"
            f"必要特徵：{', '.join(cap.required_features)}\n"
            f"執行時間：{cap.execution_time_estimate}\n"
            f"成本：{cap.cost_estimate}"
            for cap in capabilities.values()
        ])

        # Use LLM to select tools
        response = await self.llm.ainvoke(
            self.SELECTION_PROMPT.format(
                tool_descriptions=tool_descriptions,
                query_analysis=analysis.model_dump_json(indent=2)
            )
        )

        # Parse response
        selection = json.loads(response.content)

        return selection["selected_tools"]
```

### 5.3 Enhanced Planning Agent Implementation

```python
# src/finagent/agents/planning_agent.py (refactored)

class EnhancedPlanningAgent:
    """Dynamic planning agent with tool selection."""

    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.tool_selector = ToolSelector()

    async def plan(self, state: AgentState) -> AgentState:
        """
        Analyze query and create dynamic execution plan.

        Returns updated state with:
        - query_analysis: QueryAnalysis
        - selected_tools: List[dict]
        - execution_plan: ResearchPlan
        """
        query = state.query

        # Step 1: Analyze query
        analysis = await self.query_analyzer.analyze(query)

        # Step 2: Select tools
        selected_tools = await self.tool_selector.select_tools(query, analysis)

        # Step 3: Create execution plan
        execution_plan = ResearchPlan(
            analysis=analysis,
            tasks=[
                PlanTask(
                    id=i,
                    task=tool["reason"],
                    status="pending",
                    search_method=tool["tool_name"],
                    estimated_time=None  # From tool capability
                )
                for i, tool in enumerate(selected_tools, 1)
            ],
            max_results=self._determine_max_results(analysis),
            use_hard_search=analysis.requires_exhaustive_search,
            estimated_total_time=sum(
                self._estimate_tool_time(tool["tool_name"])
                for tool in selected_tools
            )
        )

        # Update state
        state.research_plan = execution_plan
        state.metadata["query_analysis"] = analysis.model_dump()
        state.metadata["selected_tools"] = selected_tools

        return state

    def _determine_max_results(self, analysis: QueryAnalysis) -> int:
        """Determine max results based on query intent."""
        if analysis.requires_exhaustive_search:
            return -1  # All results
        elif analysis.complexity == "complex":
            return 20
        elif analysis.complexity == "medium":
            return 10
        else:
            return 5

    def _estimate_tool_time(self, tool_name: str) -> int:
        """Estimate tool execution time in seconds."""
        estimates = {
            "vector_search": 3,
            "metadata_search": 2,
            "list_documents": 2,
            "read_file": 3,
            "hybrid_search": 5,
            "multi_entity_search": 10
        }
        return estimates.get(tool_name, 5)
```

## 6. Enhanced Action Agent

The action agent will execute tools selected by the planning agent:

```python
# src/finagent/agents/action_agent.py (refactored)

class EnhancedActionAgent:
    """Multi-tool executor with aggregation logic."""

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute selected tools and aggregate results.
        """
        selected_tools = state.metadata.get("selected_tools", [])

        if not selected_tools:
            # Fallback to legacy vector search
            return await self._legacy_vector_search(state)

        # Execute tools
        all_results = []

        for tool_spec in selected_tools:
            tool_name = tool_spec["tool_name"]
            parameters = tool_spec["parameters"]

            # Get tool from registry
            registry = get_registry()
            tool = registry.get_tool(tool_name)

            if not tool:
                logger.error(f"Tool not found: {tool_name}")
                continue

            # Execute tool
            tool_input = ToolInput(
                query=state.query,
                parameters=parameters
            )

            tool_output = await tool.execute(tool_input)

            if tool_output.success:
                all_results.extend(tool_output.results)
                logger.info(
                    f"Tool {tool_name} returned {len(tool_output.results)} results"
                )
            else:
                logger.error(f"Tool {tool_name} failed: {tool_output.error}")

        # Aggregate and deduplicate results
        aggregated_results = self._aggregate_results(all_results)

        # Convert to RetrievalResult format
        retrieval_results = [
            self._convert_to_retrieval_result(r)
            for r in aggregated_results
        ]

        # Update state
        state.retrieved_documents = retrieval_results
        state.metadata["tool_execution_count"] = len(selected_tools)
        state.metadata["total_results"] = len(retrieval_results)

        return state

    def _aggregate_results(self, results: List[dict]) -> List[dict]:
        """Aggregate and deduplicate results."""
        seen_ids = set()
        aggregated = []

        for result in results:
            result_id = result.get("id") or result.get("filename")

            if result_id not in seen_ids:
                seen_ids.add(result_id)
                aggregated.append(result)

        return aggregated

    def _convert_to_retrieval_result(self, result: dict) -> RetrievalResult:
        """Convert tool output to RetrievalResult format."""
        # Implementation depends on result structure
        # This ensures backward compatibility with existing validation/answer agents
        pass
```

## 7. Metadata Layer Implementation

### 7.1 Document Metadata Schema

```python
# src/finagent/models/document_metadata.py

class DocumentMetadata(BaseModel):
    """Extended document metadata for filtering."""

    # File information
    filename: str = Field(..., description="Document filename")
    file_path: str = Field(..., description="Full file path")

    # Entity information
    entity: str = Field(..., description="Bank or institution name")
    entity_normalized: str = Field(
        ...,
        description="Normalized entity name (e.g., '玉山銀行' → '玉山商業銀行股份有限公司')"
    )

    # Penalty information
    penalty_type: str = Field(..., description="Penalty type (洗錢防制, 內線交易, etc.)")
    penalty_amount: float | None = Field(None, description="Penalty amount in NTD")

    # Date information
    date: str = Field(..., description="Document date (ISO format)")
    year_roc: int | None = Field(None, description="ROC year (民國)")
    year_ad: int | None = Field(None, description="AD year")

    # Jurisdiction
    jurisdiction: str = Field(..., description="Regulatory body (金管會, 中央銀行, etc.)")

    # Document characteristics
    document_type: str = Field(..., description="Document type (裁罰書, 判決書, etc.)")
    case_number: str | None = Field(None, description="Case number (案號)")

    # Content metadata
    content_length: int = Field(..., description="Content length in characters")
    chunk_count: int = Field(..., description="Number of chunks indexed")

    # Timestamps
    indexed_at: str = Field(..., description="Indexing timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
```

### 7.2 Metadata Extraction During Indexing

```python
# src/finagent/document_processing/metadata_extractor.py

class MetadataExtractor:
    """Extract structured metadata from documents."""

    EXTRACTION_PROMPT = """你是文件元資料提取專家。從文件檔名和內容提取結構化元資料。

檔名：{filename}
內容摘要：{content_preview}

請提取以下資訊（JSON 格式）：
{{
  "entity": "實體名稱（銀行或機構）",
  "entity_normalized": "正式全名",
  "penalty_type": "裁罰類型（洗錢防制、內線交易等）",
  "penalty_amount": 罰款金額（數字，無則為 null）,
  "date": "文件日期（ISO 格式 YYYY-MM-DD）",
  "year_roc": 民國年（數字）,
  "year_ad": 西元年（數字）,
  "jurisdiction": "監管機構（金管會、中央銀行等）",
  "document_type": "文件類型（裁罰書、判決書等）",
  "case_number": "案號（無則為 null）"
}}
"""

    async def extract(
        self,
        filename: str,
        content: str
    ) -> DocumentMetadata:
        """Extract metadata from document."""

        # Get content preview (first 1000 chars)
        content_preview = content[:1000]

        # Use LLM to extract metadata
        response = await self.llm.ainvoke(
            self.EXTRACTION_PROMPT.format(
                filename=filename,
                content_preview=content_preview
            )
        )

        # Parse JSON
        metadata_dict = json.loads(response.content)

        # Complete metadata
        metadata = DocumentMetadata(
            filename=filename,
            file_path=self._get_file_path(filename),
            content_length=len(content),
            chunk_count=0,  # Will be updated after chunking
            indexed_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            **metadata_dict
        )

        return metadata
```

### 7.3 Metadata Database

```python
# src/finagent/database/metadata_db.py

class MetadataDB:
    """Database for document metadata."""

    def __init__(self, db_path: str = "./data/finagent.db"):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        """Initialize metadata table schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    entity_normalized TEXT NOT NULL,
                    penalty_type TEXT NOT NULL,
                    penalty_amount REAL,
                    date TEXT NOT NULL,
                    year_roc INTEGER,
                    year_ad INTEGER,
                    jurisdiction TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    case_number TEXT,
                    content_length INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    -- Indexes for fast querying
                    INDEX idx_entity ON document_metadata(entity),
                    INDEX idx_date ON document_metadata(date),
                    INDEX idx_penalty_type ON document_metadata(penalty_type),
                    INDEX idx_jurisdiction ON document_metadata(jurisdiction)
                )
            """)

    async def insert(self, metadata: DocumentMetadata):
        """Insert document metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO document_metadata
                (filename, file_path, entity, entity_normalized, penalty_type,
                 penalty_amount, date, year_roc, year_ad, jurisdiction,
                 document_type, case_number, content_length, chunk_count,
                 indexed_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.filename,
                metadata.file_path,
                metadata.entity,
                metadata.entity_normalized,
                metadata.penalty_type,
                metadata.penalty_amount,
                metadata.date,
                metadata.year_roc,
                metadata.year_ad,
                metadata.jurisdiction,
                metadata.document_type,
                metadata.case_number,
                metadata.content_length,
                metadata.chunk_count,
                metadata.indexed_at,
                metadata.updated_at
            ))

    async def search(self, filters: dict) -> List[dict]:
        """Search metadata with filters."""
        query = "SELECT * FROM document_metadata WHERE 1=1"
        params = []

        if entity := filters.get("entity"):
            query += " AND entity LIKE ?"
            params.append(f"%{entity}%")

        if date_from := filters.get("date_from"):
            query += " AND date >= ?"
            params.append(date_from)

        if date_to := filters.get("date_to"):
            query += " AND date <= ?"
            params.append(date_to)

        if penalty_type := filters.get("penalty_type"):
            query += " AND penalty_type LIKE ?"
            params.append(f"%{penalty_type}%")

        if jurisdiction := filters.get("jurisdiction"):
            query += " AND jurisdiction = ?"
            params.append(jurisdiction)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]

        return results

    async def list_all(
        self,
        entity: str | None = None,
        penalty_type: str | None = None
    ) -> List[dict]:
        """List all documents matching criteria."""
        filters = {}
        if entity:
            filters["entity"] = entity
        if penalty_type:
            filters["penalty_type"] = penalty_type

        return await self.search(filters)

    async def get_file_path(self, filename: str) -> str | None:
        """Get file path by filename."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT file_path FROM document_metadata WHERE filename = ?",
                (filename,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    async def get_metadata(self, filename: str) -> dict | None:
        """Get metadata by filename."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM document_metadata WHERE filename = ?",
                (filename,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
```

## 8. State Management Updates

Update `AgentState` to include tool-related information:

```python
# src/finagent/agents/state.py (updated)

class AgentState(BaseModel):
    """Extended agent state for tool-based workflow."""

    # ... existing fields ...

    # Tool-related fields
    query_analysis: dict | None = Field(
        None,
        description="Structured query analysis from QueryAnalyzer"
    )

    selected_tools: List[dict] = Field(
        default_factory=list,
        description="Tools selected by ToolSelector"
    )

    tool_outputs: List[dict] = Field(
        default_factory=list,
        description="Raw outputs from tool executions"
    )

    # Metadata
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (tool_execution_count, etc.)"
    )
```

## 9. LangGraph Workflow Updates

The workflow remains largely the same, but planning and action nodes are enhanced:

```python
# src/finagent/agents/workflow.py (updated)

def create_workflow() -> StateGraph:
    """Create enhanced LangGraph workflow."""

    workflow = StateGraph(AgentState)

    # Initialize agents
    planning_agent = EnhancedPlanningAgent()
    action_agent = EnhancedActionAgent()
    validation_agent = ValidationAgent()
    answer_agent = AnswerAgent()

    # Add nodes
    workflow.add_node("planning", planning_agent.plan)
    workflow.add_node("action", action_agent.execute)
    workflow.add_node("validation", validation_agent.validate)
    workflow.add_node("answer", answer_agent.synthesize)

    # Add edges (same as before)
    workflow.set_entry_point("planning")
    workflow.add_edge("planning", "action")
    workflow.add_edge("action", "validation")
    workflow.add_edge("validation", "answer")
    workflow.set_finish_point("answer")

    return workflow.compile()
```

## 10. Implementation Checkpoints

### Phase 1: Foundation (Week 1)

**Checkpoint 1.1: Tool Interface & Registry**
- [ ] Implement `BaseTool` interface ([src/finagent/tools/base.py](src/finagent/tools/base.py))
- [ ] Implement `ToolRegistry` ([src/finagent/tools/registry.py](src/finagent/tools/registry.py))
- [ ] Add unit tests for registry (register, get, find_tools_for_intent)
- [ ] Document tool interface contract

**Checkpoint 1.2: Metadata Layer**
- [ ] Define `DocumentMetadata` model ([src/finagent/models/document_metadata.py](src/finagent/models/document_metadata.py))
- [ ] Implement `MetadataDB` ([src/finagent/database/metadata_db.py](src/finagent/database/metadata_db.py))
- [ ] Implement `MetadataExtractor` ([src/finagent/document_processing/metadata_extractor.py](src/finagent/document_processing/metadata_extractor.py))
- [ ] Add metadata extraction to indexing pipeline
- [ ] Test metadata extraction with sample documents

**Verification Criteria:**
- ✅ Tool registry can register and retrieve tools
- ✅ Metadata can be extracted from existing documents
- ✅ Metadata DB can store and query metadata
- ✅ All unit tests pass

### Phase 2: Basic Tools (Week 2)

**Checkpoint 2.1: Migrate Existing Vector Search**
- [ ] Refactor existing retriever as `VectorSearchTool`
- [ ] Implement `get_capability()`, `execute()`, `validate_input()`
- [ ] Register tool in registry
- [ ] Add integration tests with existing Chroma index

**Checkpoint 2.2: Implement Metadata Search Tool**
- [ ] Implement `MetadataSearchTool` ([src/finagent/tools/metadata_search.py](src/finagent/tools/metadata_search.py))
- [ ] Add temporal filtering logic (latest, past)
- [ ] Add entity filtering
- [ ] Test with sample queries

**Checkpoint 2.3: Implement List Documents Tool**
- [ ] Implement `ListDocumentsTool` ([src/finagent/tools/list_documents.py](src/finagent/tools/list_documents.py))
- [ ] Test exhaustive listing
- [ ] Verify no top-k limitation

**Checkpoint 2.4: Implement Read File Tool**
- [ ] Implement `ReadFileTool` ([src/finagent/tools/read_file.py](src/finagent/tools/read_file.py))
- [ ] Add filename resolution logic
- [ ] Test direct file access

**Verification Criteria:**
- ✅ Query "玉山銀行最近一次的罰款紀錄" returns latest record
- ✅ Query "玉山銀行過去所有的裁罰紀錄" lists all matching files
- ✅ Query "「國泰世華銀行_內線交易_2021.txt」這個檔案的摘要" loads specific file
- ✅ All tool tests pass

### Phase 3: Advanced Tools (Week 3)

**Checkpoint 3.1: Implement Hybrid Search Tool**
- [ ] Implement `HybridSearchTool` ([src/finagent/tools/hybrid_search.py](src/finagent/tools/hybrid_search.py))
- [ ] Integrate metadata filtering with vector search
- [ ] Test combined queries

**Checkpoint 3.2: Implement Multi-Entity Search Tool**
- [ ] Implement `MultiEntitySearchTool` ([src/finagent/tools/multi_entity_search.py](src/finagent/tools/multi_entity_search.py))
- [ ] Add parallel execution logic
- [ ] Test comparison queries

**Verification Criteria:**
- ✅ Query "玉山銀行與國泰世華銀行的裁罰紀錄比較" returns both entities
- ✅ Hybrid search combines filters and semantic search correctly
- ✅ Multi-entity search executes in parallel

### Phase 4: Enhanced Planning Agent (Week 4)

**Checkpoint 4.1: Query Analyzer**
- [ ] Implement `QueryAnalyzer` ([src/finagent/agents/query_analyzer.py](src/finagent/agents/query_analyzer.py))
- [ ] Add LLM-based intent classification
- [ ] Test with all 4 problematic query types
- [ ] Validate JSON parsing

**Checkpoint 4.2: Tool Selector**
- [ ] Implement `ToolSelector` ([src/finagent/agents/tool_selector.py](src/finagent/agents/tool_selector.py))
- [ ] Add tool capability matching logic
- [ ] Test tool selection for different intents

**Checkpoint 4.3: Integrate with Planning Agent**
- [ ] Refactor `PlanningAgent` to use `QueryAnalyzer` and `ToolSelector`
- [ ] Update `ResearchPlan` to include selected tools
- [ ] Test end-to-end planning

**Verification Criteria:**
- ✅ Planning agent correctly analyzes all query types
- ✅ Planning agent selects appropriate tools
- ✅ Planning agent generates valid execution plan

### Phase 5: Enhanced Action Agent (Week 5)

**Checkpoint 5.1: Multi-Tool Executor**
- [ ] Refactor `ActionAgent` to execute multiple tools
- [ ] Add tool result aggregation logic
- [ ] Handle tool failures gracefully

**Checkpoint 5.2: Result Conversion**
- [ ] Convert tool outputs to `RetrievalResult` format
- [ ] Ensure backward compatibility with validation/answer agents
- [ ] Test with all tool types

**Verification Criteria:**
- ✅ Action agent can execute multiple tools sequentially
- ✅ Action agent aggregates results correctly
- ✅ Validation and answer agents work with new results

### Phase 6: Integration & Testing (Week 6)

**Checkpoint 6.1: End-to-End Testing**
- [ ] Test all 4 problematic queries end-to-end
- [ ] Verify correct results for each query type
- [ ] Test with real documents

**Checkpoint 6.2: Performance Testing**
- [ ] Measure query latency for each tool
- [ ] Optimize slow queries
- [ ] Verify cost estimates

**Checkpoint 6.3: Documentation**
- [ ] Update CLAUDE.md with new architecture
- [ ] Document tool development guide
- [ ] Add troubleshooting guide

**Verification Criteria:**
- ✅ All 4 query types return correct results
- ✅ Query latency < 60 seconds for complex queries
- ✅ Documentation complete and accurate

### Phase 7: Frontend Integration (Week 7)

**Checkpoint 7.1: Tool Execution Visualization**
- [ ] Add tool execution panel to query page
- [ ] Show which tools are being used
- [ ] Display tool-specific progress

**Checkpoint 7.2: Metadata Display**
- [ ] Show document metadata in results
- [ ] Add metadata filters to UI
- [ ] Test metadata-based queries from UI

**Verification Criteria:**
- ✅ Users can see which tools are being executed
- ✅ Metadata is visible in results
- ✅ UI supports metadata filtering

## 11. Migration Strategy

### Backward Compatibility

1. **Fallback to Legacy Behavior**: If no tools are selected, fall back to vector search only
2. **Existing Tests**: All existing tests should continue to pass
3. **Gradual Rollout**: Enable new tools incrementally, starting with metadata search

### Rollout Plan

1. **Phase 1-2**: Deploy foundation and basic tools to staging
2. **Phase 3-4**: Deploy advanced tools and planning agent to staging
3. **Phase 5**: Deploy action agent to staging
4. **Phase 6**: Full end-to-end testing in staging
5. **Phase 7**: Deploy to production with feature flag
6. **Phase 8**: Monitor and optimize based on real usage

## 12. Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| LLM-based tool selection is unreliable | Add rule-based fallback logic |
| Metadata extraction is inaccurate | Manual review of extracted metadata |
| Tool execution is too slow | Add caching and parallel execution |
| Tool results are incompatible | Strict output format validation |

### User Experience Risks

| Risk | Mitigation |
|------|------------|
| Users confused by tool selection | Add explanatory UI messages |
| Query latency increases | Show progress indicators and estimated time |
| Results quality decreases | Add confidence scoring and quality metrics |

## 13. Success Metrics

### Functional Metrics
- ✅ All 4 query types return correct results
- ✅ Tool selection accuracy > 90%
- ✅ Metadata extraction accuracy > 95%

### Performance Metrics
- Query latency < 60 seconds (95th percentile)
- Tool execution time meets estimates (±20%)
- Cost per query < $0.01 USD

### Quality Metrics
- User satisfaction > 4/5
- Result relevance > 90%
- Citation accuracy > 95%

## 14. Future Enhancements

### Post-Launch Improvements
1. **Adaptive Tool Selection**: Learn from user feedback to improve tool selection
2. **Custom Tool Creation**: Allow users to define custom tools
3. **Tool Chaining**: Support complex multi-step tool workflows
4. **Cross-Document Analysis**: Aggregate insights across multiple documents
5. **Temporal Trend Analysis**: Analyze penalty trends over time

### Advanced Features
1. **Graph-Based Entity Resolution**: Build entity relationship graph
2. **Predictive Analytics**: Predict penalty likelihood based on historical data
3. **Natural Language Queries**: Support more conversational query styles
4. **Multi-Modal Support**: Add PDF, DOCX, HTML document support

## 15. Appendix

### A. Example Query Flows

#### Example 1: Temporal Query

**Query:** "玉山銀行最近一次的罰款紀錄"

**Flow:**
1. **Query Analyzer**:
   - Intent: `temporal`
   - Entity: `["玉山銀行"]`
   - Temporal type: `latest`

2. **Tool Selector**:
   - Selected: `metadata_search` (filter by entity + sort by date DESC)

3. **Action Agent**:
   - Execute metadata_search with `entity="玉山銀行"`, `limit=1`, `sort="date DESC"`
   - Return latest record

4. **Answer Agent**:
   - Synthesize answer with latest record details

#### Example 2: Comprehensive Query

**Query:** "玉山銀行過去所有的裁罰紀錄"

**Flow:**
1. **Query Analyzer**:
   - Intent: `comprehensive`
   - Entity: `["玉山銀行"]`
   - Requires exhaustive: `true`

2. **Tool Selector**:
   - Selected: `list_documents` (list all) + `vector_search` (get details)

3. **Action Agent**:
   - Execute list_documents with `entity="玉山銀行"`
   - Execute vector_search for top details
   - Aggregate results

4. **Answer Agent**:
   - Provide comprehensive summary with all records

#### Example 3: Specific File Query

**Query:** "「國泰世華銀行_內線交易_2021.txt」這個檔案的摘要"

**Flow:**
1. **Query Analyzer**:
   - Intent: `specific_file`
   - Filename: `"國泰世華銀行_內線交易_2021.txt"`

2. **Tool Selector**:
   - Selected: `read_file`

3. **Action Agent**:
   - Execute read_file with `filename="國泰世華銀行_內線交易_2021.txt"`
   - Load full file content

4. **Answer Agent**:
   - Generate summary from full content

#### Example 4: Comparison Query

**Query:** "玉山銀行與國泰世華銀行的裁罰紀錄比較"

**Flow:**
1. **Query Analyzer**:
   - Intent: `comparison`
   - Entities: `["玉山銀行", "國泰世華銀行"]`
   - Requires multi-entity: `true`

2. **Tool Selector**:
   - Selected: `multi_entity_search`

3. **Action Agent**:
   - Execute multi_entity_search for both entities in parallel
   - Aggregate results by entity

4. **Answer Agent**:
   - Generate comparative analysis

### B. File Structure

```
src/finagent/
├── tools/
│   ├── __init__.py (initialize_tools)
│   ├── base.py (BaseTool, ToolCapability, ToolInput, ToolOutput)
│   ├── registry.py (ToolRegistry)
│   ├── vector_search.py (VectorSearchTool)
│   ├── metadata_search.py (MetadataSearchTool)
│   ├── list_documents.py (ListDocumentsTool)
│   ├── read_file.py (ReadFileTool)
│   ├── hybrid_search.py (HybridSearchTool)
│   └── multi_entity_search.py (MultiEntitySearchTool)
├── agents/
│   ├── query_analyzer.py (QueryAnalyzer, QueryAnalysis)
│   ├── tool_selector.py (ToolSelector)
│   ├── planning_agent.py (EnhancedPlanningAgent)
│   ├── action_agent.py (EnhancedActionAgent)
│   └── ...
├── models/
│   └── document_metadata.py (DocumentMetadata)
├── database/
│   └── metadata_db.py (MetadataDB)
└── document_processing/
    └── metadata_extractor.py (MetadataExtractor)
```

### C. Dependencies

**New Python Dependencies:**
- None (all functionality uses existing dependencies)

**Database Schema Changes:**
- Add `document_metadata` table to `finagent.db`

### D. Configuration Changes

**New .env Variables:**
```bash
# Metadata extraction (optional, uses main LLM if not specified)
METADATA_EXTRACTION_MODEL=gpt-4o-mini  # Faster/cheaper model for metadata
METADATA_EXTRACTION_ENABLED=true  # Enable LLM metadata extraction

# Tool execution
TOOL_EXECUTION_TIMEOUT_SECONDS=30  # Max time per tool
MAX_PARALLEL_TOOLS=3  # Max tools to run in parallel
```

---

**End of Architecture Document**

This comprehensive design provides a clear roadmap for implementing the dynamic planning agent and tool registry system. Each checkpoint is well-defined with verification criteria, ensuring systematic progress and quality control throughout the implementation.
