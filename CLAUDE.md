# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Legal Research Agent System** (法律研究代理系統) specialized for analyzing bank penalties, regulatory enforcement actions, and legal precedents in Taiwan. The system is adapted from the Dexter financial research agent architecture, optimized for the legal domain where precise citations, unstructured document processing, and jurisdictional complexity are critical.

**Target Region:** Taiwan (繁體中文)
**Domain:** Banking penalties, regulatory enforcement, legal precedents
**Base Architecture:** Multi-agent system based on Dexter

## Core Architecture

### Multi-Agent System

The system follows a sequential multi-agent pipeline:

1. **Planning Agent** (規劃代理)
   - Query decomposition with legal context
   - Jurisdiction identification
   - Task sequencing (metadata → documents → analysis)

2. **Action Agent** (行動代理)
   - Tool selection (search/retrieval/analysis)
   - Parameter optimization
   - Multi-source coordination

3. **Document Processing Pipeline** (文件處理管線)
   - PDF extraction and OCR
   - Smart chunking (paragraph-aware)
   - Embedding generation
   - Vector database indexing

4. **Validation Agent** (驗證代理)
   - Citation integrity checking
   - Source authority validation
   - Fact statement coverage verification

5. **Answer Agent** (答案代理)
   - Legal analysis synthesis
   - Formal citation generation (Taiwan legal citation format)
   - Precedent comparison
   - Confidence scoring

## Key Technical Differences from Dexter

| Aspect | Dexter (Finance) | Legal Research Agent (Law/Regulatory) |
|--------|------------------|--------------------------------------|
| Primary Data | Structured APIs (JSON) | Unstructured documents (PDF, HTML) |
| Data Volume | Small, filtered datasets | Large documents (50-200 pages) |
| Context Strategy | LLM context window | Hybrid RAG + selective retrieval |
| Citations | Soft references | Formal legal citation format |
| Time Sensitivity | Real-time/latest data | Historical precedents (lookback) |
| Jurisdiction | Single (US market) | Multiple (Federal/State regulators) |
| Query Precision | Best-effort autonomous | May require clarification |

## Taiwan-Specific Adaptations

### Regulatory Bodies Integration
- **金管會** (FSC - Financial Supervisory Commission)
  - 銀行局 (Banking Bureau)
  - 證期局 (Securities and Futures Bureau)
  - 保險局 (Insurance Bureau)
- **中央銀行** (CBC - Central Bank)
- **公平會** (FTC - Fair Trade Commission)

### Legal Citation Formats
- Statute format: "銀行法第125條"
- Court judgment format: "最高法院110年台上字第1234號判決"
- Enforcement action format: "金管會108年金管銀法字第10800123456號裁罰書"
- Case number format: "110年金上字第15號"

### NLP Processing for Traditional Chinese
- CKIP (中文知識與資訊處理) for NER and tokenization
- Jieba for Chinese word segmentation
- Full-width/half-width number conversion
- Traditional Chinese-optimized embeddings

## Technology Stack

### Core Framework
- **LLM Framework:** LangChain / LlamaIndex
- **LLM Provider:** OpenAI GPT-4 / Claude 3 Opus
- **Agent Orchestration:** LangGraph or custom multi-agent framework

### Document Processing
- **PDF Parsing:** PyPDF2, pdfplumber, or PyMuPDF
- **OCR:** Tesseract (with Traditional Chinese support)
- **Text Chunking:** Semantic chunking with section awareness
- **Embeddings:** OpenAI text-embedding-ada-002 or multilingual-e5-large

### Vector Database
- **Options:**
  - Chroma (self-hosted, recommended for cost)
  - Pinecone (managed service)
  - Weaviate (alternative)
- **Index Strategy:** Separate indices per document type

### NLP Tools for Chinese
- **CKIP:** https://ckip.iis.sinica.edu.tw/
- **Jieba:** https://github.com/fxsjy/jieba
- **spaCy zh_core_web_trf:** Chinese language model (alternative)

### Infrastructure
- **Async Processing:** Celery + Redis
- **API Framework:** FastAPI
- **Database:** PostgreSQL (metadata storage)
- **Containerization:** Docker

## Data Models

### Core Pydantic Models

