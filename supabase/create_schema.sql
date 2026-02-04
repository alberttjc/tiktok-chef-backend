-- TiktokChef Database Schema for Supabase PostgreSQL
-- Run this SQL in your Supabase SQL Editor to create the required tables

-- recipes table (parent)
CREATE TABLE recipes (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    source_url VARCHAR,
    creator_username VARCHAR,
    thumbnail_url VARCHAR,
    base_servings INTEGER NOT NULL DEFAULT 4,
    prep_time VARCHAR,
    cook_time VARCHAR,
    difficulty VARCHAR,
    cuisine_type VARCHAR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on source_url for caching lookups
CREATE INDEX idx_recipes_source_url ON recipes(source_url);

-- Create index on creator_username for filtering by creator
CREATE INDEX idx_recipes_creator_username ON recipes(creator_username);

-- ingredients table (child of recipes)
CREATE TABLE ingredients (
    id BIGSERIAL PRIMARY KEY,
    recipe_id BIGINT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    unit VARCHAR,
    original_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on recipe_id for faster joins
CREATE INDEX idx_ingredients_recipe_id ON ingredients(recipe_id);

-- instructions table (child of recipes)
CREATE TABLE instructions (
    id BIGSERIAL PRIMARY KEY,
    recipe_id BIGINT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    instruction_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on recipe_id for faster joins
CREATE INDEX idx_instructions_recipe_id ON instructions(recipe_id);

-- Auto-update updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at on recipes table
CREATE TRIGGER update_recipes_updated_at
    BEFORE UPDATE ON recipes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify tables were created successfully
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM
    information_schema.columns
WHERE
    table_name IN ('recipes', 'ingredients', 'instructions')
ORDER BY
    table_name, ordinal_position;
