# Changelog

All notable changes to FinAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-01-14

### Added

- **Cross-platform Electron desktop application**
  - Modern graphical interface for Windows and macOS
  - Traditional Chinese UI optimized for Taiwan users
  - Real-time backend status monitoring
  - Query examples for quick start

- **Hybrid Architecture**
  - Electron frontend with Node.js main process
  - Python FastAPI backend as subprocess
  - Automatic health monitoring and recovery
  - IPC-based communication bridge

- **Build System**
  - electron-builder configuration for Windows and macOS
  - Automated Python distribution bundling
  - Platform-specific installers (NSIS for Windows, DMG for macOS)
  - Build scripts for cross-platform development

- **Documentation**
  - Comprehensive Electron Desktop Guide
  - Development and build instructions
  - Troubleshooting guide
  - Architecture documentation

### Changed

- Updated project version from 0.1.0 to 0.0.2
- Enhanced CLAUDE.md with Electron development commands
- Updated README.md with desktop app information

### Technical Details

- Electron 28.2.0
- React-style vanilla JavaScript frontend
- Secure IPC with context isolation
- Python subprocess management with graceful shutdown
- Cross-platform compatibility (Windows 10+, macOS 10.13+)

## [0.0.1-beta] - Previous Release

### Added

- LangGraph multi-agent architecture
  - Planning Agent for query decomposition
  - Action Agent for RAG retrieval
  - Validation Agent for citation verification
  - Answer Agent for synthesis

- RAG Pipeline
  - Chroma vector database integration
  - OpenAI embeddings support
  - Document chunking and indexing
  - Semantic search with relevance filtering

- Database Layer
  - SQLite for persistent storage
  - Settings and configuration management
  - Query history tracking
  - Model configuration presets

- CLI Interface
  - Interactive REPL mode
  - Command system (/query, /config, /init, etc.)
  - Rich terminal formatting
  - Configuration wizard

- Document Processing
  - TXT file support
  - Traditional Chinese with Jieba
  - Paragraph-aware chunking
  - Metadata extraction

- Configuration System
  - Unified OpenAI-compatible API support
  - OpenAI, Ollama, and custom endpoint support
  - Environment variable configuration
  - Database-backed settings

### Features

- Traditional Chinese language support
- Taiwan legal citation formatting
- Confidence scoring for answers
- Multi-source document retrieval
- Real-time query processing

---

[0.0.2]: https://github.com/p988744/FinAgent/compare/v0.0.1...v0.0.2
[0.0.1-beta]: https://github.com/p988744/FinAgent/releases/tag/v0.0.1
