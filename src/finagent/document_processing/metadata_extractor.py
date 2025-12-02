"""Extract structured metadata from documents using LLM."""

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI

from finagent.config import settings
from finagent.config_manager import ConfigManager
from finagent.document_processing.metadata_models import (
    DocumentMetadata,
    MetadataExtractionResult,
)
from finagent.models.document_metadata import ExtendedDocumentMetadata

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract structured metadata from documents using LLM."""

    EXTRACTION_PROMPT = """你是文件元資料提取專家。從文件檔名和內容提取結構化元資料。

檔名：{filename}
內容摘要（前1000字）：
{content_preview}

請分析文件並提取以下資訊，以 JSON 格式回答：

```json
{{
  "entity": "實體名稱（銀行或機構，簡稱）",
  "entity_normalized": "正式全名（如：玉山商業銀行股份有限公司）",
  "penalty_type": "裁罰類型（如：洗錢防制、內線交易、內控缺失等）",
  "penalty_amount": 罰款金額（數字，無則為 null）,
  "date": "文件日期（ISO 格式 YYYY-MM-DD）",
  "year_roc": 民國年（數字，如 109）,
  "year_ad": 西元年（數字，如 2020）,
  "jurisdiction": "監管機構（金管會、中央銀行、公平會等）",
  "document_type": "文件類型（裁罰書、判決書、處分書等）",
  "case_number": "案號（如：金管銀法字第10900123456號，無則為 null）"
}}
```

**重要規則**：
1. 罰款金額：只提取數字（元），例如 2.5億 = 250000000
2. 日期格式：必須是 YYYY-MM-DD
3. 民國與西元：民國109年 = 西元2020年
4. 實體名稱：優先提取簡稱（如「玉山銀行」），正式全名放在 entity_normalized
5. 所有欄位都必須填寫，無法確定的填 null
6. 必須輸出有效的 JSON，不要添加額外文字"""

    # New enhanced extraction prompt for DocumentMetadata model
    NEW_EXTRACTION_PROMPT = """你是台灣金融法律文件元資料提取專家。請分析以下文件並提取完整的結構化元資料。

**文件資訊**
檔名：{filename}
內容摘要（前2000字）：
{content_preview}

請以 JSON 格式提取以下元資料：

```json
{{
  "title": "文件標題（如：金融監督管理委員會裁罰書 - 玉山銀行洗錢防制違規）",
  "description": "2-3句文件摘要，說明主要內容、處分對象、違規事項及結果",
  "document_type": "文件類型（裁罰書、判決書、法規、新聞、研究報告、或其他）",
  "issuing_authority": "發文機關（金管會、銀行局、證券期貨局、保險局、中央銀行、公平會、法院、或 null）",
  "case_number": "案號或文號（如：金管銀法字第10900123456號，無則為 null）",
  "document_date": "文件日期（YYYY-MM-DD格式，將民國年轉換為西元年，無則為 null）",
  "related_institutions": ["涉及的金融機構完整正式名稱列表（如：玉山商業銀行股份有限公司）"],
  "violation_types": ["違規類型列表（如：洗錢防制、內部控制、內線交易等，可為空陣列）"],
  "penalty_amount": "裁罰金額字串（如：NT$250,000,000 或 新臺幣貳億伍仟萬元，無則為 null）",
  "keywords": ["5-10個關鍵詞，用於搜尋和分類"],
  "extraction_confidence": 0.0到1.0之間的信心分數（根據文件清晰度和資訊完整度評估）
}}
```

**提取規則**：
1. **標題 (title)**：整合文件類型、主要當事人、違規事項形成完整標題
2. **摘要 (description)**：2-3句話，涵蓋何時、何地、何人、何事、結果
3. **文件類型 (document_type)**：必須是以下之一：裁罰書、判決書、法規、新聞、研究報告、其他
4. **發文機關 (issuing_authority)**：使用標準簡稱
5. **日期轉換**：民國109年 = 2020年，民國110年 = 2021年（民國年 + 1911）
6. **機構名稱**：使用完整正式名稱，包含「股份有限公司」
7. **違規類型**：可以有多個，從內容中提取所有提及的違規事項
8. **關鍵詞**：包含機構名、違規類型、監管機關、重要法條等
9. **信心分數**：
   - 0.9-1.0：文件資訊完整清晰，所有欄位都有明確依據
   - 0.7-0.9：大部分資訊清晰，少數欄位需要推論
   - 0.5-0.7：資訊部分模糊，多個欄位基於推測
   - 0.0-0.5：文件資訊不足，多數欄位無法確定

