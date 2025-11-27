# Note-Taking Agent Pattern for Research Workflows

**Maintaining Context Across Multi-Step Research**

**Last Updated**: 2025-01-20
**Pattern**: Memory Accumulator with State Reducers
**Use Case**: Legal research workflows with extensive document processing

---

## Problem Statement

### The Challenge

In legal research workflows, agents process massive amounts of context:
- Read 50-200 page documents
- Extract key findings from multiple sources
- Make connections across different document sections
- Build upon previous discoveries

**Without note-taking**: Each step processes information in isolation, losing context between steps.

**With note-taking**: A dedicated note agent maintains a running summary of discoveries, insights, and key facts throughout the workflow.

---

## Solution: Note-Taking Agent Pattern

### Core Concept

Add a **notes** field to your state that accumulates insights throughout the workflow using LangGraph's **state reducer pattern**.

### Key Benefits

1. **Persistent Context**: Insights from step 1 available in step 5
2. **Incremental Learning**: Agent builds knowledge progressively
3. **Better Synthesis**: Final answer incorporates all discoveries
4. **Debugging**: Clear trace of what agent learned when
5. **Memory Efficient**: Summarized notes vs. raw document chunks

---

## Implementation Pattern

### Pattern 1: Simple Note Accumulator

**Use Case**: Basic note-taking across workflow steps

```python
from typing import TypedDict, Annotated, List
from operator import add

class ResearchState(TypedDict):
    """State with accumulated notes."""
    input: str
    documents: List[dict]
    notes: Annotated[List[str], add]  # Accumulates notes
    response: str

# Notes automatically accumulate with each update
def step1(state: ResearchState) -> dict:
    return {"notes": ["Found 3 relevant penalty cases"]}

def step2(state: ResearchState) -> dict:
    # Previous note still in state
    # state["notes"] = ["Found 3 relevant penalty cases"]
    return {"notes": ["All cases involve AML violations"]}

# After both steps:
# state["notes"] = [
#   "Found 3 relevant penalty cases",
#   "All cases involve AML violations"
# ]
```

### Pattern 2: Structured Note Agent

**Use Case**: Dedicated agent for note-taking with LLM

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class Note(BaseModel):
    """Structured note with metadata."""
    step: str = Field(description="Workflow step name")
    insight: str = Field(description="Key insight or finding")
    confidence: str = Field(description="high/medium/low")
    citations: List[str] = Field(description="Source citations")

class ResearchState(TypedDict):
    input: str
    current_step: str
    documents: List[dict]
    notes: Annotated[List[Note], add]  # Structured notes
    response: str

