-- FinAgent SQLite Database Schema

-- Settings table: Store application settings
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on key for fast lookups
CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
CREATE INDEX IF NOT EXISTS idx_settings_category ON settings(category);

-- Model configurations table: Store saved model configurations
CREATE TABLE IF NOT EXISTS model_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    config_type TEXT NOT NULL CHECK(config_type IN ('llm', 'embedding')),
    api_key TEXT DEFAULT '',
    base_url TEXT DEFAULT '',
    model TEXT NOT NULL,
    temperature REAL DEFAULT 0.0,
    is_active BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for model_configs
CREATE INDEX IF NOT EXISTS idx_model_configs_type ON model_configs(config_type);
CREATE INDEX IF NOT EXISTS idx_model_configs_active ON model_configs(is_active);

-- History table: Store query/interaction history
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    query TEXT NOT NULL,
    response TEXT,
    model_used TEXT,
    tokens_used INTEGER,
    cost_usd REAL,
    processing_time_seconds REAL,
    success BOOLEAN DEFAULT 1,
    error_message TEXT,
    metadata TEXT,  -- JSON string for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for history
CREATE INDEX IF NOT EXISTS idx_history_session ON history(session_id);
CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_history_model ON history(model_used);

-- Trigger to update updated_at on settings update
CREATE TRIGGER IF NOT EXISTS update_settings_timestamp
AFTER UPDATE ON settings
FOR EACH ROW
BEGIN
    UPDATE settings SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Trigger to update updated_at on model_configs update
CREATE TRIGGER IF NOT EXISTS update_model_configs_timestamp
AFTER UPDATE ON model_configs
FOR EACH ROW
BEGIN
    UPDATE model_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Trigger to ensure only one active config per type (on UPDATE)
CREATE TRIGGER IF NOT EXISTS ensure_single_active_config_update
BEFORE UPDATE ON model_configs
FOR EACH ROW
WHEN NEW.is_active = 1
BEGIN
    UPDATE model_configs SET is_active = 0
    WHERE config_type = NEW.config_type AND id != NEW.id;
END;

-- Trigger to ensure only one active config per type (on INSERT)
CREATE TRIGGER IF NOT EXISTS ensure_single_active_config_insert
BEFORE INSERT ON model_configs
FOR EACH ROW
WHEN NEW.is_active = 1
BEGIN
    UPDATE model_configs SET is_active = 0
    WHERE config_type = NEW.config_type;
END;

-- Documents table: Store document metadata for indexed documents
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL UNIQUE,  -- Unique document identifier (e.g., filename hash)
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    description TEXT,  -- Human-readable description of document content
    document_type TEXT,  -- e.g., "裁罰書", "判決書", "法規", "新聞報導"
    keywords TEXT,  -- JSON array of keywords
    document_date TEXT,  -- Document date (e.g., "2020-09-15")
    issuing_authority TEXT,  -- e.g., "金管會", "中央銀行"
    related_institutions TEXT,  -- JSON array of related institutions
    penalty_amount TEXT,  -- If penalty document
    violation_types TEXT,  -- JSON array of violation types
    custom_fields TEXT,  -- JSON object for additional custom metadata
    indexed BOOLEAN DEFAULT 0,  -- Whether document is indexed in vector DB
    chunk_count INTEGER DEFAULT 0,  -- Number of chunks in vector DB
    -- Metadata extraction status fields (added 2025-01-19)
    metadata_extracted BOOLEAN DEFAULT 0,  -- Whether metadata has been extracted by LLM
    metadata_extraction_status TEXT DEFAULT 'pending',  -- Status: pending, processing, completed, failed, user_edited
    metadata_extraction_error TEXT,  -- Error message if extraction failed
    metadata_extraction_attempts INTEGER DEFAULT 0,  -- Number of extraction attempts
    metadata_last_extracted_at TIMESTAMP,  -- Timestamp of last extraction
    metadata_edited_by_user BOOLEAN DEFAULT 0,  -- Whether user manually edited metadata
    extraction_confidence REAL,  -- Extraction confidence score (0-1)
    -- Pipeline monitoring fields (added 2025-11-19)
    pipeline_stage TEXT DEFAULT 'uploaded',  -- Current pipeline stage
    pipeline_status TEXT DEFAULT 'in_progress',  -- Overall pipeline status
    pipeline_data TEXT,  -- JSON data with detailed pipeline stage information
    pipeline_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Pipeline start time
    pipeline_completed_at TIMESTAMP,  -- Pipeline completion time
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for documents
CREATE INDEX IF NOT EXISTS idx_documents_doc_id ON documents(doc_id);
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_issuing_authority ON documents(issuing_authority);
CREATE INDEX IF NOT EXISTS idx_documents_indexed ON documents(indexed);
CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at DESC);

