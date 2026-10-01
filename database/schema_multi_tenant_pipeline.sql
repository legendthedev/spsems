-- ==============================================================================
-- SPSEMS MULTI-TENANT INSTITUTION ONBOARDING PIPELINE SCHEMA (PostgreSQL / Supabase)
-- Enables autonomous self-onboarding for multiple universities and polytechnics
-- ==============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- TABLE 1: institutions (Central Directory of Onboarded Schools)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS institutions (
    institution_id       SERIAL PRIMARY KEY,
    name                 VARCHAR(200) NOT NULL,
    code                 VARCHAR(30) NOT NULL UNIQUE,       -- e.g. 'KWASU', 'UNILORIN', 'UI', 'OAU'
    slug                 VARCHAR(60) NOT NULL UNIQUE,       -- e.g. 'kwasu', 'unilorin', used for subdomain/routing
    official_domain      VARCHAR(120) NOT NULL UNIQUE,      -- e.g. 'kwasu.edu.ng', 'unilorin.edu.ng'
    institution_type     VARCHAR(50) NOT NULL DEFAULT 'State University', -- 'Federal University', 'State University', 'Private University', 'Polytechnic'
    country              VARCHAR(60) NOT NULL DEFAULT 'Nigeria',
    state                VARCHAR(60),
    city                 VARCHAR(60),
    contact_email        VARCHAR(120) NOT NULL,
    contact_phone        VARCHAR(30),
    logo_url             VARCHAR(255) DEFAULT '/kwasu.png',
    primary_color        VARCHAR(20) DEFAULT '#16a34a',     -- Custom university branding
    secondary_color      VARCHAR(20) DEFAULT '#080808',
    status               VARCHAR(30) NOT NULL DEFAULT 'pending_verification',
                         -- 'pending_verification', 'domain_verified', 'provisioned', 'configuring', 'active', 'suspended'
    verification_token   VARCHAR(128),
    is_verified          BOOLEAN DEFAULT FALSE,
    current_stage        VARCHAR(60) DEFAULT '1_registration',
    onboarding_percent   INT DEFAULT 15,
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_at          TIMESTAMP WITH TIME ZONE,
    activated_at         TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_institutions_code ON institutions(code);
CREATE INDEX IF NOT EXISTS idx_institutions_domain ON institutions(official_domain);
CREATE INDEX IF NOT EXISTS idx_institutions_slug ON institutions(slug);
CREATE INDEX IF NOT EXISTS idx_institutions_status ON institutions(status);

-- ==============================================================================
-- TABLE 2: institution_settings (Tenant Governance & Supervision Policies)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS institution_settings (
    setting_id                     SERIAL PRIMARY KEY,
    institution_id                 INT NOT NULL REFERENCES institutions(institution_id) ON DELETE CASCADE,
    academic_session               VARCHAR(20) DEFAULT '2025/2026',
    current_semester               VARCHAR(30) DEFAULT 'First Semester',
    max_supervisor_load            INT DEFAULT 10,
    dual_supervisor_for_postgrad   BOOLEAN DEFAULT TRUE,   -- MSc & PhD require 1 Main + 1 Co-Supervisor
    auto_assign_co_supervisor      BOOLEAN DEFAULT TRUE,   -- Automatically pair co-supervisors at random/by domain
    enable_ai_pairing              BOOLEAN DEFAULT TRUE,   -- TF-IDF / NLP similarity matching
    allow_public_student_reg       BOOLEAN DEFAULT TRUE,
    allow_public_lecturer_reg      BOOLEAN DEFAULT TRUE,
    require_admin_approval         BOOLEAN DEFAULT TRUE,
    min_abstract_word_count        INT DEFAULT 50,
    max_chapters                   INT DEFAULT 5,
    plagiarism_threshold_percent   INT DEFAULT 20,
    updated_at                     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_institution_settings UNIQUE(institution_id)
);

-- ==============================================================================
-- TABLE 3: tenant_onboarding_pipeline (Execution Log & Audit Trail)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS tenant_onboarding_pipeline (
    pipeline_id         SERIAL PRIMARY KEY,
    institution_id      INT NOT NULL REFERENCES institutions(institution_id) ON DELETE CASCADE,
    stage_order         INT NOT NULL,
    stage_code          VARCHAR(60) NOT NULL,
    stage_name          VARCHAR(120) NOT NULL,
    status              VARCHAR(30) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed', 'skipped'
    required_action     VARCHAR(255),
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    executed_by         VARCHAR(120),
    metadata            JSONB DEFAULT '{}',
    error_message       TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_institution ON tenant_onboarding_pipeline(institution_id);

-- ==============================================================================
-- TABLE 4: faculties & departments (Academic Organization Hierarchy)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS faculties (
    faculty_id         SERIAL PRIMARY KEY,
    institution_id     INT NOT NULL REFERENCES institutions(institution_id) ON DELETE CASCADE,
    name               VARCHAR(150) NOT NULL,
    code               VARCHAR(30) NOT NULL,
    dean_name          VARCHAR(120),
    dean_email         VARCHAR(120),
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_faculty_institution UNIQUE(institution_id, code)
);

CREATE TABLE IF NOT EXISTS departments (
    department_id      SERIAL PRIMARY KEY,
    institution_id     INT NOT NULL REFERENCES institutions(institution_id) ON DELETE CASCADE,
    faculty_id         INT REFERENCES faculties(faculty_id) ON DELETE SET NULL,
    name               VARCHAR(150) NOT NULL,
    code               VARCHAR(30) NOT NULL,
    hod_name           VARCHAR(120),
    hod_email          VARCHAR(120),
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_dept_institution UNIQUE(institution_id, code)
);

CREATE INDEX IF NOT EXISTS idx_depts_institution ON departments(institution_id);

-- ==============================================================================
-- TABLE 5: tenant_data_imports (CSV/Batch Ingestion Pipeline)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS tenant_data_imports (
    import_id          SERIAL PRIMARY KEY,
    institution_id     INT NOT NULL REFERENCES institutions(institution_id) ON DELETE CASCADE,
    batch_reference    VARCHAR(60) NOT NULL,
    import_type        VARCHAR(40) NOT NULL, -- 'lecturers_csv', 'students_csv', 'courses_csv', 'historical_projects'
    file_name          VARCHAR(180) NOT NULL,
    file_size_bytes    BIGINT,
    total_records      INT DEFAULT 0,
    success_records    INT DEFAULT 0,
    failed_records     INT DEFAULT 0,
    status             VARCHAR(30) DEFAULT 'queued', -- 'queued', 'validating', 'processing', 'completed', 'failed'
    log_summary        TEXT,
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at        TIMESTAMP WITH TIME ZONE
);

-- ==============================================================================
-- STEP 6: ALTER EXISTING TABLES TO ATTACH TENANT ID (MULTI-TENANT LINKING)
-- ==============================================================================

-- Add institution_id to users
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='institution_id') THEN
        ALTER TABLE users ADD COLUMN institution_id INT REFERENCES institutions(institution_id) ON DELETE RESTRICT;
        CREATE INDEX idx_users_institution ON users(institution_id);
    END IF;
END $$;

-- Add institution_id to supervisors
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='supervisors' AND column_name='institution_id') THEN
        ALTER TABLE supervisors ADD COLUMN institution_id INT REFERENCES institutions(institution_id) ON DELETE RESTRICT;
        CREATE INDEX idx_supervisors_institution ON supervisors(institution_id);
    END IF;
