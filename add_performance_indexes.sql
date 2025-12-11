-- Performance indexes for faster queries (only missing ones)
CREATE INDEX IF NOT EXISTS idx_facts_created ON facts(created);
CREATE INDEX IF NOT EXISTS idx_facts_updated ON facts(updated);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_timestamp ON conversation_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity);
