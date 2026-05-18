-- DevSecOps Jira Dashboard - Database Schema Creation
-- PostgreSQL
-- Generated from design/er_diagram.mmd

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- 1. specializations
-- =============================================
CREATE TABLE IF NOT EXISTS specializations (
    specialization_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    specialization_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 2. statuses
-- =============================================
CREATE TABLE IF NOT EXISTS statuses (
    status_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 3. projects
-- =============================================
CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status_id UUID REFERENCES statuses(status_id),
    sn_project_id VARCHAR(255),
    project_name VARCHAR(255) NOT NULL,
    onboarded_date DATE NOT NULL,
    project_type VARCHAR(255) NOT NULL,
    specialization_name VARCHAR(255),
    is_applicable BOOLEAN DEFAULT TRUE,
    client VARCHAR(255),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 4. devsecops_tickets
-- =============================================
CREATE TABLE IF NOT EXISTS devsecops_tickets (
    ticket_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    specialization_id UUID REFERENCES specializations(specialization_id),
    project_id UUID,
    sn_project_id VARCHAR(255),
    devsec_project_id VARCHAR(255),
    project_name VARCHAR(255) NOT NULL,
    client VARCHAR(255),
    requested_by VARCHAR(255),
    approver VARCHAR(255),
    sync_method VARCHAR(255),
    requested_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 5. repositories
-- =============================================
CREATE TABLE IF NOT EXISTS repositories (
    repository_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES devsecops_tickets(ticket_id),
    repository_name VARCHAR(255) NOT NULL,
    ado_repo_id VARCHAR(255),
    lead_approvers VARCHAR(1000),
    pipeline_runs_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0,
    last_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 6. settings
-- =============================================
CREATE TABLE IF NOT EXISTS settings (
    setting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    specialization_id UUID REFERENCES specializations(specialization_id),
    at_risk_threshold INTEGER NOT NULL,
    email_digest VARCHAR(50),
    at_risk_alert VARCHAR(50),
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 7. email_recipient
-- =============================================
CREATE TABLE IF NOT EXISTS email_recipient (
    email_recipient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_id UUID REFERENCES settings(setting_id),
    specialization_id UUID REFERENCES specializations(specialization_id),
    alert_recipient VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 8. email_templates
-- =============================================
CREATE TABLE IF NOT EXISTS email_templates (
    email_template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(255) NOT NULL,
    template_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 9. email_history
-- =============================================
CREATE TABLE IF NOT EXISTS email_history (
    email_history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_id UUID REFERENCES settings(setting_id),
    email_status VARCHAR(50) NOT NULL,
    email_type VARCHAR(100) NOT NULL,
    report_url TEXT,
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 10. error_log
-- =============================================
CREATE TABLE IF NOT EXISTS error_log (
    error_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_message TEXT NOT NULL,
    error_function TEXT NOT NULL,
    error_file TEXT NOT NULL,
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 11. jira_tickets
-- =============================================
CREATE TABLE IF NOT EXISTS jira_tickets (
    jira_ticket_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id),
    jira_id VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    assignee VARCHAR(255) NOT NULL,
    priority VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    reason_category VARCHAR(255) NOT NULL,
    comments TEXT NOT NULL,
    evidence_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 12. pipeline_runs
-- =============================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    pipeline_run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(repository_id),
    run_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    branch VARCHAR(255) NOT NULL,
    duration_seconds INTEGER,
    triggered_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 13. commits
-- =============================================
CREATE TABLE IF NOT EXISTS commits (
    commit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(repository_id),
    hash VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    committed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 14. pull_requests
-- =============================================
CREATE TABLE IF NOT EXISTS pull_requests (
    pull_request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(repository_id),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 15. security_scans
-- =============================================
CREATE TABLE IF NOT EXISTS security_scans (
    security_scan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(repository_id),
    scan_type VARCHAR(100) NOT NULL,
    findings_count INTEGER DEFAULT 0,
    description VARCHAR(500),
    scanned_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 16. artifacts
-- =============================================
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_run_id UUID REFERENCES pipeline_runs(pipeline_run_id),
    artifact_name VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL,
    url TEXT NOT NULL,
    uploaded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 17. cron_jobs
-- =============================================
CREATE TABLE IF NOT EXISTS cron_jobs (
    cron_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    specialization_id VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    sync_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- 18. kpi_history
-- =============================================
CREATE TABLE IF NOT EXISTS kpi_history (
    kpi_history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    specialization_id UUID REFERENCES specializations(specialization_id),
    projects_count INTEGER DEFAULT 0,
    projects_increase_count INTEGER DEFAULT 0,
    projects_decrease_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    completed_increase_count INTEGER DEFAULT 0,
    completed_decrease_count INTEGER DEFAULT 0,
    active_count INTEGER DEFAULT 0,
    active_increase_count INTEGER DEFAULT 0,
    active_decrease_count INTEGER DEFAULT 0,
    inactive_count INTEGER DEFAULT 0,
    inactive_increase_count INTEGER DEFAULT 0,
    inactive_decrease_count INTEGER DEFAULT 0,
    at_risk_count INTEGER DEFAULT 0,
    at_risk_increase_count INTEGER DEFAULT 0,
    at_risk_decrease_count INTEGER DEFAULT 0,
    not_applicable_count INTEGER DEFAULT 0,
    not_applicable_increase_count INTEGER DEFAULT 0,
    not_applicable_decrease_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    modified_at TIMESTAMP,
    modified_by VARCHAR(255),
    is_active INT DEFAULT 1
);

-- =============================================
-- INDEXES for performance
-- =============================================
CREATE INDEX IF NOT EXISTS idx_projects_sn_project_id ON projects(sn_project_id);
CREATE INDEX IF NOT EXISTS idx_projects_status_id ON projects(status_id);
CREATE INDEX IF NOT EXISTS idx_projects_is_active ON projects(is_active);
CREATE INDEX IF NOT EXISTS idx_projects_project_name ON projects(project_name);

CREATE INDEX IF NOT EXISTS idx_devsecops_tickets_specialization_id ON devsecops_tickets(specialization_id);
CREATE INDEX IF NOT EXISTS idx_devsecops_tickets_sn_project_id ON devsecops_tickets(sn_project_id);
CREATE INDEX IF NOT EXISTS idx_devsecops_tickets_is_active ON devsecops_tickets(is_active);

CREATE INDEX IF NOT EXISTS idx_repositories_ticket_id ON repositories(ticket_id);
CREATE INDEX IF NOT EXISTS idx_repositories_is_active ON repositories(is_active);

CREATE INDEX IF NOT EXISTS idx_settings_specialization_id ON settings(specialization_id);

CREATE INDEX IF NOT EXISTS idx_email_recipient_specialization_id ON email_recipient(specialization_id);
CREATE INDEX IF NOT EXISTS idx_email_recipient_is_active ON email_recipient(is_active);

CREATE INDEX IF NOT EXISTS idx_email_history_setting_id ON email_history(setting_id);
CREATE INDEX IF NOT EXISTS idx_email_history_email_type ON email_history(email_type);
CREATE INDEX IF NOT EXISTS idx_email_history_last_synced ON email_history(last_synced);

CREATE INDEX IF NOT EXISTS idx_kpi_history_specialization_id ON kpi_history(specialization_id);
CREATE INDEX IF NOT EXISTS idx_kpi_history_created_at ON kpi_history(created_at);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_repository_id ON pipeline_runs(repository_id);
CREATE INDEX IF NOT EXISTS idx_commits_repository_id ON commits(repository_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_repository_id ON pull_requests(repository_id);
CREATE INDEX IF NOT EXISTS idx_security_scans_repository_id ON security_scans(repository_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_pipeline_run_id ON artifacts(pipeline_run_id);

CREATE INDEX IF NOT EXISTS idx_cron_jobs_type ON cron_jobs(type);
CREATE INDEX IF NOT EXISTS idx_cron_jobs_sync_status ON cron_jobs(sync_status);

CREATE INDEX IF NOT EXISTS idx_specializations_is_active ON specializations(is_active);
CREATE INDEX IF NOT EXISTS idx_statuses_is_active ON statuses(is_active);
