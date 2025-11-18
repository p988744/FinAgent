# FinAgent Project Vision: Law & Banking Knowledge Management

## Mission Statement

**FinAgent is a comprehensive knowledge management platform for legal and banking professionals, enabling users to build, organize, and research their institutional knowledge base through intelligent document wikis and AI-powered research tools.**

## Core Product Goals

### 1. Document Wiki Management
**"Upload, organize, and visualize your legal knowledge"**

Users can:
- ✅ Upload legal documents (penalties, court decisions, regulations)
- ✅ Automatically organize documents into a structured wiki
- ✅ View document relationships and categories
- ✅ Browse knowledge by topic, institution, date, or violation type
- ✅ Delete documents and see wiki update dynamically
- ✅ Search and filter the document collection

**Key Features:**
- **Dynamic Wiki Generation**: Automatically build document wiki on upload/delete
- **Knowledge Graph**: Visual representation of document relationships
- **Smart Categorization**: Auto-categorize by type, authority, topic, institution
- **Statistics Dashboard**: Overview of knowledge coverage
- **Document Browser**: Explore documents like a wiki with navigation

### 2. AI-Powered Research Tools
**"Research your knowledge base with intelligent tools"**

Users can:
- ✅ Submit research queries in natural language
- ✅ System analyzes query and selects appropriate research tools
- ✅ Dynamic planning determines optimal search strategy
- ✅ Execute multiple tools in parallel or sequence
- ✅ Verify tool usage and retrieval quality
- ✅ Receive comprehensive answers with citations

**Key Features:**
- **Dynamic Planning**: Query analysis → Tool selection → Execution plan
- **Multi-Tool Research**: 6 specialized search tools (vector, metadata, hybrid, multi-entity, etc.)
- **Tool Usage Verification**: See exactly what tools were used and what they found
- **Transparent Retrieval**: Verify request parameters and sample results
- **Citation Tracking**: Every fact traced back to source documents
- **Quality Assurance**: Confidence scores and relevance metrics

## User Workflow

### Workflow 1: Building Knowledge Base

```
1. User uploads document
   ↓
2. System processes document
   - Extract text content
   - Generate metadata (LLM-powered)
   - Create vector embeddings
   - Index in database
   ↓
3. System updates document wiki
   - Add to category tree
   - Update statistics
   - Generate new relationships
   - Refresh knowledge graph
   ↓
4. User sees updated wiki
   - New document appears
   - Statistics updated
   - Related docs linked
```

**Example:**
```
User uploads: "玉山銀行_洗錢防制裁罰_2020.txt"

System extracts:
- Document Type: 裁罰書
- Authority: 金管會
- Institution: 玉山銀行
- Violation: 洗錢防制
- Date: 2020-09-15
- Penalty: NT$10,000,000

Wiki updates:
📁 金管會裁罰書 (127 documents) ← +1
  📁 洗錢防制 (43 documents) ← +1
    📄 玉山銀行_洗錢防制裁罰_2020.txt ← NEW
  📁 玉山銀行 (18 documents) ← +1
```

### Workflow 2: Researching Knowledge

```
1. User submits query
   "玉山銀行洗錢防制裁罰案件有哪些？"
   ↓
2. System analyzes query
   - Intent: comprehensive listing
   - Entities: 玉山銀行
   - Topic: 洗錢防制
   - Complexity: medium
   ↓
3. System selects tools
   Tool 1: metadata_search (filter by institution + violation)
   Tool 2: hybrid_search (metadata + semantic)
   ↓
4. System executes tools
   metadata_search → 8 documents found
   hybrid_search → 12 relevant chunks
   ↓
5. User verifies tool usage
   - Sees request parameters
   - Reviews sample results
   - Checks relevance scores
   ↓
6. System generates answer
   - Synthesizes findings
   - Adds citations
   - Provides confidence score
   ↓
7. User receives comprehensive answer
   - Summary of cases
   - Key findings
   - Detailed analysis
   - All citations linked to wiki
```

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Document Wiki  │  │  Research Query  │  │  Tool Verify   │ │
│  │    Browser      │  │      Page        │  │     Panel      │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ WebSocket + REST API
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI + LangGraph)              │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Document       │  │  Dynamic         │  │  Research      │ │
│  │  Manager        │  │  Planning        │  │  Tools         │ │
│  │  + Wiki Gen     │  │  Agent           │  │  (6 tools)     │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Metadata       │  │  LangGraph       │  │  Answer        │ │
│  │  Extractor      │  │  Orchestrator    │  │  Generator     │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Storage Layer                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  SQLite DB      │  │  Chroma Vector   │  │  File System   │ │
│  │  (metadata)     │  │  DB (embeddings) │  │  (documents)   │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Document Wiki System (NEW)

