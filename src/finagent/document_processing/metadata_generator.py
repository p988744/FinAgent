"""LLM-based document metadata generator."""

import json
from datetime import datetime

from openai import OpenAI
from pydantic import BaseModel, Field

from finagent.config import reload_settings, settings
from finagent.document_processing.metadata_store import DocumentMetadata


class MetadataGenerationResult(BaseModel):
    """Result from LLM metadata generation."""

    description: str = Field(description="1-2 sentence description of the document")
    document_type: str = Field(description="Document type (e.g., 裁罰書, 判決書, 法規條文)")
    keywords: list[str] = Field(description="5-10 keywords extracted from document")
    date: str | None = Field(default=None, description="Document date in YYYY-MM-DD format")
    issuing_authority: str | None = Field(
        default=None, description="Issuing authority (e.g., 金管會, 中央銀行)"
    )
    related_institutions: list[str] = Field(
        default_factory=list, description="Related banks/institutions"
    )
    penalty_amount: str | None = Field(
        default=None, description="Penalty amount if applicable (e.g., 2.5億元)"
    )
    violation_types: list[str] = Field(
        default_factory=list, description="Violation types if applicable"
    )


class MetadataGenerator:
    """Generate document metadata using LLM."""

    # Document type mapping for validation
    VALID_DOCUMENT_TYPES = [
        "裁罰書",
        "判決書",
        "法規條文",
        "新聞報導",
        "監管公告",
        "銀行聲明",
        "分析報告",
        "其他",
    ]

    VALID_AUTHORITIES = ["金管會", "中央銀行", "公平會", "最高法院", "高等法院", "地方法院", "其他"]

    VALID_VIOLATION_TYPES = [
        "洗錢防制",
        "內線交易",
        "資訊揭露",
        "法規遵循",
        "作業風險",
        "信用風險",
        "市場操縱",
        "消費者保護",
        "其他",
    ]

    def __init__(self):
        """Initialize metadata generator."""
        # Reload settings to get latest config
        reload_settings()

        # Initialize OpenAI client based on config
        base_url = settings.effective_llm_base_url

        if base_url:
            # Custom endpoint
            self.client = OpenAI(api_key=settings.effective_llm_api_key, base_url=base_url)
        else:
            # OpenAI default
            self.client = OpenAI(api_key=settings.effective_llm_api_key)

        self.model = settings.llm_model

    def generate_metadata(
        self, doc_id: str, filename: str, content: str, max_content_length: int = 4000
    ) -> DocumentMetadata:
        """
        Generate metadata for a document using LLM.

        Args:
            doc_id: Document ID
            filename: Document filename
            content: Document content (will be truncated if too long)
            max_content_length: Maximum content length to send to LLM

        Returns:
            DocumentMetadata object with generated metadata
        """
        # Truncate content if too long
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[內容已截斷...]"

        # Create system prompt
        system_prompt = self._create_system_prompt()

        # Create user prompt
        user_prompt = f"""請分析以下文件並提取元資料：

檔名: {filename}

文件內容:
{content}

請以 JSON 格式回傳以下資訊：
{{
  "description": "文件描述（1-2句話）",
  "document_type": "文件類型（從以下選擇：{', '.join(self.VALID_DOCUMENT_TYPES)}）",
  "keywords": ["關鍵字1", "關鍵字2", ...],
  "date": "文件日期（YYYY-MM-DD格式，如果有的話）",
  "issuing_authority": "發布機關（從以下選擇：{', '.join(self.VALID_AUTHORITIES)}，如果有的話）",
  "related_institutions": ["相關機構1", "相關機構2", ...],
  "penalty_amount": "裁罰金額（如果是裁罰書）",
  "violation_types": ["違規類型1", "違規類型2", ...]（從以下選擇：{', '.join(self.VALID_VIOLATION_TYPES)}）
}}
"""

        try:
            # Call LLM
            # Note: response_format is not well-supported by many OpenAI-compatible endpoints
            # Skip it for non-OpenAI endpoints to avoid issues
            base_url = settings.effective_llm_base_url
            use_response_format = not base_url or "api.openai.com" in base_url

            if use_response_format:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
            else:
                # Don't use response_format for custom endpoints (Ollama, local models, etc.)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                )

            # Parse response
            result_text = response.choices[0].message.content

            # Check if response is empty
            if not result_text or result_text.strip() == "":
                raise RuntimeError(f"LLM returned empty response for {filename}")

            # Try to extract JSON if response contains other text
            result_text = result_text.strip()
            if not result_text.startswith("{"):
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
                else:
                    raise RuntimeError(f"LLM response is not valid JSON: {result_text[:200]}")

            result_data = json.loads(result_text)

            # Validate and create result
            result = MetadataGenerationResult(**result_data)

            # Convert to DocumentMetadata
            now = datetime.now().isoformat()

            metadata = DocumentMetadata(
                doc_id=doc_id,
                filename=filename,
                description=result.description,
                document_type=result.document_type,
                keywords=result.keywords,
                date=result.date,
                issuing_authority=result.issuing_authority,
                related_institutions=result.related_institutions,
                penalty_amount=result.penalty_amount,
                violation_types=result.violation_types,
                indexed=False,  # Not indexed yet
                chunk_count=0,  # Not indexed yet
                created_at=now,
                updated_at=now,
            )

            return metadata

        except Exception as e:
            raise RuntimeError(f"Failed to generate metadata: {str(e)}")

    def _create_system_prompt(self) -> str:
        """Create system prompt for metadata generation."""
        return """你是一個專業的法律文件分析助手，專門分析台灣的金融監管文件。

你的任務是：
1. 閱讀文件內容
2. 提取關鍵資訊
3. 以結構化的 JSON 格式回傳元資料

注意事項：
- description: 用1-2句話精確描述文件的核心內容
- document_type: 必須從提供的選項中選擇最符合的類型
- keywords: 提取5-10個最重要的關鍵字（包括機構名稱、違規類型、重要數字等）
- date: 如果文件中有明確日期，轉換為 YYYY-MM-DD 格式（民國年份請轉換為西元年）
- issuing_authority: 識別發布機關（金管會、中央銀行等）
- related_institutions: 提取所有相關的銀行或金融機構名稱
- penalty_amount: 如果是裁罰案件，提取裁罰金額（保留原始格式，例如：2.5億元）
- violation_types: 識別違規類型（洗錢防制、內線交易等）

請確保：
- 所有欄位都基於文件實際內容
- 如果某個欄位無法從文件中提取，設為 null 或空陣列
- 日期格式正確（YYYY-MM-DD）
- 使用繁體中文
- 回傳有效的 JSON 格式
"""


def generate_metadata_with_llm(doc_id: str, filename: str, content: str) -> DocumentMetadata:
    """
    Convenience function to generate metadata using LLM.

    Args:
        doc_id: Document ID
        filename: Document filename
        content: Document content

    Returns:
        DocumentMetadata object
    """
    generator = MetadataGenerator()
    return generator.generate_metadata(doc_id, filename, content)
