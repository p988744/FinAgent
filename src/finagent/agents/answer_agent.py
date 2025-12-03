"""Answer Agent - Synthesizes final answer using LLM."""

import json
import logging
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError

from finagent.agents.state import AgentState
from finagent.config import settings
from finagent.document_processing.retriever import RetrievedChunk
from finagent.models.answers import ConfidenceLevel, LegalAnswer
from finagent.models.citations import LegalCitation

logger = logging.getLogger(__name__)


class StructuredAnswerOutput(BaseModel):
    """Structured output format for LLM answer synthesis."""

    executive_summary: str = Field(
        ...,
        description="執行摘要（100-150字）：簡明說明查詢結果，包含找到幾筆文件、主要機構/違規類型、核心發現",
    )
    key_findings: list[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="關鍵發現（3-5點）：每點必須包含引用編號，例如「裁罰金額：新臺幣2.5億元 [引用1]」",
    )
    detailed_analysis: str = Field(
        ...,
        description="詳細分析：深入分析檢索內容，包含背景說明、具體違規事實、裁罰理由與法律依據。每個段落都必須包含引用編號。",
    )
    final_answer: str = Field(
        ...,
        description="最終答案（50-100字）：用一段話直接回應使用者的查詢問題，例如「玉山銀行於民國109年因洗錢防制缺失被處以新臺幣2.5億元罰鍰 [引用1]」",
    )


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

        # Use string output and parse manually (more compatible with all LLM providers)
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _get_system_prompt(self) -> str:
        """Get system prompt for answer synthesis."""
        return """你是台灣法律研究系統的答案代理（Answer Agent）。

你的任務是根據檢索到的法律文件，綜合分析並生成專業的法律研究報告。

## 核心原則

1. **精確引用**：每個事實陳述必須附上引用編號，使用 markdown 連結格式：[引用1](#cite-1)、[引用2](#cite-2)
2. **客觀中立**：使用正式法律用語，避免主觀判斷或推測
3. **結構完整**：包含執行摘要、關鍵發現、詳細分析、最終答案
4. **繁體中文**：全部使用台灣繁體中文，符合法律文書規範

## 引用格式規範

**重要**：必須使用 markdown 連結格式，讓引用可點擊跳轉：

- 單一來源：[引用1](#cite-1)
- 多個來源：[引用1](#cite-1)、[引用2](#cite-2)
- 特定章節：[引用1，第三章A節](#cite-1)
- 特定頁碼：[引用1，第5頁](#cite-1)

錯誤示範：[引用1]（純文字，無法點擊）
正確示範：[引用1](#cite-1)（markdown 連結，可點擊）

## 重要提醒

- **不要捏造資訊**：只根據提供的文件內容進行分析
- **不要省略引用**：每個事實陳述都要標註來源，並使用 markdown 連結格式
- **不要使用模糊語言**：避免「可能」、「或許」等詞彙，使用「根據文件顯示」等明確表述
- **日期格式**：優先使用民國紀年（例：民國109年），或標註西元年份
- **格式化**：可使用 markdown 格式（如 **粗體**、列表、段落分隔）提升可讀性"""

    def _get_user_prompt(self) -> str:
        """Get user prompt template."""
        return """請根據以下資訊，生成結構化的法律研究報告：

## 查詢問題
{query}

## 檢索到的文件（共 {num_chunks} 筆）

{context}

## 引用來源清單

{citations}

---

請以 JSON 格式輸出，包含以下四個欄位：

```json
{{
  "executive_summary": "執行摘要（100-150字）：簡明說明找到幾筆文件、主要涉及的機構/違規類型、核心發現",
  "key_findings": [
    "關鍵發現1：包含引用 [引用1](#cite-1)",
    "關鍵發現2：包含引用 [引用2](#cite-2)",
    "關鍵發現3：包含引用 [引用3](#cite-3)"
  ],
  "detailed_analysis": "詳細分析：深入分析檢索內容，包含背景說明、具體違規事實、裁罰理由與法律依據。每個段落都必須包含引用 [引用X](#cite-X)。可使用 markdown 格式（**粗體**、段落分隔等）提升可讀性。",
  "final_answer": "最終答案（50-100字）：用一段話直接回應使用者的查詢問題 [引用1](#cite-1)"
}}
```

**重要規則**：
1. 必須輸出有效的 JSON 格式
2. key_findings 必須是陣列，包含 3-5 個項目
3. 所有引用必須使用 markdown 連結格式 [引用X](#cite-X)
4. 不要在 JSON 外添加任何額外文字
5. 確保 JSON 的引號和逗號正確"""

    async def synthesize(self, state: AgentState) -> AgentState:
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
                try:
                    await self.ui_callback.on_todo_started(synthesis_todo)
                except Exception as e:
                    logger.warning(f"Failed to send callback: {e}")

        # Emit answer generation start callback
        if self.ui_callback:
            try:
                await self.ui_callback.on_answer_generation_start()
            except Exception as e:
                logger.warning(f"Failed to send callback: {e}")

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

            # Invoke LLM to synthesize answer (returns JSON string)
            # Note: chain.invoke is sync. Ideally we should use ainvoke if available,
            # or run in executor if it blocks. LangChain usually supports ainvoke.
            if hasattr(self.chain, "ainvoke"):
                response = await self.chain.ainvoke(
                    {
                        "query": query.text,
                        "num_chunks": len(chunks),
                        "context": context,
                        "citations": citations_text,
                    }
                )
            else:
                # Fallback to sync invoke if ainvoke not available
                response = self.chain.invoke(
                    {
                        "query": query.text,
                        "num_chunks": len(chunks),
                        "context": context,
                        "citations": citations_text,
                    }
                )

            # Parse JSON response to structured output
            structured_response = self._parse_json_response(response)

            # Convert structured response to LegalAnswer
            answer = self._convert_to_legal_answer(
                structured_response, chunks, citations, state["processing_steps"]
            )

            # Emit citations extracted callback
            if self.ui_callback:
                try:
                    await self.ui_callback.on_citations_extracted(citations=citations)
                except Exception as e:
                    logger.warning(f"Failed to send callback: {e}")

            # Update state
            state["answer"] = answer
            state["processing_steps"].append("答案代理：生成完整法律研究報告")

            # Emit answer generation complete callback
            if self.ui_callback:
                try:
                    await self.ui_callback.on_answer_generation_complete(answer=answer)
                except Exception as e:
                    logger.warning(f"Failed to send callback: {e}")

            # Phase 5: Mark synthesis todo as completed
            if synthesis_todo:
                synthesis_todo.mark_completed(result={"citations": len(answer.citations)})
                if self.ui_callback:
                    try:
                        await self.ui_callback.on_todo_completed(synthesis_todo)
                    except Exception as e:
                        logger.warning(f"Failed to send callback: {e}")

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
                    try:
                        await self.ui_callback.on_todo_failed(synthesis_todo, str(e))
                    except Exception as e:
                        logger.warning(f"Failed to send callback: {e}")
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

    def _parse_json_response(self, response: str) -> StructuredAnswerOutput:
        """
        Parse LLM JSON response to StructuredAnswerOutput.

        Args:
            response: Raw LLM response (should be JSON)

        Returns:
            StructuredAnswerOutput object

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON object found in response")

            # Parse JSON
            data = json.loads(json_str)

            logger.debug(f"Parsed JSON data keys: {list(data.keys())}")

            # Post-process: Some LLMs output literal "\n" as text instead of newlines
            # Replace any literal \n strings with actual newlines for proper markdown rendering
            def fix_newlines(text: str) -> str:
                """Replace literal \n with actual newlines if present."""
                if not isinstance(text, str):
                    return text
                # Check if there are literal \n characters (not already converted)
                # by looking for the pattern where \n appears but not as actual newline
                if r'\n' in text or '\\n' in text:
                    text = text.replace(r'\n', '\n').replace('\\n', '\n')
                return text

            # Clean all text fields
            for key in ['executive_summary', 'detailed_analysis', 'final_answer']:
                if key in data:
                    data[key] = fix_newlines(data[key])

            # Clean key_findings array
            if 'key_findings' in data and isinstance(data['key_findings'], list):
                data['key_findings'] = [fix_newlines(f) for f in data['key_findings']]

            # Validate and create StructuredAnswerOutput
            return StructuredAnswerOutput(**data)

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response[:500]}...")

            # Fallback: try to extract fields manually
            return self._fallback_parse(response)

    def _fallback_parse(self, response: str) -> StructuredAnswerOutput:
        """
        Fallback parser when JSON parsing fails.

        Args:
            response: Raw LLM response

        Returns:
            StructuredAnswerOutput with best-effort parsing
        """
        logger.warning("Using fallback parser for malformed response")

        # Try to extract sections
        sections = response.split("\n\n")

        # Extract executive summary (first substantial paragraph)
        executive_summary = "根據檢索結果進行分析。"
        for section in sections:
            if len(section.strip()) > 50 and not section.startswith("#"):
                executive_summary = section.strip()[:500]
                break

        # Extract key findings (look for bullet points or numbered lists)
        key_findings = []
        for section in sections:
            lines = section.strip().split("\n")
            for line in lines:
                if line.strip() and any(
                    line.strip().startswith(p) for p in ["- ", "• ", "1.", "2.", "3.", "4.", "5."]
                ):
                    finding = line.strip().lstrip("- •123456789.").strip()
                    if finding and len(finding) > 10:
                        key_findings.append(finding)

        # Ensure we have 3-5 findings
        if len(key_findings) < 3:
            key_findings = ["資料不足，無法提供詳細發現"] * 3

        key_findings = key_findings[:5]

        # Use full response as detailed analysis
        detailed_analysis = response

        # Try to extract final answer
        final_answer = "根據檢索結果，請參閱詳細分析。"
        for section in sections:
            if "最終答案" in section or "結論" in section:
                lines = section.strip().split("\n")
                for line in lines:
                    if line.strip() and not line.startswith("#") and "最終答案" not in line:
                        final_answer = line.strip()[:500]
                        break

        return StructuredAnswerOutput(
            executive_summary=executive_summary,
            key_findings=key_findings,
            detailed_analysis=detailed_analysis,
            final_answer=final_answer,
        )

    def _convert_to_legal_answer(
        self,
        structured_output: StructuredAnswerOutput,
        chunks: list[RetrievedChunk],
        citations: list[LegalCitation],
        processing_steps: list[str],
    ) -> LegalAnswer:
        """
        Convert structured LLM output to LegalAnswer.

        Args:
            structured_output: Structured output from LLM
            chunks: Retrieved chunks
            citations: Citations list
            processing_steps: Workflow processing steps

        Returns:
            Complete LegalAnswer object
        """
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
            executive_summary=structured_output.executive_summary,
            key_findings=structured_output.key_findings,
            detailed_analysis=structured_output.detailed_analysis,
            final_answer=structured_output.final_answer,
            citations=citations,
            confidence_score=confidence_score,
            confidence_explanation=confidence_explanation,
            limitations=["本系統基於已索引文件進行分析，實際案件可能更多"],
            processing_steps=processing_steps,
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
