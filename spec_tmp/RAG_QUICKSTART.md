# RAG Pipeline Quick Start

## Overview

The document processing pipeline is now implemented with RAG (Retrieval-Augmented Generation) support. The system can now:

1. Load legal documents from TXT files
2. Chunk them intelligently (preserving Chinese text structure)
3. Generate embeddings with OpenAI
4. Index them in Chroma vector database
5. Retrieve relevant chunks for queries
6. Synthesize answers from retrieved documents

## 📁 File Structure

```
backend/
├── data/
│   ├── documents/                    # Put your TXT files here
│   │   ├── 玉山銀行_洗錢防制裁罰_2020.txt
│   │   └── 國泰世華銀行_內線交易_2021.txt
│   └── vector_db/                    # Chroma persistence (auto-created)
├── scripts/
│   └── index_documents.py            # Indexing script
└── src/finagent/document_processing/
    ├── loader.py                     # Document loader
    ├── chunker.py                    # Chinese text chunking
    ├── embeddings.py                 # OpenAI embeddings
    ├── indexer.py                    # Chroma indexing
    └── retriever.py                  # RAG retrieval
```

## 🚀 Getting Started

### Step 1: Prepare Documents

Add your legal documents (TXT format, UTF-8 encoding) to `backend/data/documents/`:

```bash
cd backend
mkdir -p data/documents

# Sample documents are already provided:
# - 玉山銀行_洗錢防制裁罰_2020.txt
# - 國泰世華銀行_內線交易_2021.txt
```

### Step 2: Set OpenAI API Key

Make sure your `.env` file has the OpenAI API key:

```bash
cd backend
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Step 3: Index Documents

Run the indexing script to process and index all documents:

```bash
cd backend
uv run python scripts/index_documents.py
```

Expected output:
```
🚀 Starting document indexing...

📄 Loading documents...
   Found 2 documents:
   - 玉山銀行_洗錢防制裁罰_2020.txt (5234 bytes)
   - 國泰世華銀行_內線交易_2021.txt (6891 bytes)

🔍 Indexing documents...

   Processing: 玉山銀行_洗錢防制裁罰_2020.txt
   ✅ Indexed 12 chunks

   Processing: 國泰世華銀行_內線交易_2021.txt
   ✅ Indexed 15 chunks

📊 Indexing complete!
   Total chunks in collection: 27
   Collection: legal_documents
   Persist directory: ./data/vector_db

✨ Done!
```

### Step 4: Start Backend

```bash
uv run uvicorn finagent.main:app --reload
```

### Step 5: Query with CLI

```bash
# In a new terminal
uv run finagent
```

Try these queries:
```
玉山銀行洗錢防制裁罰
國泰世華銀行內線交易
洗錢防制法違規
客戶盡職調查缺失
```

## 💡 How It Works

### 1. Document Loading

```python
from finagent.document_processing import DocumentLoader

loader = DocumentLoader(base_path="./data/documents")

# Load single file
doc = loader.load_txt("玉山銀行_洗錢防制裁罰_2020.txt")

# Load all files in directory
docs = loader.load_directory(".", pattern="*.txt")
```

### 2. Text Chunking

```python
from finagent.document_processing import ChineseTextChunker

chunker = ChineseTextChunker(
    chunk_size=500,          # Characters per chunk
    chunk_overlap=50,        # Overlap for context
    preserve_paragraphs=True # Keep paragraphs intact
)

chunks = chunker.chunk_text(document.content, doc_id=document.id)
```

### 3. Embedding Generation

```python
from finagent.document_processing import EmbeddingGenerator

generator = EmbeddingGenerator()

# Single embedding
embedding = generator.generate_embedding("查詢文字")

# Batch embeddings
embeddings = generator.generate_embeddings_batch(["文字1", "文字2", "文字3"])
```

### 4. Indexing

```python
from finagent.document_processing import DocumentIndexer

indexer = DocumentIndexer(
    collection_name="legal_documents",
    persist_directory="./data/vector_db"
)

# Index a document
chunks_count = indexer.index_document(document)

# Check if document exists
exists = indexer.document_exists(doc_id="doc_123")
```

### 5. Retrieval

```python
from finagent.document_processing import DocumentRetriever

retriever = DocumentRetriever(collection_name="legal_documents")

# Retrieve relevant chunks
chunks = retriever.retrieve(
    query="玉山銀行洗錢防制",
    n_results=5
)

# Format as context for LLM
context = retriever.format_context(chunks)
```

## 📊 What Happens During a Query

1. **User submits query** via CLI: `玉山銀行洗錢防制裁罰`

2. **Embedding generation**: Query is converted to vector embedding

3. **Vector search**: Chroma finds the 5 most similar document chunks

4. **Citation extraction**: System identifies source documents

5. **Answer synthesis**: Orchestrator combines chunks into structured answer

6. **Response display**: CLI shows formatted results with citations

## 🔍 Example Query Flow

**Query**: `玉山銀行洗錢防制裁罰`

**Retrieved Chunks** (simplified):
```
Chunk 1 (score: 0.12):
玉山商業銀行股份有限公司因違反洗錢防制法第6條及銀行法相關規定，
處新臺幣貳億伍仟萬元罰鍰。

