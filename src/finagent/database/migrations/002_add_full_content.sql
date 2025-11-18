-- Migration 002: Add full_content field for wiki document display
-- Purpose: Store complete document content in database for easy wiki access
-- Date: 2025-11-18

-- Add full_content column to documents table
-- SQLite supports TEXT up to 1GB, sufficient for legal documents
ALTER TABLE documents ADD COLUMN full_content TEXT;

-- Note: For existing documents, full_content will be NULL
-- Run backfill script to populate from files:
--   uv run python scripts/backfill_full_content.py