**Purpose:** Organize and visualize knowledge base

**Components:**
- **WikiGenerator**: Build wiki structure from documents
- **CategoryBuilder**: Auto-categorize by type, authority, topic
- **RelationshipMapper**: Find document relationships
- **StatisticsAggregator**: Calculate coverage metrics
- **WikiAPI**: Serve wiki data to frontend

**Data Model:**
```python
class WikiCategory(BaseModel):
    id: str
    name: str
    type: str  # authority, institution, violation_type, document_type
    document_count: int
    subcategories: list['WikiCategory']
    documents: list[str]  # doc_ids

class WikiDocument(BaseModel):
    doc_id: str
    title: str
    description: str
    document_type: str
    metadata: dict
    related_docs: list[str]
    category_path: list[str]

class DocumentWiki(BaseModel):
    total_documents: int
    total_categories: int
    root_categories: list[WikiCategory]
    recent_documents: list[WikiDocument]
    statistics: WikiStatistics
```

#### 2. Dynamic Planning System (EXISTING)

**Purpose:** Analyze queries and select research tools

**Components:**
- **QueryAnalyzer**: Extract intent, entities, complexity
- **ToolSelector**: Choose appropriate research tools
- **ExecutionPlanner**: Determine tool execution order
- **ProgressTracker**: Monitor tool execution status

#### 3. Research Tools (EXISTING + ENHANCED)

**Available Tools:**
1. **vector_search**: Semantic similarity search
2. **metadata_search**: Filter by metadata (authority, date, type)
3. **hybrid_search**: Two-stage (metadata + vector)
4. **multi_entity_search**: Compare multiple institutions
5. **list_documents**: Exhaustive listing with filters
6. **read_file**: Direct file access by name

**Enhancement:** Tool usage tracking for verification

#### 4. Knowledge Extraction Pipeline (NEW)

**Purpose:** Extract structured metadata from documents

**Pipeline:**
```
Document Upload
    ↓
Text Extraction
    ↓
LLM Metadata Extraction
    ├─ Document Type
    ├─ Issuing Authority
    ├─ Related Institutions
    ├─ Violation Types
    ├─ Date & Case Number
    ├─ Penalty Amount
    └─ Keywords & Description
    ↓
Concept Extraction
    ├─ Main Topics
    ├─ Related Concepts
    └─ Relevance Scores
    ↓
Embedding Generation
    ↓
Dual Storage
    ├─ SQLite (metadata + wiki data)
    └─ Chroma (vector embeddings)
    ↓
Wiki Regeneration
```

## Database Schema Enhancement

### Documents Table (ENHANCED)

```sql
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    title TEXT,  -- Human-readable title
    description TEXT,  -- Summary/abstract

    -- Classification
    document_type TEXT,  -- 裁罰書, 判決書, 法規, etc.
    category_id INTEGER,  -- Link to wiki category

    -- Legal metadata
    issuing_authority TEXT,  -- 金管會, 中央銀行, etc.
    case_number TEXT,  -- 金管銀法字第10902345678號
    document_date TEXT,  -- 2020-09-15

    -- Entities
    related_institutions TEXT,  -- JSON: ["玉山銀行", "國泰世華"]
    violation_types TEXT,  -- JSON: ["洗錢防制", "內部控制"]
    penalty_amount TEXT,

    -- Content
    keywords TEXT,  -- JSON: ["洗錢", "裁罰", "金管會"]
    content_preview TEXT,  -- First 500 chars

    -- Technical
    indexed BOOLEAN DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    file_size INTEGER,
    language TEXT DEFAULT 'zh-TW',

    -- Extraction metadata
    extraction_method TEXT,  -- 'llm', 'manual'
    extraction_confidence REAL,

    -- Usage tracking
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id) REFERENCES wiki_categories(id)
);
```

### Wiki Categories Table (NEW)

```sql
CREATE TABLE IF NOT EXISTS wiki_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_type TEXT NOT NULL,  -- 'authority', 'institution', 'violation', 'type'
    parent_id INTEGER,  -- For hierarchical categories
    description TEXT,
    icon TEXT,  -- Emoji or icon identifier
    document_count INTEGER DEFAULT 0,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES wiki_categories(id)
);

CREATE INDEX idx_wiki_categories_type ON wiki_categories(category_type);
CREATE INDEX idx_wiki_categories_parent ON wiki_categories(parent_id);
```