```python
# Key models to implement
- LegalCitation: Formal legal citations with source authority
- EnforcementAction: Regulatory enforcement metadata
- DocumentMetadata: Extracted metadata from legal documents
- CourtJudgment: Court judgment metadata
- PrecedentCase: Precedent cases for comparison
- LegalAnswer: Structured answer with formal citations
- Task: Legal-specific task with jurisdiction context
```

### Citation Types
- **Primary Sources:** Official enforcement documents, court judgments
- **Secondary Sources:** News articles, regulatory announcements
- **Tertiary Sources:** Legal commentary, analysis

## Tool Categories

### Category 1: Regulatory & Enforcement Search
- `search_enforcement_actions()`: Search across regulatory bodies
- `get_institution_enforcement_history()`: Entity-specific enforcement history
- `search_court_judgments()`: Search court judgments

### Category 2: Document Retrieval
- `get_enforcement_document()`: Retrieve full enforcement documents
- `get_judgment_document()`: Retrieve court judgment full text

### Category 3: Legal Research & Analysis
- `search_precedent_cases()`: Find similar precedent cases
- `search_statute_text()`: Retrieve statute/regulation text
- `compare_penalty_cases()`: Side-by-side case comparison

### Category 4: Document Analysis (RAG-Enhanced)
- `index_legal_document()`: Index documents for RAG
- `search_document_sections()`: Semantic search within documents
- `extract_document_metadata()`: Extract structured metadata

### Category 5: Entity & Cross-Reference
- `resolve_entity_name()`: Resolve ambiguous entity names
- `get_related_cases()`: Find related cases
- `track_appeal_status()`: Track case appeal status

## Document Processing Strategy

### Smart Chunking for Traditional Chinese

Priority order:
1. Keep complete sections intact (e.g., "第三章：事實")
2. Maintain paragraph integrity
3. Respect page boundaries
4. Maintain context through overlap

### Citation Validation

Every factual statement must be cited:
- Penalty amounts: "玉山銀行被處以2.5億元罰鍰 [引用1，第3頁]"
- Violation descriptions: "該銀行未能維持適當的洗錢防制控制 [引用2，第四章B節]"
- Dates: "裁罰書於民國109年9月15日作成 [引用1]"
- Quoted text: "金管會認定該銀行從事「不安全或不健全業務」[引用1，第1頁]"

### In-Text Citation Format
- First citation: [引用1]
- Subsequent same source: [引用1]
- Specific section: [引用1，第三章A節]
- Page numbers: [引用1，第5頁]
- Multiple sources: [引用1、2、3]

## Confidence Scoring System

### High Confidence (高信心)
- Multiple primary sources (official enforcement documents)
- All key facts verified in official documents
- Complete documents with formal citations
- No conflicting information

### Medium Confidence (中信心)
- Mostly primary sources with some gaps
- Some facts from secondary sources (news)
- Minor details unverified
- Slight ambiguity in interpretation

### Low Confidence (低信心)
- Heavy reliance on secondary sources
- Significant information gaps
- Conflicting information between sources
- Limited official documents available

## Development Workflow

### Phase 1: Foundation (Weeks 1-3)
1. Set up RAG infrastructure (vector DB, embeddings)
2. Implement Taiwan legal citation formatter
3. Build document processing pipeline
4. Create metadata extraction system

### Phase 2: Agent Components (Weeks 4-6)
1. Implement Planning Agent with Traditional Chinese prompts
2. Build Action Agent with tool selection logic
3. Develop 10+ core legal research tools
4. Implement Validation Agent with citation checking
5. Build Answer Agent with Taiwan legal citation generation

### Phase 3: Testing & Optimization (Weeks 7-8)
1. Unit tests for all components
2. Integration tests with real-world queries
3. Citation accuracy validation
4. Performance benchmarking
5. Prompt engineering refinement

### Phase 4: Advanced Features (Weeks 9-12)
1. Advanced RAG capabilities
2. CLI interface with legal-specific commands
3. Export formatting (PDF with proper citations)
4. Deployment (Docker containerization)

## Testing Strategy

