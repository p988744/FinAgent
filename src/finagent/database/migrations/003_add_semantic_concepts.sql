-- Migration: Add semantic concepts system
-- Date: 2025-11-14
-- Purpose: Enable abstract semantic concept mapping instead of literal keyword matching

-- Semantic concepts table (core concept definitions)
CREATE TABLE IF NOT EXISTS semantic_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_key TEXT UNIQUE NOT NULL,        -- e.g., 'ANTI_MONEY_LAUNDERING'
    concept_level INTEGER NOT NULL,          -- 1=domain, 2=violation, 3=entity
    parent_concept_key TEXT,                 -- hierarchical relationship
    name_zh TEXT NOT NULL,                   -- 洗錢防制
    name_en TEXT,                            -- Anti-Money Laundering
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_concept_key) REFERENCES semantic_concepts(concept_key)
);

-- Concept synonyms table (surface forms that map to concepts)
CREATE TABLE IF NOT EXISTS concept_synonyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_key TEXT NOT NULL,
    synonym TEXT NOT NULL,                   -- 洗錢, AML, 反洗錢, etc.
    synonym_type TEXT NOT NULL,              -- zh/en/abbreviation/variant
    weight REAL DEFAULT 1.0,                 -- relevance weight (0-1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (concept_key) REFERENCES semantic_concepts(concept_key) ON DELETE CASCADE
);

-- Document-semantic-concept mapping (many-to-many)
CREATE TABLE IF NOT EXISTS document_semantic_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    concept_key TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,             -- confidence in this mapping (0-1)
    source TEXT,                             -- how concept was assigned (metadata/llm/manual)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (filename) REFERENCES documents(filename) ON DELETE CASCADE,
    FOREIGN KEY (concept_key) REFERENCES semantic_concepts(concept_key) ON DELETE CASCADE,
    UNIQUE(filename, concept_key)            -- prevent duplicates
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_concepts_level ON semantic_concepts(concept_level);
CREATE INDEX IF NOT EXISTS idx_concepts_parent ON semantic_concepts(parent_concept_key);
CREATE INDEX IF NOT EXISTS idx_synonyms_lookup ON concept_synonyms(synonym);
CREATE INDEX IF NOT EXISTS idx_synonyms_concept ON concept_synonyms(concept_key);
CREATE INDEX IF NOT EXISTS idx_doc_sem_concepts_filename ON document_semantic_concepts(filename);
CREATE INDEX IF NOT EXISTS idx_doc_sem_concepts_concept ON document_semantic_concepts(concept_key);

-- Full-text search index on synonyms for fuzzy matching
CREATE VIRTUAL TABLE IF NOT EXISTS concept_synonyms_fts USING fts5(
    concept_key UNINDEXED,
    synonym,
    content=concept_synonyms,
    content_rowid=id
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS concept_synonyms_ai AFTER INSERT ON concept_synonyms BEGIN
    INSERT INTO concept_synonyms_fts(rowid, concept_key, synonym)
    VALUES (new.id, new.concept_key, new.synonym);
END;

CREATE TRIGGER IF NOT EXISTS concept_synonyms_ad AFTER DELETE ON concept_synonyms BEGIN
    DELETE FROM concept_synonyms_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS concept_synonyms_au AFTER UPDATE ON concept_synonyms BEGIN
    DELETE FROM concept_synonyms_fts WHERE rowid = old.id;
    INSERT INTO concept_synonyms_fts(rowid, concept_key, synonym)
    VALUES (new.id, new.concept_key, new.synonym);
END;

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS concepts_update_timestamp
AFTER UPDATE ON semantic_concepts
BEGIN
    UPDATE semantic_concepts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
