-- MEM-002: Add subject column to facts table
-- Safe to run multiple times: uses IF NOT EXISTS where supported
-- Compatible with SQLite (production database)

-- Step 1: Add subject column with default 'user'
ALTER TABLE facts ADD COLUMN subject TEXT NOT NULL DEFAULT 'user';

-- Step 2: Create index for subject-filtered queries
CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject);

-- Step 3: Verify migration
SELECT COUNT(*) as total_facts,
       COUNT(subject) as facts_with_subject
FROM facts;
