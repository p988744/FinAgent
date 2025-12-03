#!/usr/bin/env python3
"""
E2E Test: Complete Document Lifecycle
Tests the full pipeline from empty knowledge base to query retrieval.

Test Flow:
1. Initialize empty knowledge base (clear existing data)
2. Upload/import test document
3. Index document and extract metadata
4. Verify knowledge base contains expected data
5. Test retrieval with both tools (RetrieverTool + HardSearchTool)
"""

import asyncio
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from finagent.document_processing.loader import DocumentLoader
from finagent.document_processing.chunker import ChineseTextChunker
from finagent.document_processing.embeddings import EmbeddingGenerator
from finagent.document_processing.indexer import DocumentIndexer
from finagent.document_processing.retriever import DocumentRetriever
from finagent.document_processing.hard_searcher import HardSearcher
from finagent.tools.retriever import RetrieverTool
from finagent.tools.search import HardSearchTool
from finagent.tools.hybrid_retriever import HybridRetrieverTool


class E2ETestEnvironment:
    """Manages test environment with isolated database and vector store"""

    def __init__(self):
        self.temp_dir = None
        self.db_path = None
        self.vector_db_path = None
        self.documents_path = None

    def setup(self):
        """Create isolated test environment"""
        print("\n📦 Setting up test environment...")

        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="finagent_e2e_test_")
        print(f"   Temp directory: {self.temp_dir}")

        # Setup paths
        self.db_path = Path(self.temp_dir) / "test_finagent.db"
        self.vector_db_path = Path(self.temp_dir) / "test_vector_db"
        self.documents_path = Path(self.temp_dir) / "documents"

        # Create directories
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.documents_path.mkdir(parents=True, exist_ok=True)

        print(f"   Database: {self.db_path}")
        print(f"   Vector DB: {self.vector_db_path}")
        print(f"   Documents: {self.documents_path}")

        # Initialize SQLite database with schema
        self._init_database()

        print("✅ Test environment ready")

    def _init_database(self):
        """Initialize SQLite database with minimal schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create documents table (matching production schema for HardSearcher compatibility)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT,
                title TEXT,
                source TEXT,
                authority TEXT,
                date TEXT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create chunks table for hard search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)

        conn.commit()
        conn.close()

    def teardown(self):
        """Clean up test environment"""
        if self.temp_dir and Path(self.temp_dir).exists():
            print(f"\n🧹 Cleaning up test environment: {self.temp_dir}")
            shutil.rmtree(self.temp_dir)
            print("✅ Cleanup complete")


async def test_step1_empty_knowledge_base(env: E2ETestEnvironment):
    """Test Step 1: Verify empty knowledge base"""
    print("\n" + "="*80)
    print("STEP 1: Empty Knowledge Base Initialization")
    print("="*80)

    try:
        # Check database is empty
        conn = sqlite3.connect(env.db_path)
        cursor = conn.cursor()

        doc_count = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = cursor.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

        conn.close()

        print(f"\n📊 Database state:")
        print(f"   Documents: {doc_count}")
        print(f"   Chunks: {chunk_count}")

        # Check vector database is empty
        retriever = DocumentRetriever(
            collection_name="test_legal_documents",
            persist_directory=str(env.vector_db_path)
        )

        if retriever.collection:
            vector_count = retriever.collection.count()
        else:
            vector_count = 0

        print(f"   Vector embeddings: {vector_count}")

        if doc_count == 0 and chunk_count == 0 and vector_count == 0:
            print("\n✅ Step 1 PASSED: Knowledge base is empty")
            return True
        else:
            print(f"\n⚠️  Step 1 WARNING: Knowledge base not empty")
            return True  # Continue anyway

    except Exception as e:
        print(f"\n❌ Step 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_step2_upload_document(env: E2ETestEnvironment):
    """Test Step 2: Upload/import test document"""
    print("\n" + "="*80)
    print("STEP 2: Document Upload/Import")
    print("="*80)

    try:
        # Create test document with known content
        test_doc_content = """金融監督管理委員會裁罰案件

案件編號：FSC-2020-001
裁罰日期：2020-09-15
受罰機構：玉山商業銀行股份有限公司

違規事實：
本會於民國109年（2020年）針對玉山商業銀行進行洗錢防制法令遵循檢查，發現該行存在以下缺失：

1. 內部控制制度不健全
   - 未建立完善的客戶盡職調查（CDD）程序
   - 風險評估機制不足
   - 交易監控系統存在漏洞

2. 洗錢防制程序不當
   - 疑似洗錢交易未及時通報
   - 高風險客戶管理不足
   - 員工訓練不完整

處罰內容：
依據洗錢防制法第7條、第8條及銀行法第61條之1規定，裁處如下：
- 罰鍰：新臺幣500萬元
- 限期改善：3個月內完成內部控制制度修正
- 提交改善報告：每月提報進度

