# Changelog

All notable changes to FinAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 5: Todo state synchronization in LangGraph workflow
- Enhanced agent state with todo tracking across all agents
- Real-time task status updates (pending → in_progress → completed)

### Removed
- Electron desktop GUI (reverted due to runtime issues)

## [0.0.1-beta] - 2025-01-12

### Added

- **LangGraph Multi-Agent Architecture**
  - Planning Agent for query decomposition
  - Action Agent for RAG retrieval
  - Validation Agent for citation verification
  - Answer Agent for LLM synthesis

- **RAG Pipeline**
  - Chroma vector database integration
  - OpenAI embeddings support (text-embedding-3-small)
  - Document chunking and indexing (512 tokens, 128 overlap)
  - Semantic search with 0.8 relevance filtering

- **Database Layer**
  - SQLite for persistent storage
  - Settings and configuration management
  - Query history tracking
  - Model configuration presets

- **CLI Interface**
  - Interactive REPL mode
  - Commands: /query, /config, /init, /reindex, /help
  - Rich terminal formatting
  - Configuration wizard

- **Document Processing**
  - TXT file support
  - Traditional Chinese with Jieba tokenization
  - Paragraph-aware chunking
  - LLM-generated metadata extraction

- **Configuration System**
  - Unified OpenAI-compatible API support
  - OpenAI, Ollama, and custom endpoint support
  - Environment variable configuration (.env)
  - Database-backed settings with priority system

### Features

- Traditional Chinese (繁體中文) language support
- Taiwan legal citation formatting ([引用1]、[引用2])
- Confidence scoring (高信心/中信心/低信心)
- Multi-source document retrieval
- Real-time query processing (~40 seconds)
- Cost tracking (~$0.0015 USD per query)

### Performance

- True positive rate: 95%
- False positive rate: 0%
- 494 documents indexed
- 2,858 vector chunks

---

[Unreleased]: https://github.com/p988744/FinAgent/compare/v0.0.1-beta...HEAD
[0.0.1-beta]: https://github.com/p988744/FinAgent/releases/tag/v0.0.1-beta