Chunk 2 (score: 0.18):
該銀行對於高風險客戶之身分驗證程序不確實，未能充分瞭解客戶背景
及交易目的...

Chunk 3 (score: 0.24):
可疑交易監控系統之警示參數設定過於寬鬆，導致部分可疑交易未能及
時觸發警示...
```

**Generated Answer**:
```
執行摘要:
找到 5 筆洗錢防制相關的裁罰案件資訊。

關鍵發現:
• 玉山商業銀行股份有限公司因違反洗錢防制法第6條及銀行法相關規定... [引用1]
• 該銀行對於高風險客戶之身分驗證程序不確實... [引用1]
• 可疑交易監控系統之警示參數設定過於寬鬆... [引用1]

引用清單:
[1] 玉山銀行_洗錢防制裁罰_2020.txt
    類型: enforcement_document
    權威: primary

信心評分: 高 (85%)
找到 5 筆相關文件，資料來源充足且具權威性
```

## 🛠️ Advanced Usage

### Re-index Everything

```bash
# Clear and re-index all documents
uv run python -c "
from finagent.document_processing import DocumentIndexer, DocumentLoader

indexer = DocumentIndexer()
indexer.clear_collection()

loader = DocumentLoader()
docs = loader.load_directory('.', pattern='*.txt')

for doc in docs:
    indexer.index_document(doc)
    print(f'Indexed: {doc.metadata[\"filename\"]}')
"
```

### Add New Documents

1. Drop TXT files into `data/documents/`
2. Run indexing script again:
   ```bash
   uv run python scripts/index_documents.py
   ```
3. New documents are automatically indexed (existing ones skipped)

### Query Statistics

```python
from finagent.document_processing import DocumentRetriever

retriever = DocumentRetriever()
stats = retriever.get_stats()

print(stats)
# {
#   'exists': True,
#   'collection_name': 'legal_documents',
#   'total_chunks': 27,
#   'persist_directory': './data/vector_db'
# }
```

## 📝 Document Format Guidelines

### TXT File Requirements

1. **Encoding**: UTF-8
2. **Language**: Traditional Chinese (繁體中文)
3. **Structure**: Use double newlines for paragraph breaks

### Recommended Structure

```
標題

主文

事實

一、違規事實
（一）客戶盡職調查措施
1. 具體內容...

理由

一、裁罰理由
...

依據

一、法律依據
二、相關規定
```

### Best Practices

1. **Clear sections**: Use headers like「一、」「（一）」「1.」
2. **Paragraph breaks**: Separate ideas with double newlines
3. **Metadata in filename**: Include entity, violation type, year
   - ✅ `玉山銀行_洗錢防制裁罰_2020.txt`
   - ❌ `document1.txt`

## 🐛 Troubleshooting

### No results for queries

**Problem**: Queries return no results

**Solutions**:
1. Check if documents are indexed:
   ```bash
   uv run python -c "from finagent.document_processing import DocumentRetriever; print(DocumentRetriever().get_stats())"
   ```
2. Re-run indexing script
3. Try broader keywords

### Indexing fails

**Problem**: `index_documents.py` fails

**Solutions**:
1. Check OpenAI API key in `.env`
2. Verify documents are UTF-8 encoded
3. Check for empty files
4. Review error messages for specific issues

### Out of memory

**Problem**: Large documents cause memory issues

**Solutions**:
1. Reduce chunk size in `ChineseTextChunker`:
   ```python
   chunker = ChineseTextChunker(chunk_size=300)  # Smaller chunks
   ```
2. Process documents in smaller batches
3. Increase system RAM

## 📈 Next Steps

This MVP RAG pipeline provides the foundation. Future enhancements:

1. **LLM Integration**: Use GPT-4 to generate better summaries
2. **PDF Support**: Add PDF loader alongside TXT
3. **Metadata Extraction**: Parse case numbers, dates, penalties automatically
4. **Multi-hop Reasoning**: Chain multiple queries for complex research
5. **Citation Validation**: Verify page numbers and sections
6. **FSC Integration**: Scrape real enforcement data

## 🎯 Current Capabilities

✅ TXT document loading
✅ Smart Chinese text chunking
✅ OpenAI embedding generation
✅ Chroma vector database
✅ Semantic search retrieval
✅ Citation extraction
✅ Answer synthesis
✅ CLI integration

## 🔮 Coming Soon

⏳ LLM-powered analysis
⏳ PDF document support
⏳ FSC data scraping
⏳ Advanced metadata extraction
⏳ Multi-document comparison

---

**You're all set!** The RAG pipeline is ready to use. Add more legal documents to `data/documents/` and run the indexing script to expand your knowledge base.
