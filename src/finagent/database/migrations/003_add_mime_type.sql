-- Migration 003: Add mime_type field for file type identification
-- Purpose: Distinguish between text files (show content) and binary files (download)
-- Date: 2025-11-18

-- Add mime_type column
ALTER TABLE documents ADD COLUMN mime_type TEXT DEFAULT 'text/plain';

-- Update existing text files
UPDATE documents SET mime_type = 'text/plain' WHERE filename LIKE '%.txt';
UPDATE documents SET mime_type = 'application/pdf' WHERE filename LIKE '%.pdf';
UPDATE documents SET mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' WHERE filename LIKE '%.docx';
UPDATE documents SET mime_type = 'application/msword' WHERE filename LIKE '%.doc';
