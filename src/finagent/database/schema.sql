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