class NoteAgent:
    """Agent that takes notes during workflow execution."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a research assistant taking notes during legal research.\n"
             "Review the current findings and extract key insights.\n"
             "Previous notes: {previous_notes}\n"
             "Current step: {step}\n"
             "Documents processed: {documents}\n\n"
             "Create a concise note capturing the most important finding."
            ),
            ("user", "What is the key insight from this step?")
        ])

    async def take_note(self, state: ResearchState) -> dict:
        """Generate a note for the current step."""

        # Format previous notes for context
        prev_notes = "\n".join([
            f"- {note.step}: {note.insight}"
            for note in state.get("notes", [])
        ])

        # Generate note using LLM
        response = await self.llm.ainvoke(
            self.prompt.format(
                previous_notes=prev_notes,
                step=state["current_step"],
                documents=state.get("documents", [])
            )
        )

        # Extract structured note
        note = Note(
            step=state["current_step"],
            insight=response.content,
            confidence="high",
            citations=[doc["source"] for doc in state.get("documents", [])]
        )

        return {"notes": [note]}
```

### Pattern 3: Hot Path (Real-Time Note-Taking)

**Use Case**: Notes taken during each workflow step

```python
from langgraph.graph import StateGraph, START, END

class ResearchWorkflow:
    """Workflow with integrated note-taking."""

    def __init__(self):
        self.note_agent = NoteAgent()

        # Build graph
        workflow = StateGraph(ResearchState)

        # Add workflow nodes
        workflow.add_node("plan", self.plan)
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("take_note_retrieve", self.note_agent.take_note)
        workflow.add_node("analyze", self.analyze)
        workflow.add_node("take_note_analyze", self.note_agent.take_note)
        workflow.add_node("synthesize", self.synthesize)

        # Flow: action -> note -> next action
        workflow.add_edge(START, "plan")
        workflow.add_edge("plan", "retrieve")
        workflow.add_edge("retrieve", "take_note_retrieve")
        workflow.add_edge("take_note_retrieve", "analyze")
        workflow.add_edge("analyze", "take_note_analyze")
        workflow.add_edge("take_note_analyze", "synthesize")
        workflow.add_edge("synthesize", END)

        self.graph = workflow.compile()

    async def plan(self, state: ResearchState) -> dict:
        return {"current_step": "planning"}

    async def retrieve(self, state: ResearchState) -> dict:
        # Retrieve documents
        docs = [...]  # RAG retrieval
        return {
            "current_step": "retrieval",
            "documents": docs
        }

    async def analyze(self, state: ResearchState) -> dict:
        # Analyze with access to previous notes
        notes_context = "\n".join([n.insight for n in state["notes"]])

        # Use notes in analysis prompt
        analysis = f"Based on previous findings:\n{notes_context}\n..."

        return {"current_step": "analysis"}

    async def synthesize(self, state: ResearchState) -> dict:
        """Final synthesis using all accumulated notes."""

        # Format all notes for final answer
        notes_summary = "\n\n".join([
            f"**{note.step}**: {note.insight} (Confidence: {note.confidence})"
            for note in state["notes"]
        ])

        # Generate answer incorporating all notes
        response = f"""
        ## Research Summary

        {notes_summary}

        ## Final Answer

        [Synthesis based on accumulated insights...]
        """

        return {"response": response}
```

### Pattern 4: Background Note Consolidation

**Use Case**: Periodic summarization to prevent note overflow

```python
from langchain_core.messages import trim_messages

class ConsolidatingNoteAgent(NoteAgent):
    """Note agent with consolidation to prevent context overflow."""

    async def consolidate_notes(self, state: ResearchState) -> dict:
        """Consolidate old notes into summary when threshold reached."""

        notes = state.get("notes", [])

        # Trigger consolidation if too many notes
        if len(notes) > 10:
            # Keep last 3 notes as-is
            recent_notes = notes[-3:]

            # Summarize older notes
            old_notes = notes[:-3]
            old_notes_text = "\n".join([n.insight for n in old_notes])

            summary_prompt = f"""
            Consolidate these research notes into 2-3 key findings:

            {old_notes_text}

            Return only the consolidated insights.
            """

            summary = await self.llm.ainvoke(summary_prompt)

            # Create consolidated note
            consolidated = Note(
                step="consolidation",
                insight=summary.content,
                confidence="high",
                citations=[]
            )

            # Replace old notes with consolidated + recent
            return {"notes": [consolidated] + recent_notes}

        # No consolidation needed
        return {}
```

---

## Implementation for FinAgent v1.1

### Current State

**Plan-and-Execute workflow** processes documents but doesn't maintain running notes.

**Problem**:
- Executor processes tasks independently
- Replanner sees task results but not synthesized insights
- Final answer may miss connections across tasks

### Recommended Implementation

#### Step 1: Add Notes to State

**File**: `src/finagent/agents/plan_execute/models.py`

```python
from typing import Annotated
from operator import add

class Note(BaseModel):
    """Research note with metadata."""
    task_id: int
    insight: str = Field(description="Key finding or insight")
    citations: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class PlanExecuteState(TypedDict):
    input: str
    plan: Plan
    past_steps: Annotated[List[tuple], add]
    notes: Annotated[List[Note], add]  # ⭐ NEW: Accumulated notes
    response: Optional[str]
```

#### Step 2: Create Note Agent

**File**: `src/finagent/agents/plan_execute/note_agent.py`

```python
"""Note-taking agent for Plan-and-Execute workflow."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from finagent.agents.plan_execute.models import Note, PlanExecuteState
from finagent.config import settings

class NoteAgent:
    """Takes notes after each task execution."""

    def __init__(self):
        base_url = settings.effective_llm_base_url
        if base_url:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                base_url=base_url,
                temperature=0,
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.effective_llm_api_key,
                temperature=0,
            )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "你是金融法律研究助理，負責記錄研究過程中的重要發現。\n"
             "根據任務執行結果，提取最關鍵的洞察。\n\n"
             "先前筆記：\n{previous_notes}\n\n"
             "當前任務：{task_description}\n"
             "任務結果：{task_result}\n\n"
             "用繁體中文，以一句話總結此任務的核心發現。"
            ),
            ("user", "這個任務的關鍵發現是什麼？")
        ])

    async def take_note(self, state: PlanExecuteState) -> dict:
        """Take note after task execution."""

        # Get last executed task
        if not state["past_steps"]:
            return {}

        last_task, result = state["past_steps"][-1]

        # Format previous notes
        prev_notes = "\n".join([
            f"- 任務 {note.task_id}: {note.insight}"
            for note in state.get("notes", [])
        ]) if state.get("notes") else "尚無先前筆記"

        # Generate note
        response = await self.llm.ainvoke(
            self.prompt.format(
                previous_notes=prev_notes,
                task_description=last_task.get("description", ""),
                task_result=str(result)[:500]  # Truncate for token limit
            )
        )

        # Extract citations from result
        citations = self._extract_citations(result)

        note = Note(
            task_id=last_task.get("id", 0),
            insight=response.content,
            citations=citations
        )

        return {"notes": [note]}

    def _extract_citations(self, result: str) -> List[str]:
        """Extract citation sources from task result."""
        # Simple extraction - look for [Document N] or source: patterns
        import re
        sources = re.findall(r'來源: ([^\n]+)', str(result))
        return sources[:3]  # Keep top 3
