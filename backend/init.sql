-- Database initialization script for PromptFlow
-- This script runs when PostgreSQL container starts for the first time

-- Create the database (handled by POSTGRES_DB environment variable)
-- $POSTGRES_DB; $POSTGRES_USER; $POSTGRES_PASSWORD

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create basic indexes for performance
-- These will be created by SQLAlchemy models, but we can add custom indexes here

-- Create functions for IDs generation if needed
CREATE OR REPLACE FUNCTION generate_ulid() RETURNS TEXT AS $$
DECLARE
    timestamp_part TEXT;
    random_part TEXT;
BEGIN
    -- Get timestamp part (48 bits = 12 hex chars)
    timestamp_part := lpad(to_hex(floor(extract(epoch from now() * 1000)::bigint), 12);
    
    -- Get random part (80 bits = 20 hex chars)
    random_part := substr(md5(random()::text), 1, 20);
    
    RETURN timestamp_part || random_part;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO promptflow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO promptflow;

-- Enable pgcrypto for additional cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types if needed
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('owner', 'admin', 'member');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE run_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE document_status AS ENUM ('uploaded', 'processing', 'indexed', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;