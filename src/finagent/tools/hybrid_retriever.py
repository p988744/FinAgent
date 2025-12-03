"""
Hybrid Retriever Tool - Combines BM25 keyword search with semantic vector search.

This module implements the industry-standard hybrid search approach using:
- BM25Retriever for keyword-based matching (in-memory)
- Vector Search for semantic similarity (Chroma)
- EnsembleRetriever for weighted ranking of combined results

Reference: https://python.langchain.com/docs/how_to/ensemble_retriever/
"""

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from finagent.document_processing.retriever import DocumentRetriever


class HybridSearchInput(BaseModel):
    """Input schema for hybrid search tool."""
    query: str = Field(description="研究查詢問題 (Search query)")
    k: int = Field(default=5, description="返回結果數量 (Number of results to return)")


class HybridRetrieverTool(BaseTool):
    """
    混合檢索工具 - 結合關鍵字搜尋與語義理解

    Hybrid search tool combining keyword matching (BM25) and semantic understanding (vector search).

    Use this tool when you need both:
    - Exact keyword matching (dates, numbers, specific terms)
    - Semantic understanding (concepts, related topics)

    Examples:
    - "2020年金管會裁罰500萬" → BM25 finds exact "2020", "500萬" + Vector finds related penalties
    - "玉山銀行洗錢防制" → BM25 finds exact bank name + Vector finds AML-related documents
    """

    name: str = "hybrid_search"
    description: str = """搜尋知識庫文件，結合語義理解與精確關鍵字匹配。

    適用情境：
    - 需要精確關鍵字（日期、金額、機構名稱）
    - 需要語義理解（概念、相關主題）
    - 需要高品質排序的綜合結果

    Search knowledge base using both semantic understanding and exact keyword matching.
    Best for queries requiring both precise terms and conceptual understanding."""

    args_schema: type[BaseModel] = HybridSearchInput
    retriever: DocumentRetriever = Field(exclude=True)

    # Ensemble weights (60% semantic, 40% keyword by default)
    semantic_weight: float = Field(default=0.6, exclude=True)
    keyword_weight: float = Field(default=0.4, exclude=True)

    def _run(self, query: str, k: int = 5) -> str:
        """
        Execute hybrid search combining BM25 and vector search.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Formatted search results with citations
        """
        try:
            # Step 1: Get all indexed documents from Chroma
            collection = self.retriever.collection
            all_data = collection.get(include=["documents", "metadatas"])

            if not all_data or not all_data.get("documents"):
                return "❌ 知識庫為空，請先索引文件。\n(Knowledge base is empty. Please index documents first.)"

            # Step 2: Convert to LangChain Document objects for BM25
            documents = [
                Document(page_content=doc, metadata=meta if meta else {})
                for doc, meta in zip(all_data["documents"], all_data["metadatas"])
            ]

            if not documents:
                return "❌ 無法載入文件。\n(Unable to load documents.)"

            # Step 3: Get vector search results (using native retriever)
            vector_results = self.retriever.retrieve(query=query, n_results=k)
            vector_docs = [
                Document(page_content=chunk.text, metadata=chunk.metadata)
                for chunk in vector_results
            ]

            # Step 4: Get BM25 keyword search results
            bm25_retriever = BM25Retriever.from_documents(documents, k=k)
            bm25_docs = bm25_retriever.invoke(query)

            # Step 5: Combine results with weighted scoring
            # Simple approach: interleave based on weights
            combined_docs = []
            semantic_count = int(k * self.semantic_weight)
            keyword_count = int(k * self.keyword_weight)

            # Take top results from each based on weights
            combined_docs.extend(vector_docs[:semantic_count])
            combined_docs.extend(bm25_docs[:keyword_count])

            # Deduplicate and limit to k results
            seen_content = set()
            results = []
            for doc in combined_docs:
                content_hash = hash(doc.page_content[:100])  # Hash first 100 chars
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    results.append(doc)
                    if len(results) >= k:
                        break

            # Step 7: Format output with citations
            if not results:
                return f"❌ 未找到相關文件：「{query}」\n(No relevant documents found for: \"{query}\")"

            output = []
            seen_sources = set()  # Deduplicate by source

            for i, doc in enumerate(results, 1):
                # Get metadata
                filename = doc.metadata.get("filename", "未知來源")
                source = doc.metadata.get("source", filename)

                # Skip duplicates
                if source in seen_sources:
                    continue
                seen_sources.add(source)

                # Format citation
                citation = f"[{len(output) + 1}] 來源: {source}"
                content = doc.page_content.strip()

                # Truncate long content
                if len(content) > 500:
                    content = content[:500] + "..."

                output.append(f"{citation}\n內容: {content}\n")

            if not output:
                return f"❌ 未找到相關文件：「{query}」\n(No relevant documents found for: \"{query}\")"

            header = f"🔍 混合檢索結果（語義 {int(self.semantic_weight*100)}% + 關鍵字 {int(self.keyword_weight*100)}%）\n"
            header += f"查詢: {query}\n"
            header += f"找到 {len(output)} 個相關文件:\n\n"

            return header + "\n---\n".join(output)

        except Exception as e:
            return f"❌ 混合檢索失敗: {str(e)}\n(Hybrid search failed: {str(e)})"

    async def _arun(self, query: str, k: int = 5) -> str:
        """Async version of _run (calls sync version)."""
        return self._run(query, k)


def create_hybrid_retriever_tool(
    retriever: DocumentRetriever,
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.4
) -> HybridRetrieverTool:
    """
    Factory function to create a HybridRetrieverTool.

    Args:
        retriever: DocumentRetriever instance with Chroma collection
        semantic_weight: Weight for vector search (0.0 to 1.0)
        keyword_weight: Weight for BM25 keyword search (0.0 to 1.0)

    Returns:
        Configured HybridRetrieverTool instance

    Example:
        >>> retriever = DocumentRetriever(collection_name="legal_documents")
        >>> tool = create_hybrid_retriever_tool(retriever, semantic_weight=0.7, keyword_weight=0.3)
        >>> result = tool.run("2020年金管會裁罰")
    """
    return HybridRetrieverTool(
        retriever=retriever,
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight
    )