### Document Relationships Table (NEW)

```sql
CREATE TABLE IF NOT EXISTS document_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id_1 TEXT NOT NULL,
    doc_id_2 TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- 'related', 'supersedes', 'amendment', 'references'
    strength REAL DEFAULT 0.5,  -- 0-1 relationship strength
    metadata TEXT,  -- JSON for additional info
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_id_1, doc_id_2, relationship_type)
);

CREATE INDEX idx_doc_rel_doc1 ON document_relationships(doc_id_1);
CREATE INDEX idx_doc_rel_doc2 ON document_relationships(doc_id_2);
```

### Wiki Statistics Table (NEW)

```sql
CREATE TABLE IF NOT EXISTS wiki_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_type TEXT NOT NULL,  -- 'total_docs', 'by_authority', 'by_year', etc.
    stat_key TEXT,  -- e.g., '2020', '金管會'
    stat_value INTEGER,
    metadata TEXT,  -- JSON for detailed stats
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wiki_stats_type ON wiki_statistics(stat_type);
CREATE INDEX idx_wiki_stats_key ON wiki_statistics(stat_key);
```

## Frontend Enhancement: Document Wiki UI

### New Pages/Components

#### 1. Document Wiki Browser

**Location:** `/wiki` or `/documents`

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📚 Knowledge Base                            🔍 Search  [Upload] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📊 Overview                                                      │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│ │ 📄 Total    │ │ 🏛️ 金管會    │ │ 🏦 銀行機構   │ │ 📅 2024   │ │
│ │ 494 docs    │ │ 287 docs    │ │ 156 docs    │ │ 23 docs   │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│                                                                 │
│ 📁 Categories                                                   │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ▼ 🏛️ 按主管機關 (By Authority)                               ││
│ │   ▶ 金管會 (287)                                             ││
│ │   ▶ 中央銀行 (45)                                            ││
│ │   ▶ 公平會 (12)                                              ││
│ │                                                               ││
│ │ ▼ 🏦 按金融機構 (By Institution)                              ││
│ │   ▶ 玉山銀行 (18)                                            ││
│ │   ▶ 國泰世華銀行 (22)                                        ││
│ │   ▶ 中國信託銀行 (15)                                        ││
│ │                                                               ││
│ │ ▼ ⚖️ 按違規類型 (By Violation Type)                            ││
│ │   ▶ 洗錢防制 (43)                                            ││
│ │   ▶ 內部控制 (56)                                            ││
│ │   ▶ 內線交易 (28)                                            ││
│ │                                                               ││
│ │ ▼ 📄 按文件類型 (By Document Type)                            ││
│ │   ▶ 裁罰書 (234)                                             ││
│ │   ▶ 判決書 (145)                                             ││
│ │   ▶ 法規 (89)                                                ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 📅 Recent Documents                                             │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📄 玉山銀行_洗錢防制裁罰_2020.txt                             ││
│ │    金管會 • 裁罰書 • 2020-09-15 • NT$10M                      ││
│ │    洗錢防制、內部控制缺失                                      ││
│ │                                                               ││
│ │ 📄 國泰世華銀行_內線交易_2021.txt                             ││
│ │    金管會 • 裁罰書 • 2021-03-22 • NT$5M                       ││
│ │    內線交易、資訊揭露                                          ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- Statistical overview cards
- Hierarchical category tree (collapsible)
- Recent documents list
- Search within wiki
- Quick upload button

#### 2. Document Detail View

