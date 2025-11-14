"""Answer Agent - Synthesizes final answer using LLM."""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.agents.state import AgentState
from finagent.config import settings
from finagent.document_processing.retriever import RetrievedChunk
from finagent.models.answers import ConfidenceLevel, LegalAnswer
from finagent.models.citations import LegalCitation

logger = logging.getLogger(__name__)


class AnswerAgent:
    """
    Answer Agent synthesizes final legal research answer using LLM.

    Responsibilities:
    - Generate executive summary from retrieved context
    - Extract key findings with proper citations
    - Create detailed analysis with embedded references
    - Assess confidence level
    - Identify limitations
    """

    def __init__(self, model: str | None = None, ui_callback=None):
        """Initialize answer agent with LLM.

        Args:
            model: Optional model name override
            ui_callback: Optional UICallback for progress updates
        """
        effective_model = model or settings.llm_model
        base_url = settings.effective_llm_base_url
        self.ui_callback = ui_callback

        if base_url:
            # Custom endpoint
            self.llm = ChatOpenAI(
                model=effective_model,
                api_key=settings.effective_llm_api_key,
                base_url=base_url,
                temperature=0.3,
            )
        else:
            # OpenAI default
            self.llm = ChatOpenAI(
                model=effective_model,
                api_key=settings.effective_llm_api_key,
                temperature=0.3,  # Balanced creativity for synthesis
            )

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", self._get_system_prompt()), ("user", self._get_user_prompt())]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()

    def _get_system_prompt(self) -> str:
        """Get system prompt for answer synthesis."""
        return """你是台灣法律研究系統的答案代理（Answer Agent）。

你的任務是根據檢索到的法律文件，綜合分析並生成專業的法律研究報告。

## 核心原則

1. **精確引用**：每個事實陳述必須附上引用編號，例如 [引用1] 或 [引用1、2]
2. **客觀中立**：使用正式法律用語，避免主觀判斷或推測
3. **結構完整**：包含執行摘要、關鍵發現、詳細分析
4. **繁體中文**：全部使用台灣繁體中文，符合法律文書規範

## 引用格式規範

- 首次引用：[引用1]
- 重複引用同一來源：[引用1]
- 特定章節：[引用1，第三章A節]
- 特定頁碼：[引用1，第5頁]
- 多個來源：[引用1、2、3]

## 輸出結構

### 1. 執行摘要（100-150字）
簡明扼要說明查詢結果，包含：
- 找到幾筆相關文件
- 主要涉及的機構/違規類型
- 核心發現

### 2. 關鍵發現（3-5點，每點含引用）
列出最重要的發現，例如：
- 裁罰金額與日期 [引用X]
- 違規事實描述 [引用X]
- 法律依據 [引用X]

### 3. 詳細分析（含完整引用）
深入分析檢索內容，包含：
- 背景說明
- 具體違規事實
- 裁罰理由與法律依據
- 相關比較（如有）

每個段落都必須包含引用。

### 4. 最終答案（50-100字）
**重要**：在分析結束後，必須提供一個簡短的最終答案，直接回應使用者的查詢問題。
例如：
- 查詢「玉山銀行洗錢防制裁罰」→ 最終答案：「玉山銀行於民國109年因洗錢防制缺失被處以新臺幣2.5億元罰鍰。」
- 查詢「國泰世華內線交易」→ 最終答案：「根據檢索結果，國泰世華銀行主要涉及資訊系統異常及內部控制缺失的裁罰案件。」

## 重要提醒

- **不要捏造資訊**：只根據提供的文件內容進行分析
- **不要省略引用**：每個事實陳述都要標註來源
- **不要使用模糊語言**：避免「可能」、「或許」等詞彙，使用「根據文件顯示」等明確表述
- **日期格式**：優先使用民國紀年（例：民國109年），或標註西元年份"""

    def _get_user_prompt(self) -> str:
        """Get user prompt template."""
        return """請根據以下資訊，生成法律研究報告：

## 查詢問題
{query}

## 檢索到的文件（共 {num_chunks} 筆）

{context}

## 引用來源清單

{citations}

---

請以繁體中文生成完整的法律研究報告，包含：
1. 執行摘要
2. 關鍵發現（每點必須含引用）
3. 詳細分析（每段必須含引用）
4. **最終答案**（50-100字，直接回應使用者的查詢問題）

務必確保所有事實陳述都有對應的引用編號。

**重要**：報告結尾必須包含「最終答案」部分，用一段話總結回應使用者的問題。"""

    def synthesize(self, state: AgentState) -> AgentState:
        """
        Synthesize final answer from retrieved context.

        Args:
            state: Current agent state with retrieved chunks and citations

        Returns:
            Updated state with final answer
        """
        query = state["query"]
        chunks = state.get("retrieved_chunks", [])
        citations = state.get("citations", [])

        logger.info("Answer agent synthesizing final response")

        # Phase 5: Find and mark synthesis todo as in_progress
        todos = state.get("todos", [])
        synthesis_todo = next((t for t in todos if t.category == "synthesis"), None)

        if synthesis_todo and synthesis_todo.status == "pending":
            synthesis_todo.mark_started()
            if self.ui_callback:
                import asyncio
                try:
                    asyncio.create_task(self.ui_callback.on_todo_started(synthesis_todo))
                except RuntimeError:
                    pass

        # Emit answer generation start callback
        if self.ui_callback:
            import asyncio
            try:
                asyncio.create_task(self.ui_callback.on_answer_generation_start())
            except RuntimeError:
                pass

        try:
            if not chunks:
                # No documents found - generate fallback answer
                answer = self._generate_fallback_answer(query, "未找到相關文件")
                state["answer"] = answer
                state["processing_steps"].append("答案代理：生成降級回應（無文件）")
                return state

            # Format context and citations for LLM
            context = self._format_context(chunks)
            citations_text = self._format_citations(citations)

            # Invoke LLM to synthesize answer
            response = self.chain.invoke(
                {
                    "query": query.text,
                    "num_chunks": len(chunks),
                    "context": context,
                    "citations": citations_text,
                }
            )

            # Parse LLM response into structured answer
            answer = self._parse_response(response, chunks, citations, state["processing_steps"])

            # Emit citations extracted callback
            if self.ui_callback:
                import asyncio
                try:
                    asyncio.create_task(
                        self.ui_callback.on_citations_extracted(citations=citations)
                    )
                except RuntimeError:
                    pass

            # Update state
            state["answer"] = answer
            state["processing_steps"].append("答案代理：生成完整法律研究報告")

            # Emit answer generation complete callback
            if self.ui_callback:
                import asyncio
                try:
                    asyncio.create_task(
                        self.ui_callback.on_answer_generation_complete(answer=answer)
                    )
                except RuntimeError:
                    pass

            # Phase 5: Mark synthesis todo as completed
            if synthesis_todo:
                synthesis_todo.mark_completed(result={"citations": len(answer.citations)})
                if self.ui_callback:
                    import asyncio
                    try:
                        asyncio.create_task(self.ui_callback.on_todo_completed(synthesis_todo))
                    except RuntimeError:
                        pass

            # Update state with todos
            state["todos"] = todos

            logger.info("Answer synthesis completed")

        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}", exc_info=True)
            state["errors"].append(f"答案生成失敗：{str(e)}")
            answer = self._generate_fallback_answer(query, f"系統錯誤：{str(e)}")
            state["answer"] = answer

            # Phase 5: Mark synthesis todo as failed
            todos = state.get("todos", [])
            synthesis_todo = next((t for t in todos if t.category == "synthesis"), None)
            if synthesis_todo:
                synthesis_todo.mark_failed(error=str(e))
                if self.ui_callback:
                    import asyncio
                    try:
                        asyncio.create_task(self.ui_callback.on_todo_failed(synthesis_todo, str(e)))
                    except RuntimeError:
                        pass
            state["todos"] = todos

        return state

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format retrieved chunks for LLM context."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            filename = chunk.metadata.get("filename", "未知文件")
            context_parts.append(
                f"### 文件 {i}：{filename}\n" f"相似度分數：{chunk.score:.3f}\n\n" f"{chunk.text}\n"
            )
        return "\n---\n".join(context_parts)

    def _format_citations(self, citations: list[LegalCitation]) -> str:
        """Format citations for LLM context."""
        citations_parts = []
        for citation in citations:
            citations_parts.append(
                f"[引用{citation.id}] {citation.formatted_citation}\n"
                f"  - 類型：{citation.type.value}\n"
                f"  - 權威性：{citation.authority.value}\n"
                f"  - 發布機關：{citation.issuing_authority}"
            )
        return "\n\n".join(citations_parts)

    def _parse_response(
        self,
        response: str,
        chunks: list[RetrievedChunk],
        citations: list[LegalCitation],
        processing_steps: list[str],
    ) -> LegalAnswer:
        """
        Parse LLM response into structured LegalAnswer.

        Args:
            response: Raw LLM response text
            chunks: Retrieved chunks
            citations: Citations list
            processing_steps: Workflow processing steps

        Returns:
            Structured LegalAnswer object
        """
        # Split response into sections (simplified parsing)
        sections = response.split("\n\n")

        # Extract executive summary (first paragraph)
        executive_summary = sections[0].strip() if sections else "根據檢索結果進行分析。"

        # Extract key findings (look for bullet points or numbered lists)
        key_findings = []
        detailed_analysis = response
        final_answer = None

        for section in sections:
            # Check for final answer section
            if "最終答案" in section or "## 最終答案" in section or "### 最終答案" in section:
                # Extract final answer
                lines = section.strip().split("\n")
                for line in lines:
                    if line.strip() and not line.startswith("#") and "最終答案" not in line:
                        final_answer = line.strip()
                        break

            # Extract key findings
            if "關鍵發現" in section or any(
                section.strip().startswith(prefix) for prefix in ["- ", "• ", "1.", "2.", "3."]
            ):
                lines = section.strip().split("\n")
                for line in lines:
                    if line.strip() and any(
                        line.strip().startswith(p)
                        for p in ["- ", "• ", "1.", "2.", "3.", "4.", "5."]
                    ):
                        key_findings.append(line.strip().lstrip("- •123456789.").strip())

        # If no key findings extracted, generate from first few chunks
        if not key_findings:
            for i, chunk in enumerate(chunks[:3], 1):
                first_sentence = chunk.text.split("。")[0] + "。"
                key_findings.append(f"{first_sentence} [引用{i}]")

        # Calculate confidence based on number of results and validation
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
            key_findings=key_findings[:5],  # Limit to 5
            detailed_analysis=detailed_analysis,
            final_answer=final_answer,  # Add final answer
            citations=citations,
            confidence_score=confidence_score,
            confidence_explanation=confidence_explanation,
            limitations=["本系統基於已索引文件進行分析，實際案件可能更多"],
            processing_steps=processing_steps,  # Add processing steps
        )

    def _generate_fallback_answer(self, query, reason: str) -> LegalAnswer:
        """Generate fallback answer when processing fails."""
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
