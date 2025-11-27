-- Query History Table Schema
-- Purpose: Track all research queries with execution metadata and results
-- Used by: Celery tasks, HTTP API, WebSocket

CREATE TABLE IF NOT EXISTS query_history (
    -- Primary identification
    id SERIAL PRIMARY KEY,
    query_id TEXT UNIQUE NOT NULL,
    thread_id TEXT NOT NULL,

    -- Query details
    query_text TEXT NOT NULL,
    query_type TEXT,
    use_plan_execute BOOLEAN DEFAULT TRUE,

    -- Execution metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'pending',  -- pending, running, completed, failed
    error_message TEXT,

    -- Results (stored as JSONB for flexibility)
    query_insight JSONB,
    plan JSONB,
    past_steps JSONB,
    response TEXT,

    -- Performance metrics
    total_tokens INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    llm_cost_usd DECIMAL(10, 6),
    execution_time_seconds DECIMAL(10, 3),

    -- User context
    user_id TEXT,
    session_id TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_query_history_thread_id ON query_history(thread_id);
CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_status ON query_history(status);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop trigger if exists (for re-running this script)
DROP TRIGGER IF EXISTS update_query_history_updated_at ON query_history;

CREATE TRIGGER update_query_history_updated_at
    BEFORE UPDATE ON query_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE query_history IS 'Tracks all research queries with execution metadata and results';
COMMENT ON COLUMN query_history.query_id IS 'UUID for unique query identification';
COMMENT ON COLUMN query_history.thread_id IS 'LangGraph thread ID for checkpoint tracking';
COMMENT ON COLUMN query_history.status IS 'Query execution status: pending, running, completed, failed';
COMMENT ON COLUMN query_history.query_insight IS 'JSON result from QueryAnalyzer agent';
COMMENT ON COLUMN query_history.plan IS 'JSON result from Planner agent';
COMMENT ON COLUMN query_history.past_steps IS 'JSON array of execution steps';
COMMENT ON COLUMN query_history.response IS 'Final response from Reporter agent';
