#!/bin/bash
# Script to verify reindex results

echo "=========================================="
echo "1. Checking finagent.db (Metadata Database)"
echo "=========================================="
echo ""

echo "Total documents in database:"
sqlite3 data/finagent.db "SELECT COUNT(*) as total_documents FROM documents;"
echo ""

echo "Indexed vs Unindexed:"
sqlite3 data/finagent.db "SELECT indexed, COUNT(*) as count FROM documents GROUP BY indexed;"
echo ""

echo "Total chunks across all documents:"
sqlite3 data/finagent.db "SELECT SUM(chunk_count) as total_chunks FROM documents;"
echo ""

echo "Documents by type:"
sqlite3 data/finagent.db "SELECT document_type, COUNT(*) as count FROM documents GROUP BY document_type ORDER BY count DESC LIMIT 5;"
echo ""

echo "Sample documents:"
sqlite3 -header -column data/finagent.db "SELECT doc_id, filename, indexed, chunk_count FROM documents LIMIT 5;"
echo ""

echo "=========================================="
echo "2. Checking vector_db/chroma.sqlite3 (Vector Database)"
echo "=========================================="
echo ""

echo "Total chunks in vector database:"
sqlite3 data/vector_db/chroma.sqlite3 "SELECT COUNT(*) FROM embeddings;" 2>/dev/null || echo "Table structure may vary - checking collection stats..."
echo ""

echo "=========================================="
echo "3. Summary"
echo "=========================================="
echo ""
echo "Expected after reindex of 492 documents:"
echo "  - finagent.db: 492 rows in documents table, all indexed=1"
echo "  - chroma.sqlite3: ~2,858+ embedding rows (chunks)"
echo "  - Average: ~5-6 chunks per document"
