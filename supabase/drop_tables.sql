-- TiktokChef Database - Drop All Tables
-- Run this SQL in your Supabase SQL Editor to delete all tables
-- WARNING: This will permanently delete all data!

-- Drop tables in correct order (child tables first, then parent)
-- This avoids foreign key constraint errors

-- Drop child tables first
DROP TABLE IF EXISTS instructions CASCADE;
DROP TABLE IF EXISTS ingredients CASCADE;

-- Drop parent table
DROP TABLE IF EXISTS recipes CASCADE;

-- Drop the trigger function
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Verify tables were dropped successfully
SELECT
    table_name
FROM
    information_schema.tables
WHERE
    table_schema = 'public'
    AND table_name IN ('recipes', 'ingredients', 'instructions')
ORDER BY
    table_name;

-- If the query above returns no rows, all tables were successfully dropped
