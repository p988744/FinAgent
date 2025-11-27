"""
WebSocket API for real-time query progress streaming.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from finagent.agents.orchestrator import AgentOrchestrator
from finagent.agents.ui_callback import UICallback
from finagent.models.answers import LegalAnswer
from finagent.models.citations import LegalCitation
from finagent.models.queries import Query
from finagent.models.todo_item import TodoItem
from finagent.models.resolution_plan import ResolutionPlan

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Demo delay for testing real-time workflow monitoring
# Set ENABLE_DEMO_DELAY=true in environment to enable
ENABLE_DEMO_DELAY = os.getenv("ENABLE_DEMO_DELAY", "false").lower() == "true"


class WebSocketUICallback(UICallback):
    """UICallback implementation that streams updates via WebSocket."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.current_step = "idle"
        self.step_start_times: dict[str, datetime] = {}

    async def _send(self, message_type: str, payload: dict[str, Any]):
        """Send a message through the WebSocket."""
        try:
            message = {
                "type": message_type,
                "timestamp": datetime.now().isoformat(),
                "payload": payload,
            }
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")

    async def on_analysis_start(self, query: Query):
        """Query analysis has started."""
        self.current_step = "planning"
        self.step_start_times["planning"] = datetime.now()
        await self._send("step_update", {
            "step": "planning",
            "status": "active",
            "description": "分析查詢意圖與關鍵字",
            "elapsed_ms": 0,
        })
        await self._send("activity_log", {
            "level": "info",
            "message": f"開始分析查詢: {query.text[:50]}...",
        })

    async def on_analysis_complete(self, analysis: dict[str, Any]):
        """Query analysis completed."""
        elapsed = int((datetime.now() - self.step_start_times.get("planning", datetime.now())).total_seconds() * 1000)
        await self._send("step_update", {
            "step": "planning",
            "status": "done",
            "description": "查詢分析完成",
            "elapsed_ms": elapsed,
        })
        await self._send("activity_log", {
            "level": "success",
            "message": f"分析完成 - 識別意圖: {analysis.get('intent', 'unknown')}",
        })

    async def on_dynamic_plan_analysis(self, query_analysis: dict[str, Any], selected_tools: list[dict[str, Any]]):
        """Dynamic planning analysis completed (query analysis + tool selection)."""
        await self._send("dynamic_plan_analysis", {
            "query_analysis": query_analysis,
            "selected_tools": selected_tools,
        })
        await self._send("activity_log", {
            "level": "info",
            "message": f"動態規劃: 識別意圖={query_analysis.get('intent', 'unknown')}, 選擇工具={len(selected_tools)}個",
        })

    async def on_tool_execution_start(self, tool_name: str, parameters: dict[str, Any]):
        """Tool execution has started."""
        await self._send("tool_execution_update", {
            "tool_name": tool_name,
            "status": "executing",
            "parameters": parameters,
        })
        await self._send("activity_log", {
            "level": "info",
            "message": f"執行工具: {tool_name}",
        })

    async def on_tool_execution_complete(self, tool_name: str, result_count: int, execution_time_ms: int):
        """Tool execution has completed."""
        await self._send("tool_execution_update", {
            "tool_name": tool_name,
            "status": "completed",
            "result_count": result_count,
            "execution_time_ms": execution_time_ms,
        })
        await self._send("activity_log", {
            "level": "success",
            "message": f"工具完成: {tool_name} - {result_count} 個結果 ({execution_time_ms}ms)",
        })

    async def on_tool_execution_failed(self, tool_name: str, error: str):
        """Tool execution has failed."""
        await self._send("tool_execution_update", {
            "tool_name": tool_name,
            "status": "failed",
            "error": error,
        })
        await self._send("activity_log", {
            "level": "error",
            "message": f"工具失敗: {tool_name} - {error}",
        })

    async def on_task_tool_usage(self, task_id: int, tool_usage: dict[str, Any]):
        """Update task with tool usage information."""
        await self._send("task_tool_usage", {
            "task_id": task_id,
            "tool_usage": tool_usage,
        })

    async def on_clarification_request(self, questions: list[str]) -> Optional[str]:
        """Handle clarification request (not implemented for WebSocket)."""
        await self._send("activity_log", {
            "level": "warning",
            "message": "需要用戶確認 (WebSocket 模式不支援)",
        })
        return None

    async def on_plan_created(self, plan: ResolutionPlan):
        """Research plan has been created."""
        self.current_step = "action"
        self.step_start_times["action"] = datetime.now()
        await self._send("step_update", {
            "step": "planning",
            "status": "done",
            "description": "研究計畫已建立",
            "elapsed_ms": int((datetime.now() - self.step_start_times.get("planning", datetime.now())).total_seconds() * 1000),
        })
        await self._send("step_update", {
            "step": "action",
            "status": "active",
            "description": "執行 RAG 檢索",
            "elapsed_ms": 0,
        })
        await self._send("activity_log", {
            "level": "info",
            "message": f"研究計畫: {plan.summary if hasattr(plan, 'summary') else '已建立'}",
        })

    async def on_todo_list_created(self, todos: list[TodoItem]):
        """Todo list has been created."""
        todo_list = []
        for todo in todos:
            todo_list.append({
                "id": str(todo.id),
                "description": todo.content,  # TodoItem uses 'content' not 'description'
                "status": todo.status if isinstance(todo.status, str) else str(todo.status),
                "priority": 1,
            })
        await self._send("todo_update", {
            "todos": todo_list,
            "total_count": len(todos),
            "completed_count": 0,
            "progress_percentage": 0,
        })

    async def on_todo_started(self, todo: TodoItem):
        """A todo item has started."""
        await self._send("todo_item_update", {
            "id": str(todo.id),
            "status": "in_progress",
            "description": todo.content,
        })
        await self._send("activity_log", {
            "level": "info",
            "message": f"開始任務: {todo.content}",
        })

    async def on_todo_progress(self, todo: TodoItem, percentage: int, message: str = ""):
        """Progress update for a todo item."""
        await self._send("todo_item_update", {
            "id": str(todo.id),
            "status": "in_progress",
            "progress": percentage,
            "message": message,
        })

    async def on_todo_completed(self, todo: TodoItem):
        """A todo item has completed."""
        await self._send("todo_item_update", {
            "id": str(todo.id),
            "status": "completed",
            "description": todo.content,
        })
        await self._send("activity_log", {
            "level": "success",
            "message": f"完成任務: {todo.content}",
        })

    async def on_todo_failed(self, todo: TodoItem, error: str):
        """A todo item has failed."""
        await self._send("todo_item_update", {
            "id": str(todo.id),
            "status": "failed",
            "error": error,
        })
        await self._send("activity_log", {
            "level": "error",
            "message": f"任務失敗: {todo.content} - {error}",
        })

    async def on_retrieval_result(self, strategy: str = "", count: int = 0, total_chunks: int = 0, **kwargs):
        """RAG retrieval completed."""
        # Handle both old and new parameter names
        total = kwargs.get('total', total_chunks)
        await self._send("activity_log", {
            "level": "info",
            "message": f"檢索完成: {count} 相關文件 (共 {total} 區塊)",
        })

    async def on_answer_generation_start(self):
        """Answer generation has started."""
        self.current_step = "validation"
        self.step_start_times["validation"] = datetime.now()
        elapsed = int((datetime.now() - self.step_start_times.get("action", datetime.now())).total_seconds() * 1000)
        await self._send("step_update", {
            "step": "action",
            "status": "done",
            "description": "RAG 檢索完成",
            "elapsed_ms": elapsed,
        })
        await self._send("step_update", {
            "step": "validation",
            "status": "active",
            "description": "驗證引用完整性",
            "elapsed_ms": 0,
        })

    async def on_citations_formatted(self, citations: list[LegalCitation]):
        """Citations have been formatted."""
        citation_list = []
        for i, citation in enumerate(citations):
            citation_list.append({
                "id": i + 1,
                "source": citation.source,
                "authority": citation.authority.value if hasattr(citation.authority, 'value') else str(citation.authority),
                "citation_type": citation.citation_type.value if hasattr(citation.citation_type, 'value') else str(citation.citation_type),
            })
        await self._send("citations_update", {
            "citations": citation_list,
            "count": len(citations),
        })

    async def on_answer_complete(self, answer: LegalAnswer):
        """Answer generation completed."""
        self.current_step = "answer"
        self.step_start_times["answer"] = datetime.now()
        elapsed = int((datetime.now() - self.step_start_times.get("validation", datetime.now())).total_seconds() * 1000)
        await self._send("step_update", {
            "step": "validation",
            "status": "done",
            "description": "驗證完成",
            "elapsed_ms": elapsed,
        })
        await self._send("step_update", {
            "step": "answer",
            "status": "active",
            "description": "生成最終答案",
            "elapsed_ms": 0,
        })

    async def on_error(self, error: str, context: Optional[dict[str, Any]] = None):
        """An error occurred."""
        await self._send("error", {
            "message": error,
            "context": context or {},
        })
        await self._send("activity_log", {
            "level": "error",
            "message": f"錯誤: {error}",
        })

    # Additional methods called by agents but not in base UICallback interface
    # These must be async since agents wrap them in asyncio.create_task()
    async def on_retrieval_start(self, query: str, strategy: str, max_results: int):
        """RAG retrieval has started."""
        await self._send("activity_log", {
            "level": "info",
            "message": f"開始檢索: 查詢={query[:30]}..., 策略={strategy}, 最大結果={max_results}",
        })

    async def on_validation_start(self):
        """Validation has started."""
        await self._send("activity_log", {
            "level": "info",
            "message": "開始驗證引用完整性",
        })

    async def on_validation_complete(self, is_valid: bool = True, issues: list[str] = None, **kwargs):
        """Validation completed."""
        # Handle both old and new parameter names
        passed = kwargs.get('passed', is_valid)
        if passed:
            await self._send("activity_log", {
                "level": "success",
                "message": "引用完整性驗證通過",
            })
        else:
            await self._send("activity_log", {
                "level": "warning",
                "message": f"驗證發現問題: {', '.join(issues or [])}",
            })

    async def on_citations_extracted(self, citations: list[LegalCitation]):
        """Citations have been extracted."""
        await self._send("activity_log", {
            "level": "info",
            "message": f"提取 {len(citations)} 個引用來源",
        })

    async def on_answer_generation_complete(self, answer: LegalAnswer):
        """Answer generation completed."""
        confidence = answer.confidence.value if hasattr(answer.confidence, 'value') else str(answer.confidence)
        await self._send("activity_log", {
            "level": "success",
            "message": f"答案生成完成 - 信心度: {confidence}",
        })

    async def on_clarification_requested(self, questions: list[str]):
        """Clarification questions requested."""
        await self._send("activity_log", {
            "level": "warning",
            "message": f"需要澄清: {', '.join(questions)}",
        })


