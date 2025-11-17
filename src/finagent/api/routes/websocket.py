"""
WebSocket API for real-time query progress streaming.
"""

import asyncio
import json
import logging
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
                "id": str(todo.id) if hasattr(todo, 'id') else str(hash(todo.description)),
                "description": todo.description,
                "status": todo.status.value if hasattr(todo.status, 'value') else str(todo.status),
                "priority": todo.priority if hasattr(todo, 'priority') else 1,
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
            "id": str(todo.id) if hasattr(todo, 'id') else str(hash(todo.description)),
            "status": "in_progress",
            "description": todo.description,
        })
        await self._send("activity_log", {
            "level": "info",
            "message": f"開始任務: {todo.description}",
        })

    async def on_todo_progress(self, todo: TodoItem, percentage: int, message: str = ""):
        """Progress update for a todo item."""
        await self._send("todo_item_update", {
            "id": str(todo.id) if hasattr(todo, 'id') else str(hash(todo.description)),
            "status": "in_progress",
            "progress": percentage,
            "message": message,
        })

    async def on_todo_completed(self, todo: TodoItem):
        """A todo item has completed."""
        await self._send("todo_item_update", {
            "id": str(todo.id) if hasattr(todo, 'id') else str(hash(todo.description)),
            "status": "completed",
            "description": todo.description,
        })
        await self._send("activity_log", {
            "level": "success",
            "message": f"完成任務: {todo.description}",
        })

    async def on_todo_failed(self, todo: TodoItem, error: str):
        """A todo item has failed."""
        await self._send("todo_item_update", {
            "id": str(todo.id) if hasattr(todo, 'id') else str(hash(todo.description)),
            "status": "failed",
            "error": error,
        })
        await self._send("activity_log", {
            "level": "error",
            "message": f"任務失敗: {todo.description} - {error}",
        })

    async def on_retrieval_result(self, strategy: str, count: int, total_chunks: int):
        """RAG retrieval completed."""
        await self._send("activity_log", {
            "level": "info",
            "message": f"檢索完成: {count} 相關文件 (共 {total_chunks} 區塊)",
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

                try:
                    answer = await orchestrator.process_query(query)

                    # Mark answer step as done
                    elapsed = int((datetime.now() - callback.step_start_times.get("answer", datetime.now())).total_seconds() * 1000)
                    await callback._send("step_update", {
                        "step": "answer",
                        "status": "done",
                        "description": "答案生成完成",
                        "elapsed_ms": elapsed,
                    })

                    # Send complete result
                    result = {
                        "summary": answer.summary,
                        "key_findings": answer.key_findings,
                        "detailed_analysis": answer.detailed_analysis,
                        "confidence": answer.confidence.value if hasattr(answer.confidence, 'value') else str(answer.confidence),
                        "processing_time_ms": answer.processing_time_ms,
                        "citations": [
                            {
                                "id": i + 1,
                                "source": c.source,
                                "authority": c.authority.value if hasattr(c.authority, 'value') else str(c.authority),
                                "citation_type": c.citation_type.value if hasattr(c.citation_type, 'value') else str(c.citation_type),
                                "date": c.date,
                                "relevance": c.relevance,
                            }
                            for i, c in enumerate(answer.citations)
                        ],
                    }

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