END $$;

-- Add institution_id to students
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='students' AND column_name='institution_id') THEN
        ALTER TABLE students ADD COLUMN institution_id INT REFERENCES institutions(institution_id) ON DELETE RESTRICT;
        CREATE INDEX idx_students_institution ON students(institution_id);
    END IF;
END $$;

-- Add institution_id to projects
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='projects' AND column_name='institution_id') THEN
        ALTER TABLE projects ADD COLUMN institution_id INT REFERENCES institutions(institution_id) ON DELETE RESTRICT;
        CREATE INDEX idx_projects_institution ON projects(institution_id);
    END IF;
END $$;

-- Add institution_id to alerts
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='alerts' AND column_name='institution_id') THEN
        ALTER TABLE alerts ADD COLUMN institution_id INT REFERENCES institutions(institution_id) ON DELETE RESTRICT;
        CREATE INDEX idx_alerts_institution ON alerts(institution_id);
    END IF;
END $$;

-- Add institution_id to messages
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='messages' AND column_name='institution_id') THEN
        ALTER TABLE messages ADD COLUMN institution_id INT REFERENCES institutions(institution_id) ON DELETE RESTRICT;
        CREATE INDEX idx_messages_institution ON messages(institution_id);
    END IF;
END $$;

-- Add institution_id to audit_logs
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='institution_id') THEN
        ALTER TABLE audit_logs ADD COLUMN institution_id INT REFERENCES institutions(institution_id) ON DELETE RESTRICT;
        CREATE INDEX idx_audit_logs_institution ON audit_logs(institution_id);
    END IF;
