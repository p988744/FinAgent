"""Agent orchestrator for coordinating the multi-agent workflow."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from finagent.models.queries import Query
from finagent.models.answers import LegalAnswer, ConfidenceLevel
from finagent.models.citations import LegalCitation, CitationAuthority, CitationType
from finagent.document_processing import DocumentRetriever

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the multi-agent research workflow.

    Coordinates Planning → Action → Validation → Answer agents.
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.logger = logger
        # Agents will be initialized later when we implement them
        self.planning_agent = None
        self.action_agent = None
        self.validation_agent = None
        self.answer_agent = None

        # Initialize RAG retriever
        try:
            self.retriever = DocumentRetriever(collection_name="legal_documents")
            self.use_rag = self.retriever.collection_exists()
            if self.use_rag:
                self.logger.info("RAG retriever initialized successfully")
            else:
                self.logger.warning("Vector database is empty, using fallback mode")
        except Exception as e:
            self.logger.warning(f"Failed to initialize RAG retriever: {e}, using fallback mode")
            self.retriever = None
            self.use_rag = False

    async def process_query(self, query: Query) -> LegalAnswer:
        """
        Process a legal research query through the multi-agent pipeline.

        Args:
            query: User query

        Returns:
            Legal answer with citations

        Workflow:
            1. Planning Agent: Decompose query into tasks
            2. Action Agent: Execute tasks (search, retrieve, analyze)
            3. Validation Agent: Validate citations and facts
            4. Answer Agent: Synthesize final answer
        """
        start_time = datetime.now()
        self.logger.info(f"Processing query: {query.text[:100]}...")

        try:
            # Use RAG pipeline if available, otherwise use mock
            if self.use_rag and self.retriever:
                answer = await self._process_with_rag(query)
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

    def _extract_citations(self, chunks) -> List[LegalCitation]:
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

    def _synthesize_answer(self, query: Query, chunks, citations: List[LegalCitation]) -> LegalAnswer:
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
                "完整的多代理研究系統將在後續版本提供"
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
            limitations=[
                "此為MVP測試版本",
                "尚未整合實際資料源",
                "完整功能開發中"
            ],
        )
