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
-- NOTE: Full HTML templates are too large for inline SQL.
-- Use scripts/update_email_templates.py to load templates from files, or
-- run src/migrations/email_templates_seed.sql separately after initial seed.
-- The templates below are placeholders that will be replaced by the update script.

INSERT INTO email_templates (email_template_id, template_name, template_content, created_by, is_active) VALUES
('b8000000-0000-0000-0000-000000000001', 'Weekly Digest', '<h1>Weekly DevSecOps Digest</h1><p>Here is your weekly summary of project metrics and pipeline health.</p>', 'seed_script', 1),
('b8000000-0000-0000-0000-000000000002', 'At Risk Alert', '<h1>At Risk Alert</h1><p>The following projects have been flagged as at risk and require immediate attention.</p>', 'seed_script', 1),
('b8000000-0000-0000-0000-000000000003', 'Daily Summary', '<h1>Daily Summary</h1><p>Your daily overview of pipeline runs, security scans, and project status changes.</p>', 'seed_script', 1),
(
  'b8000000-0000-0000-0000-000000000004',
  'Weekly Summary Report',
  '<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weekly DevSecOps Report - {{ specialization_name }}</title>
        <style>
            @page {
                size: A4;
                margin: 1.5cm;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, ''Segoe UI'', Roboto, ''Helvetica Neue'', Arial, sans-serif;
                line-height: 1.6;
                color: #2c3e50;
                background: #f8f9fa;
            }

            .page-wrapper {
                max-width: 900px;
                margin: 0 auto;
                background: white;
            }

            /* Header with company branding */
            .report-header {
                background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                padding: 40px 50px;
                color: white;
                position: relative;
                overflow: hidden;
            }

            .report-header::before {
                content: '''';
                position: absolute;
                top: -50%;
                right: -10%;
                width: 300px;
                height: 300px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
            }

            .company-logo {
                width: 180px;
                height: 50px;
                background: white;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 20px;
                color: #1e3a8a;
                margin-bottom: 25px;
                letter-spacing: -0.5px;
            }

            .report-title {
                font-size: 34px;
                font-weight: 700;
                margin-bottom: 12px;
                letter-spacing: -0.5px;
            }

            .report-subtitle {
                font-size: 18px;
                opacity: 0.95;
                font-weight: 400;
            }

            .report-meta {
                margin-top: 20px;
                display: flex;
                gap: 30px;
                font-size: 14px;
            }

            .meta-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .meta-icon {
                font-size: 16px;
            }

            /* Content area */
            .report-content {
                padding: 50px;
            }

            .section {
                margin-bottom: 45px;
            }

            .section-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 25px;
                padding-bottom: 12px;
                border-bottom: 3px solid #e5e7eb;
            }

            .section-icon {
                font-size: 24px;
                width: 40px;
                height: 40px;
                background: #eff6ff;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .section-title {
                font-size: 24px;
                font-weight: 700;
                color: #1e3a8a;
            }

            /* Metrics grid */
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .metric-card {
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 25px;
                text-align: center;
                transition: transform 0.2s;
            }

            .metric-card:hover {
                transform: translateY(-2px);
                border-color: #3b82f6;
            }

            .metric-value {
                font-size: 42px;
                font-weight: 700;
                color: #1e3a8a;
                margin-bottom: 8px;
                line-height: 1;
            }

            .metric-label {
                font-size: 14px;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 600;
            }

            .metric-card.success .metric-value { color: #059669; }
            .metric-card.warning .metric-value { color: #dc2626; }
            .metric-card.info .metric-value { color: #3b82f6; }

            /* Statistics */
            .stats-container {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }

            .stat-box {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #3b82f6;
            }

            .stat-label {
                font-size: 13px;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
                font-weight: 600;
            }

            .stat-value {
                font-size: 32px;
                font-weight: 700;
                color: #1e3a8a;
            }

            .stat-value-small {
                font-size: 28px;
            }

            /* Project table */
            .project-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                overflow: hidden;
            }

            .project-table thead {
                background: #1e3a8a;
                color: white;
            }

            .project-table th {
                padding: 16px;
                text-align: left;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .project-table td {
                padding: 16px;
                border-top: 1px solid #e5e7eb;
                font-size: 14px;
            }

            .project-table tbody tr:hover {
                background: #f8f9fa;
            }

            .project-name {
                font-weight: 600;
                color: #1e3a8a;
            }

            .status-badge {
                display: inline-block;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }

            .status-active {
                background: #d1fae5;
                color: #065f46;
            }

            .status-completed {
                background: #dbeafe;
                color: #1e40af;
            }

            .status-at-risk {
                background: #fee2e2;
                color: #991b1b;
            }

            .success-rate {
                font-weight: 600;
                color: #059669;
            }

            /* Footer */
            .report-footer {
                background: #f8f9fa;
                padding: 30px 50px;
                border-top: 3px solid #e5e7eb;
                margin-top: 40px;
            }

            .footer-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .footer-company {
                font-weight: 600;
                color: #1e3a8a;
                font-size: 16px;
            }

            .footer-timestamp {
                font-size: 13px;
                color: #6b7280;
            }

            .footer-link {
                color: #3b82f6;
                text-decoration: none;
                font-weight: 600;
            }

            .footer-disclaimer {
                margin-top: 15px;
                font-size: 12px;
                color: #9ca3af;
                text-align: center;
            }

            @media print {
                .report-header::before {
                    display: none;
                }
            }
        </style>
    </head>
    <body>
        <div class="page-wrapper">
            <!-- Header with Branding -->
            <div class="report-header">
                <div class="company-logo">ZEB COMPANY</div>
                <h1 class="report-title">Weekly DevSecOps Report</h1>
                <p class="report-subtitle">{{ specialization_name }} Team Performance & Insights</p>
                <div class="report-meta">
                    <div class="meta-item">
                        <span class="meta-icon">📅</span>
                        <span>{{ start_date }} - {{ end_date }}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-icon">📊</span>
                        <span>Week {{ report_date }}</span>
                    </div>
                </div>
            </div>

            <!-- Content -->
            <div class="report-content">
                <!-- Key Metrics Section -->
                <div class="section">
                    <div class="section-header">
                        <div class="section-icon">📈</div>
                        <h2 class="section-title">Key Performance Indicators</h2>
                    </div>

                    <div class="metrics-grid">
                        <div class="metric-card success">
                            <div class="metric-value">{{ total_projects }}</div>
                            <div class="metric-label">Total Projects</div>
                        </div>
                        <div class="metric-card info">
                            <div class="metric-value">{{ active_projects }}</div>
                            <div class="metric-label">Active</div>
                        </div>
                        <div class="metric-card success">
                            <div class="metric-value">{{ completed_projects }}</div>
                            <div class="metric-label">Completed</div>
                        </div>
                        <div class="metric-card warning">
                            <div class="metric-value">{{ at_risk_count }}</div>
                            <div class="metric-label">At Risk</div>
                        </div>
                    </div>
                </div>

                <!-- Performance Statistics -->
                <div class="section">
                    <div class="section-header">
                        <div class="section-icon">🎯</div>
                        <h2 class="section-title">Performance Metrics</h2>
                    </div>

                    <div class="stats-container">
                        <div class="stat-box">
                            <div class="stat-label">Adoption Rate</div>
                            <div class="stat-value">{{ adoption_rate }}%</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">Pipeline Success</div>
                            <div class="stat-value">{{ pipeline_success_rate }}%</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">Security Scans Passed</div>
                            <div class="stat-value stat-value-small">{{ security_scans_passed }}</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">Week Over Week Change</div>
                            <div class="stat-value stat-value-small" style="color: #059669;">+12%</div>
                        </div>
                    </div>
                </div>

                {% if top_projects %}
                <!-- Top Performing Projects -->
                <div class="section">
                    <div class="section-header">
                        <div class="section-icon">🏆</div>
                        <h2 class="section-title">Top Performing Projects</h2>
                    </div>

                    <table class="project-table">
                        <thead>
                            <tr>
                                <th>Project Name</th>
                                <th>Client</th>
                                <th>Status</th>
                                <th style="text-align: right;">Success Rate</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for project in top_projects %}
                            <tr>
                                <td class="project-name">{{ project.project_name }}</td>
                                <td>{{ project.client }}</td>
                                <td>
                                    <span class="status-badge status-{{ project.status|lower|replace('' '', ''-'') }}">
                                        {{ project.status }}
                                    </span>
                                </td>
                                <td style="text-align: right;">
                                    <span class="success-rate">{{ project.success_rate }}%</span>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}
            </div>

            <!-- Footer -->
            <div class="report-footer">
                <div class="footer-content">
                    <div>
                        <div class="footer-company">ZEB Company</div>
                        <div class="footer-timestamp">Generated on {{ generated_at }}</div>
                    </div>
                    <div>
                        <a href="{{ dashboard_url }}" class="footer-link">View Dashboard →</a>
                    </div>
                </div>
                <div class="footer-disclaimer">
                    This is an automated report generated by the DevSecOps Platform. For questions or concerns, please contact your platform administrator.
                </div>
            </div>
        </div>
    </body>
    </html>',
    'seed_script',
    1
),
(
  'b8000000-0000-0000-0000-000000000005',
  'At Risk Report',
  '<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>At Risk Projects Alert - {{ specialization_name }}</title>
        <style>
            @page {
                size: A4;
                margin: 1.5cm;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, ''Segoe UI'', Roboto, ''Helvetica Neue'', Arial, sans-serif;
                line-height: 1.6;
                color: #2c3e50;
                background: #f8f9fa;
            }

            .page-wrapper {
                max-width: 900px;
                margin: 0 auto;
                background: white;
            }

            /* Header with warning styling */
            .report-header {
                background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
                padding: 40px 50px;
                color: white;
                position: relative;
                overflow: hidden;
            }

            .report-header::before {
                content: '''';
                position: absolute;
                top: -30%;
                right: -5%;
                width: 250px;
                height: 250px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
            }

            .company-logo {
                width: 180px;
                height: 50px;
                background: white;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 20px;
                color: #dc2626;
                margin-bottom: 25px;
                letter-spacing: -0.5px;
            }

            .report-title {
                font-size: 34px;
                font-weight: 700;
                margin-bottom: 12px;
                letter-spacing: -0.5px;
                display: flex;
                align-items: center;
                gap: 15px;
            }

            .alert-badge {
                background: rgba(255, 255, 255, 0.3);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
            }

            .report-subtitle {
                font-size: 18px;
                opacity: 0.95;
                font-weight: 400;
            }

            .report-meta {
                margin-top: 20px;
                display: flex;
                gap: 30px;
                font-size: 14px;
            }

            .meta-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            /* Alert banner */
            .alert-banner {
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                border-left: 6px solid #f59e0b;
                padding: 30px;
                margin: 30px 50px;
                border-radius: 10px;
            }

            .alert-content {
                display: flex;
                align-items: center;
                gap: 20px;
            }

            .alert-icon {
                font-size: 48px;
                line-height: 1;
            }

            .alert-text h3 {
                font-size: 22px;
                color: #92400e;
                margin-bottom: 8px;
                font-weight: 700;
            }

            .alert-text p {
                font-size: 15px;
                color: #78350f;
                line-height: 1.5;
            }

            .severity-badge {
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 10px;
            }

            .severity-critical {
                background: #dc2626;
                color: white;
            }

            .severity-high {
                background: #f59e0b;
                color: white;
            }

            .severity-medium {
                background: #fbbf24;
                color: #78350f;
            }

            /* Content area */
            .report-content {
                padding: 50px;
            }

            .section {
                margin-bottom: 45px;
            }

            .section-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 25px;
                padding-bottom: 12px;
                border-bottom: 3px solid #e5e7eb;
            }

            .section-icon {
                font-size: 24px;
                width: 40px;
                height: 40px;
                background: #fee2e2;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .section-title {
                font-size: 24px;
                font-weight: 700;
                color: #dc2626;
            }

            /* Summary card */
            .summary-card {
                background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
                color: white;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                margin-bottom: 40px;
            }

            .summary-count {
                font-size: 72px;
                font-weight: 700;
                line-height: 1;
                margin-bottom: 15px;
            }

            .summary-label {
                font-size: 20px;
                text-transform: uppercase;
                letter-spacing: 2px;
                opacity: 0.95;
            }

            /* Projects table */
            .projects-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                border: 2px solid #fecaca;
                border-radius: 10px;
                overflow: hidden;
            }

            .projects-table thead {
                background: #dc2626;
                color: white;
            }

            .projects-table th {
                padding: 16px;
                text-align: left;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .projects-table td {
                padding: 16px;
                border-top: 1px solid #fecaca;
                font-size: 14px;
            }

            .projects-table tbody tr:nth-child(even) {
                background: #fef2f2;
            }

            .projects-table tbody tr:hover {
                background: #fee2e2;
            }

            .project-name {
                font-weight: 600;
                color: #dc2626;
                font-size: 15px;
            }

            .overdue-badge {
                display: inline-block;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 700;
                background: #dc2626;
                color: white;
            }

            .overdue-critical {
                background: #7f1d1d;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0%, 100% {
                    opacity: 1;
                }
                50% {
                    opacity: 0.7;
                }
            }

            /* Action items */
            .action-section {
                background: #fef2f2;
                border-left: 6px solid #dc2626;
                padding: 30px;
                border-radius: 10px;
            }

            .action-section h3 {
                font-size: 20px;
                color: #dc2626;
                margin-bottom: 20px;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .action-list {
                list-style: none;
            }

            .action-item {
                padding: 15px 0;
                border-bottom: 1px solid #fecaca;
                display: flex;
                align-items: flex-start;
                gap: 15px;
            }

            .action-item:last-child {
                border-bottom: none;
            }

            .action-number {
                background: #dc2626;
                color: white;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 14px;
                flex-shrink: 0;
            }

            .action-content {
                flex: 1;
            }

            .action-title {
                font-weight: 700;
                color: #991b1b;
                margin-bottom: 4px;
                font-size: 15px;
            }

            .action-description {
                color: #7f1d1d;
                font-size: 14px;
                line-height: 1.5;
            }

            /* Footer */
            .report-footer {
                background: #f8f9fa;
                padding: 30px 50px;
                border-top: 3px solid #e5e7eb;
                margin-top: 40px;
            }

            .footer-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .footer-company {
                font-weight: 600;
                color: #dc2626;
                font-size: 16px;
            }

            .footer-timestamp {
                font-size: 13px;
                color: #6b7280;
            }

            .footer-link {
                color: #dc2626;
                text-decoration: none;
                font-weight: 600;
            }

            .footer-disclaimer {
                margin-top: 15px;
                font-size: 12px;
                color: #9ca3af;
                text-align: center;
            }

            @media print {
                .report-header::before {
                    display: none;
                }
            }
        </style>
    </head>
    <body>
        <div class="page-wrapper">
            <!-- Header -->
            <div class="report-header">
                <div class="company-logo">ZEB COMPANY</div>
                <h1 class="report-title">
                    ⚠️ At Risk Alert
                    {% if at_risk_count > 5 %}
                    <span class="alert-badge">Critical</span>
                    {% elif at_risk_count > 2 %}
                    <span class="alert-badge">High</span>
                    {% else %}
                    <span class="alert-badge">Medium</span>
                    {% endif %}
                </h1>
                <p class="report-subtitle">{{ specialization_name }} - Immediate Attention Required</p>
                <div class="report-meta">
                    <div class="meta-item">
                        <span>📅</span>
                        <span>{{ report_date }}</span>
                    </div>
                    <div class="meta-item">
                        <span>⏰</span>
                        <span>Action Required</span>
                    </div>
                </div>
            </div>

            <!-- Alert Banner -->
            <div class="alert-banner">
                <div class="alert-content">
                    <div class="alert-icon">🚨</div>
                    <div class="alert-text">
                        <h3>Critical Action Required</h3>
                        <p>
                            {{ at_risk_count }} project{{ ''s'' if at_risk_count != 1 else '''' }}
                            {% if at_risk_count == 1 %}is{% else %}are{% endif %} currently at risk
                            and require immediate attention. These projects have exceeded their onboarding
                            timeline and may impact delivery commitments.
                        </p>
                        {% if at_risk_count > 5 %}
                        <span class="severity-badge severity-critical">Critical Severity</span>
                        {% elif at_risk_count > 2 %}
                        <span class="severity-badge severity-high">High Severity</span>
                        {% else %}
                        <span class="severity-badge severity-medium">Medium Severity</span>
                        {% endif %}
                    </div>
                </div>
            </div>

            <!-- Content -->
            <div class="report-content">
                <!-- Summary -->
                <div class="summary-card">
                    <div class="summary-count">{{ at_risk_count }}</div>
                    <div class="summary-label">Projects At Risk</div>
                </div>

                {% if projects %}
                <!-- Projects Table -->
                <div class="section">
                    <div class="section-header">
                        <div class="section-icon">📋</div>
                        <h2 class="section-title">At Risk Projects Details</h2>
                    </div>

                    <table class="projects-table">
                        <thead>
                            <tr>
                                <th>Project Name</th>
                                <th>Client</th>
                                <th>Onboarded Date</th>
                                <th style="text-align: center;">Days Overdue</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for project in projects %}
                            <tr>
                                <td class="project-name">{{ project.project_name }}</td>
                                <td>{{ project.client or ''N/A'' }}</td>
                                <td>{{ project.onboarded_date }}</td>
                                <td style="text-align: center;">
                                    <span class="overdue-badge {% if project.days_overdue > 30 %}overdue-critical{% endif %}">
                                        {{ project.days_overdue }} days
                                    </span>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}

                <!-- Action Items -->
                <div class="section">
                    <div class="action-section">
                        <h3>📋 Recommended Actions</h3>
                        <ul class="action-list">
                            <li class="action-item">
                                <div class="action-number">1</div>
                                <div class="action-content">
                                    <div class="action-title">Immediate Review</div>
                                    <div class="action-description">
                                        Schedule meetings with project leads for critically overdue projects (>30 days) within the next 24 hours.
                                    </div>
                                </div>
                            </li>
                            <li class="action-item">
                                <div class="action-number">2</div>
                                <div class="action-content">
                                    <div class="action-title">Status Update</div>
                                    <div class="action-description">
                                        Request detailed status updates from project owners and identify blockers preventing progress.
                                    </div>
                                </div>
                            </li>
                            <li class="action-item">
                                <div class="action-number">3</div>
                                <div class="action-content">
                                    <div class="action-title">Resource Assessment</div>
                                    <div class="action-description">
                                        Evaluate if additional resources, training, or support is needed to bring projects back on track.
                                    </div>
                                </div>
                            </li>
                            <li class="action-item">
                                <div class="action-number">4</div>
                                <div class="action-content">
                                    <div class="action-title">Timeline Review</div>
                                    <div class="action-description">
                                        Update project timelines based on current status and communicate revised expectations to stakeholders.
                                    </div>
                                </div>
                            </li>
                            <li class="action-item">
                                <div class="action-number">5</div>
                                <div class="action-content">
                                    <div class="action-title">Stakeholder Communication</div>
                                    <div class="action-description">
                                        Inform relevant stakeholders about project status and proposed mitigation plans.
                                    </div>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="report-footer">
                <div class="footer-content">
                    <div>
                        <div class="footer-company">ZEB Company</div>
                        <div class="footer-timestamp">Generated on {{ generated_at }}</div>
                    </div>
                    <div>
                        <a href="{{ dashboard_url }}" class="footer-link">View Dashboard →</a>
                    </div>
                </div>
                <div class="footer-disclaimer">
                    This is an automated alert generated by the DevSecOps Platform. Please do not reply to this notification.
                </div>
            </div>
        </div>
    </body>
    </html>',
    'seed_script',
    1
);


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
INSERT INTO cron_jobs (cron_id, type, sync_status, created_by, is_active) VALUES
('e0200000-0000-0000-0000-000000000001', 'azure', 'success', 'seed_script', 1),
('e0200000-0000-0000-0000-000000000002', 'azure', 'success', 'seed_script', 1),
('e0200000-0000-0000-0000-000000000003', 'azure', 'fail', 'seed_script', 1),
('e0200000-0000-0000-0000-000000000004', 'email', 'success', 'seed_script', 1),
('e0200000-0000-0000-0000-000000000005', 'email', 'pending', 'seed_script', 1);

-- =============================================
-- 18. kpi_history
-- =============================================
INSERT INTO kpi_history (kpi_history_id, specialization_id, projects_count, projects_increase_count, projects_decrease_count, completed_count, completed_increase_count, completed_decrease_count, active_count, active_increase_count, active_decrease_count, inactive_count, inactive_increase_count, inactive_decrease_count, at_risk_count, at_risk_increase_count, at_risk_decrease_count, not_applicable_count, not_applicable_increase_count, not_applicable_decrease_count, created_by, is_active) VALUES
('f0300000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 12, 2, 0, 5, 1, 0, 4, 1, 0, 1, 0, 0, 2, 1, 0, 0, 0, 0, 'seed_script', 1),
('f0300000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000002', 8, 1, 0, 3, 0, 0, 3, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 'seed_script', 1),
('f0300000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000003', 6, 0, 1, 2, 0, 0, 2, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 'seed_script', 1),
('f0300000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000004', 10, 1, 0, 4, 1, 0, 3, 0, 0, 2, 0, 0, 1, 0, 1, 0, 0, 0, 'seed_script', 1),
('f0300000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000005', 4, 0, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 'seed_script', 1);
