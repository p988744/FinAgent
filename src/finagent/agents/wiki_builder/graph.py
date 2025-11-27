"""LangGraph workflow for the WikiBuilder agent.

This workflow processes uploaded documents through:
1. Load document
2. Extract metadata (LLM-powered)
3. Extract concepts (entities, topics, regulations)
4. Chunk document
5. Index chunks to vector DB
6. Build/update categories
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from finagent.agents.wiki_builder.models import (
    CategoryUpdate,
    Concept,
    ExtractedMetadata,
    ProcessingStage,
    TextChunk,
    WikiBuilderState,
)
from finagent.config import settings
from finagent.database.document_db import DocumentDatabase
from finagent.document_processing.chunker import ChineseTextChunker
from finagent.document_processing.embeddings import EmbeddingGenerator
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.loader import Document, DocumentLoader
from finagent.wiki.category_builder import CategoryBuilder

logger = logging.getLogger(__name__)


# Pydantic models for LLM output parsing
class MetadataOutput(BaseModel):
    """Output schema for metadata extraction."""

    title: str = Field(description="文件標題")
    description: str = Field(description="2-3句文件摘要")
    document_type: str = Field(description="文件類型：裁罰書、判決書、法規、新聞、其他")
    issuing_authority: Optional[str] = Field(default=None, description="發文機關")
    case_number: Optional[str] = Field(default=None, description="案號")
    document_date: Optional[str] = Field(default=None, description="文件日期 YYYY-MM-DD")
    related_institutions: list[str] = Field(default_factory=list, description="涉及機構")
    violation_types: list[str] = Field(default_factory=list, description="違規類型")
    penalty_amount: Optional[str] = Field(default=None, description="裁罰金額")
    keywords: list[str] = Field(default_factory=list, description="關鍵詞")
    extraction_confidence: float = Field(default=0.8, description="信心分數 0-1")


class ConceptsOutput(BaseModel):
    """Output schema for concept extraction."""

    concepts: list[dict] = Field(description="提取的概念列表")


class WikiBuilderWorkflow:
    """LangGraph workflow for document processing and indexing."""

    # Prompts
    METADATA_PROMPT = """你是台灣金融法律文件元資料提取專家。請分析以下文件並提取完整的結構化元資料。

**文件資訊**
檔名：{filename}
內容摘要（前2000字）：
{content_preview}

請以 JSON 格式提取以下元資料：

{{
  "title": "文件標題（如：金融監督管理委員會裁罰書 - 玉山銀行洗錢防制違規）",
  "description": "2-3句文件摘要，說明主要內容、處分對象、違規事項及結果",
  "document_type": "文件類型（裁罰書、判決書、法規、新聞、研究報告、或其他）",
  "issuing_authority": "發文機關（金管會、銀行局、證券期貨局、保險局、中央銀行、公平會、法院、或 null）",
  "case_number": "案號或文號（如：金管銀法字第10900123456號，無則為 null）",
  "document_date": "文件日期（YYYY-MM-DD格式，將民國年轉換為西元年，無則為 null）",
  "related_institutions": ["涉及的金融機構完整正式名稱列表"],
  "violation_types": ["違規類型列表（如：洗錢防制、內部控制、內線交易等）"],
  "penalty_amount": "裁罰金額字串（如：NT$250,000,000，無則為 null）",
  "keywords": ["5-10個關鍵詞，用於搜尋和分類"],
  "extraction_confidence": 0.0到1.0之間的信心分數
}}

**提取規則**：
1. 日期轉換：民國109年 = 2020年（民國年 + 1911）
2. 機構名稱：使用完整正式名稱
3. 所有字串使用繁體中文
4. 無法確定的欄位填 null 或空陣列"""

    CONCEPTS_PROMPT = """你是台灣金融法律概念提取專家。從以下文件中提取關鍵概念。

**文件資訊**
檔名：{filename}
內容：
{content}

請提取以下類型的概念並以 JSON 格式回答：

{{
  "concepts": [
    {{
      "name": "概念名稱",
      "concept_type": "類型（entity/topic/regulation/institution）",
      "confidence": 0.0-1.0,
      "source_text": "來源文本片段（選填）"
    }}
  ]
}}

**概念類型說明**：
- entity: 具體實體（人名、公司名、銀行名）
- topic: 主題概念（洗錢防制、內部控制、資訊安全）
- regulation: 法規引用（銀行法第X條、洗錢防制法）
- institution: 機構組織（金管會、銀行局、證券期貨局）

