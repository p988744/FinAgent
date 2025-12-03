"""Agent orchestrator for coordinating the multi-agent workflow."""

import logging
from datetime import datetime

from finagent.agents.deep_agent import create_finagent_deep_agent
from finagent.agents.plan_execute.graph import PlanExecuteWorkflow
from finagent.agents.query_memo import QueryMemoLogger
from finagent.agents.wiki_builder.graph import WikiBuilderWorkflow
from finagent.agents.wiki_search.graph import WikiSearchWorkflow
from finagent.config import settings
from finagent.document_processing import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.models.answers import ConfidenceLevel, LegalAnswer
from finagent.models.citations import CitationAuthority, CitationType, LegalCitation
from finagent.models.queries import Query

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the multi-agent research workflow.

    Supports three primary workflow modes:
    1. Plan-Execute (v1.1): Planner → Executor → Replanner → Reporter workflow
    2. Wiki Search: Specialized document browsing
    3. Deep Agent (v2.0): Claude Code-like capabilities with task planning, sub-agents, and context management

    Available Tools (Research Workflow):
    - retriever: Semantic vector search (best for conceptual queries)
    - hard_search: Exact keyword matching (best for specific terms)
    - hybrid_search: BM25 + Vector hybrid (recommended default - combines both)

    Deep Agent Capabilities:
    - write_todos: Built-in task planning
    - task: Sub-agent delegation (rag_researcher, legal_analyzer, penalty_comparator)
    - semantic_search, keyword_search, hybrid_search: RAG tools

    Coordinates Planning → Action → Validation → Answer agents.
    """

    def __init__(
        self,
        enable_query_logging: bool = True,
        clarification_handler=None,
        ui_callback=None,
    ):
        """
        Initialize orchestrator with LangGraph workflow.

        Args:
            enable_query_logging: Whether to log queries to database (default: True)
            clarification_handler: Optional async callback for user clarification
                                   Signature: async def handler(clarification_request) -> str
            ui_callback: Optional UICallback for progress updates
        """
        self.logger = logger
        self.enable_query_logging = enable_query_logging
        self.clarification_handler = clarification_handler
        self.ui_callback = ui_callback

        # Initialize query memo logger
        if enable_query_logging:
            self.query_logger = QueryMemoLogger()
        else:
            self.query_logger = None

        # Initialize RAG retriever
        try:
            self.retriever = DocumentRetriever(collection_name="legal_documents")
            self.use_rag = self.retriever.collection_exists()
            if self.use_rag:
                self.logger.info("RAG retriever initialized successfully")

                # Initialize Plan-and-Execute workflow (v1.1 - primary workflow)
                self.hard_searcher = HardSearcher(db_path="data/finagent.db")
                self.plan_execute_workflow = PlanExecuteWorkflow(
                    retriever=self.retriever,
                    hard_searcher=self.hard_searcher
                )

                # Initialize Wiki Search workflow (specialized browsing)
                self.wiki_search_workflow = WikiSearchWorkflow(retriever=self.retriever)

                # Initialize Wiki Builder workflow (document processing)
                self.wiki_builder_workflow = WikiBuilderWorkflow()

                # Initialize Deep Agent (v2.0 - advanced workflow)
                try:
                    self.deep_agent = create_finagent_deep_agent(
                        enable_subagents=True,
                        enable_filesystem=False,  # Disabled for security
                    )
                    self.logger.info("Deep Agent initialized successfully")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize Deep Agent: {e}")
                    self.deep_agent = None

                self.logger.info("v1.2 LangGraph workflows initialized successfully (Plan-Execute, WikiSearch, WikiBuilder, DeepAgent)")
            else:
                self.logger.warning("Vector database is empty, using fallback mode")
                self.plan_execute_workflow = None
                self.wiki_search_workflow = None
                self.wiki_builder_workflow = WikiBuilderWorkflow()  # Builder works without RAG
                self.deep_agent = None
        except Exception as e:
            self.logger.warning(f"Failed to initialize RAG retriever: {e}, using fallback mode")
            self.retriever = None
            self.plan_execute_workflow = None
            self.wiki_search_workflow = None
            self.wiki_builder_workflow = WikiBuilderWorkflow()  # Builder works without RAG
            self.deep_agent = None
            self.use_rag = False

    async def process_query(self, query: Query) -> LegalAnswer:
        """
        Process a legal research query using the v1.1 Plan-and-Execute workflow.

        Args:
            query: User query

        Returns:
            Legal answer with citations

        Workflow (LangGraph v1.1):
            START → QueryAnalyzer → Planner → Executor → Replanner → Reporter → END
        """
        start_time = datetime.now()
        self.logger.info(f"Processing query with v1.1 Plan-and-Execute workflow: {query.text[:100]}...")

        try:
            # Use v1.1 Plan-and-Execute workflow if available, otherwise use fallback
            if self.use_rag and self.plan_execute_workflow:
                answer = await self._process_with_plan_execute(query)
            else:
                answer = await self._generate_mock_answer(query)

            # Calculate processing time
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            answer.processing_time_ms = processing_time_ms

            self.logger.info(f"Query processed successfully in {processing_time_ms}ms")
            return answer

        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise

    async def _process_with_langgraph(self, query: Query) -> LegalAnswer:
        """
        Process query using LangGraph multi-agent workflow.

        Args:
            query: User query

        Returns:
            LegalAnswer generated by workflow
        """
        self.logger.info("Processing query with LangGraph workflow")

        # Start query logging
        if self.query_logger:
            self.query_logger.start_query()

        # Initialize state
        initial_state: dict = {
            "query": query,
            "plan": None,
            "plan_analysis": None,  # Query analysis results
            "research_tasks": None,
            "retrieved_chunks": None,
            "citations": None,
            "validation_passed": False,
            "validation_issues": None,
            "answer": None,
            "search_iteration": 0,  # Start at iteration 0
            "max_search_iterations": 2,  # Max 2 re-searches
            "search_strategy": "strict",  # Start with strict strategy
            "processing_steps": [],
            "errors": [],
        }

        try:
            # Run workflow
            final_state = self.workflow.run(initial_state)

            # Extract answer from final state
            answer = final_state.get("answer")

            if not answer:
                # Workflow failed to generate answer
                if self.query_logger:
                    self.query_logger.log_query(
                        query=query,
                        answer=None,
                        state=final_state,
                        model_used=settings.llm_model,
                        success=False,
                        error_message="工作流程失敗",
                    )
                return await self._generate_fallback_answer(query, "工作流程失敗")

            # Log processing steps for debugging
            if final_state.get("processing_steps"):
                for step in final_state["processing_steps"]:
                    self.logger.info(f"Workflow step: {step}")

            if final_state.get("errors"):
                for error in final_state["errors"]:
                    self.logger.warning(f"Workflow error: {error}")

            # Log successful query
            if self.query_logger:
                history_id = self.query_logger.log_query(
                    query=query,
                    answer=answer,
                    state=final_state,
                    model_used=settings.llm_model,
                    success=True,
                )
                self.logger.info(f"Query logged to database with ID {history_id}")

            return answer

        except Exception as e:
            # Log failed query
            if self.query_logger:
                self.query_logger.log_query(
                    query=query,
                    answer=None,
                    state=initial_state,
                    model_used=settings.llm_model,
                    success=False,
                    error_message=str(e),
                )
            raise

    async def _process_with_plan_execute(self, query: Query) -> LegalAnswer:
        """
        Process query using v1.1 Plan-and-Execute LangGraph workflow.

        Args:
            query: User query

        Returns:
            LegalAnswer generated by v1.1 workflow
        """
        self.logger.info("Processing query with v1.1 Plan-and-Execute workflow")

        # Start query logging
        if self.query_logger:
            self.query_logger.start_query()

        # Initialize state for v1.1 workflow
        initial_state = {
            "input": query.text,
            "query_insight": None,
            "plan": None,
            "past_steps": [],
            "response": None,
            "scratchpad": []
        }

        try:
            # Run v1.1 workflow
            final_state = None
            async for event in self.plan_execute_workflow.graph.astream(initial_state):
                for node_name, state_update in event.items():
                    self.logger.debug(f"Node: {node_name}, Update: {state_update.keys()}")
                    if final_state is None:
                        final_state = state_update.copy()
                    else:
                        final_state.update(state_update)

                    # Send progress updates via ui_callback
                    if self.ui_callback:
                        await self._send_progress_update(node_name, state_update, final_state)

            if final_state is None:
                final_state = initial_state

            # Extract response from final state
            response_text = final_state.get("response")

            if not response_text:
                # Workflow failed to generate response
                if self.query_logger:
                    self.query_logger.log_query(
                        query=query,
                        answer=None,
                        state=final_state,
                        model_used=settings.llm_model,
                        success=False,
                        error_message="v1.1 workflow failed to generate response",
                    )
                return await self._generate_fallback_answer(query, "v1.1 workflow failed")

            # Convert v1.1 response to LegalAnswer format
            answer = self._convert_plan_execute_response(query, response_text, final_state)

            # Log successful query
            if self.query_logger:
                # Convert Pydantic models to dict for JSON serialization
                serializable_state = {}
                for key, value in final_state.items():
                    if hasattr(value, 'dict'):
                        # Pydantic model
                        serializable_state[key] = value.dict()
                    elif hasattr(value, '__dict__'):
                        # Other objects with __dict__
                        serializable_state[key] = vars(value)
                    else:
                        serializable_state[key] = value

                history_id = self.query_logger.log_query(
                    query=query,
                    answer=answer,
                    state=serializable_state,
                    model_used=settings.llm_model,
                    success=True,
                )
                self.logger.info(f"Query logged to database with ID {history_id}")

            return answer

        except Exception as e:
            # Log failed query
            if self.query_logger:
                self.query_logger.log_query(
                    query=query,
                    answer=None,
                    state=initial_state,
                    model_used=settings.llm_model,
                    success=False,
                    error_message=str(e),
                )
            raise

    def _convert_plan_execute_response(
        self, query: Query, response_text: str, state: dict
    ) -> LegalAnswer:
        """
        Convert v1.1 Plan-and-Execute response to LegalAnswer format.

        Args:
            query: Original query
            response_text: Generated response text
            state: Final workflow state

        Returns:
            LegalAnswer object
        """
        # Extract past steps
        past_steps = state.get("past_steps", [])

        # Parse response to extract sections
        lines = response_text.split("\n")
        executive_summary = ""
        key_findings = []
        detailed_analysis = response_text

        # Try to parse structured response
        current_section = None
        summary_lines = []
        findings_lines = []

        for line in lines:
            line_lower = line.lower().strip()
            if "executive summary" in line_lower or "執行摘要" in line_lower:
                current_section = "summary"
            elif "key finding" in line_lower or "關鍵發現" in line_lower:
                current_section = "findings"
            elif "analysis" in line_lower or "分析" in line_lower:
                current_section = "analysis"
            elif current_section == "summary" and line.strip():
                summary_lines.append(line.strip())
            elif current_section == "findings" and line.strip() and (line.strip().startswith("-") or line.strip().startswith("•") or line.strip().startswith("*")):
                findings_lines.append(line.strip().lstrip("-•* "))

        # Use parsed sections if available
        if summary_lines:
            executive_summary = " ".join(summary_lines)
        else:
            # Use first paragraph as summary
            paragraphs = [p.strip() for p in response_text.split("\n\n") if p.strip()]
            executive_summary = paragraphs[0] if paragraphs else response_text[:200]

        if findings_lines:
            key_findings = findings_lines[:5]  # Limit to 5
        else:
            # Extract from past steps
            key_findings = [f"任務 {i}: {task.get('description', 'Unknown')}"
                          for i, (task, result) in enumerate(past_steps[:3], 1)]

        # Extract citations from past steps
        citations = self._extract_citations_from_steps(past_steps)

        # Determine confidence based on results
        if len(past_steps) >= 2 and len(citations) > 0:
            confidence_score = ConfidenceLevel.HIGH
            confidence_explanation = f"執行了 {len(past_steps)} 個研究任務，找到 {len(citations)} 個引用來源"
        elif len(past_steps) >= 1:
            confidence_score = ConfidenceLevel.MEDIUM
            confidence_explanation = f"執行了 {len(past_steps)} 個研究任務，資料來源有限"
        else:
            confidence_score = ConfidenceLevel.LOW
            confidence_explanation = "研究任務執行不足，結果可能不完整"

        return LegalAnswer(
            executive_summary=executive_summary[:1000],  # Limit length
            key_findings=key_findings if key_findings else ["查詢已完成"],
            detailed_analysis=detailed_analysis,
            citations=citations,
            confidence_score=confidence_score,
            confidence_explanation=confidence_explanation,
            limitations=["此為 v1.1 Plan-and-Execute workflow 自動生成結果"],
            processing_steps=[f"Step {i}: {task.get('description', 'Unknown')}"
                            for i, (task, _) in enumerate(past_steps, 1)],
        )

    def _extract_citations_from_steps(self, past_steps: list) -> list[LegalCitation]:
        """
        Extract citations from v1.1 workflow execution steps.

        Args:
            past_steps: List of (task, result) tuples

        Returns:
            List of LegalCitation objects
        """
        citations = []
        seen_sources = set()

        for idx, (task, result) in enumerate(past_steps, 1):
            # Parse result to find source documents
            if not result or not isinstance(result, str):
                continue

            # Look for [N] Source: pattern
            import re
            source_pattern = r'\[(\d+)\]\s*Source:\s*([^\n]+)'
            matches = re.findall(source_pattern, result)

            for match_num, source_name in matches:
                if source_name not in seen_sources:
                    seen_sources.add(source_name)
                    citation = LegalCitation(
                        id=len(citations) + 1,
                        type=CitationType.ENFORCEMENT_DOCUMENT,
                        authority=CitationAuthority.PRIMARY,
                        title=source_name.strip(),
                        formatted_citation=f"[{len(citations) + 1}] {source_name.strip()}",
                        issuing_authority="金管會",
                    )
                    citations.append(citation)

        return citations

    async def stream_query(self, query: Query, enable_demo_delay: bool = False, use_plan_execute: bool = False, use_wiki_search: bool = False, use_deep_agent: bool = False):
        """
        Stream query processing, yielding events for each workflow step.

        Args:
            query: User query
            enable_demo_delay: If True, add delays for demo/testing purposes (default: False)
            use_plan_execute: If True, use the new Plan-and-Execute workflow (default: False)
            use_wiki_search: If True, use the Wiki Search workflow (default: False)
            use_deep_agent: If True, use the Deep Agent workflow (default: False)

        Yields:
            Tuples of (node_name, state_update) for each step
        """
        if not self.use_rag or not self.plan_execute_workflow:
            return

        mode_name = "Plan-and-Execute (v1.1)"
        if use_deep_agent:
            mode_name = "Deep Agent (v2.0)"
        elif use_wiki_search:
            mode_name = "Wiki Search"

        self.logger.info(f"Streaming query with {mode_name} workflow (demo_delay={enable_demo_delay})")

        # Deep Agent workflow
        if use_deep_agent and self.deep_agent:
            try:
                async for chunk in self.stream_deep_agent(query):
                    # Convert Deep Agent chunks to the expected format
                    yield "deep_agent", chunk
            except Exception as e:
                self.logger.error(f"Streaming Deep Agent query failed: {e}", exc_info=True)
                raise
            return

        if use_wiki_search and self.wiki_search_workflow:
            # Wiki Search Workflow
            initial_state = {
                "input": query.text,
                "documents": [],
                "response": ""
            }

            try:
                async for event in self.wiki_search_workflow.graph.astream(initial_state):
                    for node_name, state_update in event.items():
                        yield node_name, state_update
            except Exception as e:
                self.logger.error(f"Streaming Wiki Search query failed: {e}", exc_info=True)
                raise

        else:
            # Default to Plan-and-Execute Workflow (v1.1)
            initial_state = {
                "input": query.text,
                "query_insight": None,
                "plan": None,
                "past_steps": [],
                "response": None,
                "scratchpad": []
            }

            # Start query logging
            if self.query_logger:
                self.query_logger.start_query()

            try:
                # Stream v1.1 workflow execution
                async for event in self.plan_execute_workflow.graph.astream(initial_state):
                    for node_name, state_update in event.items():
                        yield node_name, state_update

                # Log successful query (if logger is enabled)
                if self.query_logger:
                    # Note: We don't have the final answer here in streaming mode
                    # Logging would need to be done by the caller
                    pass

            except Exception as e:
                self.logger.error(f"Streaming Plan-and-Execute query failed: {e}", exc_info=True)
                if self.query_logger:
                    self.query_logger.log_query(
                        query=query,
                        answer=None,
                        state=initial_state,
                        model_used=settings.llm_model,
                        success=False,
                        error_message=str(e),
                    )
                raise

    async def _process_with_rag(self, query: Query) -> LegalAnswer:
        """
        Process query using RAG pipeline with real documents.

        Args:
            query: User query

        Returns:
            LegalAnswer generated from retrieved documents
        """
        self.logger.info("Processing query with RAG pipeline")

        # Retrieve relevant document chunks
        retrieved_chunks = self.retriever.retrieve(
            query=query.text, n_results=query.max_results or 5
        )

        if not retrieved_chunks:
            self.logger.warning("No relevant documents found")
            return await self._generate_fallback_answer(query, "未找到相關文件")

        self.logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks")

        # Extract citations from retrieved documents
        citations = self._extract_citations(retrieved_chunks)

        # Generate answer from retrieved context
        answer = self._synthesize_answer(query, retrieved_chunks, citations)

        return answer

    def _extract_citations(self, chunks) -> list[LegalCitation]:
        """
        Extract citations from retrieved document chunks.

        Args:
            chunks: List of RetrievedChunk objects

        Returns:
            List of LegalCitation objects
        """
        citations = []
        seen_docs = set()

        for idx, chunk in enumerate(chunks, 1):
            doc_id = chunk.doc_id

            # Avoid duplicate citations from same document
            if doc_id in seen_docs:
                continue
            seen_docs.add(doc_id)

            # Extract metadata
            filename = chunk.metadata.get("filename", "未知文件")
            source = chunk.metadata.get("source", "")

            # Create citation
            citation = LegalCitation(
                id=idx,
                type=CitationType.ENFORCEMENT_DOCUMENT,
                authority=CitationAuthority.PRIMARY,
                title=filename,
                formatted_citation=f"{filename}",
                issuing_authority="金管會",
                source_url=source if source.startswith("http") else None,
            )

            citations.append(citation)

        return citations

    def _synthesize_answer(
        self, query: Query, chunks, citations: list[LegalCitation]
    ) -> LegalAnswer:
        """
        Synthesize answer from retrieved chunks.

        Args:
            query: User query
            chunks: Retrieved document chunks
            citations: Extracted citations

        Returns:
            Synthesized LegalAnswer
        """
        # Format context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[文件{i}] {chunk.text}")

        full_context = "\n\n".join(context_parts)

        # Extract key information
        key_findings = []
        for i, chunk in enumerate(chunks[:3], 1):  # Top 3 chunks
            # Simple extraction - in production, use LLM for better summarization
            first_sentence = chunk.text.split("。")[0] + "。"
            key_findings.append(f"{first_sentence} [引用{i}]")

        # Generate executive summary
        if "裁罰" in query.text or "罰鍰" in query.text:
            executive_summary = f"根據相關文件，找到 {len(chunks)} 筆與裁罰相關的資訊。"
        elif "洗錢" in query.text:
            executive_summary = f"找到 {len(chunks)} 筆洗錢防制相關的裁罰案件資訊。"
        elif "內線交易" in query.text:
            executive_summary = f"找到 {len(chunks)} 筆內線交易相關的裁罰案件資訊。"
        else:
            executive_summary = f"根據查詢「{query.text}」，找到 {len(chunks)} 筆相關法律文件。"

        # Detailed analysis is the concatenated context
        detailed_analysis = (
            f"## 檢索結果\n\n"
            f"共找到 {len(chunks)} 筆相關文件片段，以下為詳細內容：\n\n"
            f"{full_context}\n\n"
            f"## 分析說明\n\n"
            f"以上資訊來自 {len(citations)} 份主要來源文件。"
            f"所有引用均為官方裁罰文件，具有高度權威性。"
        )

        # Calculate confidence based on number of results
        if len(chunks) >= 3:
            confidence_score = ConfidenceLevel.HIGH
            confidence_explanation = f"找到 {len(chunks)} 筆相關文件，資料來源充足且具權威性"
        elif len(chunks) >= 1:
            confidence_score = ConfidenceLevel.MEDIUM
            confidence_explanation = f"找到 {len(chunks)} 筆相關文件，建議擴大搜尋範圍"
        else:
            confidence_score = ConfidenceLevel.LOW
            confidence_explanation = "相關文件數量較少，結果可能不完整"

        return LegalAnswer(
            executive_summary=executive_summary,
            key_findings=key_findings,
            detailed_analysis=detailed_analysis,
            citations=citations,
            confidence_score=confidence_score,
            confidence_explanation=confidence_explanation,
            limitations=["本系統目前僅索引部分文件，實際案件可能更多"],
        )

    async def _generate_fallback_answer(self, query: Query, reason: str) -> LegalAnswer:
        """
        Generate fallback answer when RAG fails.

        Args:
            query: User query
            reason: Reason for fallback

        Returns:
            Fallback LegalAnswer
        """
        return LegalAnswer(
            executive_summary=f"抱歉，{reason}。",
            key_findings=[
                "系統目前未找到相關文件",
                "建議嘗試其他關鍵字或擴大搜尋範圍",
            ],
            detailed_analysis=f"查詢「{query.text}」未能找到匹配的法律文件。可能原因：\n\n"
            f"1. 相關文件尚未建立索引\n"
            f"2. 關鍵字過於具體或模糊\n"
            f"3. 資料庫中無相關案例\n\n"
            f"建議調整查詢關鍵字後重試。",
            citations=[],
            confidence_score=ConfidenceLevel.LOW,
            confidence_explanation=reason,
            limitations=["未找到相關文件", "建議擴充資料庫或調整查詢"],
        )

    async def process_document(
        self,
        file_path: str,
        filename: str,
        content: str | None = None,
    ) -> dict:
        """
        Process a document through the WikiBuilder workflow.

        Args:
            file_path: Path to the document file
            filename: Original filename
            content: Optional pre-loaded content

        Returns:
            WikiBuilder workflow result containing:
            - doc_id: Document ID
            - metadata: Extracted metadata
            - concepts: Extracted concepts
            - chunk_count: Number of chunks indexed
            - categories_updated: Updated categories
        """
        self.logger.info(f"Processing document with WikiBuilder workflow: {filename}")

        if not hasattr(self, 'wiki_builder_workflow') or not self.wiki_builder_workflow:
            raise RuntimeError("WikiBuilder workflow not initialized")

        try:
            result = await self.wiki_builder_workflow.process(
                file_path=file_path,
                filename=filename,
                content=content,
            )
            self.logger.info(f"Document processed successfully: {result.get('doc_id')}")
            return result

        except Exception as e:
            self.logger.error(f"Document processing failed: {e}", exc_info=True)
            raise

    async def stream_document_processing(
        self,
        file_path: str,
        filename: str,
        content: str | None = None,
    ):
        """
        Stream document processing with progress updates.

        Args:
            file_path: Path to the document file
            filename: Original filename
            content: Optional pre-loaded content

        Yields:
            Tuples of (node_name, state_update) for each processing step
        """
        self.logger.info(f"Streaming document processing: {filename}")

        if not hasattr(self, 'wiki_builder_workflow') or not self.wiki_builder_workflow:
            raise RuntimeError("WikiBuilder workflow not initialized")

        try:
            async for node_name, state_update in self.wiki_builder_workflow.stream_process(
                file_path=file_path,
                filename=filename,
                content=content,
            ):
                yield node_name, state_update

        except Exception as e:
            self.logger.error(f"Document streaming failed: {e}", exc_info=True)
            raise

    async def _generate_mock_answer(self, query: Query) -> LegalAnswer:
        """
        Generate a mock answer for MVP testing.

        This will be replaced with real agent processing.
        """
        mock_citation = LegalCitation(
            id=1,
            type=CitationType.ENFORCEMENT_DOCUMENT,
            authority=CitationAuthority.PRIMARY,
            title="範例裁罰書",
            formatted_citation="金融監督管理委員會，金管銀法字第XXXXX號裁罰書（民國XXX年X月X日）",
            issuing_authority="金管會",
        )

        return LegalAnswer(
            executive_summary=f"正在處理您的查詢：「{query.text[:50]}...」",
            key_findings=[
                "此為測試回應，實際功能開發中",
                "系統已成功接收並解析您的查詢",
                "完整的多代理研究系統將在後續版本提供",
            ],
            detailed_analysis=(
                "這是一個測試回應。完整的法律研究代理系統正在開發中，將包含：\n\n"
                "1. 規劃代理：分解研究任務\n"
                "2. 行動代理：執行搜尋與檢索\n"
                "3. 驗證代理：驗證引用與事實\n"
                "4. 答案代理：綜合最終答案\n\n"
                "目前您看到的是API架構的驗證版本。"
            ),
            citations=[mock_citation],
            confidence_score=ConfidenceLevel.LOW,
            confidence_explanation="這是測試回應，非實際研究結果",
            limitations=["此為MVP測試版本", "尚未整合實際資料源", "完整功能開發中"],
        )

    async def process_with_deep_agent(self, query: Query, thread_id: str | None = None) -> LegalAnswer:
        """
        Process a legal research query using the Deep Agent workflow.

        Deep Agent provides Claude Code-like capabilities:
        - Task planning with write_todos
        - Sub-agent delegation for specialized tasks
        - Context management

        Args:
            query: User query
            thread_id: Optional thread ID for conversation continuity

        Returns:
            LegalAnswer generated by Deep Agent
        """
        if not self.deep_agent:
            self.logger.warning("Deep Agent not available, falling back to Plan-Execute workflow")
            return await self._process_with_plan_execute(query)

        self.logger.info(f"Processing query with Deep Agent: {query.text[:100]}...")

        try:
            # Invoke Deep Agent asynchronously
            result = await self.deep_agent.ainvoke(
                query=query.text,
                thread_id=thread_id,
            )

            response_text = result.get("response", "")

            if not response_text:
                return await self._generate_fallback_answer(query, "Deep Agent failed to generate response")

            # Convert Deep Agent response to LegalAnswer format
            answer = self._convert_deep_agent_response(query, response_text, result)

            return answer

        except Exception as e:
            self.logger.error(f"Deep Agent processing failed: {e}", exc_info=True)
            # Fallback to Plan-Execute workflow
            self.logger.info("Falling back to Plan-Execute workflow")
            return await self._process_with_plan_execute(query)

    def _convert_deep_agent_response(
        self, query: Query, response_text: str, result: dict
    ) -> LegalAnswer:
        """
        Convert Deep Agent response to LegalAnswer format.

        Args:
            query: Original query
            response_text: Generated response text
            result: Full result from Deep Agent

        Returns:
            LegalAnswer object
        """
        import re

        # Parse response to extract sections
        lines = response_text.split("\n")
        executive_summary = ""
        key_findings = []
        detailed_analysis = response_text

        # Try to parse structured response
        current_section = None
        summary_lines = []
        findings_lines = []

        for line in lines:
            line_lower = line.lower().strip()
            if "執行摘要" in line_lower or "executive summary" in line_lower:
                current_section = "summary"
            elif "關鍵發現" in line_lower or "key finding" in line_lower:
                current_section = "findings"
            elif "詳細分析" in line_lower or "analysis" in line_lower:
                current_section = "analysis"
            elif "信心評分" in line_lower or "confidence" in line_lower:
                current_section = "confidence"
            elif current_section == "summary" and line.strip():
                summary_lines.append(line.strip())
            elif current_section == "findings" and line.strip():
                if line.strip().startswith(("-", "•", "*", "1", "2", "3", "4", "5")):
                    findings_lines.append(line.strip().lstrip("-•* 0123456789."))

        # Use parsed sections if available
        if summary_lines:
            executive_summary = " ".join(summary_lines)
        else:
            # Use first paragraph as summary
            paragraphs = [p.strip() for p in response_text.split("\n\n") if p.strip()]
            executive_summary = paragraphs[0] if paragraphs else response_text[:300]

        if findings_lines:
            key_findings = findings_lines[:5]  # Limit to 5
        else:
            key_findings = ["查詢已完成，請參閱詳細分析"]

        # Extract citations from response
        citations = []
        citation_pattern = r'\[(\d+)\]\s*([^\n]+)'
        matches = re.findall(citation_pattern, response_text)

        for idx, (num, source_text) in enumerate(matches[:10], 1):  # Limit to 10
            citation = LegalCitation(
                id=idx,
                type=CitationType.ENFORCEMENT_DOCUMENT,
                authority=CitationAuthority.PRIMARY,
                title=source_text.strip()[:100],
                formatted_citation=f"[{idx}] {source_text.strip()[:100]}",
                issuing_authority="金管會",
            )
            citations.append(citation)

        # Determine confidence based on response quality
        if len(citations) >= 3 and len(response_text) > 500:
            confidence_score = ConfidenceLevel.HIGH
            confidence_explanation = f"Deep Agent 找到 {len(citations)} 個引用來源，分析完整"
        elif len(citations) >= 1:
            confidence_score = ConfidenceLevel.MEDIUM
            confidence_explanation = f"Deep Agent 找到 {len(citations)} 個引用來源"
        else:
            confidence_score = ConfidenceLevel.LOW
            confidence_explanation = "Deep Agent 未找到引用來源"

        return LegalAnswer(
            executive_summary=executive_summary[:1000],
            key_findings=key_findings,
            detailed_analysis=detailed_analysis,
            citations=citations,
            confidence_score=confidence_score,
            confidence_explanation=confidence_explanation,
            limitations=["此為 Deep Agent (v2.0) 自動生成結果"],
            processing_steps=["Deep Agent workflow"],
        )

    async def stream_deep_agent(self, query: Query, thread_id: str | None = None):
        """
        Stream query processing with Deep Agent.

        Args:
            query: User query
            thread_id: Optional thread ID for conversation continuity

        Yields:
            Streaming chunks from Deep Agent
        """
        if not self.deep_agent:
            self.logger.warning("Deep Agent not available")
            return

        self.logger.info(f"Streaming query with Deep Agent: {query.text[:100]}...")

        try:
            async for chunk in self.deep_agent.astream(
                query=query.text,
                thread_id=thread_id,
            ):
                yield chunk

        except Exception as e:
            self.logger.error(f"Deep Agent streaming failed: {e}", exc_info=True)
            raise

    async def _send_progress_update(self, node_name: str, state_update: dict, full_state: dict):
        """
        Send progress update to UI callback.

        Maps LangGraph node names to UI-friendly step updates and triggers
        appropriate callback methods.

        Args:
            node_name: Name of the LangGraph node that just executed
            state_update: The state update from this node
            full_state: The complete current state
        """
        if not self.ui_callback:
            return

        # Map node names to UI-friendly descriptions
        node_descriptions = {
            "query_analyzer": "分析查詢意圖",
            "planner": "制定研究計畫",
            "execute_task": "執行研究任務",
            "replanner": "檢視並調整計畫",
            "reporter": "生成研究報告",
        }

        step_description = node_descriptions.get(node_name, node_name)

        try:
            # Update current step
            await self.ui_callback.on_step_update(
                step=node_name,
                status="completed",
                data={"description": step_description}
            )

            # Log activity
            await self.ui_callback.on_activity_log(
                level="info",
                message=f"完成步驟: {step_description}"
            )

            # If planner node, send research plan
            if node_name == "planner" and "plan" in state_update:
                plan = state_update.get("plan")
                if plan:
                    # Convert plan to dict format for UI
                    plan_dict = {
                        "goal": getattr(plan, 'goal', '') if hasattr(plan, 'goal') else '',
                        "tasks": []
                    }

                    tasks = getattr(plan, 'tasks', []) if hasattr(plan, 'tasks') else []
                    for i, task in enumerate(tasks):
                        task_dict = {
                            "task_number": i + 1,
                            "description": getattr(task, 'description', str(task)) if hasattr(task, 'description') else str(task),
                            "status": getattr(task, 'status', 'pending') if hasattr(task, 'status') else 'pending',
                        }
                        plan_dict["tasks"].append(task_dict)

                    await self.ui_callback.on_plan_created(plan_dict)

            # If execute_task or replanner node, update research plan with task statuses
            if node_name in ("execute_task", "replanner"):
                past_steps = full_state.get("past_steps", [])
                plan = full_state.get("plan")

                if plan:
                    tasks = getattr(plan, 'tasks', []) if hasattr(plan, 'tasks') else []
                    total_tasks = len(tasks)
                    completed_tasks = len(past_steps)

                    # Build updated plan with task statuses
                    plan_dict = {
                        "goal": getattr(plan, 'goal', '') if hasattr(plan, 'goal') else '',
                        "tasks": []
                    }

                    # Get IDs of completed tasks from past_steps
                    completed_task_ids = set()
                    for step in past_steps:
                        if isinstance(step, tuple) and len(step) >= 1:
                            task_info = step[0]
                            if isinstance(task_info, dict) and 'id' in task_info:
                                completed_task_ids.add(task_info['id'])

                    for i, task in enumerate(tasks):
                        task_id = getattr(task, 'id', f'task-{i}') if hasattr(task, 'id') else f'task-{i}'
                        task_status = getattr(task, 'status', 'pending') if hasattr(task, 'status') else 'pending'

                        # Check if task is completed based on past_steps
                        if task_id in completed_task_ids or i < completed_tasks:
                            task_status = 'complete'
                        elif i == completed_tasks:
                            task_status = 'in_progress'

                        # Get result from past_steps if available
                        task_result = None
                        for step in past_steps:
                            if isinstance(step, tuple) and len(step) >= 2:
                                task_info, result = step[0], step[1]
                                if isinstance(task_info, dict):
                                    step_task_id = task_info.get('id', '')
                                    if step_task_id == task_id or (isinstance(step_task_id, str) and task_id in step_task_id):
                                        task_result = result[:200] if isinstance(result, str) and len(result) > 200 else result
                                        break

                        task_dict = {
                            "task_number": i + 1,
                            "description": getattr(task, 'description', str(task)) if hasattr(task, 'description') else str(task),
                            "status": task_status,
                            "result": task_result,
                        }
                        plan_dict["tasks"].append(task_dict)

                    # Send updated plan
                    await self.ui_callback.on_plan_created(plan_dict)

                    # Also update dynamic plan progress
                    await self.ui_callback.on_dynamic_plan({
                        "current_task": completed_tasks,
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                    })

        except Exception as e:
            self.logger.warning(f"Failed to send progress update: {e}")
