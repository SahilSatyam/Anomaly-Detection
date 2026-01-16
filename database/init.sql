-- Database Initialization Script
-- This script runs when PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON DATABASE stock_db TO stockuser;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized at %', NOW();
END $$;
