-- Migration: Enhance history table for query memo system
-- Date: 2025-11-14
-- Purpose: Add fields to track planning analysis, search iterations, and user notes

-- Add new columns to history table
ALTER TABLE history ADD COLUMN query_analysis TEXT;  -- JSON: QueryAnalysis data
ALTER TABLE history ADD COLUMN plan_data TEXT;  -- JSON: ResearchPlan data
ALTER TABLE history ADD COLUMN search_iterations INTEGER DEFAULT 0;  -- Number of re-search iterations
ALTER TABLE history ADD COLUMN search_strategy TEXT;  -- Final strategy used (strict/relaxed/broad)
ALTER TABLE history ADD COLUMN vector_chunks_count INTEGER DEFAULT 0;  -- Number of vector search results
ALTER TABLE history ADD COLUMN hard_chunks_count INTEGER DEFAULT 0;  -- Number of hard search results
ALTER TABLE history ADD COLUMN total_chunks_count INTEGER DEFAULT 0;  -- Total unique chunks
ALTER TABLE history ADD COLUMN citations_count INTEGER DEFAULT 0;  -- Number of citations
ALTER TABLE history ADD COLUMN confidence_level TEXT;  -- 高/中/低
ALTER TABLE history ADD COLUMN validation_issues TEXT;  -- JSON: List of validation issues
ALTER TABLE history ADD COLUMN user_notes TEXT;  -- User's notes/memo about this query
ALTER TABLE history ADD COLUMN processing_steps TEXT;  -- JSON: List of processing steps

-- Create additional indexes for new fields
CREATE INDEX IF NOT EXISTS idx_history_confidence ON history(confidence_level);
CREATE INDEX IF NOT EXISTS idx_history_iterations ON history(search_iterations);
CREATE INDEX IF NOT EXISTS idx_history_strategy ON history(search_strategy);