**Triggered by:** Clicking on document in wiki

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ← Back to Wiki                                          [Delete] │
├─────────────────────────────────────────────────────────────────┤
│ 📄 玉山銀行_洗錢防制裁罰_2020.txt                                 │
│                                                                 │
│ 📋 Metadata                                                     │
│ 文件類型: 裁罰書                                                 │
│ 主管機關: 金管會                                                 │
│ 案號: 金管銀法字第10902345678號                                  │
│ 日期: 2020-09-15                                                │
│ 裁罰金額: NT$10,000,000                                         │
│ 違規類型: 洗錢防制、內部控制                                      │
│                                                                 │
│ 📝 Description                                                  │
│ 金管會於2020年9月15日對玉山商業銀行股份有限公司處以新臺幣         │
│ 1,000萬元罰鍰，因該行辦理防制洗錢及打擊資恐作業存有缺失...       │
│                                                                 │
│ 🔗 Related Documents (3)                                        │
│ • 玉山銀行_內部控制缺失_2019.txt                                 │
│ • 金管會_洗錢防制法規_2019.txt                                   │
│ • 玉山銀行_改善報告_2020.txt                                     │
│                                                                 │
│ 📊 Statistics                                                   │
│ Indexed: ✅  Chunks: 24  Size: 156 KB  Accessed: 12 times       │
└─────────────────────────────────────────────────────────────────┘
```

#### 3. Enhanced Upload Dialog

**Features:**
- Drag & drop upload
- Multiple file upload
- Real-time processing progress
- Automatic metadata extraction preview
- Manual metadata editing
- Wiki category assignment

### REST API Endpoints (NEW)

```python
# Wiki Management
GET /api/wiki/overview              # Get wiki statistics
GET /api/wiki/categories            # Get category tree
GET /api/wiki/category/{id}         # Get documents in category
GET /api/wiki/document/{doc_id}     # Get document details
GET /api/wiki/search?q=...          # Search wiki
GET /api/wiki/stats                 # Get detailed statistics

# Document Management
POST /api/documents/upload          # Upload new document(s)
DELETE /api/documents/{doc_id}      # Delete document
PUT /api/documents/{doc_id}         # Update metadata
GET /api/documents/{doc_id}/related # Get related documents

# Wiki Regeneration
POST /api/wiki/rebuild              # Rebuild entire wiki
POST /api/wiki/refresh              # Refresh statistics
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal:** Database integration and metadata extraction

- ✅ Connect DocumentIndexer to SQLite
- ✅ Create wiki-related database tables
- ✅ Implement LLM metadata extractor
- ✅ Populate documents table on indexing
- ✅ Test with existing documents

### Phase 2: Wiki Generation (Week 3)
**Goal:** Build document wiki system

- Create WikiGenerator class
- Implement category builder
- Build relationship mapper
- Create statistics aggregator
- Test wiki generation

### Phase 3: Wiki API & UI (Week 4)
**Goal:** Expose wiki to frontend

- Create REST endpoints
- Build DocumentWikiPage component
- Implement category tree browser
- Add document detail view
- Create statistics dashboard

### Phase 4: Enhanced Upload (Week 5)
**Goal:** Streamline document addition

- Enhanced upload dialog
- Real-time metadata extraction
- Wiki auto-refresh on upload
- Delete with wiki update
- Bulk operations

### Phase 5: Tool Integration (Week 6)
**Goal:** Complete research tool verification

- Tool usage tracking in database
- Integrate tools with Action Agent
- Connect to UI callbacks
- Test end-to-end workflow

### Phase 6: Polish & Testing (Week 7-8)
**Goal:** Production-ready system

- Performance optimization
- UI/UX refinements
- Comprehensive testing
- Documentation
- Demo preparation

## Success Metrics

### Knowledge Management Metrics
1. **Upload Success Rate:** >95% documents processed successfully
2. **Metadata Accuracy:** >90% extracted metadata is correct
3. **Wiki Coverage:** 100% documents appear in wiki
4. **Wiki Refresh Time:** <5 seconds after upload/delete

### Research Tool Metrics
1. **Tool Selection Accuracy:** >85% queries use appropriate tools
2. **Retrieval Quality:** >80% results have relevance >0.8
3. **Query Success Rate:** >90% queries produce useful answers
4. **User Verification:** Users can verify 100% of tool usage

### User Experience Metrics
1. **Upload Time:** <30 seconds per document (including extraction)
2. **Wiki Navigation:** <3 clicks to find any document
3. **Search Response:** <2 seconds for any wiki search
4. **Research Time:** <60 seconds from query to answer

## Competitive Advantages

1. **Automatic Organization:** Wiki builds itself from documents
2. **Transparent Research:** Users see exactly how tools work
3. **Verifiable Results:** Every retrieval can be inspected
4. **Specialized Tools:** Legal/banking-specific research capabilities
5. **Bilingual Support:** Traditional Chinese + English
6. **Local Deployment:** No cloud dependency, data stays private

## Conclusion

FinAgent transforms from a simple RAG system into a **comprehensive knowledge management platform** where:

1. **Documents organize themselves** into an intelligent wiki
2. **Research tools work transparently** with full verification
3. **Users maintain control** over their legal/banking knowledge base

The enhanced system provides the foundation for institutional knowledge management while maintaining the advanced AI-powered research capabilities that make FinAgent unique.