**輸出要求**：
- 必須輸出有效的 JSON
- 所有字串使用繁體中文
- 無法確定的欄位填 null 或空陣列
- 不要添加 JSON 之外的額外文字"""

    def __init__(self, use_new_model: bool = False):
        """
        Initialize MetadataExtractor.

        Args:
            use_new_model: If True, use direct OpenAI client and new DocumentMetadata model
                          If False, use LangChain and legacy ExtendedDocumentMetadata model
        """
        self.use_new_model = use_new_model

        if use_new_model:
            # New: Direct OpenAI client
            self.config_manager = ConfigManager()
            config = self.config_manager.get_active_llm_config()

            self.openai_client = AsyncOpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"] or None,
            )
            self.model_name = config["model"]
        else:
            # Legacy: LangChain
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                base_url=settings.effective_llm_base_url,
                api_key=settings.effective_llm_api_key,
                temperature=0.0,  # Deterministic for metadata extraction
            )

            self.prompt = ChatPromptTemplate.from_messages(
                [("system", "你是文件元資料提取專家。"), ("user", self.EXTRACTION_PROMPT)]
            )

            self.chain = self.prompt | self.llm | StrOutputParser()

    async def extract(
        self, filename: str, content: str, file_path: str
    ) -> ExtendedDocumentMetadata:
        """
        Extract metadata from document.

        Args:
            filename: Document filename
            content: Full document content
            file_path: Full file path

        Returns:
            ExtendedDocumentMetadata object
        """
        # Get content preview (first 1000 chars)
        content_preview = content[:1000]

        try:
            # Use LLM to extract metadata
            response = await self.chain.ainvoke(
                {"filename": filename, "content_preview": content_preview}
            )

            # Parse JSON from response
            metadata_dict = self._parse_json_response(response)

            # Complete metadata with file information
            metadata = ExtendedDocumentMetadata(
                filename=filename,
                file_path=file_path,
                content_length=len(content),
                chunk_count=0,  # Will be updated after chunking
                indexed_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                **metadata_dict,
            )

            logger.info(f"Extracted metadata for: {filename}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to extract metadata for {filename}: {e}")
            # Fallback to filename-based extraction
            return self._fallback_extract(filename, content, file_path)

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON object found in response")

            # Parse JSON
            data = json.loads(json_str)

            # Validate required fields
            required_fields = [
                "entity",
                "entity_normalized",
                "penalty_type",
                "date",
                "jurisdiction",
                "document_type",
            ]

            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response[:500]}...")
            raise

    def _fallback_extract(
        self, filename: str, content: str, file_path: str
    ) -> ExtendedDocumentMetadata:
        """
        Fallback metadata extraction from filename.

        Expected filename format: {entity}_{penalty_type}_{year}.txt
        Example: 玉山銀行_洗錢防制_2020.txt
        """
        logger.warning(f"Using fallback extraction for: {filename}")

        # Parse filename
        stem = Path(filename).stem
        parts = stem.split("_")

        # Default values
        entity = parts[0] if len(parts) > 0 else "未知機構"
        penalty_type = parts[1] if len(parts) > 1 else "未知違規類型"
        year_str = parts[2] if len(parts) > 2 else "2020"

        # Try to extract year
        try:
            year_ad = int(year_str)
            year_roc = year_ad - 1911
            date = f"{year_ad}-01-01"  # Default to Jan 1st
        except ValueError:
            year_ad = 2020
            year_roc = 109
            date = "2020-01-01"

        return ExtendedDocumentMetadata(
            filename=filename,
            file_path=file_path,
            entity=entity,
            entity_normalized=entity,  # Same as entity for fallback
            penalty_type=penalty_type,
            penalty_amount=None,
            date=date,
            year_roc=year_roc,
            year_ad=year_ad,
            jurisdiction="金管會",  # Default
            document_type="裁罰書",  # Default
            case_number=None,
            content_length=len(content),
            chunk_count=0,
            indexed_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

    async def extract_new(
        self, doc_id: str, filename: str, content: str
    ) -> MetadataExtractionResult:
        """
        Extract metadata using new DocumentMetadata model and direct OpenAI client.

        This method uses the enhanced extraction prompt with better structure,
        multiple violation types, keywords, and confidence scoring.

        Args:
            doc_id: Document identifier
            filename: Document filename
            content: Full document content

        Returns:
            MetadataExtractionResult with extracted metadata and operational info
        """
        if not self.use_new_model:
            raise ValueError(
                "extract_new() requires use_new_model=True in constructor"
            )

        start_time = time.time()

        # Get content preview (first 2000 chars for better context)
        content_preview = content[:2000]

        try:
            # Call OpenAI API directly
            # Note: response_format may not be supported by all models/endpoints
            api_params = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是台灣金融法律文件元資料提取專家。請仔細分析文件並提取完整的結構化元資料。",
                    },
                    {
                        "role": "user",
                        "content": self.NEW_EXTRACTION_PROMPT.format(
                            filename=filename, content_preview=content_preview
                        ),
                    },
                ],
                "temperature": 0.0,  # Deterministic for metadata extraction
            }

            # Only add response_format for OpenAI models (not Ollama)
            if not self.model_name.startswith("ollama/"):
                api_params["response_format"] = {"type": "json_object"}

            response = await self.openai_client.chat.completions.create(**api_params)

            # Extract response
            response_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Estimate cost (GPT-4o-mini pricing: $0.15/1M input, $0.60/1M output)
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            cost_usd = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000

            # Log response for debugging
            logger.debug(f"LLM response preview: {response_content[:200] if response_content else '(empty)'}...")

            # Parse JSON response
            metadata_dict = self._parse_new_json_response(response_content)

            # Create DocumentMetadata object
            metadata = DocumentMetadata(**metadata_dict)

            processing_time = time.time() - start_time

            logger.info(
                f"Extracted metadata for {filename}: confidence={metadata.extraction_confidence:.2f}, "
                f"tokens={tokens_used}, cost=${cost_usd:.4f}, time={processing_time:.2f}s"
            )

            return MetadataExtractionResult(
                doc_id=doc_id,
                metadata=metadata,
                success=True,
                error=None,
                processing_time=processing_time,
                llm_tokens_used=tokens_used,
                llm_cost_usd=cost_usd,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Metadata extraction failed: {str(e)}"
            logger.error(f"{error_msg} (doc_id={doc_id})")

            return MetadataExtractionResult(
                doc_id=doc_id,
                metadata=None,
                success=False,
                error=error_msg,
                processing_time=processing_time,
                llm_tokens_used=None,
                llm_cost_usd=None,
            )

    def _parse_new_json_response(self, response: str) -> dict:
        """
        Parse JSON from LLM response for new DocumentMetadata model.

        Args:
            response: Raw LLM response (may be JSON or markdown-wrapped JSON)

        Returns:
            Dictionary with metadata fields

        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            # Extract JSON from markdown code blocks if present
            json_str = response.strip()

            # Try to extract from ```json ... ``` blocks
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to extract from ``` ... ``` blocks (without json tag)
                json_match = re.search(r"```\s*(\{.*?\})\s*```", json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                # Otherwise assume it's raw JSON

            # Parse JSON
            data = json.loads(json_str)

            # Validate required fields
            required_fields = [
                "title",
                "description",
                "document_type",
                "extraction_confidence",
            ]

            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate document_type
            valid_types = ["裁罰書", "判決書", "法規", "新聞", "研究報告", "其他"]
            if data["document_type"] not in valid_types:
                logger.warning(
                    f"Invalid document_type: {data['document_type']}, defaulting to '其他'"
                )
                data["document_type"] = "其他"

            # Validate confidence score
            confidence = data["extraction_confidence"]
            if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
                logger.warning(
                    f"Invalid confidence score: {confidence}, defaulting to 0.5"
                )
                data["extraction_confidence"] = 0.5

            # Set extraction_method
            data["extraction_method"] = "llm"

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response[:500]}...")
            raise ValueError(f"Invalid JSON in LLM response: {e}")
        except Exception as e:
            logger.error(f"Failed to validate metadata: {e}")
            raise

    def extract_batch(
        self, documents: list[tuple[str, str, str]]
    ) -> list[MetadataExtractionResult]:
        """
        Extract metadata from multiple documents in batch.

        Args:
            documents: List of (doc_id, filename, content) tuples

        Returns:
            List of MetadataExtractionResult objects
        """
        if not self.use_new_model:
            raise ValueError(
                "extract_batch() requires use_new_model=True in constructor"
            )

        import asyncio

        async def extract_all():
            tasks = [
                self.extract_new(doc_id, filename, content)
                for doc_id, filename, content in documents
            ]
            return await asyncio.gather(*tasks)

        return asyncio.run(extract_all())

    async def extract_metadata(self, content: str, filename: str) -> dict:
        """
        Simple wrapper for metadata extraction that returns a dict.

        This is used by the API endpoint for single document extraction.

        Args:
            content: Full document content
            filename: Document filename

        Returns:
            Dictionary with extracted metadata fields
        """
        # Use new model by default
        if not self.use_new_model:
            # Initialize new model if not already done
            self.__init__(use_new_model=True)

        # Extract metadata
        result = await self.extract_new(
            doc_id="temp",  # Temporary ID, not stored
            filename=filename,
            content=content
        )

        if not result.success or not result.metadata:
            raise Exception(result.error or "Metadata extraction failed")

        # Convert DocumentMetadata to dict
        metadata_dict = {
            "document_type": result.metadata.document_type,
            "issuing_authority": result.metadata.issuing_authority,
            "related_institutions": result.metadata.related_institutions,
            "violation_types": result.metadata.violation_types,
            "penalty_amount": result.metadata.penalty_amount,
            "keywords": result.metadata.keywords,
            "confidence": result.metadata.extraction_confidence,
        }

        return metadata_dict