END $$;

-- ==============================================================================
-- STEP 7: ROW LEVEL SECURITY (RLS) FOR MULTI-TENANT ISOLATION
-- ==============================================================================

-- Enable RLS on core tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE supervisors ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Tenant Isolation RLS Policy Example:
-- Authenticated users only see rows matching their current session tenant
CREATE OR REPLACE FUNCTION current_user_institution_id() 
RETURNS INT AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_institution_id', TRUE), '')::INT;
EXCEPTION
    WHEN OTHERS THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Users Policy
DROP POLICY IF EXISTS tenant_users_isolation ON users;
CREATE POLICY tenant_users_isolation ON users
    USING (institution_id = current_user_institution_id() OR current_user_institution_id() IS NULL);

-- Projects Policy
DROP POLICY IF EXISTS tenant_projects_isolation ON projects;
CREATE POLICY tenant_projects_isolation ON projects
    USING (institution_id = current_user_institution_id() OR current_user_institution_id() IS NULL);

-- ==============================================================================
-- STEP 8: AUTOMATED SCHOOL ONBOARDING STORED PROCEDURE
-- ==============================================================================

CREATE OR REPLACE FUNCTION fn_onboard_new_institution(
    p_name              VARCHAR(200),
    p_code              VARCHAR(30),
    p_domain            VARCHAR(120),
    p_type              VARCHAR(50),
    p_contact_email     VARCHAR(120),
    p_contact_phone     VARCHAR(30),
    p_admin_fullname    VARCHAR(120),
    p_admin_username    VARCHAR(60),
    p_admin_password    VARCHAR(120)
)
RETURNS TABLE (
    out_institution_id   INT,
    out_code             VARCHAR(30),
    out_verification_tok VARCHAR(128),
    out_status           VARCHAR(30),
    out_message          VARCHAR(255)
) AS $$
DECLARE
    v_inst_id INT;
    v_slug VARCHAR(60);
    v_token VARCHAR(128);
    v_hashed_pw VARCHAR(255);
    v_admin_user_id INT;
BEGIN
    -- Normalize slug and token
    v_slug := LOWER(REGEXP_REPLACE(p_code, '[^a-zA-Z0-9]', '', 'g'));
    v_token := MD5(p_domain || CURRENT_TIMESTAMP::TEXT || RANDOM()::TEXT);

    -- 1. Insert Institution Record
    INSERT INTO institutions (
        name, code, slug, official_domain, institution_type,
        contact_email, contact_phone, verification_token,
        status, current_stage, onboarding_percent
    ) VALUES (
        p_name, UPPER(p_code), v_slug, LOWER(p_domain), p_type,
        LOWER(p_contact_email), p_contact_phone, v_token,
        'pending_verification', '1_registration', 15
    ) RETURNING institution_id INTO v_inst_id;

    -- 2. Provision Default Institutional Settings
    INSERT INTO institution_settings (
        institution_id, max_supervisor_load, dual_supervisor_for_postgrad,
        auto_assign_co_supervisor, enable_ai_pairing
    ) VALUES (
        v_inst_id, 10, TRUE, TRUE, TRUE
    );

    -- 3. Seed 7-Stage Onboarding Pipeline
    INSERT INTO tenant_onboarding_pipeline (institution_id, stage_order, stage_code, stage_name, status, required_action)
    VALUES
    (v_inst_id, 1, '1_registration',        'Institution Registration & Identity Verification', 'completed', 'Initial school metadata submitted'),
    (v_inst_id, 2, '2_domain_verification', 'Institutional Domain DNS/Email Verification',       'in_progress', 'Verify DNS TXT or institutional email PIN'),
    (v_inst_id, 3, '3_tenant_provisioning', 'Database Isolation & Dedicated Storage Bucket',     'pending',     'Allocate storage bucket and RLS boundaries'),
    (v_inst_id, 4, '4_department_setup',    'Faculties & Academic Departments Tree',             'pending',     'Configure faculties and departments'),
    (v_inst_id, 5, '5_faculty_import',      'Faculty Supervisors Batch Onboarding',              'pending',     'Upload supervisors CSV or manual registration'),
    (v_inst_id, 6, '6_policy_config',       'Supervision Rules & MSc/PhD Dual Allocation',       'pending',     'Confirm degree level supervision guidelines'),
    (v_inst_id, 7, '7_live_activation',     'Production Handoff & University Launch',            'pending',     'Activate live students/lecturers login');

    -- 4. Create Initial Institutional Super Admin (Pending verification)
    INSERT INTO users (
        institution_id, username, email, password, role, full_name, phone, is_active
    ) VALUES (
        v_inst_id, LOWER(p_admin_username), LOWER(p_contact_email),
        crypt(p_admin_password, gen_salt('bf')),
        'admin', p_admin_fullname, p_contact_phone, FALSE
    ) RETURNING user_id INTO v_admin_user_id;

    -- Return result row
    RETURN QUERY
    SELECT v_inst_id, UPPER(p_code), v_token, 'pending_verification'::VARCHAR,
           'Institution registered successfully. Verification token generated.'::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- STEP 9: SAMPLE SEED DATA (KWASU, UNILORIN, UI, OAU)