### Test Case Structure
```python
TAIWAN_LEGAL_RESEARCH_TEST_CASES = [
    {
        "test_id": "enforcement_tw_001",
        "query": "玉山銀行在2020年因洗錢防制違規受到金管會什麼處分？",
        "expected_elements": {
            "entity": "玉山商業銀行",
            "regulator": "金管會",
            "year": 2020,
            "violation_type": "洗錢防制",
            "min_citations": 1,
            "citation_type": "主要來源"
        }
    }
]
```

## Important Data Sources

### Official Taiwan Sources
- 金管會: https://www.fsc.gov.tw/
- 中央銀行: https://www.cbc.gov.tw/
- 公平會: https://www.ftc.gov.tw/
- 司法院法學資料檢索系統: https://law.judicial.gov.tw/
- 全國法規資料庫: https://law.moj.gov.tw/

### Data Characteristics
- Enforcement documents: PDF format
- Case number format: 金管銀法字第○○○○○○○○○○號
- Judgment format: ○○年度○字第○○○○號
- Update frequency: Daily (FSC), irregular (CBC)
- Historical coverage: 2000-present (FSC), 1995-present (CBC)

## Prompt Engineering Guidelines

### Language Requirements
- All system prompts in Traditional Chinese (繁體中文)
- Support natural language queries in Traditional Chinese
- Generate responses in formal legal writing style
- Use Taiwan-specific legal terminology

### Answer Format Requirements
- Executive summary (執行摘要)
- Key findings (關鍵發現) with embedded citations
- Detailed analysis (詳細分析) with comprehensive citations
- Precedent comparison table (判例比較)
- Confidence score with explanation
- Limitations section

### Style Guide
- Use formal legal writing style
- Be precise and objective (avoid "I think", "possibly", "maybe")
- Use passive voice for formal tone ("被處以" not "收到")
- Define abbreviations on first use
- Use proper legal terminology (裁罰書 ≠ 和解協議)
- Present numbers clearly: "2.5億元" or "250,000,000元" (consistent)
- Use specific dates: "民國109年9月15日" not "在109年"

## Cost Considerations

### Estimated Monthly Costs (100 queries/month)
- LLM API (GPT-4): ~NT$3,000-6,000
- Embeddings API: ~NT$300-600
- Vector DB (Pinecone): ~NT$2,100-6,000
- Vector DB (Chroma self-hosted): NT$0
- Document storage: ~NT$300
- Compute resources: ~NT$1,350

**Total: ~NT$7,050-13,050/month** (depending on vector DB choice)

## Future Enhancements

### Advanced RAG
- Multi-hop reasoning across documents
- Automatic citation validation (check URLs, dates)
- Cross-document consistency checking

### Expanded Coverage
- Local court judgments (district courts)
- Administrative litigation cases
- Arbitration awards
- Settlement agreement databases

### AI Capabilities
- Predictive penalty modeling
- Trend analysis (enforcement patterns over time)
- Institution risk scoring
- Auto-alert system for new penalty cases

### User Features
- Saved research sessions
- Collaborative research (multi-user)
- Custom report templates
- Email alerts for new relevant cases

## Critical Implementation Notes

1. **Citation Integrity:** Every factual statement MUST have a citation to a verifiable source
2. **Source Hierarchy:** Always prefer primary sources (official documents) over secondary (news)
3. **Temporal Logic:** For precedent cases, only cases BEFORE the target date are valid
4. **Document Size:** Legal documents are 50-200 pages; RAG is REQUIRED, not optional
5. **Entity Resolution:** Use official legal names (e.g., "玉山商業銀行股份有限公司" not "玉山")
6. **Date Format:** Use ROC (民國) calendar format for Taiwan documents
7. **Chunking Strategy:** Preserve document structure (sections/chapters) during chunking
8. **Bilingual Support:** System must handle both Traditional Chinese queries and English legal terms

## Key Terminology (繁體中文)

- **民國**: Republic of China calendar (starting from 1911)
- **裁罰書**: Regulatory penalty/enforcement document
- **判決書**: Court judgment document
- **案號**: Case number (e.g., 110年台上字第1234號)
- **主文**: Main text/conclusion of judgment
- **事實**: Facts section of judgment
- **理由**: Reasoning/rationale section
- **洗錢防制**: Anti-Money Laundering (AML)
- **內線交易**: Insider trading
- **資訊揭露**: Information disclosure
