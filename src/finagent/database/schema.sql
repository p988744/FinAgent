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
