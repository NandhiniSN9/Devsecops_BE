-- Migration: Add is_devsecops_onboarded column to projects table
-- Purpose: Flag projects that have been onboarded to DevSecOps
-- Logic: Match by project_id or by normalized project_name

-- =============================================
-- Step 1: Add the column
-- =============================================
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS is_devsecops_onboarded BOOLEAN DEFAULT FALSE;

-- =============================================
-- Step 2: Update based on direct project_id match
-- (projects.project_id = devsecops_tickets.project_id)
-- =============================================
UPDATE projects
SET is_devsecops_onboarded = TRUE,
    modified_at = CURRENT_TIMESTAMP,
    modified_by = 'migration_script'
WHERE project_id IN (
    SELECT DISTINCT dt.project_id
    FROM devsecops_tickets dt
    WHERE dt.project_id IS NOT NULL
      AND dt.is_active = 1
);

-- =============================================
-- Step 3: Update based on normalized project_name match
-- Normalization: remove 'zeb-' prefix, replace '-' with space, lowercase, trim
-- Example: "zeb-touchpoint-pj" → "touchpoint pj" matches "Touchpoint PJ"
-- =============================================
UPDATE projects p
SET is_devsecops_onboarded = TRUE,
    modified_at = CURRENT_TIMESTAMP,
    modified_by = 'migration_script'
WHERE p.is_devsecops_onboarded = FALSE
  AND p.is_active = 1
  AND EXISTS (
    SELECT 1
    FROM devsecops_tickets dt
    WHERE dt.is_active = 1
      AND LOWER(TRIM(p.project_name)) = TRIM(
          REPLACE(
              REGEXP_REPLACE(LOWER(TRIM(dt.project_name)), '^zeb-', ''),
              '-',
              ' '
          )
      )
  );

-- =============================================
-- Index for performance on the new column
-- =============================================
CREATE INDEX IF NOT EXISTS idx_projects_is_devsecops_onboarded
ON projects(is_devsecops_onboarded);
