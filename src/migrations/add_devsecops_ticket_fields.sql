-- Add status_id FK to devsecops_tickets
ALTER TABLE devsecops_tickets ADD COLUMN IF NOT EXISTS status_id UUID REFERENCES statuses(status_id);

-- Add at_risk_at timestamp
ALTER TABLE devsecops_tickets ADD COLUMN IF NOT EXISTS at_risk_at TIMESTAMP;

-- Add completed_at timestamp
ALTER TABLE devsecops_tickets ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;

-- Remove completed_at from projects (move to devsecops_tickets)
-- Note: keeping the column in projects for backward compat but it's deprecated
