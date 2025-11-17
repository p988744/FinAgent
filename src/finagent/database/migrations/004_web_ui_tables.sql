-- Migration 002: Web UI Tables
-- Version: v0.1.0-alpha.1
-- Date: 2025-11-17
-- Description: Add tables for Web UI document versioning and query templates

-- Document versions table: Track version history for documents
CREATE TABLE IF NOT EXISTS document_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,  -- References documents.doc_id
    version INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    checksum TEXT,  -- SHA-256 hash of file
    change_summary TEXT,  -- Brief description of changes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    UNIQUE(document_id, version)
);

-- Create indexes for document_versions
CREATE INDEX IF NOT EXISTS idx_doc_versions_doc_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_versions_version ON document_versions(version DESC);
CREATE INDEX IF NOT EXISTS idx_doc_versions_created ON document_versions(created_at DESC);

-- Query templates table: Store saved query templates for quick access
CREATE TABLE IF NOT EXISTS query_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    template TEXT NOT NULL,  -- Query template text
    description TEXT,  -- Brief description of what this template searches for
    category TEXT DEFAULT 'general',  -- e.g., "penalty", "aml", "disclosure"
    usage_count INTEGER DEFAULT 0,  -- How many times this template was used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for query_templates
CREATE INDEX IF NOT EXISTS idx_query_templates_name ON query_templates(name);
CREATE INDEX IF NOT EXISTS idx_query_templates_category ON query_templates(category);
CREATE INDEX IF NOT EXISTS idx_query_templates_usage ON query_templates(usage_count DESC);

-- Trigger to update updated_at on query_templates update
CREATE TRIGGER IF NOT EXISTS update_query_templates_timestamp
AFTER UPDATE ON query_templates
FOR EACH ROW
BEGIN
    UPDATE query_templates SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Add version tracking column to documents table if not exists
-- Note: SQLite doesn't support IF NOT EXISTS for columns, so we handle this in application code
-- ALTER TABLE documents ADD COLUMN current_version INTEGER DEFAULT 1;

-- Wiki pages table: Store auto-generated wiki content for documents
CREATE TABLE IF NOT EXISTS wiki_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL UNIQUE,  -- References documents.doc_id
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- Markdown content
    summary TEXT,  -- Brief summary of document
    entities TEXT,  -- JSON array of extracted entities (banks, dates, amounts)
    tags TEXT,  -- JSON array of tags
    category TEXT,  -- Primary category
    related_documents TEXT,  -- JSON array of related doc_ids
    auto_generated BOOLEAN DEFAULT 1,
    last_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);

-- Create indexes for wiki_pages
CREATE INDEX IF NOT EXISTS idx_wiki_pages_doc_id ON wiki_pages(document_id);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_category ON wiki_pages(category);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_tags ON wiki_pages(tags);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_generated ON wiki_pages(last_generated_at DESC);

-- Trigger to update updated_at on wiki_pages update
CREATE TRIGGER IF NOT EXISTS update_wiki_pages_timestamp
AFTER UPDATE ON wiki_pages
FOR EACH ROW
BEGIN
    UPDATE wiki_pages SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Insert default query templates
INSERT OR IGNORE INTO query_templates (name, template, description, category) VALUES
    ('洗錢防制裁罰', '洗錢防制相關裁罰案件', '搜尋反洗錢合規違規案例', 'aml'),
    ('內線交易案例', '內線交易判決與裁罰', '搜尋內線交易相關案例', 'insider'),
    ('資訊揭露違規', '資訊揭露不實或延遲申報', '搜尋資訊揭露相關違規', 'disclosure'),
    ('金管會裁罰', '金管會裁罰案件', '搜尋金管會行政處分', 'penalty'),
    ('銀行違規案例', '[銀行名稱]違規裁罰案件', '搜尋特定銀行違規記錄', 'general');
