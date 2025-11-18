-- Migration 001: Wiki Tables for v1.0
-- Purpose: Add wiki_categories, document_relationships, and wiki_statistics tables
-- Also enhance documents table with wiki-related fields

-- ============================================================================
-- Wiki Categories Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS wiki_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_type TEXT NOT NULL CHECK(category_type IN ('authority', 'institution', 'violation', 'document_type')),
    parent_id INTEGER,
    description TEXT,
    icon TEXT,  -- Emoji or icon identifier
    document_count INTEGER DEFAULT 0,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES wiki_categories(id) ON DELETE CASCADE,
    UNIQUE(name, category_type)  -- Prevent duplicate categories
);

CREATE INDEX IF NOT EXISTS idx_wiki_categories_type ON wiki_categories(category_type);
CREATE INDEX IF NOT EXISTS idx_wiki_categories_parent ON wiki_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_wiki_categories_count ON wiki_categories(document_count DESC);

-- Trigger to update updated_at on wiki_categories
CREATE TRIGGER IF NOT EXISTS update_wiki_categories_timestamp
AFTER UPDATE ON wiki_categories
FOR EACH ROW
BEGIN
    UPDATE wiki_categories SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- ============================================================================
-- Document Relationships Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id_1 TEXT NOT NULL,
    doc_id_2 TEXT NOT NULL,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN ('related', 'supersedes', 'amendment', 'references', 'similar')),
    strength REAL DEFAULT 0.5 CHECK(strength >= 0 AND strength <= 1),  -- 0-1 relationship strength
    metadata TEXT,  -- JSON for additional info
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doc_id_1, doc_id_2, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_doc_rel_doc1 ON document_relationships(doc_id_1);
CREATE INDEX IF NOT EXISTS idx_doc_rel_doc2 ON document_relationships(doc_id_2);
CREATE INDEX IF NOT EXISTS idx_doc_rel_type ON document_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_doc_rel_strength ON document_relationships(strength DESC);

-- ============================================================================
-- Wiki Statistics Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS wiki_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_type TEXT NOT NULL,  -- 'total_docs', 'by_authority', 'by_year', 'by_institution', 'by_violation', 'by_type'
    stat_key TEXT,  -- e.g., '2020', '金管會', 'all'
    stat_value INTEGER NOT NULL,
    metadata TEXT,  -- JSON for detailed stats
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wiki_stats_type ON wiki_statistics(stat_type);
CREATE INDEX IF NOT EXISTS idx_wiki_stats_key ON wiki_statistics(stat_key);
CREATE INDEX IF NOT EXISTS idx_wiki_stats_calculated ON wiki_statistics(calculated_at DESC);

-- ============================================================================
-- Enhance Documents Table (if columns don't exist)
-- ============================================================================

-- Add title field (human-readable title)
ALTER TABLE documents ADD COLUMN title TEXT;

-- Add category_id (link to wiki category)
ALTER TABLE documents ADD COLUMN category_id INTEGER;

-- Add content_preview (first 500 chars for quick display)
ALTER TABLE documents ADD COLUMN content_preview TEXT;

-- Add extraction_method ('llm', 'manual', 'none')
ALTER TABLE documents ADD COLUMN extraction_method TEXT DEFAULT 'none';

-- Add extraction_confidence (0-1)
ALTER TABLE documents ADD COLUMN extraction_confidence REAL;

-- Add case_number (e.g., 金管銀法字第10902345678號)
ALTER TABLE documents ADD COLUMN case_number TEXT;

-- Add language (default: zh-TW)
ALTER TABLE documents ADD COLUMN language TEXT DEFAULT 'zh-TW';

-- Add document_status ('active', 'archived', 'deleted')
ALTER TABLE documents ADD COLUMN document_status TEXT DEFAULT 'active';

-- Add access tracking
ALTER TABLE documents ADD COLUMN last_accessed TIMESTAMP;
ALTER TABLE documents ADD COLUMN access_count INTEGER DEFAULT 0;

-- Add file_size (in bytes)
ALTER TABLE documents ADD COLUMN file_size INTEGER;

-- Create index on category_id
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category_id);

-- Create index on document_status
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(document_status);

-- Create index on case_number
CREATE INDEX IF NOT EXISTS idx_documents_case_number ON documents(case_number);

-- ============================================================================
-- Insert Root Categories (if not exists)
-- ============================================================================

-- 按主管機關 (By Authority)
INSERT OR IGNORE INTO wiki_categories (name, category_type, description, icon, display_order)
VALUES ('按主管機關', 'authority', '依照主管機關分類文件', '🏛️', 1);

-- 按金融機構 (By Institution)
INSERT OR IGNORE INTO wiki_categories (name, category_type, description, icon, display_order)
VALUES ('按金融機構', 'institution', '依照金融機構分類文件', '🏦', 2);

-- 按違規類型 (By Violation Type)
INSERT OR IGNORE INTO wiki_categories (name, category_type, description, icon, display_order)
VALUES ('按違規類型', 'violation', '依照違規類型分類文件', '⚖️', 3);

-- 按文件類型 (By Document Type)
INSERT OR IGNORE INTO wiki_categories (name, category_type, description, icon, display_order)
VALUES ('按文件類型', 'document_type', '依照文件類型分類文件', '📄', 4);

-- ============================================================================
-- Migration Complete
-- ============================================================================
