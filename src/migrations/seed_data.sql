-- DevSecOps Jira Dashboard - Seed Data
-- PostgreSQL
-- Inserts sample data for all tables in the ER diagram
-- Run AFTER create_tables.sql

-- =============================================
-- 1. specializations
-- =============================================
INSERT INTO specializations (specialization_id, specialization_name, created_by, is_active) VALUES
('a1000000-0000-0000-0000-000000000001', 'Backend', 'seed_script', 1),
('a1000000-0000-0000-0000-000000000002', 'Frontend', 'seed_script', 1),
('a1000000-0000-0000-0000-000000000003', 'DevOps', 'seed_script', 1),
('a1000000-0000-0000-0000-000000000004', 'QA', 'seed_script', 1),
('a1000000-0000-0000-0000-000000000005', 'Security', 'seed_script', 1);

-- =============================================
-- 2. statuses
-- =============================================
INSERT INTO statuses (status_id, status_name, created_by, is_active) VALUES
('b2000000-0000-0000-0000-000000000001', 'Active', 'seed_script', 1),
('b2000000-0000-0000-0000-000000000002', 'Completed', 'seed_script', 1),
('b2000000-0000-0000-0000-000000000003', 'Inactive', 'seed_script', 1),
('b2000000-0000-0000-0000-000000000004', 'At Risk', 'seed_script', 1),
('b2000000-0000-0000-0000-000000000005', 'Not Applicable', 'seed_script', 1);