-- ==============================================================================

-- Seed KWASU as primary tenant #1 if not exists
INSERT INTO institutions (
    institution_id, name, code, slug, official_domain, institution_type,
    state, city, contact_email, contact_phone, logo_url, primary_color,
    status, is_verified, current_stage, onboarding_percent, activated_at
) VALUES (
    1, 'Kwara State University', 'KWASU', 'kwasu', 'kwasu.edu.ng', 'State University',
    'Kwara', 'Malete', 'ict@kwasu.edu.ng', '+2348030000001', '/kwasu.png', '#16a34a',
    'active', TRUE, '7_live_activation', 100, CURRENT_TIMESTAMP
) ON CONFLICT (code) DO NOTHING;

-- Seed KWASU settings
INSERT INTO institution_settings (
    institution_id, academic_session, current_semester, max_supervisor_load,
    dual_supervisor_for_postgrad, auto_assign_co_supervisor, enable_ai_pairing
) VALUES (
    1, '2025/2026', 'First Semester', 10, TRUE, TRUE, TRUE
) ON CONFLICT (institution_id) DO NOTHING;

-- Associate existing users and data with KWASU (#1) if NULL
UPDATE users SET institution_id = 1 WHERE institution_id IS NULL;
UPDATE supervisors SET institution_id = 1 WHERE institution_id IS NULL;
UPDATE students SET institution_id = 1 WHERE institution_id IS NULL;
UPDATE projects SET institution_id = 1 WHERE institution_id IS NULL;
UPDATE alerts SET institution_id = 1 WHERE institution_id IS NULL;
UPDATE messages SET institution_id = 1 WHERE institution_id IS NULL;
UPDATE audit_logs SET institution_id = 1 WHERE institution_id IS NULL;

-- Seed UNILORIN as onboarding tenant #2
INSERT INTO institutions (
    institution_id, name, code, slug, official_domain, institution_type,
    state, city, contact_email, contact_phone, logo_url, primary_color,
    status, is_verified, current_stage, onboarding_percent
) VALUES (
    2, 'University of Ilorin', 'UNILORIN', 'unilorin', 'unilorin.edu.ng', 'Federal University',
    'Kwara', 'Ilorin', 'cit@unilorin.edu.ng', '+2348030000002', '/unilorin.png', '#1d4ed8',
    'configuring', TRUE, '4_department_setup', 65
) ON CONFLICT (code) DO NOTHING;

INSERT INTO institution_settings (
    institution_id, academic_session, current_semester, max_supervisor_load,
    dual_supervisor_for_postgrad, auto_assign_co_supervisor, enable_ai_pairing
) VALUES (
    2, '2025/2026', 'Harmattan Semester', 12, TRUE, TRUE, TRUE
) ON CONFLICT (institution_id) DO NOTHING;

-- Reset sequence to avoid conflict
SELECT setval('institutions_institution_id_seq', (SELECT MAX(institution_id) FROM institutions));
