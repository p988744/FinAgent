# LangGraph Multi-Agent Implementation

## Overview

This document describes the LangGraph-based multi-agent workflow implementation for the FinAgent legal research system.

## Architecture

### Workflow Pipeline

```
START → Planning Agent → Action Agent → Validation Agent → Answer Agent → END
```

### Components

#### 1. Agent State Schema (`state.py`)

Defines the state passed through the workflow:

```python
class AgentState(TypedDict):
    query: Query                              # Input query
    plan: Dict[str, Any]                      # Research plan
    research_tasks: List[str]                 # Decomposed tasks
    retrieved_chunks: List[RetrievedChunk]   # RAG results
    citations: List[LegalCitation]            # Extracted citations
    validation_passed: bool                   # Validation result
    validation_issues: List[str]              # Issues found
    answer: LegalAnswer                       # Final answer
    processing_steps: List[str]               # Execution log
    errors: List[str]                         # Error log
```

#### 2. Planning Agent (`planning_agent.py`)

**Purpose**: Decomposes complex legal queries into structured research plans

**LLM**: GPT-4o-mini (temperature: 0.2)

**Capabilities**:
- Query type identification (裁罰查詢, 判例查詢, 法規查詢)
- Jurisdiction identification (金管會, 中央銀行, etc.)
- Entity extraction (institution, violation type, time range)
- Task decomposition

**Example Output**:
```json
{
  "query_type": "裁罰查詢",
  "jurisdiction": ["金管會-銀行局"],
  "entities": {
    "institution": "玉山銀行",
    "violation_type": "洗錢防制",
    "time_range": "2020"
  },
  "research_tasks": [
    "檢索玉山銀行2020年洗錢防制相關裁罰文件",
    "提取裁罰金額、違規事實、法律依據",
    "尋找類似案例進行比較分析"
  ]
}
```

#### 3. Action Agent (`action_agent.py`)

**Purpose**: Executes research tasks using RAG and other tools

**Current Capabilities**:
- Semantic search via Chroma vector database
- **Relevance filtering** with configurable threshold (default: 0.8)
- Citation extraction from document metadata

**Relevance Threshold**:
- Distance metric: Lower is better (0 = perfect match, 2 = completely different)
- Default threshold: 0.8 (filters out irrelevant results)
- Handles boundary cases (e.g., "酸辣湯怎麼做" → no results)

**Future Capabilities**:
- Web search for recent cases
- Database queries for structured data
- API calls to regulatory bodies

**Performance**:
- Average retrieval time: ~0.5s for 494 documents
- Filtering overhead: <0.1s

#### 4. Validation Agent (`validation_agent.py`)

**Purpose**: Ensures citation integrity and fact coverage

**Validation Checks**:
1. Minimum citation count (default: 1)
2. Metadata completeness for all chunks
3. Citation format compliance (Taiwan legal format)
4. Source authority verification

**Output**:
- `validation_passed`: Boolean flag
- `validation_issues`: List of specific issues found

#### 5. Answer Agent (`answer_agent.py`)

**Purpose**: Synthesizes final legal research answer using LLM

**LLM**: GPT-4o-mini (temperature: 0.3)

**Key Features**:
- **Intelligent Summarization**: Context-aware executive summaries
- **Citation Management**: Proper legal citation format ([引用1], [引用1、2])
- **Confidence Scoring**: Based on retrieval quality and quantity
- **Formal Writing Style**: Taiwan legal document standards

**System Prompt Highlights**:
```
核心原則：
1. 精確引用：每個事實陳述必須附上引用編號
2. 客觀中立：使用正式法律用語，避免主觀判斷
3. 結構完整：包含執行摘要、關鍵發現、詳細分析
4. 繁體中文：全部使用台灣繁體中文
```

**Output Structure**:
- Executive Summary (執行摘要): 100-150 characters
- Key Findings (關鍵發現): 3-5 points with citations
- Detailed Analysis (詳細分析): Comprehensive with embedded references
- Confidence Score: HIGH/MEDIUM/LOW with explanation
- Limitations: Known constraints

#### 6. Workflow Orchestrator (`workflow.py`)

**Purpose**: Coordinates agent execution using LangGraph

