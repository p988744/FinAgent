"""Extract structured metadata from documents using LLM."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finagent.config import settings
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

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.effective_llm_model,
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
