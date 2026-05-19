-- DevSecOps Jira Dashboard - Test Data Load
-- PostgreSQL
-- Inserts test data for projects, devsecops_tickets, and repositories tables
-- Source: projectData.txt (Azure DevOps Organization: zeb-ai)
-- Run AFTER create_tables.sql and seed_data.sql

-- =============================================
-- 1. projects (from ADO organization data)
-- Using status_id references from seed_data.sql:
--   Active:         b2000000-0000-0000-0000-000000000001
--   Completed:      b2000000-0000-0000-0000-000000000002
--   Inactive:       b2000000-0000-0000-0000-000000000003
--   At Risk:        b2000000-0000-0000-0000-000000000004
--   Not Applicable: b2000000-0000-0000-0000-000000000005
-- =============================================
INSERT INTO projects (project_id, status_id, sn_project_id, project_name, onboarded_date, project_type, is_applicable, client, created_by, is_active) VALUES
('29943320-f52d-4607-98a7-283ea971ba5c', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-101', 'zeb-zeb-devsecops-demo-poc', '2024-01-10', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('b526956e-8d37-436d-b703-49e785ac1e21', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-102', 'zeb-test3-demo', '2024-01-15', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('84f88925-f2b9-4f25-a742-3520cf019a3c', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-103', 'zeb-devtest-demo', '2024-01-20', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('9d057a67-5709-49af-bebd-129ca6d33c0c', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-104', 'zeb-dbx-demo', '2024-02-01', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('b2bbe81f-7b41-4946-a284-e24b720b509a', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-105', 'ds-mccain', '2024-02-05', 'Platform', TRUE, 'McCain', 'test_data_script', 1),
('7df0b1b6-1f16-4060-b1c5-38bd605c3f5f', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-106', 'zeb-adani-demo', '2024-02-10', 'Application', TRUE, 'Adani', 'test_data_script', 1),
('dee9fa35-f881-43ee-b6c9-b60bb588ed0b', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-107', 'zeb-williams-demo', '2024-02-15', 'Application', TRUE, 'Williams', 'test_data_script', 1),
('af4e523a-e375-40cc-af77-09321f08deee', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-108', 'zeb-brehotels-demo', '2024-02-20', 'Application', TRUE, 'BRE Hotels', 'test_data_script', 1),
('32d89a82-92eb-4ec9-b38a-e4b056540848', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-109', 'zeb-freespace-robotics-poc', '2024-03-01', 'Platform', TRUE, 'Freespace Robotics', 'test_data_script', 1),
('fe05252a-90e4-4cfa-8368-978f8fadc131', 'b2000000-0000-0000-0000-000000000002', 'SN-PRJ-110', 'cloud-centralized-pipeline', '2023-10-15', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('aa7cbfd8-1d61-40a0-b476-bbc187d2ec83', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-111', 'zeb-cloud-rnd', '2024-03-10', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('cf1638b9-db63-4814-b7a3-2e59ff1db8bd', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-112', 'ai-artifacts-store', '2024-03-15', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('5719a7c3-de77-4976-bd3a-00de58dc9f03', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-113', 'zeb-test-prototype-app-demo', '2024-03-20', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('7ee3f2c1-3e1e-4787-8660-010eafca3f94', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-114', 'zeb-zebco-demo', '2024-03-25', 'Application', TRUE, 'Zebco', 'test_data_script', 1),
('7548b20d-6467-460f-ab16-1550a2bf3b24', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-115', 'zeb-bayou-prod', '2024-04-01', 'Application', TRUE, 'Bayou', 'test_data_script', 1),
('530997fa-8de2-439e-a0b2-ad24e4463f80', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-116', 'zeb-xfinitywifi-demo', '2024-04-05', 'Application', TRUE, 'Xfinity', 'test_data_script', 1),
('b93e3b98-e92d-4a72-b9af-384cb6cc4442', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-117', 'zeb-cognosos-demo', '2024-04-10', 'Application', TRUE, 'Cognosos', 'test_data_script', 1),
('87146433-8121-496a-a73e-e338be3305fb', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-118', 'zeb-lk-packaging-demo', '2024-04-15', 'Application', TRUE, 'LK Packaging', 'test_data_script', 1),
('f4165f27-3026-4cd3-8517-111a8e34f63f', 'b2000000-0000-0000-0000-000000000003', 'SN-PRJ-119', 'newforma-assessment', '2024-04-20', 'Application', TRUE, 'Newforma', 'test_data_script', 1),
('3810179f-366b-4af8-965c-574510106268', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-120', 'zeb-apollo-agentic-usecase-prod', '2024-05-01', 'Platform', TRUE, 'Apollo', 'test_data_script', 1),
('60782aa3-8ed5-4db8-9e97-9d6e2e176e1a', 'b2000000-0000-0000-0000-000000000003', 'SN-PRJ-121', 'vzyr-ai', '2024-05-05', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('d690dbe3-9bc6-4f1b-be0e-9f9283280a84', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-122', 'zeb-aws-clients-demo', '2024-05-10', 'Application', TRUE, 'AWS Clients', 'test_data_script', 1),
('bbc3635f-8c0d-40f9-b810-b6808a7047b3', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-123', 'zeb-onbtest-demo', '2024-05-15', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('f18cc912-feba-440d-9943-4e2607989f97', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-124', 'Zeb-MAP-Assistant', '2024-05-20', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('6cb3159c-6c46-46e5-a96b-c5906c8c7ffb', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-125', 'zeb-qa-test-automation', '2024-06-01', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('bd57e19c-6865-4001-a191-9783ba1d3ac7', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-126', 'zeb-outcomehubcafe-prod', '2024-06-05', 'Application', TRUE, 'OutcomeHub Cafe', 'test_data_script', 1),
('5c1778d6-5e09-4497-867b-a8c42c70f2d1', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-127', 'zeb-fe-demo', '2024-06-10', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('797fbd84-e13d-4a55-88ee-cb3ed09baca2', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-128', 'zeb-precisely-testing-poc', '2024-06-15', 'Application', TRUE, 'Precisely', 'test_data_script', 1),
('73addb4d-b2b8-40e1-bf0b-a361e893b940', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-129', 'zeb-soundry-ai-prod', '2024-06-20', 'Platform', TRUE, 'Soundry AI', 'test_data_script', 1),
('599c3411-8c49-4670-84bc-fd6553498743', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-130', 'zeb-artifacts-store', '2024-06-25', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('ffb2e372-2ccd-4575-8211-022efae854ff', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-131', 'uxd-figma-artifact', '2024-07-01', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('dc2ad5f1-4251-4570-8a6a-747b9512e15c', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-132', 'ds-ctc', '2024-07-05', 'Platform', TRUE, 'CTC', 'test_data_script', 1),
('f7234c7e-573e-4907-bdb8-720a8f63b479', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-133', 'zeb-tai-software-prod', '2024-07-10', 'Application', TRUE, 'TAI Software', 'test_data_script', 1),
('927e1567-81f7-4606-aacc-7582f67a2f7f', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-134', 'databricks-sales', '2024-07-15', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('d25f24a8-0b92-4c63-a7cc-f3e1ab53c2c9', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-135', 'zeb-test2-demo', '2024-07-20', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('cc931b08-1ed6-4dcb-b892-5f13967efca8', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-136', 'zeb-partner-revenue-recognition-system', '2024-07-25', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('5e6b63e6-ab84-4acb-9f88-6a28d08c3fb8', 'b2000000-0000-0000-0000-000000000002', 'SN-PRJ-137', 'zeb-website', '2023-09-01', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('f0e1e81a-1353-41ab-971e-e790cccbb746', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-138', 'zeb-zap-prod', '2024-08-01', 'Platform', TRUE, 'ZAP', 'test_data_script', 1),
('f1536d99-6e35-4cd4-8b10-bd14d445b82a', 'b2000000-0000-0000-0000-000000000003', 'SN-PRJ-139', 'ai-internal-demo', '2024-08-05', 'Internal', FALSE, NULL, 'test_data_script', 1),
('aeaceab0-f7a2-4fc8-b400-9e43aeccc35f', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-140', 'zeb-eis-poc', '2024-08-10', 'Application', TRUE, 'EIS', 'test_data_script', 1),
('6dce2b4a-59e9-4cd8-aece-783f8cdc216d', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-141', 'zeb-sales-dashboard', '2024-08-15', 'Application', TRUE, 'zeb-ai', 'test_data_script', 1),
('81cc132d-5740-4420-a436-417195c54768', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-142', 'zeb-bayou-poc', '2024-08-20', 'Application', TRUE, 'Bayou', 'test_data_script', 1),
('7600e900-444f-41ab-9eb8-59f2f398f9ea', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-143', 'hive-revamp-redemtion', '2024-08-25', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('44c0b0d4-8bed-402a-90d4-fbab5b7936fb', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-144', 'zeb-mosh-jd-prod', '2024-09-01', 'Platform', TRUE, 'Mosh JD', 'test_data_script', 1),
('faf47e41-4650-4188-9122-4d0001de5c5d', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-145', 'hr-hive2.0-product', '2024-09-05', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('13bd9b0c-1e14-4dc9-8a4f-da0280358cec', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-146', 'ai-neural-hub', '2024-09-10', 'Platform', TRUE, 'zeb-ai', 'test_data_script', 1),
('6507560e-ba11-479b-8dbb-c623967a96f9', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-147', 'zeb-fortra-demo', '2024-09-15', 'Application', TRUE, 'Fortra', 'test_data_script', 1),
('ad14f6a2-44ea-490c-89c9-b2dce90d31e3', 'b2000000-0000-0000-0000-000000000004', 'SN-PRJ-148', 'crm-migration-framework', '2024-09-20', 'Migration', TRUE, 'zeb-ai', 'test_data_script', 1),
('cd9cce69-85da-483a-aa7e-075ddc2808ec', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-149', 'zeb-precisely-poc', '2024-09-25', 'Application', TRUE, 'Precisely', 'test_data_script', 1),
('d5c25b18-ddfb-414a-9fd5-7cbabf067656', 'b2000000-0000-0000-0000-000000000001', 'SN-PRJ-150', 'zeb-adanitrading-demo', '2024-10-01', 'Application', TRUE, 'Adani Trading', 'test_data_script', 1);

-- =============================================
-- 2. devsecops_tickets
-- Using specialization_id references from seed_data.sql:
--   Backend:  a1000000-0000-0000-0000-000000000001
--   Frontend: a1000000-0000-0000-0000-000000000002
--   DevOps:   a1000000-0000-0000-0000-000000000003
--   QA:       a1000000-0000-0000-0000-000000000004
--   Security: a1000000-0000-0000-0000-000000000005
-- =============================================
INSERT INTO devsecops_tickets (ticket_id, specialization_id, project_id, sn_project_id, project_name, client, requested_by, approver, sync_method, requested_at, created_by, is_active) VALUES
('d4100000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', '29943320-f52d-4607-98a7-283ea971ba5c', 'SN-PRJ-101', 'zeb-zeb-devsecops-demo-poc', 'zeb-ai', 'dev.user1@company.com', 'approver1@company.com', 'automatic', '2024-01-12 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000002', 'a1000000-0000-0000-0000-000000000002', '29943320-f52d-4607-98a7-283ea971ba5c', 'SN-PRJ-101', 'zeb-zeb-devsecops-demo-poc', 'zeb-ai', 'dev.user2@company.com', 'approver1@company.com', 'automatic', '2024-01-12 10:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000003', 'a1000000-0000-0000-0000-000000000002', 'b526956e-8d37-436d-b703-49e785ac1e21', 'SN-PRJ-102', 'zeb-test3-demo', 'zeb-ai', 'dev.user3@company.com', 'approver2@company.com', 'manual', '2024-01-17 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000004', 'a1000000-0000-0000-0000-000000000002', '84f88925-f2b9-4f25-a742-3520cf019a3c', 'SN-PRJ-103', 'zeb-devtest-demo', 'zeb-ai', 'dev.user4@company.com', 'approver2@company.com', 'manual', '2024-01-22 11:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000005', 'a1000000-0000-0000-0000-000000000001', '9d057a67-5709-49af-bebd-129ca6d33c0c', 'SN-PRJ-104', 'zeb-dbx-demo', 'zeb-ai', 'dev.user5@company.com', 'approver1@company.com', 'automatic', '2024-02-03 08:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000006', 'a1000000-0000-0000-0000-000000000003', 'b2bbe81f-7b41-4946-a284-e24b720b509a', 'SN-PRJ-105', 'ds-mccain', 'McCain', 'dev.user6@company.com', 'approver3@company.com', 'automatic', '2024-02-07 14:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000007', 'a1000000-0000-0000-0000-000000000002', '7df0b1b6-1f16-4060-b1c5-38bd605c3f5f', 'SN-PRJ-106', 'zeb-adani-demo', 'Adani', 'dev.user7@company.com', 'approver2@company.com', 'manual', '2024-02-12 09:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000008', 'a1000000-0000-0000-0000-000000000002', 'dee9fa35-f881-43ee-b6c9-b60bb588ed0b', 'SN-PRJ-107', 'zeb-williams-demo', 'Williams', 'dev.user8@company.com', 'approver2@company.com', 'manual', '2024-02-17 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000009', 'a1000000-0000-0000-0000-000000000002', 'af4e523a-e375-40cc-af77-09321f08deee', 'SN-PRJ-108', 'zeb-brehotels-demo', 'BRE Hotels', 'dev.user9@company.com', 'approver2@company.com', 'manual', '2024-02-22 11:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000010', 'a1000000-0000-0000-0000-000000000001', '32d89a82-92eb-4ec9-b38a-e4b056540848', 'SN-PRJ-109', 'zeb-freespace-robotics-poc', 'Freespace Robotics', 'dev.user10@company.com', 'approver1@company.com', 'automatic', '2024-03-03 08:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000011', 'a1000000-0000-0000-0000-000000000003', 'fe05252a-90e4-4cfa-8368-978f8fadc131', 'SN-PRJ-110', 'cloud-centralized-pipeline', 'zeb-ai', 'dev.user11@company.com', 'approver3@company.com', 'automatic', '2023-10-18 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000012', 'a1000000-0000-0000-0000-000000000003', 'aa7cbfd8-1d61-40a0-b476-bbc187d2ec83', 'SN-PRJ-111', 'zeb-cloud-rnd', 'zeb-ai', 'dev.user12@company.com', 'approver3@company.com', 'automatic', '2024-03-12 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000013', 'a1000000-0000-0000-0000-000000000001', 'cf1638b9-db63-4814-b7a3-2e59ff1db8bd', 'SN-PRJ-112', 'ai-artifacts-store', 'zeb-ai', 'dev.user13@company.com', 'approver1@company.com', 'automatic', '2024-03-17 08:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000014', 'a1000000-0000-0000-0000-000000000002', '5719a7c3-de77-4976-bd3a-00de58dc9f03', 'SN-PRJ-113', 'zeb-test-prototype-app-demo', 'zeb-ai', 'dev.user14@company.com', 'approver2@company.com', 'manual', '2024-03-22 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000015', 'a1000000-0000-0000-0000-000000000002', '7ee3f2c1-3e1e-4787-8660-010eafca3f94', 'SN-PRJ-114', 'zeb-zebco-demo', 'Zebco', 'dev.user15@company.com', 'approver2@company.com', 'manual', '2024-03-27 10:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000016', 'a1000000-0000-0000-0000-000000000001', '7548b20d-6467-460f-ab16-1550a2bf3b24', 'SN-PRJ-115', 'zeb-bayou-prod', 'Bayou', 'dev.user16@company.com', 'approver1@company.com', 'automatic', '2024-04-03 08:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000017', 'a1000000-0000-0000-0000-000000000002', '530997fa-8de2-439e-a0b2-ad24e4463f80', 'SN-PRJ-116', 'zeb-xfinitywifi-demo', 'Xfinity', 'dev.user17@company.com', 'approver2@company.com', 'manual', '2024-04-07 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000018', 'a1000000-0000-0000-0000-000000000002', 'b93e3b98-e92d-4a72-b9af-384cb6cc4442', 'SN-PRJ-117', 'zeb-cognosos-demo', 'Cognosos', 'dev.user18@company.com', 'approver2@company.com', 'manual', '2024-04-12 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000019', 'a1000000-0000-0000-0000-000000000002', '87146433-8121-496a-a73e-e338be3305fb', 'SN-PRJ-118', 'zeb-lk-packaging-demo', 'LK Packaging', 'dev.user19@company.com', 'approver2@company.com', 'manual', '2024-04-17 11:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000020', 'a1000000-0000-0000-0000-000000000001', '3810179f-366b-4af8-965c-574510106268', 'SN-PRJ-120', 'zeb-apollo-agentic-usecase-prod', 'Apollo', 'dev.user20@company.com', 'approver1@company.com', 'automatic', '2024-05-03 08:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000021', 'a1000000-0000-0000-0000-000000000001', 'd690dbe3-9bc6-4f1b-be0e-9f9283280a84', 'SN-PRJ-122', 'zeb-aws-clients-demo', 'AWS Clients', 'dev.user21@company.com', 'approver1@company.com', 'automatic', '2024-05-12 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000022', 'a1000000-0000-0000-0000-000000000002', 'bbc3635f-8c0d-40f9-b810-b6808a7047b3', 'SN-PRJ-123', 'zeb-onbtest-demo', 'zeb-ai', 'dev.user22@company.com', 'approver2@company.com', 'manual', '2024-05-17 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000023', 'a1000000-0000-0000-0000-000000000001', 'f18cc912-feba-440d-9943-4e2607989f97', 'SN-PRJ-124', 'Zeb-MAP-Assistant', 'zeb-ai', 'dev.user23@company.com', 'approver1@company.com', 'automatic', '2024-05-22 08:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000024', 'a1000000-0000-0000-0000-000000000004', '6cb3159c-6c46-46e5-a96b-c5906c8c7ffb', 'SN-PRJ-125', 'zeb-qa-test-automation', 'zeb-ai', 'dev.user24@company.com', 'approver4@company.com', 'automatic', '2024-06-03 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000025', 'a1000000-0000-0000-0000-000000000001', 'bd57e19c-6865-4001-a191-9783ba1d3ac7', 'SN-PRJ-126', 'zeb-outcomehubcafe-prod', 'OutcomeHub Cafe', 'dev.user25@company.com', 'approver1@company.com', 'automatic', '2024-06-07 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000026', 'a1000000-0000-0000-0000-000000000002', '5c1778d6-5e09-4497-867b-a8c42c70f2d1', 'SN-PRJ-127', 'zeb-fe-demo', 'zeb-ai', 'dev.user26@company.com', 'approver2@company.com', 'manual', '2024-06-12 11:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000027', 'a1000000-0000-0000-0000-000000000004', '797fbd84-e13d-4a55-88ee-cb3ed09baca2', 'SN-PRJ-128', 'zeb-precisely-testing-poc', 'Precisely', 'dev.user27@company.com', 'approver4@company.com', 'automatic', '2024-06-17 08:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000028', 'a1000000-0000-0000-0000-000000000001', '73addb4d-b2b8-40e1-bf0b-a361e893b940', 'SN-PRJ-129', 'zeb-soundry-ai-prod', 'Soundry AI', 'dev.user28@company.com', 'approver1@company.com', 'automatic', '2024-06-22 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000029', 'a1000000-0000-0000-0000-000000000003', '599c3411-8c49-4670-84bc-fd6553498743', 'SN-PRJ-130', 'zeb-artifacts-store', 'zeb-ai', 'dev.user29@company.com', 'approver3@company.com', 'automatic', '2024-06-27 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000030', 'a1000000-0000-0000-0000-000000000002', 'ffb2e372-2ccd-4575-8211-022efae854ff', 'SN-PRJ-131', 'uxd-figma-artifact', 'zeb-ai', 'dev.user30@company.com', 'approver2@company.com', 'manual', '2024-07-03 09:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000031', 'a1000000-0000-0000-0000-000000000001', 'f7234c7e-573e-4907-bdb8-720a8f63b479', 'SN-PRJ-133', 'zeb-tai-software-prod', 'TAI Software', 'dev.user31@company.com', 'approver1@company.com', 'automatic', '2024-07-12 08:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000032', 'a1000000-0000-0000-0000-000000000003', '927e1567-81f7-4606-aacc-7582f67a2f7f', 'SN-PRJ-134', 'databricks-sales', 'zeb-ai', 'dev.user32@company.com', 'approver3@company.com', 'automatic', '2024-07-17 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000033', 'a1000000-0000-0000-0000-000000000001', 'cc931b08-1ed6-4dcb-b892-5f13967efca8', 'SN-PRJ-136', 'zeb-partner-revenue-recognition-system', 'zeb-ai', 'dev.user33@company.com', 'approver1@company.com', 'automatic', '2024-07-27 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000034', 'a1000000-0000-0000-0000-000000000001', 'f0e1e81a-1353-41ab-971e-e790cccbb746', 'SN-PRJ-138', 'zeb-zap-prod', 'ZAP', 'dev.user34@company.com', 'approver1@company.com', 'automatic', '2024-08-03 08:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000035', 'a1000000-0000-0000-0000-000000000005', 'aeaceab0-f7a2-4fc8-b400-9e43aeccc35f', 'SN-PRJ-140', 'zeb-eis-poc', 'EIS', 'dev.user35@company.com', 'approver5@company.com', 'automatic', '2024-08-12 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000036', 'a1000000-0000-0000-0000-000000000001', '6dce2b4a-59e9-4cd8-aece-783f8cdc216d', 'SN-PRJ-141', 'zeb-sales-dashboard', 'zeb-ai', 'dev.user36@company.com', 'approver1@company.com', 'automatic', '2024-08-17 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000037', 'a1000000-0000-0000-0000-000000000001', '7600e900-444f-41ab-9eb8-59f2f398f9ea', 'SN-PRJ-143', 'hive-revamp-redemtion', 'zeb-ai', 'dev.user37@company.com', 'approver1@company.com', 'automatic', '2024-08-27 08:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000038', 'a1000000-0000-0000-0000-000000000001', '44c0b0d4-8bed-402a-90d4-fbab5b7936fb', 'SN-PRJ-144', 'zeb-mosh-jd-prod', 'Mosh JD', 'dev.user38@company.com', 'approver1@company.com', 'automatic', '2024-09-03 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000039', 'a1000000-0000-0000-0000-000000000001', 'faf47e41-4650-4188-9122-4d0001de5c5d', 'SN-PRJ-145', 'hr-hive2.0-product', 'zeb-ai', 'dev.user39@company.com', 'approver1@company.com', 'automatic', '2024-09-07 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000040', 'a1000000-0000-0000-0000-000000000001', '13bd9b0c-1e14-4dc9-8a4f-da0280358cec', 'SN-PRJ-146', 'ai-neural-hub', 'zeb-ai', 'dev.user40@company.com', 'approver1@company.com', 'automatic', '2024-09-12 08:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000041', 'a1000000-0000-0000-0000-000000000002', '6507560e-ba11-479b-8dbb-c623967a96f9', 'SN-PRJ-147', 'zeb-fortra-demo', 'Fortra', 'dev.user41@company.com', 'approver2@company.com', 'manual', '2024-09-17 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000042', 'a1000000-0000-0000-0000-000000000001', 'ad14f6a2-44ea-490c-89c9-b2dce90d31e3', 'SN-PRJ-148', 'crm-migration-framework', 'zeb-ai', 'dev.user42@company.com', 'approver1@company.com', 'automatic', '2024-09-22 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000043', 'a1000000-0000-0000-0000-000000000005', 'cd9cce69-85da-483a-aa7e-075ddc2808ec', 'SN-PRJ-149', 'zeb-precisely-poc', 'Precisely', 'dev.user43@company.com', 'approver5@company.com', 'automatic', '2024-09-27 08:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000044', 'a1000000-0000-0000-0000-000000000002', 'd5c25b18-ddfb-414a-9fd5-7cbabf067656', 'SN-PRJ-150', 'zeb-adanitrading-demo', 'Adani Trading', 'dev.user44@company.com', 'approver2@company.com', 'manual', '2024-10-03 09:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000045', 'a1000000-0000-0000-0000-000000000003', '7650a613-75e0-415f-a768-fffbfdb74dd5', 'SN-PRJ-152', 'zeb-fortra-prod', 'Fortra', 'dev.user45@company.com', 'approver3@company.com', 'automatic', '2024-10-12 08:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000046', 'a1000000-0000-0000-0000-000000000001', '2f38eabe-d2a7-45cf-8c0a-d262f5158762', 'SN-PRJ-154', 'ai-zeb-innovation', 'zeb-ai', 'dev.user46@company.com', 'approver1@company.com', 'automatic', '2024-10-22 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000047', 'a1000000-0000-0000-0000-000000000001', '4599e059-b2bc-4d68-abfa-6413d9d058fb', 'SN-PRJ-156', 'zeb-analytics-intell-prod', 'zeb-ai', 'dev.user47@company.com', 'approver1@company.com', 'automatic', '2024-11-03 10:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000048', 'a1000000-0000-0000-0000-000000000001', '3cbbd537-9ad7-4a3b-8b42-cb6c4ed7f289', 'SN-PRJ-158', 'zeb-splitz-prod', 'Splitz', 'dev.user48@company.com', 'approver1@company.com', 'automatic', '2024-11-12 08:30:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000049', 'a1000000-0000-0000-0000-000000000003', '26a5da04-b2bc-4611-bfd3-53e642233b35', 'SN-PRJ-159', 'zeb-lululemon-prod', 'Lululemon', 'dev.user49@company.com', 'approver3@company.com', 'automatic', '2024-11-17 09:00:00', 'test_data_script', 1),
('d4100000-0000-0000-0000-000000000050', 'a1000000-0000-0000-0000-000000000005', '833c70fe-8f85-4cff-abb9-54b6fc49e97a', 'SN-PRJ-157', 'zeb-internal-prod', 'zeb-ai', 'dev.user50@company.com', 'approver5@company.com', 'automatic', '2024-11-07 10:00:00', 'test_data_script', 1);

-- =============================================
-- 3. repositories (from ADO repository data)
-- Using actual ADO repo IDs from projectData.txt
-- ticket_id references the devsecops_tickets above
-- =============================================
INSERT INTO repositories (repository_id, ticket_id, repository_name, ado_repo_id, pipeline_runs_count, success_rate, last_run_at, created_by, is_active) VALUES
-- zeb-zeb-devsecops-demo-poc repos (ticket 01)
('5c550db8-702c-40bb-ab79-d214876075d1', 'd4100000-0000-0000-0000-000000000001', 'zeb-web-frontend', '5c550db8-702c-40bb-ab79-d214876075d1', 35, 91.4, '2024-05-15 10:30:00', 'test_data_script', 1),
('4dac43b1-ff09-479d-a92c-1b52c339f66a', 'd4100000-0000-0000-0000-000000000001', 'zeb-zeb-devsecops-demo-poc', '4dac43b1-ff09-479d-a92c-1b52c339f66a', 12, 83.3, '2024-04-20 14:00:00', 'test_data_script', 1),
-- zeb-zeb-devsecops-demo-poc FE repo (ticket 02)
('5c550db8-702c-40bb-ab79-d214876075d2', 'd4100000-0000-0000-0000-000000000002', 'zeb-web-frontend-fe', '5c550db8-702c-40bb-ab79-d214876075d1', 28, 89.3, '2024-05-14 16:00:00', 'test_data_script', 1),
-- zeb-test3-demo repos (ticket 03)
('06c75d50-d239-4e66-8179-3166ae38a8a6', 'd4100000-0000-0000-0000-000000000003', 'zeb-test3-demo', '06c75d50-d239-4e66-8179-3166ae38a8a6', 8, 75.0, '2024-03-10 09:00:00', 'test_data_script', 1),
('54ec8e73-2bea-443f-9806-a9a922ef862c', 'd4100000-0000-0000-0000-000000000003', 'zeb-test3-fe', '54ec8e73-2bea-443f-9806-a9a922ef862c', 42, 90.5, '2024-05-20 16:00:00', 'test_data_script', 1),
-- zeb-devtest-demo repos (ticket 04)
('726dd62d-a8e3-4fd6-8517-a067a61796dd', 'd4100000-0000-0000-0000-000000000004', 'zeb-devtest-demo', '726dd62d-a8e3-4fd6-8517-a067a61796dd', 5, 80.0, '2024-02-28 11:00:00', 'test_data_script', 1),
('daf50c12-1cdd-4d07-afc1-b1314b38516a', 'd4100000-0000-0000-0000-000000000004', 'zeb-devtest-fe', 'daf50c12-1cdd-4d07-afc1-b1314b38516a', 38, 89.5, '2024-05-18 15:30:00', 'test_data_script', 1),
-- zeb-dbx-demo repos (ticket 05)
('67713f4f-84f0-42a5-869a-f17bfdd709b2', 'd4100000-0000-0000-0000-000000000005', 'zeb-dbx-demo', '67713f4f-84f0-42a5-869a-f17bfdd709b2', 55, 94.5, '2024-05-22 09:00:00', 'test_data_script', 1),
('64e040b7-8cb6-4fce-bc1b-2010530ae1b1', 'd4100000-0000-0000-0000-000000000005', 'zeb-dbx-doc-iq-demo', '64e040b7-8cb6-4fce-bc1b-2010530ae1b1', 28, 92.9, '2024-05-21 17:00:00', 'test_data_script', 1),
-- ds-mccain repos (ticket 06)
('2869a8c0-cfde-483e-9c7d-20090867e571', 'd4100000-0000-0000-0000-000000000006', 'daia-powerbi-report', '2869a8c0-cfde-483e-9c7d-20090867e571', 20, 85.0, '2024-05-10 12:00:00', 'test_data_script', 1),
('5ed38c10-b502-4940-b2b0-f938f974d035', 'd4100000-0000-0000-0000-000000000006', 'powerbi', '5ed38c10-b502-4940-b2b0-f938f974d035', 15, 93.3, '2024-05-08 10:00:00', 'test_data_script', 1),
('e0cc0a91-aae2-4d72-8961-88230e8e630d', 'd4100000-0000-0000-0000-000000000006', 'synapse-to-databricks-migration', 'e0cc0a91-aae2-4d72-8961-88230e8e630d', 32, 87.5, '2024-05-12 14:30:00', 'test_data_script', 1),
-- zeb-adani-demo repos (ticket 07)
('3e255858-d90f-4f6b-b40f-0f909b68775f', 'd4100000-0000-0000-0000-000000000007', 'powertrading-frontend-web', '3e255858-d90f-4f6b-b40f-0f909b68775f', 48, 91.7, '2024-05-25 11:00:00', 'test_data_script', 1),
-- zeb-williams-demo repos (ticket 08)
('d744c689-8372-4430-9b5a-9e65f2501373', 'd4100000-0000-0000-0000-000000000008', 'williams-web-frontend', 'd744c689-8372-4430-9b5a-9e65f2501373', 40, 90.0, '2024-05-20 13:00:00', 'test_data_script', 1),
-- zeb-brehotels-demo repos (ticket 09)
('7c2903f6-4565-4723-a9fd-7752a4ae8d44', 'd4100000-0000-0000-0000-000000000009', 'brehotels-web-frontend', '7c2903f6-4565-4723-a9fd-7752a4ae8d44', 36, 88.9, '2024-05-18 16:00:00', 'test_data_script', 1),
-- zeb-freespace-robotics-poc repos (ticket 10)
('493318a0-288e-4be1-a3d7-46dca9609d65', 'd4100000-0000-0000-0000-000000000010', 'freespace-mvp-agent', '493318a0-288e-4be1-a3d7-46dca9609d65', 25, 88.0, '2024-05-15 09:30:00', 'test_data_script', 1),
('d4fce954-c16a-4e33-920d-201380b886de', 'd4100000-0000-0000-0000-000000000010', 'freespace-mvp-be', 'd4fce954-c16a-4e33-920d-201380b886de', 60, 93.3, '2024-05-22 10:00:00', 'test_data_script', 1),
('e815d2b4-8b4d-4701-83dd-9d99fd45e13f', 'd4100000-0000-0000-0000-000000000010', 'freespace-mvp-fe', 'e815d2b4-8b4d-4701-83dd-9d99fd45e13f', 52, 90.4, '2024-05-21 15:00:00', 'test_data_script', 1),
('82cc8251-7f76-464d-a925-fe3dcd0ec09b', 'd4100000-0000-0000-0000-000000000010', 'freespace-mvp-iac', '82cc8251-7f76-464d-a925-fe3dcd0ec09b', 18, 94.4, '2024-05-10 08:00:00', 'test_data_script', 1),
-- cloud-centralized-pipeline repos (ticket 11)
('03f410c6-fcd1-4d4a-b4c2-6c1f780dfd7c', 'd4100000-0000-0000-0000-000000000011', 'cloud-centralized-pipeline', '03f410c6-fcd1-4d4a-b4c2-6c1f780dfd7c', 150, 96.0, '2024-05-25 08:00:00', 'test_data_script', 1),
('b0085514-eaf6-4b43-b6b1-0f2695db53c7', 'd4100000-0000-0000-0000-000000000011', 'terraform-project', 'b0085514-eaf6-4b43-b6b1-0f2695db53c7', 80, 93.8, '2024-05-24 14:00:00', 'test_data_script', 1),
('28a20af6-8e47-478d-99a6-42a4fc4f71ac', 'd4100000-0000-0000-0000-000000000011', 'terraform-templates', '28a20af6-8e47-478d-99a6-42a4fc4f71ac', 45, 95.6, '2024-05-23 11:00:00', 'test_data_script', 1),
-- zeb-cloud-rnd repos (ticket 12)
('5174d2f3-4465-47da-8f0d-f15d95e8558e', 'd4100000-0000-0000-0000-000000000012', 'zeb-account-payable', '5174d2f3-4465-47da-8f0d-f15d95e8558e', 22, 90.9, '2024-05-20 10:00:00', 'test_data_script', 1),
('f670aeb8-5468-49d0-b8be-aa2d3722c78f', 'd4100000-0000-0000-0000-000000000012', 'zeb-cloud-and-platform-rnd-iac', 'f670aeb8-5468-49d0-b8be-aa2d3722c78f', 35, 91.4, '2024-05-22 09:30:00', 'test_data_script', 1),
-- ai-artifacts-store repos (ticket 13)
('d3cd7f1a-d559-4155-8bf9-0f8f402733a7', 'd4100000-0000-0000-0000-000000000013', 'ai-artifacts-store', 'd3cd7f1a-d559-4155-8bf9-0f8f402733a7', 40, 92.5, '2024-05-25 12:00:00', 'test_data_script', 1),
-- zeb-test-prototype-app-demo repos (ticket 14)
('189f303c-f669-4c28-9f7c-250e95335ead', 'd4100000-0000-0000-0000-000000000014', 'prototypes-test-1', '189f303c-f669-4c28-9f7c-250e95335ead', 18, 83.3, '2024-05-10 14:00:00', 'test_data_script', 1),
('71a48daa-3ca0-492c-904b-0fc07bc65a7c', 'd4100000-0000-0000-0000-000000000014', 'zeb-test-prototype', '71a48daa-3ca0-492c-904b-0fc07bc65a7c', 25, 88.0, '2024-05-15 16:00:00', 'test_data_script', 1),
-- zeb-zebco-demo repos (ticket 15)
('cbe5fd08-0a27-45ac-a8f5-dd479b8d5562', 'd4100000-0000-0000-0000-000000000015', 'zebai-website-frontend', 'cbe5fd08-0a27-45ac-a8f5-dd479b8d5562', 55, 92.7, '2024-05-28 10:00:00', 'test_data_script', 1),
-- zeb-bayou-prod repos (ticket 16)
('545870f4-5151-430f-a3a0-814a89f982af', 'd4100000-0000-0000-0000-000000000016', 'bayou-demo', '545870f4-5151-430f-a3a0-814a89f982af', 30, 90.0, '2024-05-20 11:00:00', 'test_data_script', 1),
('88dd9bf6-4f3d-45b7-9b50-e2a9b4b5db21', 'd4100000-0000-0000-0000-000000000016', 'bayou-prod', '88dd9bf6-4f3d-45b7-9b50-e2a9b4b5db21', 75, 94.7, '2024-05-28 09:00:00', 'test_data_script', 1),
-- zeb-xfinitywifi-demo repos (ticket 17)
('01b824d0-dafc-43ac-bbdf-5209b17688e4', 'd4100000-0000-0000-0000-000000000017', 'xfinitywifi-web', '01b824d0-dafc-43ac-bbdf-5209b17688e4', 44, 90.9, '2024-05-25 15:00:00', 'test_data_script', 1),
-- zeb-cognosos-demo repos (ticket 18)
('99cb35e3-0f7e-4369-8090-aa37e2ed1edc', 'd4100000-0000-0000-0000-000000000018', 'cognosos-web-frontend', '99cb35e3-0f7e-4369-8090-aa37e2ed1edc', 38, 89.5, '2024-05-22 14:00:00', 'test_data_script', 1),
-- zeb-lk-packaging-demo repos (ticket 19)
('344e9ced-6460-4b2d-8c50-adce0af24d48', 'd4100000-0000-0000-0000-000000000019', 'lkpackaging-web-frontend', '344e9ced-6460-4b2d-8c50-adce0af24d48', 32, 87.5, '2024-05-18 13:00:00', 'test_data_script', 1),
-- zeb-apollo-agentic-usecase-prod repos (ticket 20)
('a08cfc1b-922f-4b5a-9a03-a666f8961a73', 'd4100000-0000-0000-0000-000000000020', 'zeb-apollo-backend-repo', 'a08cfc1b-922f-4b5a-9a03-a666f8961a73', 65, 93.8, '2024-05-30 09:00:00', 'test_data_script', 1),
('aa2f4e7d-a660-4cd5-9aa2-40dccab9b394', 'd4100000-0000-0000-0000-000000000020', 'zeb-apollo-iac-repo', 'aa2f4e7d-a660-4cd5-9aa2-40dccab9b394', 28, 96.4, '2024-05-28 14:00:00', 'test_data_script', 1),
('41db16e6-625e-4892-8954-a1393332b957', 'd4100000-0000-0000-0000-000000000020', 'zeb-apollo-tf-repo', '41db16e6-625e-4892-8954-a1393332b957', 22, 95.5, '2024-05-27 11:00:00', 'test_data_script', 1),
-- zeb-aws-clients-demo repos (ticket 21)
('a3e047b4-36cb-4723-b7b4-81f867a9b2ca', 'd4100000-0000-0000-0000-000000000021', 'innovation-center-agentcore-backend', 'a3e047b4-36cb-4723-b7b4-81f867a9b2ca', 50, 92.0, '2024-06-01 10:00:00', 'test_data_script', 1),
('ad983559-bbfa-444a-bef2-b40e597c09d4', 'd4100000-0000-0000-0000-000000000021', 'innovation-center-demo-backend', 'ad983559-bbfa-444a-bef2-b40e597c09d4', 42, 90.5, '2024-05-30 15:00:00', 'test_data_script', 1),
('baa5b29b-60f2-46d5-a97f-cce57d4efcae', 'd4100000-0000-0000-0000-000000000021', 'innovation-center-demo-frontend', 'baa5b29b-60f2-46d5-a97f-cce57d4efcae', 38, 89.5, '2024-05-29 12:00:00', 'test_data_script', 1),
-- zeb-onbtest-demo repos (ticket 22)
('7060da66-a96a-4d55-9f68-26ffe3b2858c', 'd4100000-0000-0000-0000-000000000022', 'onbtest-web-frontend', '7060da66-a96a-4d55-9f68-26ffe3b2858c', 28, 85.7, '2024-05-25 10:00:00', 'test_data_script', 1),
-- Zeb-MAP-Assistant repos (ticket 23)
('9d1c157c-8de2-46f6-aeb4-a1fb85a5cc02', 'd4100000-0000-0000-0000-000000000023', 'Zeb-MAP-Assistant-BE', '9d1c157c-8de2-46f6-aeb4-a1fb85a5cc02', 70, 94.3, '2024-06-05 09:00:00', 'test_data_script', 1),
('68e20ef7-4dfc-4a36-a5e2-6d4ad37f0b9d', 'd4100000-0000-0000-0000-000000000023', 'Zeb-MAP-Assistant-FE', '68e20ef7-4dfc-4a36-a5e2-6d4ad37f0b9d', 55, 92.7, '2024-06-04 16:00:00', 'test_data_script', 1),
-- zeb-qa-test-automation repos (ticket 24)
('ba792162-8e23-4150-a106-39e327549ee2', 'd4100000-0000-0000-0000-000000000024', 'Hive', 'ba792162-8e23-4150-a106-39e327549ee2', 90, 95.6, '2024-06-10 08:00:00', 'test_data_script', 1),
('38b93fb5-914a-4060-a3f4-42ee3a520289', 'd4100000-0000-0000-0000-000000000024', 'LSD', '38b93fb5-914a-4060-a3f4-42ee3a520289', 45, 91.1, '2024-06-08 14:00:00', 'test_data_script', 1),
-- zeb-outcomehubcafe-prod repos (ticket 25)
('9028ba51-a66a-420d-a3a8-703e0a7cf6a9', 'd4100000-0000-0000-0000-000000000025', 'outcomehubcafe-web-backend', '9028ba51-a66a-420d-a3a8-703e0a7cf6a9', 58, 93.1, '2024-06-15 10:00:00', 'test_data_script', 1),
('3888488d-50ad-450f-ba36-ac9bca58c280', 'd4100000-0000-0000-0000-000000000025', 'outcomehubcafe-web-frontend', '3888488d-50ad-450f-ba36-ac9bca58c280', 52, 90.4, '2024-06-14 15:00:00', 'test_data_script', 1),
('b6d579d0-91c3-4185-ba18-ec90e8214602', 'd4100000-0000-0000-0000-000000000025', 'outcomehubcafe-aws-infra', 'b6d579d0-91c3-4185-ba18-ec90e8214602', 20, 95.0, '2024-06-10 09:00:00', 'test_data_script', 1),
-- zeb-fe-demo repos (ticket 26)
('5829e2b3-a68d-470f-adc6-89eb9952612d', 'd4100000-0000-0000-0000-000000000026', 'fe-test-demo2', '5829e2b3-a68d-470f-adc6-89eb9952612d', 30, 86.7, '2024-06-18 11:00:00', 'test_data_script', 1),
('9b36f3bc-bba4-4f04-8e86-65900ab03530', 'd4100000-0000-0000-0000-000000000026', 'frontend-test-demo1', '9b36f3bc-bba4-4f04-8e86-65900ab03530', 25, 88.0, '2024-06-17 14:00:00', 'test_data_script', 1),
('f0b0e99d-d477-488b-b5d8-04e6cca314f2', 'd4100000-0000-0000-0000-000000000026', 'zeb-prototype-fe', 'f0b0e99d-d477-488b-b5d8-04e6cca314f2', 35, 91.4, '2024-06-20 10:00:00', 'test_data_script', 1),
-- zeb-precisely-testing-poc repos (ticket 27)
('455a3eac-9888-4435-9135-db0e8844af8f', 'd4100000-0000-0000-0000-000000000027', 'precisely-testing-frontend-poc', '455a3eac-9888-4435-9135-db0e8844af8f', 22, 86.4, '2024-06-22 09:00:00', 'test_data_script', 1),
-- zeb-soundry-ai-prod repos (ticket 28)
('14fae56c-4909-4f77-9ca5-c7b620ebe785', 'd4100000-0000-0000-0000-000000000028', 'soundry-ai-backend', '14fae56c-4909-4f77-9ca5-c7b620ebe785', 72, 94.4, '2024-06-28 10:00:00', 'test_data_script', 1),
('c0ae6707-70aa-4eeb-8476-94f6327faf0d', 'd4100000-0000-0000-0000-000000000028', 'soundry-ai-frontend', 'c0ae6707-70aa-4eeb-8476-94f6327faf0d', 65, 92.3, '2024-06-27 15:00:00', 'test_data_script', 1),
('585d79d4-4901-4fd6-acc9-30a5a30e9263', 'd4100000-0000-0000-0000-000000000028', 'soundry-ai-iac', '585d79d4-4901-4fd6-acc9-30a5a30e9263', 18, 94.4, '2024-06-25 08:00:00', 'test_data_script', 1),
-- zeb-artifacts-store repos (ticket 29)
('c4a47d3c-48ad-4b6e-ad35-5e51f814646e', 'd4100000-0000-0000-0000-000000000029', 'agentic-ai', 'c4a47d3c-48ad-4b6e-ad35-5e51f814646e', 40, 92.5, '2024-07-01 09:00:00', 'test_data_script', 1),
('a1253456-797e-43b3-845a-d5bd46001be3', 'd4100000-0000-0000-0000-000000000029', 'ai-platform-engineering', 'a1253456-797e-43b3-845a-d5bd46001be3', 35, 91.4, '2024-06-30 14:00:00', 'test_data_script', 1),
('c5dd01f4-3f9c-49f0-942a-c250fde95d4c', 'd4100000-0000-0000-0000-000000000029', 'cloud-platform-engineering-DevOps-SRE', 'c5dd01f4-3f9c-49f0-942a-c250fde95d4c', 55, 94.5, '2024-07-02 10:00:00', 'test_data_script', 1),
-- uxd-figma-artifact repos (ticket 30)
('d54a89a6-10d3-405a-b214-4d401817e8be', 'd4100000-0000-0000-0000-000000000030', 'Creategradientbutton', 'd54a89a6-10d3-405a-b214-4d401817e8be', 12, 83.3, '2024-07-05 11:00:00', 'test_data_script', 1),
('83c39aca-d795-4b6f-8b80-90c0c4a40be6', 'd4100000-0000-0000-0000-000000000030', 'sample-repo', '83c39aca-d795-4b6f-8b80-90c0c4a40be6', 8, 87.5, '2024-07-03 09:00:00', 'test_data_script', 1),
-- zeb-tai-software-prod repos (ticket 31)
('dfc21821-67ea-406d-a2b7-f17a4fc79d0f', 'd4100000-0000-0000-0000-000000000031', 'tai-software-mcp-service', 'dfc21821-67ea-406d-a2b7-f17a4fc79d0f', 48, 93.8, '2024-07-15 10:00:00', 'test_data_script', 1),
-- databricks-sales repos (ticket 32)
('7ec66937-e00c-4f16-9df8-f8ad49bf32b2', 'd4100000-0000-0000-0000-000000000032', 'bre-hospitality-platform', '7ec66937-e00c-4f16-9df8-f8ad49bf32b2', 28, 89.3, '2024-07-20 09:00:00', 'test_data_script', 1),
-- zeb-partner-revenue-recognition-system repos (ticket 33)
('1abfca49-5f03-4602-ae32-ecb178a07908', 'd4100000-0000-0000-0000-000000000033', 'Partner-revenue-backend-repo', '1abfca49-5f03-4602-ae32-ecb178a07908', 55, 92.7, '2024-08-01 09:00:00', 'test_data_script', 1),
('0fb0220a-bdaf-423f-88b1-a6d062593cf2', 'd4100000-0000-0000-0000-000000000033', 'partner-revenue-frontend-repo', '0fb0220a-bdaf-423f-88b1-a6d062593cf2', 42, 90.5, '2024-07-30 15:00:00', 'test_data_script', 1),
('9537a0fb-d833-4303-a48f-aed787956645', 'd4100000-0000-0000-0000-000000000033', 'Partner-revenue-tf-repo', '9537a0fb-d833-4303-a48f-aed787956645', 20, 95.0, '2024-07-28 11:00:00', 'test_data_script', 1),
-- zeb-zap-prod repos (ticket 34)
('90157d2d-6896-4706-bca6-c7e44bb41a12', 'd4100000-0000-0000-0000-000000000034', 'zap-ai-services', '90157d2d-6896-4706-bca6-c7e44bb41a12', 80, 93.8, '2024-08-10 09:00:00', 'test_data_script', 1),
('2e2979d0-90f0-46a0-9a2e-747e07bee80d', 'd4100000-0000-0000-0000-000000000034', 'zap-app-fe', '2e2979d0-90f0-46a0-9a2e-747e07bee80d', 68, 91.2, '2024-08-09 16:00:00', 'test_data_script', 1),
('7482a7f9-aa5f-40f8-8477-a4887cf42e7d', 'd4100000-0000-0000-0000-000000000034', 'zap-ap-service', '7482a7f9-aa5f-40f8-8477-a4887cf42e7d', 55, 92.7, '2024-08-08 14:00:00', 'test_data_script', 1),
('e2d2c90d-5b01-453b-b230-5a2086604866', 'd4100000-0000-0000-0000-000000000034', 'zap-auth-service', 'e2d2c90d-5b01-453b-b230-5a2086604866', 45, 95.6, '2024-08-07 10:00:00', 'test_data_script', 1),
-- zeb-eis-poc repos (ticket 35)
('fd2a9b10-76b6-427e-9199-d7ca6ed1d0d9', 'd4100000-0000-0000-0000-000000000035', 'eis-frontend-poc', 'fd2a9b10-76b6-427e-9199-d7ca6ed1d0d9', 22, 86.4, '2024-08-15 11:00:00', 'test_data_script', 1),
-- zeb-sales-dashboard repos (ticket 36)
('d6907dec-3675-4206-9b5c-e76620f88633', 'd4100000-0000-0000-0000-000000000036', 'zeb-sales-dashboard', 'd6907dec-3675-4206-9b5c-e76620f88633', 60, 93.3, '2024-08-20 09:00:00', 'test_data_script', 1),
('1594c770-e081-4090-b07c-9ead6e155dd7', 'd4100000-0000-0000-0000-000000000036', 'zeb-sales-dashboard-Iac', '1594c770-e081-4090-b07c-9ead6e155dd7', 25, 96.0, '2024-08-18 14:00:00', 'test_data_script', 1),
-- hive-revamp-redemtion repos (ticket 37)
('f3f44392-b7f6-4be1-88c0-1e175320b682', 'd4100000-0000-0000-0000-000000000037', 'hive-admin', 'f3f44392-b7f6-4be1-88c0-1e175320b682', 45, 91.1, '2024-09-01 10:00:00', 'test_data_script', 1),
('15f96f7b-e10e-4c70-9422-7984065bea90', 'd4100000-0000-0000-0000-000000000037', 'hive-employee', '15f96f7b-e10e-4c70-9422-7984065bea90', 38, 89.5, '2024-08-30 15:00:00', 'test_data_script', 1),
('c09fb3be-c192-48da-997b-fbfef5fbcef4', 'd4100000-0000-0000-0000-000000000037', 'hive-ui', 'c09fb3be-c192-48da-997b-fbfef5fbcef4', 62, 93.5, '2024-09-02 09:00:00', 'test_data_script', 1),
-- zeb-mosh-jd-prod repos (ticket 38)
('30cb2639-e4db-4940-bad6-0315f8e01d32', 'd4100000-0000-0000-0000-000000000038', 'moshjd-agent-service', '30cb2639-e4db-4940-bad6-0315f8e01d32', 48, 93.8, '2024-09-10 10:00:00', 'test_data_script', 1),
('781bbab6-7a84-4388-b973-173eeea829cb', 'd4100000-0000-0000-0000-000000000038', 'moshjd-mcp-service', '781bbab6-7a84-4388-b973-173eeea829cb', 35, 91.4, '2024-09-08 14:00:00', 'test_data_script', 1),
('148e900e-496d-4423-95c8-347821a80838', 'd4100000-0000-0000-0000-000000000038', 'moshjd-workflow-service', '148e900e-496d-4423-95c8-347821a80838', 42, 92.9, '2024-09-09 11:00:00', 'test_data_script', 1),
-- hr-hive2.0-product repos (ticket 39)
('0f00218e-105e-4c57-b393-a29a719d60aa', 'd4100000-0000-0000-0000-000000000039', 'ai_services', '0f00218e-105e-4c57-b393-a29a719d60aa', 55, 94.5, '2024-09-15 09:00:00', 'test_data_script', 1),
('866c11bb-1dd0-4448-982c-5da71d64c93c', 'd4100000-0000-0000-0000-000000000039', 'auth_service_BE', '866c11bb-1dd0-4448-982c-5da71d64c93c', 70, 95.7, '2024-09-14 16:00:00', 'test_data_script', 1),
('b6a7834b-e9c3-44bb-82f3-f2ed2b51a824', 'd4100000-0000-0000-0000-000000000039', 'employee_services', 'b6a7834b-e9c3-44bb-82f3-f2ed2b51a824', 60, 93.3, '2024-09-13 14:00:00', 'test_data_script', 1),
('20eca5b8-9cdc-48a2-8307-3391dc9e707a', 'd4100000-0000-0000-0000-000000000039', 'portal_service_FE', '20eca5b8-9cdc-48a2-8307-3391dc9e707a', 48, 91.7, '2024-09-12 10:00:00', 'test_data_script', 1),
-- ai-neural-hub repos (ticket 40)
('b107d76a-d84d-48a4-9c81-93007f4603f1', 'd4100000-0000-0000-0000-000000000040', 'neuralhub-agents-be-repo', 'b107d76a-d84d-48a4-9c81-93007f4603f1', 65, 93.8, '2024-09-20 09:00:00', 'test_data_script', 1),
('42a20165-825b-4317-abb8-1f940cf3e51c', 'd4100000-0000-0000-0000-000000000040', 'neuralhub-fe-repo', '42a20165-825b-4317-abb8-1f940cf3e51c', 52, 92.3, '2024-09-19 15:00:00', 'test_data_script', 1),
('e10f614d-c8c6-410d-b544-16e526285ace', 'd4100000-0000-0000-0000-000000000040', 'neuralhub-platform-be-repo', 'e10f614d-c8c6-410d-b544-16e526285ace', 58, 94.8, '2024-09-21 10:00:00', 'test_data_script', 1),
-- zeb-fortra-demo repos (ticket 41)
('50321ac5-254d-4d28-9b3f-1467e6c8ca50', 'd4100000-0000-0000-0000-000000000041', 'fortra-dev-api', '50321ac5-254d-4d28-9b3f-1467e6c8ca50', 35, 91.4, '2024-09-25 10:00:00', 'test_data_script', 1),
('82b92caf-0210-489f-ad4b-d685ded84592', 'd4100000-0000-0000-0000-000000000041', 'fortra-web-frontend', '82b92caf-0210-489f-ad4b-d685ded84592', 42, 90.5, '2024-09-24 14:00:00', 'test_data_script', 1),
-- crm-migration-framework repos (ticket 42)
('94f1be90-e74f-433e-93ab-901094cb2887', 'd4100000-0000-0000-0000-000000000042', 'crm-mig-datamigration', '94f1be90-e74f-433e-93ab-901094cb2887', 28, 82.1, '2024-09-30 09:00:00', 'test_data_script', 1),
('849c08d8-057a-40de-b07c-8f6aa89065b7', 'd4100000-0000-0000-0000-000000000042', 'crm-mig-frontend', '849c08d8-057a-40de-b07c-8f6aa89065b7', 32, 87.5, '2024-09-29 15:00:00', 'test_data_script', 1),
('922d8d6a-f9a6-405a-b31f-52c6534c3130', 'd4100000-0000-0000-0000-000000000042', 'crm-mig-sfcrmmigrator', '922d8d6a-f9a6-405a-b31f-52c6534c3130', 25, 80.0, '2024-09-28 11:00:00', 'test_data_script', 1),
-- zeb-precisely-poc repos (ticket 43)
('9165a98b-2e9b-41be-b9f3-7756c2f3130a', 'd4100000-0000-0000-0000-000000000043', 'precisely-auth-api', '9165a98b-2e9b-41be-b9f3-7756c2f3130a', 38, 92.1, '2024-10-05 10:00:00', 'test_data_script', 1),
('eac48183-0219-4c1b-98c0-4684dc83232c', 'd4100000-0000-0000-0000-000000000043', 'precisely-web-infra', 'eac48183-0219-4c1b-98c0-4684dc83232c', 15, 93.3, '2024-10-03 09:00:00', 'test_data_script', 1),
-- zeb-adanitrading-demo repos (ticket 44)
('f5d6476e-a6cc-4581-97bf-42c3c51662b3', 'd4100000-0000-0000-0000-000000000044', 'adani-web-frontend', 'f5d6476e-a6cc-4581-97bf-42c3c51662b3', 40, 90.0, '2024-10-10 11:00:00', 'test_data_script', 1),
-- zeb-fortra-prod repos (ticket 45)
('3cb0781e-29ed-4bfb-abbc-04cc0ce9076b', 'd4100000-0000-0000-0000-000000000045', 'fortra-ga-bff-service', '3cb0781e-29ed-4bfb-abbc-04cc0ce9076b', 75, 94.7, '2024-10-20 09:00:00', 'test_data_script', 1),
('599b9988-5f1d-4477-b633-5969e9da7f3b', 'd4100000-0000-0000-0000-000000000045', 'ga-ai-chat-develop', '599b9988-5f1d-4477-b633-5969e9da7f3b', 60, 93.3, '2024-10-19 15:00:00', 'test_data_script', 1),
('73cc53ba-290e-4a04-878a-28f2f4a23666', 'd4100000-0000-0000-0000-000000000045', 'ga-be-crud', '73cc53ba-290e-4a04-878a-28f2f4a23666', 55, 92.7, '2024-10-18 14:00:00', 'test_data_script', 1),
('36ebc3f4-1e22-44e6-b6da-a608c7d618e6', 'd4100000-0000-0000-0000-000000000045', 'ga-orchestrator-agent', '36ebc3f4-1e22-44e6-b6da-a608c7d618e6', 48, 91.7, '2024-10-17 10:00:00', 'test_data_script', 1),
-- ai-zeb-innovation repos (ticket 46)
('5f484fe9-2efd-47b8-bab0-8097cdab17b0', 'd4100000-0000-0000-0000-000000000046', 'substrate-platform', '5f484fe9-2efd-47b8-bab0-8097cdab17b0', 85, 95.3, '2024-10-28 09:00:00', 'test_data_script', 1),
('af04d653-6d25-4c54-a588-01fa39e9979b', 'd4100000-0000-0000-0000-000000000046', 'substrate-plus-cloud', 'af04d653-6d25-4c54-a588-01fa39e9979b', 70, 94.3, '2024-10-27 14:00:00', 'test_data_script', 1),
('70515c20-8ad8-450e-9519-61fec727128f', 'd4100000-0000-0000-0000-000000000046', 'substrate-ui', '70515c20-8ad8-450e-9519-61fec727128f', 55, 92.7, '2024-10-26 11:00:00', 'test_data_script', 1),
('02f4a0bc-09b4-4861-9051-4727f922869d', 'd4100000-0000-0000-0000-000000000046', 'substrate-ingest', '02f4a0bc-09b4-4861-9051-4727f922869d', 42, 90.5, '2024-10-25 10:00:00', 'test_data_script', 1),
-- zeb-analytics-intell-prod repos (ticket 47)
('a957f0a1-15d1-49fa-8cae-6c3d6a38a717', 'd4100000-0000-0000-0000-000000000047', 'zeb-analytics-dev-backend', 'a957f0a1-15d1-49fa-8cae-6c3d6a38a717', 50, 92.0, '2024-11-08 09:00:00', 'test_data_script', 1),
('2afe6e34-37e9-430c-bacb-50811956a83b', 'd4100000-0000-0000-0000-000000000047', 'zeb-analytics-dev-frontend', '2afe6e34-37e9-430c-bacb-50811956a83b', 45, 91.1, '2024-11-07 15:00:00', 'test_data_script', 1),
-- zeb-splitz-prod repos (ticket 48)
('da9d0cc5-d188-4dd4-8e79-d26c8b1740c3', 'd4100000-0000-0000-0000-000000000048', 'splitz-be-repo', 'da9d0cc5-d188-4dd4-8e79-d26c8b1740c3', 58, 93.1, '2024-11-18 10:00:00', 'test_data_script', 1),
('78348e16-d2cb-49b2-a893-cf7da0db50b2', 'd4100000-0000-0000-0000-000000000048', 'splitz-frontend-repo', '78348e16-d2cb-49b2-a893-cf7da0db50b2', 48, 91.7, '2024-11-17 14:00:00', 'test_data_script', 1),
-- zeb-lululemon-prod repos (ticket 49)
('c6e8f2a0-b6c7-427d-9cf7-9d7b2f5d153c', 'd4100000-0000-0000-0000-000000000049', 'lululemon-dbx-uc-migration', 'c6e8f2a0-b6c7-427d-9cf7-9d7b2f5d153c', 32, 87.5, '2024-11-22 09:00:00', 'test_data_script', 1),
-- zeb-internal-prod repos (ticket 50)
('2f4215b3-d68b-472c-b34d-2c4ac0237221', 'd4100000-0000-0000-0000-000000000050', 'internal-client-cpq-migration-framework', '2f4215b3-d68b-472c-b34d-2c4ac0237221', 35, 88.6, '2024-11-12 10:00:00', 'test_data_script', 1),
('622f96ce-c958-4fad-b711-eb1535e0d6b9', 'd4100000-0000-0000-0000-000000000050', 'internal-server-cpq-migration-framework', '622f96ce-c958-4fad-b711-eb1535e0d6b9', 40, 90.0, '2024-11-11 15:00:00', 'test_data_script', 1);
