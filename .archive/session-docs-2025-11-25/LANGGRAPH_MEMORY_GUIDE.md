# LangGraph Memory & Session State Management Guide

**How LangChain/LangGraph Handle Temporary Memory and Memoization**

**Last Updated**: 2025-01-20
**Based on**: Official LangGraph v0.2+ documentation and 2025 best practices

---

## Overview

LangGraph handles memory through **checkpointers** (session state persistence) and **stores** (long-term memory). This is different from traditional memoization—it's about maintaining agent state across invocations, not caching function results.

**Key Distinction**:
- **Checkpointers**: Save graph state at each step (session memory)
- **Stores**: Persist data across sessions (long-term memory)
- **Memoization**: Cache computation results (not built-in, use functools.lru_cache)

---

## 🧠 Memory Types in LangGraph

### 1. Short-Term Memory (Thread-Level Persistence)

**Purpose**: Track multi-turn conversations within a session

**Implementation**: Checkpointers save graph state at every superstep

**Use Cases**:
- Chat applications (remember conversation context)
- Multi-step workflows (resume after interruption)
- Human-in-the-loop (pause for user input, resume later)

### 2. Long-Term Memory (Cross-Session Persistence)

**Purpose**: Maintain user data across different conversations

**Implementation**: Separate storage layer (InMemoryStore, MongoDB, Redis)

**Use Cases**:
- User preferences across sessions
- Historical interaction data
- Procedural, episodic, semantic memories (LangMem toolkit)

---

## 📦 Checkpointer Options

### Development: InMemorySaver (MemorySaver)

**Best for**: Experimentation, local development, testing

**Limitations**: Transient—state vanishes when program stops

**Example**:
```python
from langgraph.checkpoint.memory import InMemorySaver

# Initialize checkpointer
checkpointer = InMemorySaver()

# Compile graph with checkpointer
graph = builder.compile(checkpointer=checkpointer)

# Invoke with thread ID
config = {"configurable": {"thread_id": "conversation-1"}}
result = graph.invoke({"input": "Hello"}, config)
```

### Production: Database-Backed Checkpointers

**Options** (2025):
1. **PostgresSaver** - PostgreSQL backend
2. **SqliteSaver** - SQLite (good for local workflows)
3. **MongoDBSaver** - MongoDB clusters
4. **RedisSaver** - Redis (recommended for high-traffic apps)

**Example (PostgreSQL)**:
```python
from langgraph.checkpoint.postgres import PostgresSaver

# Initialize with connection string
checkpointer = PostgresSaver(conn_string="postgresql://user:pass@localhost/db")

# Use same pattern as InMemorySaver
graph = builder.compile(checkpointer=checkpointer)
```

**Example (Redis - Async)**:
```python
from langgraph.checkpoint.redis import AsyncRedisSaver
from redis.asyncio import Redis

# Initialize Redis connection
redis_client = Redis.from_url("redis://localhost:6379")
checkpointer = AsyncRedisSaver(redis_client)

# Compile with async checkpointer
graph = builder.compile(checkpointer=checkpointer)

# Use with async invoke
result = await graph.ainvoke({"input": "Hello"}, config)
```

**Recommendation**: Use `AsyncRedisSaver` or `AsyncSqliteSaver` for high-traffic applications to prevent bottlenecks.

---

## 🔑 Thread ID & Session Management

### Thread ID Pattern

**Thread ID** = Unique identifier for a conversation session

**Multiple threads** = Isolated conversation states (no crosstalk)

**Example: Multi-User Chat Application**:
```python
# User A's conversation
config_a = {"configurable": {"thread_id": "user-a-session-1"}}
graph.invoke({"input": "What's the weather?"}, config_a)

# User B's conversation (separate state)
config_b = {"configurable": {"thread_id": "user-b-session-1"}}
graph.invoke({"input": "Book a flight"}, config_b)

# User A continues (remembers previous context)
graph.invoke({"input": "Thanks!"}, config_a)
```

### Retrieving Conversation History

**Access saved state**:
```python
# Get current state
state = graph.get_state(config)
print(state.values)  # Current state values
print(state.next)    # Next nodes to execute

# Get full state history
history = graph.get_state_history(config)
for checkpoint in history:
    print(checkpoint.values)
```