-- Trigger to update updated_at on documents update
CREATE TRIGGER IF NOT EXISTS update_documents_timestamp
AFTER UPDATE ON documents
FOR EACH ROW
BEGIN
    UPDATE documents SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Concepts table: Store extracted topics/concepts for faster retrieval
CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_name TEXT NOT NULL UNIQUE,  -- e.g., "洗錢防制", "內線交易", "資訊揭露"
    concept_type TEXT,  -- e.g., "violation_type", "institution", "authority", "topic"
    description TEXT,  -- Brief description of the concept
    keywords TEXT,  -- JSON array of related keywords
    document_count INTEGER DEFAULT 0,  -- Number of documents related to this concept
    metadata TEXT,  -- JSON object for additional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for concepts
CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(concept_name);
CREATE INDEX IF NOT EXISTS idx_concepts_type ON concepts(concept_type);
CREATE INDEX IF NOT EXISTS idx_concepts_count ON concepts(document_count DESC);

-- Document-Concept mapping table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS document_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,  -- References documents.doc_id
    concept_id INTEGER NOT NULL,  -- References concepts.id
    relevance_score REAL DEFAULT 1.0,  -- How relevant this concept is to the document (0-1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    UNIQUE(doc_id, concept_id)  -- Prevent duplicate mappings
);

-- Create indexes for document_concepts
CREATE INDEX IF NOT EXISTS idx_doc_concepts_doc_id ON document_concepts(doc_id);
CREATE INDEX IF NOT EXISTS idx_doc_concepts_concept_id ON document_concepts(concept_id);
CREATE INDEX IF NOT EXISTS idx_doc_concepts_relevance ON document_concepts(relevance_score DESC);

-- Trigger to update concepts.document_count when mapping changes
CREATE TRIGGER IF NOT EXISTS update_concept_count_insert
AFTER INSERT ON document_concepts
FOR EACH ROW
BEGIN
    UPDATE concepts
    SET document_count = (SELECT COUNT(*) FROM document_concepts WHERE concept_id = NEW.concept_id)
    WHERE id = NEW.concept_id;
END;

CREATE TRIGGER IF NOT EXISTS update_concept_count_delete
AFTER DELETE ON document_concepts
FOR EACH ROW
BEGIN
    UPDATE concepts
    SET document_count = (SELECT COUNT(*) FROM document_concepts WHERE concept_id = OLD.concept_id)
    WHERE id = OLD.concept_id;
END;

-- Trigger to update concepts.updated_at
CREATE TRIGGER IF NOT EXISTS update_concepts_timestamp
AFTER UPDATE ON concepts
FOR EACH ROW
BEGIN
    UPDATE concepts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Tool executions table: Track all tool executions for verification and monitoring
CREATE TABLE IF NOT EXISTS tool_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id TEXT NOT NULL,  -- Associated query/research session ID
    tool_name TEXT NOT NULL,  -- Name of the tool (e.g., "vector_search", "metadata_search")
    parameters TEXT NOT NULL,  -- JSON string of input parameters
    execution_time_ms INTEGER NOT NULL,  -- Execution time in milliseconds
    results_count INTEGER NOT NULL,  -- Number of results returned
    sample_results TEXT,  -- JSON string with sample results (top 3) for verification
    metadata TEXT,  -- JSON string with tool-specific metadata (relevance scores, filters, etc.)
    success BOOLEAN DEFAULT 1,  -- Whether execution succeeded
    error_message TEXT,  -- Error message if failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for tool_executions
CREATE INDEX IF NOT EXISTS idx_tool_executions_query_id ON tool_executions(query_id);
CREATE INDEX IF NOT EXISTS idx_tool_executions_tool_name ON tool_executions(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_executions_created ON tool_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_executions_success ON tool_executions(success);