```

#### Step 3: Integrate into Workflow

**File**: `src/finagent/agents/plan_execute/graph.py`

```python
from finagent.agents.plan_execute.note_agent import NoteAgent

class PlanExecuteWorkflow:
    def __init__(self):
        # Initialize agents
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(...)
        self.replanner = ReplannerAgent()
        self.note_agent = NoteAgent()  # ⭐ NEW

        # Build workflow
        workflow = StateGraph(PlanExecuteState)

        workflow.add_node("planner", self.planner.plan)
        workflow.add_node("executor", self.executor.execute)
        workflow.add_node("take_note", self.note_agent.take_note)  # ⭐ NEW
        workflow.add_node("replanner", self.replanner.replan)

        # Update flow: executor -> take_note -> replanner
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "take_note")  # ⭐ NEW
        workflow.add_edge("take_note", "replanner")  # ⭐ NEW

        # Conditional routing from replanner
        def should_end(state: PlanExecuteState):
            if state.get("response"):
                return END
            else:
                return "executor"

        workflow.add_conditional_edges(
            "replanner",
            should_end,
            {END: END, "executor": "executor"}
        )

        self.graph = workflow.compile()
```

#### Step 4: Use Notes in Replanner

**File**: `src/finagent/agents/plan_execute/replanner.py`

```python
async def replan(self, state: PlanExecuteState) -> dict:
    """Replan with access to accumulated notes."""

    # Format past steps
    past_steps_str = ""
    for task_dict, result in state["past_steps"]:
        truncated_result = str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
        past_steps_str += f"任務: {task_dict['description']}\n結果: {truncated_result}\n---\n"

    # ⭐ NEW: Format accumulated notes
    notes_summary = "\n".join([
        f"{i+1}. 任務 {note.task_id}: {note.insight}"
        for i, note in enumerate(state.get("notes", []))
    ]) if state.get("notes") else "尚無筆記"

    # ⭐ UPDATED PROMPT: Include notes
    raw_output = await self.chain.ainvoke({
        "input": state["input"],
        "plan": state["plan"],
        "past_steps": past_steps_str,
        "notes": notes_summary  # ⭐ NEW
    })

    # ... rest of replanner logic
```

**Update prompt template**:
```python
self.prompt = ChatPromptTemplate.from_messages([
    ("system",
     "你是金融法律研究專家。檢視研究進度並決定下一步。\n"
     "原始查詢：{input}\n\n"
     "原始計畫：{plan}\n\n"
     "已執行任務：\n{past_steps}\n\n"
     "研究筆記：\n{notes}\n\n"  # ⭐ NEW
     "根據已完成任務與筆記，決定是否回答或繼續研究。\n"
     "1. 若資訊充足，提供 'response'\n"
     "2. 若需更多資訊，提供 'new_plan'\n"
     "重要：回應必須是有效 JSON。"
    ),
    ("user", "下一步該如何？")
])
```

---

## Advanced Patterns

### Pattern 5: Multi-Level Notes

**Use Case**: Different note granularities for different purposes

```python
class NoteLevel(str, Enum):
    DETAIL = "detail"      # Raw findings
    INSIGHT = "insight"    # Synthesized insights
    CONCLUSION = "conclusion"  # High-level conclusions

class MultiLevelNote(BaseModel):
    level: NoteLevel
    content: str
    parent_note_id: Optional[int] = None

class ResearchState(TypedDict):
    input: str
    detail_notes: Annotated[List[MultiLevelNote], add]
    insight_notes: Annotated[List[MultiLevelNote], add]
    conclusion_notes: Annotated[List[MultiLevelNote], add]
    response: str
```

### Pattern 6: Collaborative Note-Taking

**Use Case**: Multiple agents contribute to shared notes

```python
class CollaborativeNote(BaseModel):
    agent: str  # "retriever", "analyzer", "validator"
    insight: str
    agreed_by: List[str] = Field(default_factory=list)