---

## 🏗️ Implementation Patterns

### Pattern 1: Basic Conversation Memory

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict

class ConversationState(TypedDict):
    messages: list[str]
    context: dict

def process_message(state: ConversationState):
    # Agent processing logic
    messages = state["messages"]
    # ... process ...
    return {"messages": messages + ["response"]}

# Build graph
builder = StateGraph(ConversationState)
builder.add_node("process", process_message)
builder.add_edge(START, "process")
builder.add_edge("process", END)

# Add checkpointer
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Use with thread ID
config = {"configurable": {"thread_id": "chat-123"}}
result = graph.invoke({"messages": ["Hello"]}, config)
```

### Pattern 2: Long-Term Memory with Store

```python
from langgraph.store.memory import InMemoryStore

# Initialize both checkpointer (short-term) and store (long-term)
checkpointer = InMemorySaver()
store = InMemoryStore()

# Compile with both
graph = builder.compile(checkpointer=checkpointer, store=store)

# Store user preferences (persists across threads)
namespace = ("user_prefs", "user-123")
store.put(namespace, "language", {"value": "zh-TW"})

# Retrieve in any thread
prefs = store.get(namespace, "language")
```

### Pattern 3: Human-in-the-Loop with Checkpointer

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Create agent with checkpointer
agent = create_react_agent(
    ChatOpenAI(model="gpt-4"),
    tools=[...],
    checkpointer=InMemorySaver()
)

# Run until human input needed
config = {"configurable": {"thread_id": "agent-session-1"}}
for event in agent.stream({"input": "Book a flight"}, config):
    if "interrupt" in event:
        # Pause for human input
        user_approval = input("Approve booking? (y/n): ")

        # Resume with approval
        agent.invoke({"approval": user_approval}, config)
```

### Pattern 4: Subgraph Memory Inheritance

**Default behavior**: Subgraphs inherit parent checkpointer

```python
# Parent graph
parent_graph = parent_builder.compile(checkpointer=checkpointer)

# Subgraph automatically inherits checkpointer
subgraph = subgraph_builder.compile()  # No need to pass checkpointer

# Explicit override (if needed)
subgraph_custom = subgraph_builder.compile(
    checkpointer=different_checkpointer
)
```

---

## 🗂️ Memory Optimization Strategies

### Problem: Context Window Overflow

Long conversations exceed LLM token limits.

### Solutions

#### 1. Trim Messages (Keep Last N Tokens)

```python
from langchain_core.messages import trim_messages

def process_with_trimming(state):
    # Keep last 1000 tokens
    trimmed = trim_messages(
        state["messages"],
        max_tokens=1000,
        strategy="last"
    )
    return {"messages": trimmed}
```

#### 2. Delete Specific Messages

```python
from langchain_core.messages import RemoveMessage

def remove_old_messages(state):
    # Get message IDs to delete
    to_delete = [msg.id for msg in state["messages"][:5]]

    # Create delete commands
    return {"messages": [RemoveMessage(id=id) for id in to_delete]}
```

#### 3. Summarize Conversation

```python
from langchain_openai import ChatOpenAI

async def summarize_conversation(state):
    # Summarize messages 10-50
    old_messages = state["messages"][10:50]

    llm = ChatOpenAI(model="gpt-4o-mini")
    summary = await llm.ainvoke([
        {"role": "system", "content": "Summarize this conversation"},
        *old_messages
    ])

    # Replace old messages with summary
    new_messages = (
        state["messages"][:10] +  # Keep first 10
        [summary] +               # Add summary
        state["messages"][50:]    # Keep recent messages
    )

    return {"messages": new_messages}
```

---

## 🔄 Memoization vs. Checkpointing

### Checkpointing (Built-in LangGraph Feature)

**Purpose**: Save agent state between invocations

**Use case**: Resume conversations, handle interruptions

**Implementation**: Automatic when using checkpointer

```python
# State is automatically saved at each step
graph = builder.compile(checkpointer=InMemorySaver())
```

### Memoization (Custom Implementation Needed)

**Purpose**: Cache expensive function results