**提取規則**：
1. 每個類型提取 3-10 個最重要的概念
2. 優先提取高頻出現或核心重要的概念
3. 信心分數反映概念的明確程度
4. 所有名稱使用繁體中文"""

    def __init__(
        self,
        document_db: Optional[DocumentDatabase] = None,
        indexer: Optional[DocumentIndexer] = None,
        category_builder: Optional[CategoryBuilder] = None,
    ):
        """Initialize the WikiBuilder workflow.

        Args:
            document_db: DocumentDatabase instance
            indexer: DocumentIndexer instance
            category_builder: CategoryBuilder instance
        """
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.effective_llm_api_key,
            base_url=settings.effective_llm_base_url,
            temperature=0,
        )

        # Initialize components
        self.document_db = document_db or DocumentDatabase()
        self.indexer = indexer or DocumentIndexer()
        self.category_builder = category_builder or CategoryBuilder(db=self.document_db)
        self.chunker = ChineseTextChunker(
            chunk_size=500, chunk_overlap=50, preserve_paragraphs=True
        )
        self.loader = DocumentLoader()

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(WikiBuilderState)

        # Add nodes
        workflow.add_node("load_document", self.load_document_node)
        workflow.add_node("extract_metadata", self.extract_metadata_node)
        workflow.add_node("extract_concepts", self.extract_concepts_node)
        workflow.add_node("chunk_document", self.chunk_document_node)
        workflow.add_node("index_chunks", self.index_chunks_node)
        workflow.add_node("build_categories", self.build_categories_node)

        # Set entry point
        workflow.set_entry_point("load_document")

        # Add edges (linear flow)
        workflow.add_edge("load_document", "extract_metadata")
        workflow.add_edge("extract_metadata", "extract_concepts")
        workflow.add_edge("extract_concepts", "chunk_document")
        workflow.add_edge("chunk_document", "index_chunks")
        workflow.add_edge("index_chunks", "build_categories")
        workflow.add_edge("build_categories", END)

        return workflow.compile()

    def load_document_node(self, state: WikiBuilderState) -> dict:
        """Load document from file path."""
        logger.info(f"Loading document: {state['filename']}")

        try:
            # Generate document ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}"

            # Document is already loaded (content passed in state)
            # Just validate and prepare
            content = state.get("content", "")
            if not content:
                # Try to load from file
                file_path = Path(state["file_path"])
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")

            return {
                "doc_id": doc_id,
                "content": content,
                "document_loaded": True,
                "current_stage": ProcessingStage.LOADING.value,
                "progress": 10,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to load document: {e}")
            return {
                "document_loaded": False,
                "current_stage": ProcessingStage.ERROR.value,
                "error": str(e),
            }

    async def extract_metadata_node(self, state: WikiBuilderState) -> dict:
        """Extract metadata using LLM."""
        logger.info(f"Extracting metadata for: {state['filename']}")

        if not state.get("document_loaded"):
            return {
                "metadata_extracted": False,
                "error": "Document not loaded",
            }

        try:
            content = state["content"]
            content_preview = content[:2000] if len(content) > 2000 else content

            # Create prompt and chain
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是文件元資料提取專家。只輸出 JSON，不要添加其他文字。"),
                ("user", self.METADATA_PROMPT),
            ])

            chain = prompt | self.llm | JsonOutputParser()

            # Extract metadata
            result = await chain.ainvoke({
                "filename": state["filename"],
                "content_preview": content_preview,
            })

            # Validate and convert to ExtractedMetadata
            metadata = ExtractedMetadata(**result)

            return {
                "metadata": metadata.model_dump(),
                "metadata_extracted": True,
                "current_stage": ProcessingStage.EXTRACTING_METADATA.value,
                "progress": 30,
            }

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            # Continue with basic metadata
            return {
                "metadata": {
                    "title": state["filename"],
                    "description": f"文件：{state['filename']}",
                    "document_type": "其他",
                    "keywords": [],
                    "extraction_confidence": 0.0,
                },
                "metadata_extracted": True,
                "current_stage": ProcessingStage.EXTRACTING_METADATA.value,
                "progress": 30,
            }

    async def extract_concepts_node(self, state: WikiBuilderState) -> dict:
        """Extract concepts from document."""
        logger.info(f"Extracting concepts for: {state['filename']}")

        try:
            content = state["content"]
            # Use first 4000 chars for concept extraction
            content_preview = content[:4000] if len(content) > 4000 else content

            # Create prompt and chain
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是概念提取專家。只輸出 JSON，不要添加其他文字。"),
                ("user", self.CONCEPTS_PROMPT),
            ])

            chain = prompt | self.llm | JsonOutputParser()

            # Extract concepts
            result = await chain.ainvoke({
                "filename": state["filename"],
                "content": content_preview,
            })

            # Parse concepts
            concepts = []
            for c in result.get("concepts", []):
                try:
                    concept = Concept(**c)
                    concepts.append(concept.model_dump())
                except Exception:
                    continue

            return {
                "concepts": concepts,
                "concepts_extracted": True,
                "current_stage": ProcessingStage.EXTRACTING_CONCEPTS.value,
                "progress": 50,
            }

        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            return {
                "concepts": [],
                "concepts_extracted": True,
                "current_stage": ProcessingStage.EXTRACTING_CONCEPTS.value,
                "progress": 50,
            }

    def chunk_document_node(self, state: WikiBuilderState) -> dict:
        """Chunk document for indexing."""
        logger.info(f"Chunking document: {state['filename']}")

        try:
            content = state["content"]
            doc_id = state["doc_id"]

            # Chunk the document
            chunks = self.chunker.chunk_text(content, doc_id=doc_id)

            # Convert to dict format
            chunk_dicts = []
            for chunk in chunks:
                chunk_dicts.append({
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "metadata": chunk.metadata,
                })

            return {
                "chunks": chunk_dicts,
                "chunk_count": len(chunk_dicts),
                "current_stage": ProcessingStage.CHUNKING.value,
                "progress": 60,
            }

        except Exception as e:
            logger.error(f"Chunking failed: {e}")
            return {
                "chunks": [],
                "chunk_count": 0,
                "current_stage": ProcessingStage.ERROR.value,
                "error": str(e),
            }

    async def index_chunks_node(self, state: WikiBuilderState) -> dict:
        """Index chunks to vector database."""
        logger.info(f"Indexing {state.get('chunk_count', 0)} chunks for: {state['filename']}")

        try:
            # Create Document object for indexer
            doc = Document(
                id=state["doc_id"],
                content=state["content"],
                source=state["file_path"],
                metadata=state.get("metadata", {}),
            )

            # Index the document
            num_chunks = await self.indexer.index_document(doc)

            return {
                "indexed": True,
                "index_success": True,
                "chunk_count": num_chunks,
                "current_stage": ProcessingStage.INDEXING.value,
                "progress": 80,
            }

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            return {
                "indexed": False,
                "index_success": False,
                "current_stage": ProcessingStage.ERROR.value,
                "error": str(e),
            }

    def build_categories_node(self, state: WikiBuilderState) -> dict:
        """Build/update wiki categories from document metadata."""
        logger.info(f"Building categories for: {state['filename']}")

        try:
            # Build categories for this document
            results = self.category_builder.build_all_categories(clear_existing=False)

            # Convert to CategoryUpdate format
            category_updates = []
            for cat_type, count in results.items():
                if count > 0:
                    category_updates.append({
                        "category_type": cat_type,
                        "category_name": f"{cat_type}_category",
                        "doc_count": count,
                    })

            return {
                "categories_updated": category_updates,
                "current_stage": ProcessingStage.COMPLETE.value,
                "progress": 100,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Category building failed: {e}")
            # Don't fail the whole workflow for category building
            return {
                "categories_updated": [],
                "current_stage": ProcessingStage.COMPLETE.value,
                "progress": 100,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

    async def process(
        self,
        file_path: str,
        filename: str,
        content: Optional[str] = None,
    ) -> dict[str, Any]:
        """Process a document through the workflow.

        Args:
            file_path: Path to the document file
            filename: Original filename
            content: Optional pre-loaded content

        Returns:
            Final workflow state
        """
        # Initialize state
        initial_state: WikiBuilderState = {
            "file_path": file_path,
            "filename": filename,
            "content": content or "",
            "doc_id": None,
            "document_loaded": False,
            "metadata": None,
            "metadata_extracted": False,
            "concepts": None,
            "concepts_extracted": False,
            "chunks": None,
            "chunk_count": 0,
            "indexed": False,
            "index_success": False,
            "categories_updated": None,
            "current_stage": ProcessingStage.LOADING.value,
            "progress": 0,
            "error": None,
            "started_at": None,
            "completed_at": None,
        }

        # Run workflow
        final_state = await self.graph.ainvoke(initial_state)

        return final_state

    async def stream_process(
        self,
        file_path: str,
        filename: str,
        content: Optional[str] = None,
    ):
        """Stream document processing with progress updates.

        Args:
            file_path: Path to the document file
            filename: Original filename
            content: Optional pre-loaded content

        Yields:
            Tuples of (node_name, state_update)
        """
        # Initialize state
        initial_state: WikiBuilderState = {
            "file_path": file_path,
            "filename": filename,
            "content": content or "",
            "doc_id": None,
            "document_loaded": False,
            "metadata": None,
            "metadata_extracted": False,
            "concepts": None,
            "concepts_extracted": False,
            "chunks": None,
            "chunk_count": 0,
            "indexed": False,
            "index_success": False,
            "categories_updated": None,
            "current_stage": ProcessingStage.LOADING.value,
            "progress": 0,
            "error": None,
            "started_at": None,
            "completed_at": None,
        }

        # Stream workflow execution
        async for event in self.graph.astream(initial_state):
            for node_name, state_update in event.items():
                yield node_name, state_update