def cross_validate_notes(state: ResearchState) -> dict:
    """Have agents validate each other's notes."""

    notes = state.get("notes", [])

    for note in notes:
        # Other agents review and agree/disagree
        if validator_agrees(note):
            note.agreed_by.append("validator")

    return {"notes": notes}
```

---

## Benefits for FinAgent

### 1. Better Synthesis
- Replanner sees summarized insights, not just raw results
- Final answer incorporates all discoveries coherently

### 2. Debugging
- Clear audit trail of what was learned when
- Easy to identify where agent went off track

### 3. Context Preservation
- Task 5 benefits from insights from Task 1
- No information loss between steps

### 4. User Transparency
- Show running notes in UI (real-time research progress)
- User sees "thinking process" not just final answer

### 5. Future: Cross-Session Learning
- Store notes in database
- Learn from previous similar queries

---

## Frontend Integration

**Display notes in Research Page**:

```typescript
// In ResearchPage.tsx

interface Note {
  task_id: number;
  insight: string;
  citations: string[];
  timestamp: string;
}

// Add notes state
const [notes, setNotes] = useState<Note[]>([]);

// Handle note_added event from backend
useEffect(() => {
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "note_added") {
      setNotes(prev => [...prev, data.note]);
    }
  };
}, []);

// Render notes panel
<div className="notes-panel">
  <h3>研究筆記</h3>
  {notes.map((note, i) => (
    <div key={i} className="note">
      <strong>任務 {note.task_id}:</strong> {note.insight}
      {note.citations.length > 0 && (
        <div className="citations">
          引用: {note.citations.join(", ")}
        </div>
      )}
    </div>
  ))}
</div>
```

---

## Best Practices

### 1. Keep Notes Concise
- One key insight per note
- Max 1-2 sentences
- Avoid duplicating full document text

### 2. Use Structured Notes
- Pydantic models for type safety
- Include metadata (task ID, confidence, citations)
- Enable filtering and analysis

### 3. Consolidate Periodically
- Prevent context overflow
- Summarize every 10 notes
- Keep recent notes + consolidated summary

### 4. Leverage in Prompts
- Include notes summary in replanner prompt
- Use notes for final synthesis
- Cross-reference notes with citations

### 5. Make Notes Visible
- Display in frontend UI
- Include in final response
- Use for debugging workflow

---

## Comparison: With vs. Without Notes

### Without Notes

```
Task 1: Find penalty cases -> [3 cases found]
Task 2: Analyze violations -> [AML violations identified]
Task 3: Check amounts -> [Penalties: 5M, 3M, 2M]

Replanner: "I have task results but need to re-read everything to see connections"
```

### With Notes

```
Task 1: Find penalty cases
  ├─ Result: [3 cases found]
  └─ Note: "玉山、富邦、台新銀行於2020年因洗錢防制缺失遭裁罰"

Task 2: Analyze violations
  ├─ Result: [AML violations identified]
  └─ Note: "三案件均涉及客戶盡職調查不足，未落實可疑交易申報"

Task 3: Check amounts
  ├─ Result: [Penalties: 5M, 3M, 2M]
  └─ Note: "裁罰金額與缺失嚴重程度成正比，玉山最高達500萬元"

Replanner: [Reads notes] "Three banks violated AML rules, total penalties 10M,
            玉山 highest due to severity. Ready to respond."
```

---

## References

### LangGraph State Reducers
- **Annotated Lists**: https://harshaselvi.medium.com/building-ai-agents-using-langgraph-part-8-understanding-reducers-and-state-updates-c8056963a42c
- **Reducer Functions**: https://medium.com/fundamentals-of-artificial-intelligence/langgraph-reducer-function-03cdd621030e
- **State Management Guide**: https://medium.com/@omeryalcin48/langgraph-notes-state-management-62ea5b5a5cdd

### Memory Patterns
- **Long-Term Memory**: https://saptak.in/writing/2025/03/23/mastering-long-term-agentic-memory-with-langgraph
- **Memory Consolidation**: https://medium.com/@gopikwork/building-agentic-memory-patterns-with-strands-and-langgraph-3cc8389b350d

---

## Key Takeaways

1. **Use Annotated[List, add]** - Automatically accumulates notes
2. **Create dedicated Note Agent** - Structured note-taking with LLM
3. **Integrate after each step** - action → take_note → next_action
4. **Include notes in prompts** - Use accumulated insights in replanner
5. **Consolidate periodically** - Prevent context overflow
6. **Display in UI** - Show research progress to user
7. **Structure with Pydantic** - Type-safe notes with metadata
8. **Extract citations** - Link notes back to sources

---

**Document Version**: 1.0
**Last Updated**: 2025-01-20
**Status**: Ready for implementation
**Recommended Priority**: Medium (Phase 3 optimization)
