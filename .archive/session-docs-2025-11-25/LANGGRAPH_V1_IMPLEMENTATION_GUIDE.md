# LangGraph v1.0 Implementation Guide

**Quick Reference for FinAgent Development**

---

## 📋 Table of Contents

1. [Core Concepts](#core-concepts)
2. [State Definition](#state-definition)
3. [Building Graphs](#building-graphs)
4. [Nodes](#nodes)
5. [Edges & Routing](#edges--routing)
6. [Compilation & Execution](#compilation--execution)
7. [Best Practices](#best-practices)
8. [Common Patterns](#common-patterns)
9. [Migration Checklist](#migration-checklist)

---

## Core Concepts

### Architecture Overview
```
StateGraph = State + Nodes + Edges + Compilation
```

- **State**: Shared data structure (TypedDict) passed between nodes
- **Nodes**: Functions that process state and return updates
- **Edges**: Define execution flow (sequential or conditional)
- **Compilation**: Validates graph and enables runtime features

### Key Principles
1. **Nodes are functions** - Can contain LLM calls, tool execution, or any logic
2. **State is immutable** - Nodes return updates, don't mutate directly
3. **Reducers control merging** - Define how state updates are applied
4. **Conditional routing** - Dynamic flow based on state values

---

## State Definition

### Basic TypedDict State
```python
from typing_extensions import TypedDict
from typing import Optional, List

class AgentState(TypedDict):
    input: str                    # User query
    messages: List[str]           # Conversation history
    plan: Optional[dict]          # Research plan
    result: Optional[str]         # Final answer
```

### State with Reducers
```python
from typing import Annotated
from operator import add

class AgentState(TypedDict):
    input: str
    # List fields: use add reducer to append (not replace)
    past_steps: Annotated[List[tuple], add]
    # Default: overwrite on update
    current_step: str
```

### MessagesState (Built-in)
```python
from langgraph.graph import MessagesState

class CustomState(MessagesState):
    """Extends MessagesState with custom fields"""
    documents: List[str]
    metadata: dict
```

**Reducer Behavior:**
- **Default**: Overwrites value
- **`add`**: Appends to lists
- **`add_messages`**: Intelligent message deduplication by ID

---

## Building Graphs

### Step 1: Initialize StateGraph
```python
from langgraph.graph import StateGraph

# Define state class
class MyState(TypedDict):
    query: str
    result: str

# Create graph builder
builder = StateGraph(MyState)
```

### Step 2: Add Nodes
```python
def analyze_query(state: MyState) -> dict:
    """Node function: takes state, returns updates"""
    analyzed = analyze(state["query"])
    return {"result": analyzed}

# Register node
builder.add_node("analyze", analyze_query)
```

### Step 3: Add Edges
```python
from langgraph.graph import START, END

# Entry point
builder.add_edge(START, "analyze")

# Sequential edge
builder.add_edge("analyze", "execute")

# Exit edge
builder.add_edge("execute", END)
```

### Step 4: Compile
```python
# Compile graph (REQUIRED before use)
graph = builder.compile()
```

---

## Nodes

### Node Function Signature
```python
def my_node(state: StateType) -> dict:
    """
    Args:
        state: Current state (read-only)

    Returns:
        dict: State updates (partial state)
    """
    return {"key": "new_value"}
```

### Node with Config
```python
def my_node(state: StateType, config: dict) -> dict:
    """Access runtime configuration"""
    api_key = config.get("configurable", {}).get("api_key")
    return {"result": process(state["input"], api_key)}
```

### Async Nodes
```python
async def async_node(state: StateType) -> dict:
    """Async operations supported"""
    result = await async_api_call(state["input"])
    return {"result": result}
```

### Node Best Practices
1. **Return partial updates** - Only return changed fields
2. **Keep focused** - One responsibility per node
3. **Handle errors** - Use try/except and update state with errors
4. **Log progress** - Use callbacks for UI updates

```python
def robust_node(state: StateType) -> dict:
    try:
        result = risky_operation(state["input"])
        return {"result": result, "error": None}
    except Exception as e:
        return {"result": None, "error": str(e)}
```

---

## Edges & Routing

### Sequential Edges
```python
# Fixed transitions
builder.add_edge("node_a", "node_b")
builder.add_edge("node_b", END)
```

### Conditional Edges
```python
def route_decision(state: AgentState) -> str:
    """
    Returns: Node name to execute next
    """
    if state.get("result"):
        return END
    elif state["retry_count"] < 3:
        return "retry_node"
    else:
        return "failure_node"

builder.add_conditional_edges(
    "decision_node",
    route_decision,
    {
        END: END,
        "retry_node": "retry_node",
        "failure_node": "failure_node",
    }
)
```

### Conditional Edge Patterns

#### Pattern 1: Boolean Decision
```python
def should_continue(state: AgentState) -> str:
    return "continue" if state["has_more_work"] else END

builder.add_conditional_edges(
    "worker",
    should_continue,
    {"continue": "worker", END: END}
)
```

#### Pattern 2: Multi-way Routing
```python
def route_by_type(state: AgentState) -> str:
    query_type = state["analysis"]["query_type"]
    return {
        "penalty": "penalty_agent",
        "judgment": "judgment_agent",
        "general": "general_agent",
    }.get(query_type, "fallback_agent")

builder.add_conditional_edges("router", route_by_type)
```

#### Pattern 3: Using Command (Advanced)
```python
from langgraph.types import Command
from typing import Literal

def smart_node(state: AgentState) -> Command[Literal["next", "retry"]]:
    """Update state AND specify next node"""
    if success:
        return Command(
            update={"result": "success"},
            goto="next"
        )
    else:
        return Command(
            update={"retry_count": state["retry_count"] + 1},
            goto="retry"
        )
```

---

## Compilation & Execution

### Basic Compilation
```python
graph = builder.compile()
```

### Execution Methods

#### 1. Invoke (Synchronous)
```python
result = graph.invoke({"input": "query text"})
print(result["result"])
```

#### 2. Async Invoke
```python
result = await graph.ainvoke({"input": "query text"})
```

#### 3. Stream (Real-time Updates)
```python
async for node_name, state_update in graph.astream(
    {"input": "query text"}
):
    print(f"Node: {node_name}")
    print(f"Update: {state_update}")
```

#### 4. Stream with Events
```python
async for event in graph.astream_events(
    {"input": "query text"},
    version="v1"
):
    if event["event"] == "on_chain_end":
        print(f"Completed: {event['name']}")
```

---

## Best Practices

### 1. State Design
✅ **DO:**
- Use TypedDict for explicit typing
- Keep state flat and simple
- Use reducers for lists/collections
- Include error fields for resilience

❌ **DON'T:**
- Store large objects (keep references)
- Use mutable defaults
- Mix concerns in single state field

### 2. Node Design
✅ **DO:**
```python
# Single responsibility
def retrieve_documents(state: AgentState) -> dict:
    docs = retriever.search(state["query"])
    return {"documents": docs}

# Clear error handling
def safe_llm_call(state: AgentState) -> dict:
    try:
        response = llm.invoke(state["prompt"])
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": str(e)}
```

❌ **DON'T:**
```python
# Multiple responsibilities (BAD)
def do_everything(state: AgentState) -> dict:
    docs = retrieve(state["query"])
    answer = llm(docs)
    validated = validate(answer)
    return {"result": validated}
```

### 3. Edge Design
✅ **DO:**
- Use descriptive routing function names
- Handle all possible states
- Provide clear END conditions

```python
def route_after_validation(state: AgentState) -> str:
    """Route based on validation results"""
    if state.get("validation_passed"):
        return "answer_generation"
    elif state["retry_count"] < 3:
        return "retry_retrieval"
    else:
        return END
```

### 4. Error Handling
```python
class AgentState(TypedDict):
    input: str
    result: Optional[str]
    error: Optional[str]       # Track errors
    retry_count: int           # Enable retry logic

def resilient_node(state: AgentState) -> dict:
    try:
        result = risky_operation(state["input"])
        return {"result": result, "error": None}
    except Exception as e:
        logger.error(f"Node failed: {e}")
        return {
            "error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }
```

### 5. Retry Logic with Tenacity
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def llm_node(state: AgentState) -> dict:
    """Automatic retry on failure"""
    response = await llm.ainvoke(state["prompt"])
    return {"response": response}
```

---

## Common Patterns

### Pattern 1: Plan-and-Execute
```python
class PlanExecuteState(TypedDict):
    input: str
    plan: Optional[Plan]
    past_steps: Annotated[List[tuple], add]
    response: Optional[str]

builder = StateGraph(PlanExecuteState)

# Nodes
builder.add_node("planner", create_plan)
builder.add_node("executor", execute_task)
builder.add_node("replanner", replan_or_finish)

# Flow
builder.add_edge(START, "planner")
builder.add_edge("planner", "executor")
builder.add_edge("executor", "replanner")

# Conditional loop
def should_continue(state: PlanExecuteState) -> str:
    return END if state.get("response") else "executor"

builder.add_conditional_edges(
    "replanner",
    should_continue,
    {END: END, "executor": "executor"}
)

graph = builder.compile()
```

### Pattern 2: Multi-Agent Coordination
```python
class MultiAgentState(TypedDict):
    input: str
    agent_outputs: Annotated[List[dict], add]
    final_answer: Optional[str]

# Parallel agent execution
def supervisor(state: MultiAgentState) -> dict:
    # Analyze which agents to call
    agents_needed = ["agent_a", "agent_b"]
    return {"agents_to_call": agents_needed}

# Use Send for parallel execution
from langgraph.types import Send

def spawn_agents(state: MultiAgentState):
    """Fan-out to multiple agents"""
    return [
        Send("agent_worker", {"task": task})
        for task in state["tasks"]
    ]

builder.add_conditional_edges("supervisor", spawn_agents)
```

### Pattern 3: Human-in-the-Loop
```python
from langgraph.checkpoint.memory import MemorySaver

class HILState(TypedDict):
    query: str
    plan: Optional[dict]
    user_approval: Optional[bool]
    result: Optional[str]

def wait_for_approval(state: HILState) -> str:
    """Pause for user input"""
    if state.get("user_approval") is None:
        # Graph will pause here
        return "waiting"
    elif state["user_approval"]:
        return "execute"
    else:
        return "replan"

# Compile with checkpointer for persistence
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# Resume execution after user input
config = {"configurable": {"thread_id": "session_123"}}
result = graph.invoke(
    {"user_approval": True},
    config=config
)
```

### Pattern 4: RAG with Validation
```python
class RAGState(TypedDict):
    query: str
    documents: List[str]
    answer: Optional[str]
    validation_passed: bool
    retry_count: int

builder.add_node("retrieve", retrieve_documents)
builder.add_node("generate", generate_answer)
builder.add_node("validate", validate_citations)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", "validate")

def route_after_validation(state: RAGState) -> str:
    if state["validation_passed"]:
        return END
    elif state["retry_count"] < 2:
        return "retrieve"  # Try different retrieval
    else:
        return END  # Give up

builder.add_conditional_edges("validate", route_after_validation)
```

---

## Migration Checklist

### From Legacy LangChain to v1.0

#### ❌ **OLD WAY (Legacy)**
```python
from langchain.agents import AgentExecutor, ZeroShotAgent
from langchain.chains import LLMChain

# Legacy chain
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(input_text)

# Legacy agent
agent = ZeroShotAgent(llm_chain=chain, tools=tools)
executor = AgentExecutor(agent=agent, tools=tools)
executor.run(query)
```

#### ✅ **NEW WAY (v1.0)**
```python
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate

# LCEL chain
chain = prompt | llm | parser
result = await chain.ainvoke({"input": input_text})

# StateGraph agent
class AgentState(TypedDict):
    input: str
    result: Optional[str]

builder = StateGraph(AgentState)
builder.add_node("process", lambda s: {"result": chain.invoke(s)})
builder.add_edge(START, "process")
builder.add_edge("process", END)
graph = builder.compile()

result = await graph.ainvoke({"input": query})
```

### Migration Steps

1. **Update Imports**
```python
# Core functionality (v1.0)
from langchain.agents import create_agent  # New standard
from langgraph.graph import StateGraph, START, END

# Legacy functionality (if needed)
from langchain_classic.chains import ...
```

2. **Convert Chains to LCEL**
```python
# Before: LLMChain
chain = LLMChain(llm=llm, prompt=prompt)

# After: LCEL
chain = prompt | llm | parser
```

3. **Replace AgentExecutor**
```python
# Before: AgentExecutor
executor = AgentExecutor(agent=agent, tools=tools)

# After: create_agent or StateGraph
from langchain.agents import create_agent
agent = create_agent(model, tools)
```

4. **Update Method Calls**
```python
# Before
result = chain.run(input)
result = await chain.acall(input)

# After
result = chain.invoke(input)
result = await chain.ainvoke(input)
```

5. **Add Type Safety**
```python
# Before: Dict
state = {"input": "query", "result": None}

# After: TypedDict
class State(TypedDict):
    input: str
    result: Optional[str]

state: State = {"input": "query", "result": None}
```

---

## Quick Reference

### Minimal Working Example
```python
from typing_extensions import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

# 1. Define state
class State(TypedDict):
    input: str
    output: Optional[str]

# 2. Define nodes
def process(state: State) -> dict:
    return {"output": f"Processed: {state['input']}"}

# 3. Build graph
builder = StateGraph(State)
builder.add_node("process", process)
builder.add_edge(START, "process")
builder.add_edge("process", END)

# 4. Compile
graph = builder.compile()

# 5. Execute
result = graph.invoke({"input": "Hello"})
print(result["output"])  # "Processed: Hello"
```

### Common Imports
```python
# State and Graph
from typing_extensions import TypedDict
from typing import Annotated, Optional, List, Literal
from operator import add
from langgraph.graph import StateGraph, MessagesState, START, END

# Advanced features
from langgraph.types import Command, Send
from langgraph.checkpoint.memory import MemorySaver

# LangChain core
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.tools import BaseTool

# Retry logic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
```

---

## Resources

### Official Documentation
- **LangGraph Docs**: https://docs.langchain.com/oss/python/langgraph/
- **LangChain v1.0**: https://docs.langchain.com/oss/python/releases/langchain-v1
- **API Reference**: https://python.langchain.com/api_reference/

### Key Blog Posts
- **v1.0 Release Announcement**: https://blog.langchain.com/langchain-langgraph-1dot0/
- **Migration Guide**: Check official docs for `/oss/python/migrate/langchain-v1`

### Internal References (FinAgent)
- **Implementation Example**: [src/finagent/agents/plan_execute/graph.py](src/finagent/agents/plan_execute/graph.py)
- **State Models**: [src/finagent/agents/plan_execute/models.py](src/finagent/agents/plan_execute/models.py)
- **Agent Nodes**: [src/finagent/agents/plan_execute/](src/finagent/agents/plan_execute/)

---

## Troubleshooting

### Common Issues

**Issue**: "Graph not compiled"
```python
# ❌ Forgot to compile
graph = builder  # Wrong!

# ✅ Must compile
graph = builder.compile()
```

**Issue**: "State key not found"
```python
# ❌ Accessing undefined key
def node(state: State) -> dict:
    return {"result": state["nonexistent"]}  # KeyError!

# ✅ Use .get() with default
def node(state: State) -> dict:
    value = state.get("optional_key", "default")
    return {"result": value}
```

**Issue**: "Conditional edge returns wrong type"
```python
# ❌ Returning boolean instead of node name
def router(state: State) -> bool:
    return True  # Wrong!

# ✅ Return node name string
def router(state: State) -> str:
    return "next_node" if condition else END
```

**Issue**: "State not updating"
```python
# ❌ Mutating state directly
def node(state: State) -> dict:
    state["key"] = "value"  # Doesn't work!
    return {}

# ✅ Return updates
def node(state: State) -> dict:
    return {"key": "value"}
```

---

**Last Updated**: 2025-01-20
**LangChain Version**: v1.0
**LangGraph Version**: v1.0
**FinAgent Version**: v1.1 (Plan-and-Execute)