**Implementation**:
```python
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planning", planning_agent.plan)
workflow.add_node("action", action_agent.execute)
workflow.add_node("validation", validation_agent.validate)
workflow.add_node("answer", answer_agent.synthesize)

# Define edges
workflow.add_edge(START, "planning")
workflow.add_edge("planning", "action")
workflow.add_edge("action", "validation")
workflow.add_edge("validation", "answer")
workflow.add_edge("answer", END)

graph = workflow.compile()
```

**Execution**:
- Linear workflow (MVP)
- Future: Conditional branching based on validation results
- Future: Iterative refinement loops

## Integration

### Orchestrator Integration

The `AgentOrchestrator` class seamlessly integrates the LangGraph workflow:

```python
class AgentOrchestrator:
    def __init__(self):
        self.retriever = DocumentRetriever(...)
        self.workflow = LegalResearchWorkflow(retriever=self.retriever)

    async def process_query(self, query: Query) -> LegalAnswer:
        initial_state = {
            "query": query,
            "processing_steps": [],
            "errors": [],
            # ... other fields
        }

        final_state = self.workflow.run(initial_state)
        return final_state["answer"]
```

### CLI Integration

The CLI query command was updated to use the orchestrator directly:

```python
def execute_query(query_text: str, max_results: int = 5) -> LegalAnswer:
    orchestrator = get_orchestrator()
    answer = asyncio.run(orchestrator.process_query(query))
    return answer
```

## Performance Metrics

### Test Query: "玉山銀行洗錢防制裁罰"

**Execution Timeline**:
1. Planning Agent: ~4.2s (LLM call)
2. Action Agent: ~0.5s (RAG retrieval from 494 docs)
3. Validation Agent: <0.1s (rules-based)
4. Answer Agent: ~34.7s (LLM synthesis)

**Total Processing Time**: ~40 seconds

**Results**:
- Retrieved: 3 relevant chunks
- Citations: 2 source documents
- Confidence: HIGH (85%)
- Output: 1,500+ character comprehensive analysis

### Cost Estimation (per query)

Based on OpenAI pricing (as of 2025-01):

**Input Tokens**:
- Planning Agent: ~1,500 tokens
- Answer Agent: ~3,000 tokens (context + instructions)
- **Total**: ~4,500 tokens

**Output Tokens**:
- Planning Agent: ~300 tokens
- Answer Agent: ~1,000 tokens
- **Total**: ~1,300 tokens

**Cost per Query** (GPT-4o-mini):
- Input: 4,500 tokens × $0.15/1M = $0.000675
- Output: 1,300 tokens × $0.60/1M = $0.00078
- **Total**: ~$0.0015 USD per query (~NT$0.05)

**Monthly Cost** (1,000 queries/month):
- LLM: ~$1.50 USD (~NT$45)
- Embeddings: ~$0.50 USD (~NT$15)
- **Total**: ~$2 USD (~NT$60)

## Comparison: Before vs After

### Before (Template-Based)

```python
# Template generation
executive_summary = f"根據相關文件，找到 {len(chunks)} 筆與裁罰相關的資訊。"

# Simple extraction
first_sentence = chunk.text.split("。")[0] + "。"
key_findings.append(f"{first_sentence} [引用{i}]")
```

**Limitations**:
- Fixed templates
- No intelligent summarization
- Limited context understanding
- Generic responses

### After (LLM-Powered)

```python
# LLM synthesis with prompt engineering
response = chain.invoke({
    "query": query.text,
    "context": formatted_context,
    "citations": formatted_citations
})

# Structured parsing
answer = parse_response(response, chunks, citations)
```

**Benefits**:
- Context-aware summaries
- Natural language synthesis
- Query-specific analysis
- Professional legal writing style
- Proper citation integration

## Testing

### Test Script: `test_langgraph.py`

```bash
cd backend
uv run python test_langgraph.py
```

**Expected Output**:
```
================================================================================
RESULTS
================================================================================

執行摘要:
本報告針對玉山銀行因違反洗錢防制法及銀行法相關規定而遭金融監督管理委員會
裁罰的事件進行分析...

關鍵發現:
  1. 玉山銀行於民國109年9月15日被處以新臺幣貳億伍仟萬元罰鍰... [引用1]
  2. 該銀行在高風險客戶的加強審查措施中，有36.6%的案件未依規定執行 [引用1]
  ...

信心分數: 高
處理時間: ~40000ms
```

### CLI Testing

```bash
cd backend
uv run finagent query "國泰世華銀行內線交易" --max-results 3
```