-- =============================================
-- 3. projects
-- =============================================
INSERT INTO projects (project_id, status_id, sn_project_id, project_name, onboarded_date, project_type, is_applicable, client, created_by, is_active) VALUES
('c3000000-0000-0000-0000-000000000001', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-001', 'Payment Gateway', '2024-01-15', 'Application', TRUE, 'Acme Corp', 'seed_script', 1),
('c3000000-0000-0000-0000-000000000002', 'b2000000-0000-0000-0000-000000000002', 'SN-PRJ-002', 'User Portal', '2024-02-20', 'Application', TRUE, 'Beta Inc', 'seed_script', 1),
('c3000000-0000-0000-0000-000000000003', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-003', 'API Platform', '2024-03-10', 'Platform', TRUE, 'Acme Corp', 'seed_script', 1),
('c3000000-0000-0000-0000-000000000004', 'b2000000-0000-0000-0000-000000000004', 'SN-PRJ-004', 'Legacy Migration', '2023-11-01', 'Migration', TRUE, 'Gamma LLC', 'seed_script', 1),
('c3000000-0000-0000-0000-000000000005', 'b2000000-0000-0000-0000-000000000003', 'SN-PRJ-005', 'Internal Tools', '2024-04-05', 'Internal', FALSE, NULL, 'seed_script', 1);

-- =============================================
-- 4. devsecops_tickets
-- =============================================
INSERT INTO devsecops_tickets (ticket_id, specialization_id, project_id, sn_project_id, project_name, client, requested_by, approver, sync_method, requested_at, created_by, is_active) VALUES
('d4000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 'c3000000-0000-0000-0000-000000000001', 'SN-PRJ-001', 'Payment Gateway', 'Acme Corp', 'john.doe@company.com', 'jane.smith@company.com', 'automatic', '2024-01-20 10:00:00', 'seed_script', 1),
('d4000000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000002', 'c3000000-0000-0000-0000-000000000002', 'SN-PRJ-002', 'User Portal', 'Beta Inc', 'alice.wong@company.com', 'bob.jones@company.com', 'manual', '2024-02-25 14:30:00', 'seed_script', 1),
('d4000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000003', 'c3000000-0000-0000-0000-000000000003', 'SN-PRJ-003', 'API Platform', 'Acme Corp', 'charlie.brown@company.com', 'jane.smith@company.com', 'automatic', '2024-03-15 09:00:00', 'seed_script', 1),
('d4000000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000004', 'c3000000-0000-0000-0000-000000000004', 'SN-PRJ-004', 'Legacy Migration', 'Gamma LLC', 'dave.wilson@company.com', 'bob.jones@company.com', 'manual', '2023-11-10 11:00:00', 'seed_script', 1),
('d4000000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000005', 'c3000000-0000-0000-0000-000000000001', 'SN-PRJ-001', 'Payment Gateway', 'Acme Corp', 'eve.taylor@company.com', 'jane.smith@company.com', 'automatic', '2024-04-01 08:00:00', 'seed_script', 1);

-- =============================================
-- 5. repositories
-- =============================================
INSERT INTO repositories (repository_id, ticket_id, repository_name, ado_repo_id, pipeline_runs_count, success_rate, last_run_at, created_by, is_active) VALUES
('e5000000-0000-0000-0000-000000000001', 'd4000000-0000-0000-0000-000000000001', 'payment-gateway-api', 'ADO-REPO-001', 45, 92.5, '2024-05-10 15:30:00', 'seed_script', 1),
('e5000000-0000-0000-0000-000000000002', 'd4000000-0000-0000-0000-000000000001', 'payment-gateway-ui', 'ADO-REPO-002', 30, 88.0, '2024-05-09 12:00:00', 'seed_script', 1),
('e5000000-0000-0000-0000-000000000003', 'd4000000-0000-0000-0000-000000000002', 'user-portal-frontend', 'ADO-REPO-003', 60, 95.0, '2024-05-10 18:00:00', 'seed_script', 1),
('e5000000-0000-0000-0000-000000000004', 'd4000000-0000-0000-0000-000000000003', 'api-platform-core', 'ADO-REPO-004', 120, 90.0, '2024-05-11 09:00:00', 'seed_script', 1),
('e5000000-0000-0000-0000-000000000005', 'd4000000-0000-0000-0000-000000000004', 'legacy-migration-scripts', 'ADO-REPO-005', 15, 75.0, '2024-04-28 16:00:00', 'seed_script', 1);

-- =============================================
-- 6. settings
-- =============================================
INSERT INTO settings (setting_id, specialization_id, at_risk_threshold, email_digest, at_risk_alert, last_synced, created_by, is_active) VALUES
('f6000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 5, 'weekly', 'immediate', '2024-05-10 00:00:00', 'seed_script', 1),
('f6000000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000002', 3, 'daily', 'immediate', '2024-05-10 00:00:00', 'seed_script', 1),
('f6000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000003', 7, 'weekly', 'daily', '2024-05-09 00:00:00', 'seed_script', 1),
('f6000000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000004', 4, 'daily', 'immediate', '2024-05-10 00:00:00', 'seed_script', 1),
('f6000000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000005', 2, 'daily', 'immediate', '2024-05-10 00:00:00', 'seed_script', 1);

-- =============================================
-- 7. email_recipient
-- =============================================
INSERT INTO email_recipient (email_recipient_id, setting_id, specialization_id, alert_recipient, created_by, is_active) VALUES
('a7000000-0000-0000-0000-000000000001', 'f6000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 'backend-lead@company.com', 'seed_script', 1),
('a7000000-0000-0000-0000-000000000002', 'f6000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 'tech-manager@company.com', 'seed_script', 1),
('a7000000-0000-0000-0000-000000000003', 'f6000000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000002', 'frontend-lead@company.com', 'seed_script', 1),
('a7000000-0000-0000-0000-000000000004', 'f6000000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000003', 'devops-lead@company.com', 'seed_script', 1),
('a7000000-0000-0000-0000-000000000005', 'f6000000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000005', 'security-lead@company.com', 'seed_script', 1);

-- =============================================
-- 8. email_templates
-- =============================================
INSERT INTO email_templates (email_template_id, template_name, template_content, created_by, is_active) VALUES
('b8000000-0000-0000-0000-000000000001', 'Weekly Digest', '<h1>Weekly DevSecOps Digest</h1><p>Here is your weekly summary of project metrics and pipeline health.</p>', 'seed_script', 1),
('b8000000-0000-0000-0000-000000000002', 'At Risk Alert', '<h1>At Risk Alert</h1><p>The following projects have been flagged as at risk and require immediate attention.</p>', 'seed_script', 1),
('b8000000-0000-0000-0000-000000000003', 'Daily Summary', '<h1>Daily Summary</h1><p>Your daily overview of pipeline runs, security scans, and project status changes.</p>', 'seed_script', 1);

-- =============================================
-- 9. email_history
-- =============================================
INSERT INTO email_history (email_history_id, setting_id, email_status, email_type, report_url, last_synced, created_by, is_active) VALUES
('c9000000-0000-0000-0000-000000000001', 'f6000000-0000-0000-0000-000000000001', 'sent', 'weekly_digest', 'https://reports.company.com/digest/2024-05-06', '2024-05-06 08:00:00', 'seed_script', 1),
('c9000000-0000-0000-0000-000000000002', 'f6000000-0000-0000-0000-000000000001', 'sent', 'at_risk_alert', 'https://reports.company.com/alert/2024-05-08', '2024-05-08 10:30:00', 'seed_script', 1),
('c9000000-0000-0000-0000-000000000003', 'f6000000-0000-0000-0000-000000000002', 'failed', 'daily_summary', NULL, '2024-05-09 08:00:00', 'seed_script', 1),
('c9000000-0000-0000-0000-000000000004', 'f6000000-0000-0000-0000-000000000003', 'sent', 'weekly_digest', 'https://reports.company.com/digest/2024-05-06-devops', '2024-05-06 08:00:00', 'seed_script', 1),
('c9000000-0000-0000-0000-000000000005', 'f6000000-0000-0000-0000-000000000004', 'sent', 'at_risk_alert', 'https://reports.company.com/alert/2024-05-10', '2024-05-10 14:00:00', 'seed_script', 1);

-- =============================================
-- 10. error_log
-- =============================================
INSERT INTO error_log (error_id, error_message, error_function, error_file, stack_trace, created_by, is_active) VALUES
('da000000-0000-0000-0000-000000000001', '[trace_id:abc123] Connection timeout to database', 'get_db_session', 'src/services/dependencies.py', 'Traceback (most recent call last):\n  File "src/services/dependencies.py", line 45\nTimeoutError: Connection timed out', 'overview_service', 1),
('da000000-0000-0000-0000-000000000002', '[trace_id:def456] Invalid UUID format in request', 'parse_specialization', 'src/services/overview_service.py', 'Traceback (most recent call last):\n  File "src/services/overview_service.py", line 89\nValueError: Invalid UUID', 'overview_service', 1);

-- =============================================
-- 11. jira_tickets
-- =============================================
INSERT INTO jira_tickets (jira_ticket_id, project_id, jira_id, type, assignee, priority, status, reason_category, comments, evidence_url, created_by, is_active) VALUES
('eb000000-0000-0000-0000-000000000001', 'c3000000-0000-0000-0000-000000000001', 'JIRA-1001', 'Bug', 'john.doe@company.com', 'High', 'Open', 'Security', 'Critical vulnerability found in payment processing module', 'https://jira.company.com/browse/JIRA-1001', 'seed_script', 1),
('eb000000-0000-0000-0000-000000000002', 'c3000000-0000-0000-0000-000000000001', 'JIRA-1002', 'Task', 'alice.wong@company.com', 'Medium', 'In Progress', 'Compliance', 'Update SSL certificates before expiry', 'https://jira.company.com/browse/JIRA-1002', 'seed_script', 1),
('eb000000-0000-0000-0000-000000000003', 'c3000000-0000-0000-0000-000000000002', 'JIRA-2001', 'Bug', 'bob.jones@company.com', 'Low', 'Resolved', 'Code Quality', 'Fix linting errors in user portal components', NULL, 'seed_script', 1),
('eb000000-0000-0000-0000-000000000004', 'c3000000-0000-0000-0000-000000000003', 'JIRA-3001', 'Story', 'charlie.brown@company.com', 'High', 'Open', 'Feature', 'Implement rate limiting on API endpoints', 'https://jira.company.com/browse/JIRA-3001', 'seed_script', 1),
('eb000000-0000-0000-0000-000000000005', 'c3000000-0000-0000-0000-000000000004', 'JIRA-4001', 'Task', 'dave.wilson@company.com', 'Critical', 'Open', 'Migration', 'Data migration script failing on large datasets', 'https://jira.company.com/browse/JIRA-4001', 'seed_script', 1);

-- =============================================
-- 12. pipeline_runs
-- =============================================
INSERT INTO pipeline_runs (pipeline_run_id, repository_id, run_number, status, branch, duration_seconds, triggered_at, created_by, is_active) VALUES
('fc000000-0000-0000-0000-000000000001', 'e5000000-0000-0000-0000-000000000001', 101, 'succeeded', 'main', 245, '2024-05-10 15:30:00', 'seed_script', 1),
('fc000000-0000-0000-0000-000000000002', 'e5000000-0000-0000-0000-000000000001', 100, 'failed', 'feature/auth-update', 180, '2024-05-10 14:00:00', 'seed_script', 1),
('fc000000-0000-0000-0000-000000000003', 'e5000000-0000-0000-0000-000000000002', 55, 'succeeded', 'main', 120, '2024-05-09 12:00:00', 'seed_script', 1),
('fc000000-0000-0000-0000-000000000004', 'e5000000-0000-0000-0000-000000000003', 200, 'succeeded', 'main', 90, '2024-05-10 18:00:00', 'seed_script', 1),
('fc000000-0000-0000-0000-000000000005', 'e5000000-0000-0000-0000-000000000004', 350, 'succeeded', 'develop', 310, '2024-05-11 09:00:00', 'seed_script', 1);

-- =============================================
-- 13. commits
-- =============================================
INSERT INTO commits (commit_id, repository_id, hash, message, author, committed_at, created_by, is_active) VALUES
('ad000000-0000-0000-0000-000000000001', 'e5000000-0000-0000-0000-000000000001', 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0', 'fix: resolve payment timeout issue', 'john.doe@company.com', '2024-05-10 14:45:00', 'seed_script', 1),
('ad000000-0000-0000-0000-000000000002', 'e5000000-0000-0000-0000-000000000001', 'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1', 'feat: add retry logic for failed transactions', 'alice.wong@company.com', '2024-05-10 13:30:00', 'seed_script', 1),
('ad000000-0000-0000-0000-000000000003', 'e5000000-0000-0000-0000-000000000003', 'c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2', 'refactor: optimize component rendering', 'bob.jones@company.com', '2024-05-10 17:00:00', 'seed_script', 1),
('ad000000-0000-0000-0000-000000000004', 'e5000000-0000-0000-0000-000000000004', 'd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3', 'feat: implement rate limiting middleware', 'charlie.brown@company.com', '2024-05-11 08:30:00', 'seed_script', 1),
('ad000000-0000-0000-0000-000000000005', 'e5000000-0000-0000-0000-000000000005', 'e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4', 'fix: handle null values in migration script', 'dave.wilson@company.com', '2024-04-28 15:00:00', 'seed_script', 1);

-- =============================================
-- 14. pull_requests
-- =============================================
INSERT INTO pull_requests (pull_request_id, repository_id, title, author, status, updated_at, created_by, is_active) VALUES
('be000000-0000-0000-0000-000000000001', 'e5000000-0000-0000-0000-000000000001', 'Fix payment timeout and add retry logic', 'john.doe@company.com', 'completed', '2024-05-10 16:00:00', 'seed_script', 1),
('be000000-0000-0000-0000-000000000002', 'e5000000-0000-0000-0000-000000000001', 'Update authentication flow', 'alice.wong@company.com', 'active', '2024-05-10 14:30:00', 'seed_script', 1),
('be000000-0000-0000-0000-000000000003', 'e5000000-0000-0000-0000-000000000003', 'Optimize rendering performance', 'bob.jones@company.com', 'completed', '2024-05-10 18:30:00', 'seed_script', 1),
('be000000-0000-0000-0000-000000000004', 'e5000000-0000-0000-0000-000000000004', 'Add rate limiting to API endpoints', 'charlie.brown@company.com', 'active', '2024-05-11 10:00:00', 'seed_script', 1),
('be000000-0000-0000-0000-000000000005', 'e5000000-0000-0000-0000-000000000005', 'Fix null handling in migration', 'dave.wilson@company.com', 'abandoned', '2024-04-29 09:00:00', 'seed_script', 1);

-- =============================================
-- 15. security_scans
-- =============================================
INSERT INTO security_scans (security_scan_id, repository_id, scan_type, findings_count, description, scanned_at, created_by, is_active) VALUES
('cf000000-0000-0000-0000-000000000001', 'e5000000-0000-0000-0000-000000000001', 'SAST', 2, 'Static analysis found 2 medium-severity issues', '2024-05-10 16:00:00', 'seed_script', 1),
('cf000000-0000-0000-0000-000000000002', 'e5000000-0000-0000-0000-000000000001', 'SCA', 1, 'Dependency vulnerability in lodash 4.17.20', '2024-05-10 16:05:00', 'seed_script', 1),
('cf000000-0000-0000-0000-000000000003', 'e5000000-0000-0000-0000-000000000003', 'SAST', 0, 'No issues found', '2024-05-10 19:00:00', 'seed_script', 1),
('cf000000-0000-0000-0000-000000000004', 'e5000000-0000-0000-0000-000000000004', 'DAST', 3, 'Dynamic scan found 3 potential XSS vectors', '2024-05-11 10:00:00', 'seed_script', 1),
('cf000000-0000-0000-0000-000000000005', 'e5000000-0000-0000-0000-000000000005', 'SCA', 5, 'Multiple outdated dependencies with known CVEs', '2024-04-28 17:00:00', 'seed_script', 1);

-- =============================================
-- 16. artifacts
-- =============================================
INSERT INTO artifacts (artifact_id, pipeline_run_id, artifact_name, size_bytes, url, uploaded_at, created_by, is_active) VALUES
('d0100000-0000-0000-0000-000000000001', 'fc000000-0000-0000-0000-000000000001', 'payment-gateway-api-1.2.3.jar', 52428800, 'https://artifacts.company.com/payment-gateway/1.2.3/api.jar', '2024-05-10 15:35:00', 'seed_script', 1),
('d0100000-0000-0000-0000-000000000002', 'fc000000-0000-0000-0000-000000000003', 'payment-gateway-ui-1.1.0.zip', 15728640, 'https://artifacts.company.com/payment-gateway/1.1.0/ui.zip', '2024-05-09 12:05:00', 'seed_script', 1),
('d0100000-0000-0000-0000-000000000003', 'fc000000-0000-0000-0000-000000000004', 'user-portal-frontend-2.0.0.tar.gz', 8388608, 'https://artifacts.company.com/user-portal/2.0.0/frontend.tar.gz', '2024-05-10 18:05:00', 'seed_script', 1),
('d0100000-0000-0000-0000-000000000004', 'fc000000-0000-0000-0000-000000000005', 'api-platform-core-3.1.0.jar', 104857600, 'https://artifacts.company.com/api-platform/3.1.0/core.jar', '2024-05-11 09:10:00', 'seed_script', 1),
('d0100000-0000-0000-0000-000000000005', 'fc000000-0000-0000-0000-000000000001', 'test-report-101.html', 1048576, 'https://artifacts.company.com/payment-gateway/reports/101.html', '2024-05-10 15:34:00', 'seed_script', 1);

-- =============================================
-- 17. cron_jobs
-- =============================================
INSERT INTO cron_jobs (cron_id, specialization_id, type, sync_status, created_by, is_active) VALUES
('e0200000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 'azure', 'success', 'seed_script', 1),
('e0200000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000002', 'azure', 'success', 'seed_script', 1),
('e0200000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000003', 'azure', 'fail', 'seed_script', 1),
('e0200000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000001', 'email', 'success', 'seed_script', 1),
('e0200000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000004', 'email', 'pending', 'seed_script', 1);

-- =============================================
-- 18. kpi_history
-- =============================================
INSERT INTO kpi_history (kpi_history_id, specialization_id, projects_count, projects_increase_count, projects_decrease_count, completed_count, completed_increase_count, completed_decrease_count, active_count, active_increase_count, active_decrease_count, inactive_count, inactive_increase_count, inactive_decrease_count, at_risk_count, at_risk_increase_count, at_risk_decrease_count, not_applicable_count, not_applicable_increase_count, not_applicable_decrease_count, created_by, is_active) VALUES
('f0300000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 12, 2, 0, 5, 1, 0, 4, 1, 0, 1, 0, 0, 2, 1, 0, 0, 0, 0, 'seed_script', 1),
('f0300000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000002', 8, 1, 0, 3, 0, 0, 3, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 'seed_script', 1),
('f0300000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000003', 6, 0, 1, 2, 0, 0, 2, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 'seed_script', 1),
('f0300000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000004', 10, 1, 0, 4, 1, 0, 3, 0, 0, 2, 0, 0, 1, 0, 1, 0, 0, 0, 'seed_script', 1),
('f0300000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000005', 4, 0, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 'seed_script', 1);