**Use case**: Avoid re-computing embeddings, API calls

**Implementation**: Use `functools.lru_cache` or custom cache

```python
from functools import lru_cache

# Example: Cache document embeddings
@lru_cache(maxsize=1000)
def get_embedding(text: str) -> list[float]:
    """Cache embeddings to avoid re-computation."""
    return embedding_model.embed(text)

# Example: Cache retrieval results
from typing import List
from langchain_core.documents import Document

_retrieval_cache = {}

def cached_retrieve(query: str, top_k: int = 5) -> List[Document]:
    """Cache retrieval results for identical queries."""
    cache_key = (query, top_k)

    if cache_key not in _retrieval_cache:
        _retrieval_cache[cache_key] = retriever.retrieve(query, top_k)

    return _retrieval_cache[cache_key]
```

**For FinAgent**: Add caching to DocumentRetriever (see V1_1_RELEASE_PLAN.md Medium Priority #3)

---

## 🚀 Implementation for FinAgent v1.1

### Current State

**No checkpointer implemented** - Each query is stateless

**Impact**:
- No conversation memory
- Cannot resume interrupted workflows
- WebSocket disconnection loses state

### Recommended Implementation

#### Phase 1: Add Short-Term Memory (High Priority)

**For WebSocket state persistence** (V1_1_RELEASE_PLAN.md Low Priority #8):

```python
# In src/finagent/agents/plan_execute/graph.py

from langgraph.checkpoint.memory import InMemorySaver
# Or for production:
# from langgraph.checkpoint.sqlite import SqliteSaver

class PlanExecuteWorkflow:
    def __init__(self):
        # Initialize checkpointer
        self.checkpointer = InMemorySaver()
        # For production:
        # self.checkpointer = SqliteSaver("./data/checkpoints.db")

        # Build workflow
        workflow = StateGraph(PlanExecuteState)
        # ... add nodes ...

        # Compile with checkpointer
        self.graph = workflow.compile(checkpointer=self.checkpointer)

    async def run(self, query: str, session_id: str):
        """Execute with session persistence."""
        config = {"configurable": {"thread_id": session_id}}

        async for event in self.graph.astream(
            {"input": query},
            config,
            stream_mode="values"
        ):
            yield event
```

**In WebSocket handler** (src/finagent/api/routes/websocket.py):

```python
async def stream_query(websocket: WebSocket, query: str, use_plan_execute: bool):
    # Generate session ID from WebSocket connection
    session_id = f"session-{id(websocket)}"

    if use_plan_execute:
        workflow = PlanExecuteWorkflow()
        async for event in workflow.run(query, session_id):
            await websocket.send_json(event)
```

**Benefits**:
- Plan persists across WebSocket reconnections
- Can resume workflow if connection drops
- User can see previous plan state

#### Phase 2: Add Result Caching (Medium Priority)

**In src/finagent/document_processing/retriever.py**:

```python
from functools import lru_cache
from typing import Tuple

class DocumentRetriever:
    def __init__(self):
        self._embedding_cache = {}

    @lru_cache(maxsize=500)
    def _get_query_embedding(self, query: str) -> Tuple[float, ...]:
        """Cache query embeddings (tuple for hashability)."""
        embedding = self.embedding_model.embed(query)
        return tuple(embedding)  # Tuple is hashable for lru_cache

    def retrieve(self, query: str, top_k: int = 5):
        # Use cached embedding
        embedding = list(self._get_query_embedding(query))

        # Check result cache
        cache_key = (query, top_k)
        if cache_key in self._result_cache:
            return self._result_cache[cache_key]

        # Retrieve and cache
        results = self.vector_db.search(embedding, top_k)
        self._result_cache[cache_key] = results

        return results
```

#### Phase 3: Long-Term Memory (Optional)

**For user preferences across sessions**:

```python
from langgraph.store.memory import InMemoryStore

# In orchestrator or config manager
store = InMemoryStore()

# Store user research preferences
namespace = ("user_prefs", user_id)
store.put(namespace, "preferred_workflow", {"value": "plan_execute"})
store.put(namespace, "language", {"value": "zh-TW"})

# Retrieve in any session
prefs = store.get(namespace, "preferred_workflow")
```

---

## 📊 Comparison: Checkpointer vs. Memoization

| Feature | Checkpointer | Memoization |
|---------|--------------|-------------|
| **Purpose** | Save agent state | Cache function results |
| **Persistence** | Across invocations | During program runtime |
| **Implementation** | Built-in LangGraph | Custom (functools.lru_cache) |
| **Use Case** | Resume workflows | Avoid re-computation |
| **Storage** | Database or memory | In-memory dictionary |
| **Thread-safe** | Yes (with proper DB) | Yes (lru_cache is thread-safe) |
| **Multi-session** | Yes (with thread IDs) | No (global cache) |

---

## 🔧 Best Practices

### 1. Choose Right Checkpointer

- **Development**: `InMemorySaver`
- **Production (low traffic)**: `SqliteSaver`
- **Production (high traffic)**: `AsyncRedisSaver` or `AsyncPostgresSaver`

### 2. Use Unique Thread IDs

```python
# Good: Unique per user + session
thread_id = f"user-{user_id}-session-{session_id}"

# Bad: Same for all users
thread_id = "global-session"
```

### 3. Clean Up Old Checkpoints

```python
# Delete old conversation threads
graph.delete_thread({"configurable": {"thread_id": "old-session"}})
```

### 4. Combine Short-Term + Long-Term Memory

```python
# Short-term: Conversation history (checkpointer)
# Long-term: User preferences (store)
graph = builder.compile(
    checkpointer=SqliteSaver("./data/sessions.db"),
    store=InMemoryStore()
)
```

### 5. Implement Graceful Degradation

```python
try:
    # Try with checkpointer
    result = graph.invoke(input, config)
except Exception:
    # Fall back to stateless execution
    result = graph_without_checkpointer.invoke(input)
```

---

## 📚 References

### Official Documentation
- **LangGraph Memory Guide**: https://docs.langchain.com/oss/python/langgraph/add-memory
- **LangGraph Checkpointer API**: https://pypi.org/project/langgraph-checkpoint/
- **LangGraph v0.2 Release**: https://blog.langchain.com/langgraph-v0-2/

### Database Integrations
- **Redis + LangGraph**: https://redis.io/blog/langgraph-redis-build-smarter-ai-agents-with-memory-persistence/
- **MongoDB + LangGraph**: https://www.mongodb.com/company/blog/product-release-announcements/powering-long-term-memory-for-agents-langgraph

### Community Resources
- **Persisting Agent State**: https://jokerdii.github.io/di-blog/2025/01/24/Persisting-Agent-State/
- **Customizing Memory**: https://focused.io/lab/customizing-memory-in-langgraph-agents-for-better-conversations

---

## 🎯 Key Takeaways

1. **Checkpointers ≠ Memoization** - Different purposes, different implementations
2. **Thread IDs are crucial** - Enable multi-user, multi-session support
3. **Use InMemorySaver for dev** - Switch to database checkpointer for production
4. **Combine short + long term** - Checkpointer for conversations, Store for user data
5. **Optimize for context limits** - Trim, delete, or summarize old messages
6. **Add caching separately** - Use functools.lru_cache for expensive computations
7. **Async for high traffic** - AsyncRedisSaver or AsyncPostgresSaver prevents bottlenecks
8. **Clean up old threads** - Prevent database bloat with periodic cleanup

---

## 📝 Next Steps for FinAgent

Based on V1_1_RELEASE_PLAN.md:

### Immediate (High Priority #1 - Plan Panel Bug)
1. Add `InMemorySaver` to Plan-and-Execute workflow
2. Use WebSocket connection ID as thread ID
3. Test plan persistence across reconnections

### Short-Term (Medium Priority #3 - Caching)
4. Add `@lru_cache` to DocumentRetriever.get_embedding()
5. Implement result caching for identical queries
6. Add cache statistics logging

### Long-Term (Low Priority #8 - WebSocket Persistence)
7. Upgrade to `SqliteSaver` for production
8. Implement graceful degradation on checkpointer failure
9. Add user preference storage with InMemoryStore

---

**Document Version**: 1.0
**Last Updated**: 2025-01-20
**Status**: Ready for implementation