## Future Enhancements

### 1. Conditional Workflow (P1)

Add conditional branching based on validation results:

```python
def should_retry(state: AgentState) -> str:
    if state["validation_passed"]:
        return "answer"
    elif len(state["errors"]) < 3:
        return "action"  # Retry retrieval
    else:
        return "answer"  # Give up

workflow.add_conditional_edges(
    "validation",
    should_retry,
    {
        "answer": "answer",
        "action": "action"
    }
)
```

### 2. Iterative Refinement (P2)

Add feedback loop for answer improvement:

```python
workflow.add_node("review", review_agent.review)
workflow.add_edge("answer", "review")

def should_refine(state: AgentState) -> str:
    if state["review_score"] >= 0.8:
        return END
    elif state["refinement_count"] < 2:
        return "answer"  # Retry synthesis
    else:
        return END
```

### 3. Parallel Tool Execution (P2)

Execute multiple tools simultaneously:

```python
workflow.add_node("web_search", web_search_agent.search)
workflow.add_node("rag_search", rag_agent.retrieve)

# Fan-out
workflow.add_edge("planning", "web_search")
workflow.add_edge("planning", "rag_search")

# Fan-in
workflow.add_node("merge", merge_results)
workflow.add_edge("web_search", "merge")
workflow.add_edge("rag_search", "merge")
```

### 4. Human-in-the-Loop (P3)

Add checkpoints for user review:

```python
from langgraph.checkpoint import MemorySaver

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# Execute with interrupts
config = {"configurable": {"thread_id": "1"}}
for event in graph.stream(initial_state, config):
    if "human_review" in event:
        # Pause and wait for user input
        user_feedback = await get_user_feedback()
        # Resume with feedback
        graph.invoke({"feedback": user_feedback}, config)
```

### 5. Advanced Planning (P2)

Implement JSON-structured planning:

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser(pydantic_object=ResearchPlan)
chain = prompt | llm | parser

plan = chain.invoke({"query": query.text})
# plan.query_type, plan.jurisdiction, plan.entities, etc.
```

## Troubleshooting

### Issue: "Connection refused" Error

**Cause**: CLI trying to connect to HTTP server instead of using orchestrator directly

**Fix**: Update `query.py` to use orchestrator:
```python
from finagent.agents.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
answer = asyncio.run(orchestrator.process_query(query))
```

### Issue: Planning Agent Prompt Error

**Cause**: JSON in prompt not escaped (curly braces)

**Fix**: Double-escape curly braces:
```python
"以JSON格式輸出研究計劃：\n\n```json\n{{\n  \"query_type\": ...\n}}\n```"
```

### Issue: Irrelevant Results for Off-Topic Queries

**Symptom**: Query "酸辣湯怎麼做" returns legal documents

**Cause**: No relevance threshold, vector DB returns "closest" results even if irrelevant

**Fix**: Add relevance filtering in Action Agent:
```python
# Filter by relevance threshold (default: 0.8)
retrieved_chunks = [
    chunk for chunk in all_chunks
    if chunk.score <= self.relevance_threshold
]
```

**Result**: Off-topic queries now correctly return "no relevant documents found"

### Issue: Slow Response Time

**Optimization Options**:
1. Use faster model: `gpt-4o-mini` → `gpt-3.5-turbo`
2. Reduce context size: Limit chunks to top 3 instead of 5
3. Parallel LLM calls: Plan + Answer in parallel (if independent)
4. Caching: Cache embeddings and LLM responses
5. Adjust relevance threshold: Lower threshold (e.g., 0.6) for stricter filtering

## Dependencies

```toml
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
langchain-core>=0.3.0
langgraph>=0.2.0
openai>=1.10.0
```

## References

- [LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangChain Prompt Engineering](https://docs.langchain.com/oss/python/langchain/prompts)
- [OpenAI API Pricing](https://openai.com/pricing)
- [Taiwan Legal Citation Standards](https://law.moj.gov.tw/)

## Changelog

### v0.0.2 (2025-01-12)
- ✅ Added LangGraph multi-agent workflow
- ✅ Implemented Planning, Action, Validation, Answer agents
- ✅ LLM-powered answer synthesis
- ✅ Integrated with CLI
- ✅ Comprehensive testing

### v0.0.1-alpha (2025-01-12)
- Initial CLI and RAG implementation
- Template-based answer generation