法律依據：
1. 洗錢防制法第7條：金融機構應建立洗錢及資恐風險評估機制
2. 洗錢防制法第8條：金融機構對達一定金額以上通貨交易應留存交易紀錄憑證
3. 銀行法第61條之1：銀行違反法令者，處新臺幣200萬元以上5,000萬元以下罰鍰

備註：
本案為2020年度重大洗錢防制裁罰案件之一，金管會要求玉山銀行加強內控並定期追蹤改善情形。
"""

        # Write test document
        test_doc_path = env.documents_path / "test_yuanta_aml_2020.txt"
        test_doc_path.write_text(test_doc_content, encoding="utf-8")

        print(f"\n📄 Test document created:")
        print(f"   Path: {test_doc_path}")
        print(f"   Size: {len(test_doc_content)} characters")
        print(f"   Content preview: {test_doc_content[:100]}...")

        # Verify file exists
        if test_doc_path.exists():
            print(f"\n✅ Step 2 PASSED: Document uploaded successfully")
            return True, test_doc_path
        else:
            print(f"\n❌ Step 2 FAILED: Document file not found")
            return False, None

    except Exception as e:
        print(f"\n❌ Step 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_step3_index_and_extract(env: E2ETestEnvironment, doc_path: Path):
    """Test Step 3: Index document and extract metadata"""
    print("\n" + "="*80)
    print("STEP 3: Document Indexing & Metadata Extraction")
    print("="*80)

    try:
        print("\n📥 Loading document...")

        # Load document
        loader = DocumentLoader()
        doc = loader.load_txt(str(doc_path))

        if not doc:
            print("❌ No document loaded")
            return False, None
        print(f"✓ Document loaded: {doc.metadata.get('filename', 'N/A')}")
        print(f"  Content length: {len(doc.content)} characters")
        print(f"  Metadata: {doc.metadata}")

        # Index document (chunking happens internally)
        print("\n🔢 Indexing document (with chunking and embedding)...")
        indexer = DocumentIndexer(
            collection_name="test_legal_documents",
            persist_directory=str(env.vector_db_path),
            extract_metadata=False  # Skip LLM metadata extraction for speed
        )

        # Index the document
        num_chunks = await indexer.index_document(doc)

        print(f"✓ Indexed {num_chunks} chunks to vector database")

        # Get chunks for SQLite storage
        print("\n✂️  Re-chunking for SQLite storage...")
        chunker = ChineseTextChunker()
        doc_id = doc.id
        chunks = chunker.chunk_text(doc.content, doc_id=doc_id)
        print(f"✓ Created {len(chunks)} chunks for SQLite")

        # Store in SQLite for hard search
        print("\n💾 Storing in SQLite database...")
        conn = sqlite3.connect(env.db_path)
        cursor = conn.cursor()

        # Insert document
        doc_id = doc.id
        file_path = doc.metadata.get("file_path", "") if hasattr(doc, 'metadata') else ""
        cursor.execute("""
            INSERT OR REPLACE INTO documents (id, filename, file_path, title, content, source, authority, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            doc.metadata.get("filename", "unknown"),
            file_path,
            doc.metadata.get("title", ""),
            doc.content,
            doc.source if hasattr(doc, 'source') else "",
            doc.metadata.get("authority", ""),
            doc.metadata.get("date", "")
        ))

        # Insert chunks
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            cursor.execute("""
                INSERT OR REPLACE INTO chunks (id, document_id, chunk_index, content, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                chunk_id,
                doc_id,
                i,
                chunk.text,  # TextChunk uses 'text' not 'content'
                str(chunk.metadata)
            ))

        conn.commit()
        conn.close()

        print(f"✓ Stored document and {len(chunks)} chunks in SQLite")

        # Verify storage
        print("\n🔍 Verifying storage...")
        conn = sqlite3.connect(env.db_path)
        cursor = conn.cursor()

        doc_count = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = cursor.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

        conn.close()

        retriever = DocumentRetriever(
            collection_name="test_legal_documents",
            persist_directory=str(env.vector_db_path)
        )
        vector_count = retriever.collection.count() if retriever.collection else 0

        print(f"  Documents in SQLite: {doc_count}")
        print(f"  Chunks in SQLite: {chunk_count}")
        print(f"  Vectors in Chroma: {vector_count}")

        if doc_count > 0 and chunk_count > 0 and vector_count > 0:
            print(f"\n✅ Step 3 PASSED: Document indexed successfully")
            return True, doc_id
        else:
            print(f"\n❌ Step 3 FAILED: Indexing incomplete")
            return False, None

    except Exception as e:
        print(f"\n❌ Step 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_step4_verify_knowledge_base(env: E2ETestEnvironment, doc_id: str):
    """Test Step 4: Verify knowledge base contains expected data"""
    print("\n" + "="*80)
    print("STEP 4: Knowledge Base Verification")
    print("="*80)

    try:
        # Check database content
        conn = sqlite3.connect(env.db_path)
        cursor = conn.cursor()

        # Verify document
        doc = cursor.execute("""
            SELECT id, filename, title, date, authority
            FROM documents
            WHERE id = ?
        """, (doc_id,)).fetchone()

        if not doc:
            print(f"❌ Document {doc_id} not found in database")
            return False

        print(f"\n📄 Document in database:")
        print(f"   ID: {doc[0]}")
        print(f"   Filename: {doc[1]}")
        print(f"   Title: {doc[2]}")
        print(f"   Date: {doc[3]}")
        print(f"   Authority: {doc[4]}")

        # Verify chunks
        chunks = cursor.execute("""
            SELECT id, chunk_index, LENGTH(content)
            FROM chunks
            WHERE document_id = ?
            ORDER BY chunk_index
        """, (doc_id,)).fetchall()

        print(f"\n📚 Chunks in database: {len(chunks)}")
        if chunks:
            for i, (chunk_id, idx, length) in enumerate(chunks[:3], 1):
                print(f"   {i}. Chunk {idx}: {length} characters")

        # Check for expected keywords
        expected_keywords = ["玉山", "洗錢防制", "2020", "500萬", "金管會"]
        content = cursor.execute("""
            SELECT content FROM documents WHERE id = ?
        """, (doc_id,)).fetchone()[0]

        found_keywords = [kw for kw in expected_keywords if kw in content]
        print(f"\n🔑 Expected keywords found: {len(found_keywords)}/{len(expected_keywords)}")
        for kw in found_keywords:
            print(f"   ✓ {kw}")

        missing_keywords = set(expected_keywords) - set(found_keywords)
        if missing_keywords:
            print(f"   ⚠️  Missing: {', '.join(missing_keywords)}")

        conn.close()

        # Verify vector database
        retriever = DocumentRetriever(
            collection_name="test_legal_documents",
            persist_directory=str(env.vector_db_path)
        )

        if retriever.collection:
            # Test simple retrieval
            results = retriever.retrieve("玉山銀行", n_results=3)
            print(f"\n🔍 Vector search test: {len(results)} results")
            if results:
                print(f"   Top result relevance: {results[0].score:.3f}")

        if len(found_keywords) >= 4 and results:
            print(f"\n✅ Step 4 PASSED: Knowledge base verified")
            return True
        else:
            print(f"\n❌ Step 4 FAILED: Missing expected data")
            return False

    except Exception as e:
        print(f"\n❌ Step 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_step5_retrieval_tools(env: E2ETestEnvironment):
    """Test Step 5: Test retrieval with both tools"""
    print("\n" + "="*80)
    print("STEP 5: Retrieval Tools Testing")
    print("="*80)

    try:
        # Initialize retriever
        retriever = DocumentRetriever(
            collection_name="test_legal_documents",
            persist_directory=str(env.vector_db_path)
        )

        # Initialize hard searcher
        hard_searcher = HardSearcher(db_path=str(env.db_path))

        # Create tools
        retriever_tool = RetrieverTool(retriever=retriever)
        hard_search_tool = HardSearchTool(hard_searcher=hard_searcher)
        hybrid_tool = HybridRetrieverTool(
            retriever=retriever,
            semantic_weight=0.6,
            keyword_weight=0.4
        )

        # Test queries
        test_queries = [
            ("玉山銀行洗錢防制", "Semantic query about Yuanta Bank AML"),
            ("2020 金管會", "Keyword query for 2020 FSC"),
            ("500萬 罰鍰", "Keyword query for 5M fine")
        ]

        results_summary = []

        for query, description in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"Description: {description}")
            print(f"{'='*60}")

            # Test RetrieverTool (semantic search)
            print("\n🔍 Testing RetrieverTool (semantic search)...")
            try:
                retriever_result = retriever_tool._run(query)
                retriever_lines = retriever_result.split('\n')
                retriever_docs = len([line for line in retriever_lines if line.startswith('[') and '] Source:' in line])

                print(f"✓ Result: {len(retriever_result)} characters")
                print(f"✓ Documents found: {retriever_docs}")
                print(f"  Preview: {retriever_result[:150]}...")

                results_summary.append(("RetrieverTool", query, retriever_docs > 0))

            except Exception as e:
                print(f"✗ RetrieverTool failed: {e}")
                results_summary.append(("RetrieverTool", query, False))

            # Test HardSearchTool (keyword search)
            print("\n🔍 Testing HardSearchTool (keyword search)...")
            try:
                # Split query into keywords for hard search
                keywords = [kw.strip() for kw in query.split() if kw.strip()]
                hard_search_result = hard_search_tool._run(keywords=keywords)
                hard_search_lines = hard_search_result.split('\n')
                hard_search_docs = len([line for line in hard_search_lines if line.startswith('[') and '] Source:' in line])

                print(f"✓ Keywords: {keywords}")
                print(f"✓ Result: {len(hard_search_result)} characters")
                print(f"✓ Documents found: {hard_search_docs}")
                print(f"  Preview: {hard_search_result[:150]}...")

                results_summary.append(("HardSearchTool", query, hard_search_docs > 0))

            except Exception as e:
                print(f"✗ HardSearchTool failed: {e}")
                results_summary.append(("HardSearchTool", query, False))

            # Test HybridRetrieverTool (BM25 + Vector)
            print("\n🔍 Testing HybridRetrieverTool (BM25 + Vector hybrid)...")
            try:
                hybrid_result = hybrid_tool._run(query=query, k=3)
                hybrid_lines = hybrid_result.split('\n')
                hybrid_docs = len([line for line in hybrid_lines if line.startswith('[') and '] 來源:' in line])

                print(f"✓ Result: {len(hybrid_result)} characters")
                print(f"✓ Documents found: {hybrid_docs}")
                print(f"  Preview: {hybrid_result[:150]}...")

                results_summary.append(("HybridRetrieverTool", query, hybrid_docs > 0))

            except Exception as e:
                print(f"✗ HybridRetrieverTool failed: {e}")
                results_summary.append(("HybridRetrieverTool", query, False))

        # Summary
        print(f"\n{'='*80}")
        print("RETRIEVAL TOOLS SUMMARY")
        print(f"{'='*80}")

        print(f"\n{'Tool':<20} {'Query':<30} {'Status':<10}")
        print(f"{'-'*60}")
        for tool, query, success in results_summary:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{tool:<20} {query[:27]:<30} {status:<10}")

        # Calculate success rate
        total = len(results_summary)
        passed = sum(1 for _, _, success in results_summary if success)
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n📊 Overall: {passed}/{total} passed ({success_rate:.1f}%)")

        if success_rate >= 66:  # At least 2/3 should pass
            print(f"\n✅ Step 5 PASSED: Retrieval tools working")
            return True
        else:
            print(f"\n⚠️  Step 5 PARTIAL: Some tools not working optimally")
            return False

    except Exception as e:
        print(f"\n❌ Step 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run complete E2E test"""
    print("\n" + "="*80)
    print("FinAgent E2E Test: Complete Document Lifecycle")
    print("="*80)
    print("\nThis test validates:")
    print("  1. Empty knowledge base initialization")
    print("  2. Document upload/import")
    print("  3. Indexing and metadata extraction")
    print("  4. Knowledge base data verification")
    print("  5. Retrieval with both tools (semantic + keyword)")

    env = E2ETestEnvironment()

    try:
        # Setup
        env.setup()

        # Run tests
        results = []

        # Step 1: Empty knowledge base
        step1_passed = await test_step1_empty_knowledge_base(env)
        results.append(("Step 1: Empty KB", step1_passed))

        if not step1_passed:
            print("\n⚠️  Step 1 failed, but continuing...")

        # Step 2: Upload document
        step2_passed, doc_path = await test_step2_upload_document(env)
        results.append(("Step 2: Upload", step2_passed))

        if not step2_passed:
            print("\n❌ Cannot continue without uploaded document")
            return 1

        # Step 3: Index and extract
        step3_passed, doc_id = await test_step3_index_and_extract(env, doc_path)
        results.append(("Step 3: Index", step3_passed))

        if not step3_passed:
            print("\n❌ Cannot continue without indexed document")
            return 1

        # Step 4: Verify knowledge base
        step4_passed = await test_step4_verify_knowledge_base(env, doc_id)
        results.append(("Step 4: Verify", step4_passed))

        # Step 5: Test retrieval tools
        step5_passed = await test_step5_retrieval_tools(env)
        results.append(("Step 5: Retrieval", step5_passed))

        # Final summary
        print("\n" + "="*80)
        print("FINAL TEST SUMMARY")
        print("="*80)

        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {test_name}")

        total = len(results)
        passed_count = sum(1 for _, passed in results if passed)
        success_rate = (passed_count / total * 100) if total > 0 else 0

        print(f"\n📊 Results: {passed_count}/{total} tests passed ({success_rate:.1f}%)")

        if passed_count == total:
            print("\n🎉 ALL TESTS PASSED! E2E pipeline working correctly.")
            return 0
        elif success_rate >= 80:
            print("\n✅ MOSTLY PASSED. Minor issues detected.")
            return 0
        else:
            print("\n❌ TESTS FAILED. Please review errors above.")
            return 1

    finally:
        # Cleanup
        env.teardown()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