@router.websocket("/ws/upload")
async def websocket_upload_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming upload and indexing progress.

    Message Protocol:
    - Client sends: {"type": "upload_start", "filename": "file.txt", "content": "base64...", "auto_index": true, "extract_metadata": false}
    - Server streams: Progress updates for upload, indexing, metadata extraction
    - Server sends final: {"type": "upload_complete", "document": {...}}
    """
    # Accept WebSocket connection without origin validation
    # CORS is already handled by middleware for HTTP requests
    # For WebSockets, we accept all connections (safe for development)
    await websocket.accept()
    logger.info("WebSocket connection established for upload")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "upload_start":
                # Import here to avoid circular dependencies
                import base64
                import uuid
                from pathlib import Path
                from datetime import timezone
                from finagent.document_processing.loader import DocumentLoader
                from finagent.document_processing.indexer import DocumentIndexer
                from finagent.document_processing.metadata_store import DocumentMetadata, get_metadata_store

                filename = data.get("filename")
                content_b64 = data.get("content")
                auto_index = data.get("auto_index", False)
                extract_metadata = data.get("extract_metadata", False)

                if not filename or not content_b64:
                    await websocket.send_json({
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "payload": {"message": "Missing filename or content"},
                    })
                    continue

                # Progress: Start upload
                await websocket.send_json({
                    "type": "progress",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {
                        "stage": "uploading",
                        "message": f"上傳文件: {filename}",
                        "progress": 0,
                    },
                })

                try:
                    # Decode base64 content
                    content = base64.b64decode(content_b64)

                    # Validate file type
                    if not filename.endswith(".txt"):
                        await websocket.send_json({
                            "type": "error",
                            "timestamp": datetime.now().isoformat(),
                            "payload": {"message": "Only .txt files are supported"},
                        })
                        continue

                    # Generate document ID
                    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

                    # Save file to disk
                    DOCUMENTS_PATH = Path("data/documents")
                    DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)
                    file_path = DOCUMENTS_PATH / filename

                    # Handle duplicate filenames
                    if file_path.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        stem = file_path.stem
                        suffix = file_path.suffix
                        file_path = DOCUMENTS_PATH / f"{stem}_{timestamp}{suffix}"

                    with open(file_path, "wb") as f:
                        f.write(content)

                    # Progress: File saved
                    await websocket.send_json({
                        "type": "progress",
                        "timestamp": datetime.now().isoformat(),
                        "payload": {
                            "stage": "uploaded",
                            "message": f"文件已儲存: {file_path.name}",
                            "progress": 25,
                        },
                    })

                    # Create metadata
                    now = datetime.now(timezone.utc).isoformat()
                    metadata = DocumentMetadata(
                        doc_id=doc_id,
                        filename=filename,
                        description=f"Uploaded file: {filename}",
                        document_type="uploaded",
                        keywords=[],
                        date=None,
                        issuing_authority=None,
                        related_institutions=[],
                        penalty_amount=None,
                        violation_types=[],
                        custom_fields={},
                        indexed=False,
                        chunk_count=0,
                        created_at=now,
                        updated_at=now,
                    )

                    # Save metadata
                    store = get_metadata_store()
                    store.add_metadata(metadata, str(file_path))

                    # Progress: Metadata saved
                    await websocket.send_json({
                        "type": "progress",
                        "timestamp": datetime.now().isoformat(),
                        "payload": {
                            "stage": "metadata_saved",
                            "message": "元數據已儲存",
                            "progress": 40,
                        },
                    })

                    # Auto-index if requested
                    if auto_index:
                        # Progress: Starting indexing
                        await websocket.send_json({
                            "type": "progress",
                            "timestamp": datetime.now().isoformat(),
                            "payload": {
                                "stage": "indexing",
                                "message": "正在建立向量索引...",
                                "progress": 50,
                            },
                        })

                        loader = DocumentLoader()
                        document = loader.load_txt(file_path.name)

                        indexer = DocumentIndexer(extract_metadata=extract_metadata)

                        # Progress: Indexing in progress
                        await websocket.send_json({
                            "type": "progress",
                            "timestamp": datetime.now().isoformat(),
                            "payload": {
                                "stage": "indexing",
                                "message": "分析文件內容...",
                                "progress": 60,
                            },
                        })

                        num_chunks = await indexer.index_document(document)

                        # Progress: Indexing complete
                        await websocket.send_json({
                            "type": "progress",
                            "timestamp": datetime.now().isoformat(),
                            "payload": {
                                "stage": "indexed",
                                "message": f"索引完成 ({num_chunks} 個區塊)",
                                "progress": 80,
                                "chunks": num_chunks,
                            },
                        })

                        # Update metadata
                        store.update_metadata(doc_id, {
                            "indexed": True,
                            "chunk_count": num_chunks,
                        })
                        metadata.indexed = True
                        metadata.chunk_count = num_chunks

                    # Progress: Complete
                    await websocket.send_json({
                        "type": "upload_complete",
                        "timestamp": datetime.now().isoformat(),
                        "payload": {
                            "document": {
                                "id": metadata.doc_id,
                                "name": metadata.filename,
                                "status": "indexed" if metadata.indexed else "pending",
                                "chunk_count": metadata.chunk_count,
                                "indexed": metadata.indexed,
                                "created_at": metadata.created_at,
                            },
                            "message": "上傳完成!" if auto_index else "上傳完成 (未索引)",
                            "progress": 100,
                        },
                    })

                except Exception as e:
                    logger.error(f"Upload error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "payload": {"message": str(e)},
                    })

            elif data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {},
                })

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed for upload")
    except Exception as e:
        logger.error(f"WebSocket error in upload: {e}", exc_info=True)


@router.websocket("/ws/query")
async def websocket_query_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming query progress.

    Message Protocol:
    - Client sends: {"type": "query", "text": "查詢文字"}
    - Server streams: Various update messages (step_update, todo_update, etc.)
    - Server sends final: {"type": "query_complete", "result": {...}}
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive query from client
            data = await websocket.receive_json()

            if data.get("type") == "query":
                query_text = data.get("text", "")
                use_plan_execute = data.get("use_plan_execute", False)
                use_wiki_search = data.get("use_wiki_search", False)
                
                if not query_text:
                    await websocket.send_json({
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "payload": {"message": "Query text is required"},
                    })
                    continue

                # Create UICallback for this WebSocket connection
                callback = WebSocketUICallback(websocket)

                # Initialize orchestrator with callback
                orchestrator = AgentOrchestrator(
                    enable_query_logging=True,
                    ui_callback=callback,
                )

                # Process query
                query = Query(text=query_text)

                await websocket.send_json({
                    "type": "query_started",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {"query": query_text},
                })

                # Send initial step update immediately to show progress
                await callback.on_analysis_start(query)

                try:
                    # Process query with real-time streaming
                    start_time = datetime.now()
                    answer = None
                    final_plan = None
                    
                    # For Plan-and-Execute flow
                    final_response_text = None

                    # Map LangGraph node names to UI step names
                    node_to_step = {
                        # Standard Flow
                        "query_analysis": "planning",
                        "planning": "planning",
                        "action": "action",
                        "validation": "validation",
                        "reference_guard": "validation",
                        "answer": "answer",
                        
                        # Plan-and-Execute Flow
                        "planner": "planning",
                        "executor": "action",
                        "replanner": "validation", 
                        "reporter": "answer", 
                        
                        # Wiki Search Flow
                        "search": "action",
                        "synthesize": "answer",
                    }

                    last_node = None

                    # Stream workflow execution directly (async)
                    try:
                        async for node_name, state_update in orchestrator.stream_query(
                            query, 
                            enable_demo_delay=ENABLE_DEMO_DELAY,
                            use_plan_execute=use_plan_execute,
                            use_wiki_search=use_wiki_search
                        ):
                            step_name = node_to_step.get(node_name, None)
                            current_time = datetime.now()

                            if step_name and step_name != last_node:
                                # Mark previous step as done
                                if last_node and last_node in callback.step_start_times:
                                    elapsed = int((current_time - callback.step_start_times[last_node]).total_seconds() * 1000)
                                    await callback._send("step_update", {
                                        "step": last_node,
                                        "status": "done",
                                        "description": f"{last_node} 完成",
                                        "elapsed_ms": elapsed,
                                    })

                                # Start new step
                                callback.step_start_times[step_name] = current_time
                                callback.current_step = step_name

                                step_descriptions = {
                                    "planning": "分析查詢意圖與規劃",
                                    "action": "執行檢索任務",
                                    "validation": "驗證與重新規劃",
                                    "answer": "生成最終答案",
                                }

                                await callback._send("step_update", {
                                    "step": step_name,
                                    "status": "active",
                                    "description": step_descriptions.get(step_name, step_name),
                                    "elapsed_ms": 0,
                                })

                                await callback._send("activity_log", {
                                    "level": "info",
                                    "message": f"執行節點: {node_name}",
                                })

                                last_node = step_name

                                # Small delay to ensure messages are sent one at a time
                                await asyncio.sleep(0.01)

                            # --- Standard Flow Handling ---
                            # Extract plan data when planning completes
                            if node_name == "planning" and "plan" in state_update:
                                final_plan = state_update.get("plan")
                                if final_plan:
                                    await callback._send("plan_created", final_plan)
                                    await callback._send("activity_log", {
                                        "level": "success",
                                        "message": f"研究計畫建立完成，共 {len(final_plan.get('tasks', []))} 項任務",
                                    })

                            # Extract answer when complete
                            if "answer" in state_update and state_update["answer"]:
                                answer = state_update["answer"]
                                
                            # --- Plan-and-Execute Flow Handling ---
                            if use_plan_execute:
                                if node_name == "planner" and "plan" in state_update:
                                    # Convert Plan object to UI format
                                    plan_obj = state_update["plan"]
                                    tasks = []
                                    if hasattr(plan_obj, "tasks"):
                                        for task in plan_obj.tasks:
                                            tasks.append({
                                                "id": task.id,
                                                "description": task.description,
                                                "tool": task.tool,
                                                "status": "pending"
                                            })
                                        
                                        # Send plan update
                                        await callback._send("plan_created", {
                                            "tasks": tasks,
                                            "summary": "Plan-and-Execute Strategy",
                                            # Add required fields for frontend ResearchPlan interface
                                            "analysis": {
                                                "keywords": ["Plan-and-Execute"],
                                                "must_have_keywords": [],
                                                "entity_type": "general",
                                                "jurisdiction": "TW",
                                                "time_period": None,
                                                "query_type": "complex",
                                                "complexity": "complex"
                                            },
                                            "max_results": 10,
                                            "use_hard_search": False,
                                            "estimated_total_time": 60
                                        })
                                        
                                if node_name == "executor" and "past_steps" in state_update:
                                    # Log tool executions
                                    past_steps = state_update["past_steps"]
                                    if past_steps:
                                        last_step = past_steps[-1]
                                        # last_step is (task_dict, result)
                                        task_info = last_step[0]
                                        result_info = last_step[1]
                                        
                                        await callback._send("activity_log", {
                                            "level": "info",
                                            "message": f"執行任務: {task_info.get('description')} -> 完成",
                                        })
                                        
                                if node_name == "replanner":
                                    if "response" in state_update and state_update["response"]:
                                        final_response_text = state_update["response"]
                                        # Transition to answer step
                                        await callback._send("step_update", {
                                            "step": "answer",
                                            "status": "active",
                                            "description": "生成最終答案",
                                            "elapsed_ms": 0,
                                        })
                                    elif "plan" in state_update:
                                        await callback._send("activity_log", {
                                            "level": "info",
                                            "message": "重新規劃: 添加新任務",
                                        })
                                        
                                if node_name == "reporter" and "response" in state_update:
                                    final_response_text = state_update["response"]
                                    await callback._send("activity_log", {
                                        "level": "success",
                                        "message": "報告生成完成",
                                    })
                                        
                            # --- Wiki Search Flow Handling ---
                            if use_wiki_search:
                                if node_name == "search" and "documents" in state_update:
                                    docs = state_update["documents"]
                                    await callback._send("activity_log", {
                                        "level": "success",
                                        "message": f"Wiki Search: Found {len(docs)} documents",
                                    })
                                    
                                if node_name == "synthesize" and "response" in state_update:
                                    final_response_text = state_update["response"]
                                    # Wiki search result is the final answer
                                    result = {
                                        "summary": "Wiki Search Result",
                                        "key_findings": ["See detailed report"],
                                        "detailed_analysis": final_response_text,
                                        "confidence": "HIGH",
                                        "citations": [] 
                                    }
                                    
                                    await callback._send("query_complete", {"result": result})
                                    return

                        total_time = int((datetime.now() - start_time).total_seconds() * 1000)

                        # Mark final step as done
                        if last_node and last_node in callback.step_start_times:
                            elapsed = int((datetime.now() - callback.step_start_times[last_node]).total_seconds() * 1000)
                            await callback._send("step_update", {
                                "step": last_node,
                                "status": "done",
                                "description": f"{last_node} 完成",
                                "elapsed_ms": elapsed,
                            })

                        # Construct final result
                        result = None
                        
                        if use_plan_execute:
                            if final_response_text:
                                result = {
                                    "summary": "Plan-and-Execute Result",
                                    "key_findings": ["See detailed analysis"],
                                    "detailed_analysis": final_response_text,
                                    "confidence": "HIGH",
                                    "processing_time_ms": total_time,
                                    "citations": [] # Citations not yet implemented in P&E flow
                                }
                            else:
                                raise Exception("Plan-and-Execute flow did not produce a response")
                        else:
                            if not answer:
                                raise Exception("工作流程未生成答案")
                                
                            result = {
                                "summary": answer.executive_summary,
                                "key_findings": answer.key_findings,
                                "detailed_analysis": answer.detailed_analysis,
                                "confidence": answer.confidence_score.value if hasattr(answer.confidence_score, 'value') else str(answer.confidence_score),
                                "processing_time_ms": answer.processing_time_ms or 0,
                                "citations": [
                                    {
                                        "id": c.id,
                                        "source": c.formatted_citation or c.title,
                                        "authority": c.authority.value if hasattr(c.authority, 'value') else str(c.authority),
                                        "citation_type": c.type.value if hasattr(c.type, 'value') else str(c.type),
                                        "date": c.date,
                                        "relevance": 1.0,
                                    }
                                    for c in answer.citations
                                ],
                            }

                        await callback._send("activity_log", {
                            "level": "success",
                            "message": f"查詢完成，共耗時 {total_time/1000:.1f} 秒",
                        })

                        await websocket.send_json({
                            "type": "query_complete",
                            "timestamp": datetime.now().isoformat(),
                            "payload": result,
                        })

                    except Exception as e:
                        logger.error(f"Error processing query: {e}", exc_info=True)
                        await callback.on_error(str(e))
                        await websocket.send_json({
                            "type": "query_failed",
                            "timestamp": datetime.now().isoformat(),
                            "payload": {"error": str(e)},
                        })

                except Exception as e:
                    logger.error(f"Error processing query: {e}", exc_info=True)
                    await callback.on_error(str(e))
                    await websocket.send_json({
                        "type": "query_failed",
                        "timestamp": datetime.now().isoformat(),
                        "payload": {"error": str(e)},
                    })

            elif data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                    "payload": {},
                })

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
