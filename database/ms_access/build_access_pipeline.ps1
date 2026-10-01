# ==============================================================================
# SPSEMS - Microsoft 365 Access Multi-School Onboarding Database Pipeline
# Creates SPSEMS_MultiSchool_Pipeline.accdb with tables, queries & seed data
# ==============================================================================

param(
    [string]$OutputDir = "$PSScriptRoot",
    [switch]$LaunchAccess = $false
)

$ErrorActionPreference = "Stop"

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$dbPath = Join-Path $OutputDir "SPSEMS_MultiSchool_Pipeline.accdb"
Write-Host "[1/6] Target Access Database: $dbPath" -ForegroundColor Cyan

# Remove old database file if exists
if (Test-Path $dbPath) {
    Write-Host "      Removing old file..." -ForegroundColor Yellow
    Remove-Item $dbPath -Force
}

# Initialize Access COM object
Write-Host "[2/6] Initializing Microsoft Access 365 COM Engine..." -ForegroundColor Cyan
$access = New-Object -ComObject Access.Application
$access.Visible = $false

try {
    # Create new .accdb database
    $access.NewCurrentDatabase($dbPath)
    $db = $access.CurrentDb()
    Write-Host "      Database created successfully." -ForegroundColor Green

    # Helper function to execute SQL
    function Exec-SQL([string]$sql, [string]$desc) {
        try {
            $db.Execute($sql, 128) # 128 = dbFailOnError
            Write-Host "      + $desc" -ForegroundColor Gray
        } catch {
            Write-Host "      [!] Failed: $desc -> $($_.Exception.Message)" -ForegroundColor Red
            throw $_
        }
    }

    Write-Host "[3/6] Creating Pipeline Tables..." -ForegroundColor Cyan

    # 1. tbl_Institutions
    Exec-SQL @"
CREATE TABLE tbl_Institutions (
    InstitutionID AUTOINCREMENT PRIMARY KEY,
    InstitutionName TEXT(150) NOT NULL,
    InstitutionCode TEXT(20) NOT NULL,
    OfficialDomain TEXT(100) NOT NULL,
    SubdomainSlug TEXT(50) NOT NULL,
    InstitutionType TEXT(50) NOT NULL,
    Country TEXT(50),
    StateOrProvince TEXT(50),
    City TEXT(50),
    ContactEmail TEXT(100) NOT NULL,
    ContactPhone TEXT(30),
    LogoUrl TEXT(255),
    PrimaryColor TEXT(20),
    SecondaryColor TEXT(20),
    OnboardingStatus TEXT(30),
    VerificationToken TEXT(100),
    IsVerified YESNO,
    CurrentPipelineStage TEXT(50),
    PipelineProgressPercent INTEGER,
    RegisteredAt DATETIME,
    ActivatedAt DATETIME
);
"@ "Created tbl_Institutions"

    Exec-SQL "CREATE UNIQUE INDEX idx_inst_code ON tbl_Institutions (InstitutionCode);" "Created unique index on InstitutionCode"
    Exec-SQL "CREATE UNIQUE INDEX idx_inst_domain ON tbl_Institutions (OfficialDomain);" "Created unique index on OfficialDomain"
    Exec-SQL "CREATE UNIQUE INDEX idx_inst_slug ON tbl_Institutions (SubdomainSlug);" "Created unique index on SubdomainSlug"

    # 2. tbl_OnboardingPipeline
    Exec-SQL @"
CREATE TABLE tbl_OnboardingPipeline (
    PipelineID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    StageOrder INTEGER NOT NULL,
    StageCode TEXT(50) NOT NULL,
    StageName TEXT(100) NOT NULL,
    StageStatus TEXT(25),
    RequiredAction TEXT(255),
    StartedAt DATETIME,
    CompletedAt DATETIME,
    CompletedBy TEXT(100),
    Notes MEMO
);
"@ "Created tbl_OnboardingPipeline"

    # 3. tbl_InstitutionSettings
    Exec-SQL @"
CREATE TABLE tbl_InstitutionSettings (
    SettingID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    AcademicSession TEXT(20),
    CurrentSemester TEXT(20),
    MaxSupervisorLoad INTEGER,
    DualSupervisorForPostgrad YESNO,
    AutoAssignCoSupervisor YESNO,
    EnableAIPairing YESNO,
    AllowPublicStudentRegistration YESNO,
    AllowPublicLecturerRegistration YESNO,
    RequireAdminApproval YESNO,
    MinimumAbstractWordCount INTEGER,
    PlagiarismCheckThreshold INTEGER,
    UpdatedAt DATETIME
);
"@ "Created tbl_InstitutionSettings"

    # 4. tbl_Faculties
    Exec-SQL @"
CREATE TABLE tbl_Faculties (
    FacultyID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    FacultyName TEXT(120) NOT NULL,
    FacultyCode TEXT(20) NOT NULL,
    DeanName TEXT(100),
    DeanEmail TEXT(100),
    CreatedAt DATETIME
);
"@ "Created tbl_Faculties"

    # 5. tbl_Departments
    Exec-SQL @"
CREATE TABLE tbl_Departments (
    DepartmentID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    FacultyID INTEGER,
    DepartmentName TEXT(120) NOT NULL,
    DepartmentCode TEXT(20) NOT NULL,
    HODName TEXT(100),
    HODEmail TEXT(100),
    CreatedAt DATETIME
);
"@ "Created tbl_Departments"

    # 6. tbl_InstitutionalAdmins
    Exec-SQL @"
CREATE TABLE tbl_InstitutionalAdmins (
    AdminID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    FullName TEXT(100) NOT NULL,
    Username TEXT(50) NOT NULL,
    OfficialEmail TEXT(100) NOT NULL,
    Phone TEXT(30),
    Designation TEXT(100) NOT NULL,
    AdminRole TEXT(30),
    AdminApprovalCode TEXT(50),
    IsActive YESNO,
    CreatedAt DATETIME
);
"@ "Created tbl_InstitutionalAdmins"

    # 7. tbl_SupervisionPolicies
    Exec-SQL @"
CREATE TABLE tbl_SupervisionPolicies (
    PolicyID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    DegreeLevel TEXT(20) NOT NULL,
    SupervisorsRequired INTEGER,
    CoSupervisorAssignmentMode TEXT(30),
    MaxChapters INTEGER,
    MandatoryDefenseStages TEXT(150),
    DurationMonths INTEGER
);
"@ "Created tbl_SupervisionPolicies"

    # 8. tbl_OnboardingDataImports
    Exec-SQL @"
CREATE TABLE tbl_OnboardingDataImports (
    ImportID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    BatchReference TEXT(50) NOT NULL,
    ImportType TEXT(40) NOT NULL,
    FileName TEXT(150),
    TotalRecords INTEGER,
    SuccessCount INTEGER,
    FailedCount INTEGER,
    ImportStatus TEXT(25),
    ExecutedAt DATETIME,
    LogDetails MEMO
);
"@ "Created tbl_OnboardingDataImports"

    # 9. tbl_TenantDatabases
    Exec-SQL @"
CREATE TABLE tbl_TenantDatabases (
    TenantDBID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    IsolationModel TEXT(50),
    DatabaseHost TEXT(120),
    DatabaseName TEXT(60),
    SchemaName TEXT(50),
    StorageBucket TEXT(80),
    HealthStatus TEXT(20),
    LastHealthCheck DATETIME
);
"@ "Created tbl_TenantDatabases"

    # --------------------------------------------------------------------------
    # SEED DATA
    # --------------------------------------------------------------------------
    Write-Host "[4/6] Seeding Multi-School Pipeline Data..." -ForegroundColor Cyan

    # 1. KWASU
    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt, ActivatedAt)
VALUES
('Kwara State University', 'KWASU', 'kwasu.edu.ng', 'kwasu', 'State University', 'Nigeria', 'Kwara', 'Malete', 'ict@kwasu.edu.ng', '+2348030000001', '/kwasu.png', '#16a34a', '#080808', 'Active', True, '7_Live_Activation', 100, #2026-09-01 09:00:00#, #2026-09-06 14:00:00#);
"@ "Seeded Institution: KWASU (Active)"

    # 2. UNILORIN
    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt)
VALUES
('University of Ilorin', 'UNILORIN', 'unilorin.edu.ng', 'unilorin', 'Federal University', 'Nigeria', 'Kwara', 'Ilorin', 'director_citng@unilorin.edu.ng', '+2348030000002', '/unilorin.png', '#1d4ed8', '#0f172a', 'Configuring', True, '4_Department_Setup', 65, #2026-09-20 10:30:00#);
"@ "Seeded Institution: UNILORIN (In Setup)"

    # 3. UI
    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt)
VALUES
('University of Ibadan', 'UI', 'ui.edu.ng', 'ui', 'Federal University', 'Nigeria', 'Oyo', 'Ibadan', 'pgschool@ui.edu.ng', '+2348030000003', '/ui.png', '#b45309', '#1e293b', 'Pending_Verification', False, '2_Domain_Verification', 30, #2026-09-27 11:15:00#);
"@ "Seeded Institution: UI (Verification)"

    # 4. OAU
    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt)
VALUES
('Obafemi Awolowo University', 'OAU', 'oauife.edu.ng', 'oau', 'Federal University', 'Nigeria', 'Osun', 'Ile-Ife', 'dean_pg@oauife.edu.ng', '+2348030000004', '/oau.png', '#047857', '#0f172a', 'Provisioned', True, '3_Tenant_Provisioning', 45, #2026-09-25 08:45:00#);
"@ "Seeded Institution: OAU (Provisioned)"

    # 5. KWAPOLY
    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt)
VALUES
('Kwara State Polytechnic', 'KWAPOLY', 'kwarapoly.edu.ng', 'kwapoly', 'State Polytechnic', 'Nigeria', 'Kwara', 'Ilorin', 'rector@kwarapoly.edu.ng', '+2348030000005', '/kwapoly.png', '#7c3aed', '#111827', 'Configuring', True, '5_Faculty_Import', 80, #2026-09-22 13:00:00#);
"@ "Seeded Institution: KWAPOLY (Import)"

    # Seed Pipeline Stages for KWASU (Institution 1)
    $stagesKWASU = @(
        @(1, '1_School_Registration', 'School Profile & Registration Form', 'Completed', 'Admin registered university profile', '#2026-09-01 09:00:00#', '#2026-09-01 09:30:00#'),
        @(2, '2_Domain_Verification', 'Institutional DNS & Email Verification', 'Completed', 'Domain verified via DNS TXT record', '#2026-09-01 10:00:00#', '#2026-09-02 08:00:00#'),
        @(3, '3_Tenant_Provisioning', 'PostgreSQL Schema & Storage Allocation', 'Completed', 'Dedicated Supabase bucket kwasu-spsems', '#2026-09-02 08:30:00#', '#2026-09-02 09:00:00#'),
        @(4, '4_Department_Setup', 'Faculties & Academic Departments Tree', 'Completed', 'Configured 4 faculties and 10 departments', '#2026-09-03 10:00:00#', '#2026-09-03 16:00:00#'),
        @(5, '5_Faculty_Import', 'Batch Staff & Supervisor Import', 'Completed', 'Imported 48 lecturers via CSV pipeline', '#2026-09-04 09:00:00#', '#2026-09-04 11:30:00#'),
        @(6, '6_Policy_Config', 'Supervision Rules & MSc/PhD Dual Supervisor', 'Completed', 'Enabled random co-supervisor for MSc/PhD', '#2026-09-05 14:00:00#', '#2026-09-05 15:00:00#'),
        @(7, '7_Live_Activation', 'Production Handover & Portal Launch', 'Completed', 'Portal active at kwasu.spsems.edu', '#2026-09-06 12:00:00#', '#2026-09-06 14:00:00#')
    )

    foreach ($s in $stagesKWASU) {
        Exec-SQL @"
INSERT INTO tbl_OnboardingPipeline 
(InstitutionID, StageOrder, StageCode, StageName, StageStatus, RequiredAction, StartedAt, CompletedAt, CompletedBy)
VALUES
(1, $($s[0]), '$($s[1])', '$($s[2])', '$($s[3])', '$($s[4])', $($s[5]), $($s[6]), 'System Onboarding Pipeline');
"@ "Seeded Stage $($s[0]) for KWASU"
    }

    # Seed Pipeline Stages for UNILORIN (Institution 2)
    Exec-SQL @"
INSERT INTO tbl_OnboardingPipeline (InstitutionID, StageOrder, StageCode, StageName, StageStatus, RequiredAction, StartedAt, CompletedAt, CompletedBy)
VALUES (2, 1, '1_School_Registration', 'School Profile & Registration Form', 'Completed', 'Verified profile submitted', #2026-09-20 10:30:00#, #2026-09-20 11:00:00#, 'CIT Director');
"@ "Seeded UNILORIN Stage 1"
    Exec-SQL @"
INSERT INTO tbl_OnboardingPipeline (InstitutionID, StageOrder, StageCode, StageName, StageStatus, RequiredAction, StartedAt, CompletedAt, CompletedBy)
VALUES (2, 2, '2_Domain_Verification', 'Institutional DNS & Email Verification', 'Completed', 'Domain verified via unilorin.edu.ng', #2026-09-21 09:00:00#, #2026-09-21 15:00:00#, 'CIT Director');
"@ "Seeded UNILORIN Stage 2"
    Exec-SQL @"
INSERT INTO tbl_OnboardingPipeline (InstitutionID, StageOrder, StageCode, StageName, StageStatus, RequiredAction, StartedAt, CompletedAt, CompletedBy)
VALUES (2, 3, '3_Tenant_Provisioning', 'PostgreSQL Schema & Storage Allocation', 'Completed', 'Allocated tenant isolation schema', #2026-09-22 08:00:00#, #2026-09-22 08:45:00#, 'Pipeline Daemon');
"@ "Seeded UNILORIN Stage 3"
    Exec-SQL @"
INSERT INTO tbl_OnboardingPipeline (InstitutionID, StageOrder, StageCode, StageName, StageStatus, RequiredAction, StartedAt, CompletedBy)
VALUES (2, 4, '4_Department_Setup', 'Faculties & Academic Departments Tree', 'In_Progress', 'Awaiting HOD list for Faculty of CIS', #2026-09-25 14:00:00#, 'CIT Director');
"@ "Seeded UNILORIN Stage 4"

    # Seed Institution Settings
    Exec-SQL @"
INSERT INTO tbl_InstitutionSettings 
(InstitutionID, AcademicSession, CurrentSemester, MaxSupervisorLoad, DualSupervisorForPostgrad, AutoAssignCoSupervisor, EnableAIPairing, AllowPublicStudentRegistration, AllowPublicLecturerRegistration, RequireAdminApproval, MinimumAbstractWordCount, PlagiarismCheckThreshold, UpdatedAt)
VALUES
(1, '2025/2026', 'First Semester', 10, True, True, True, True, True, True, 50, 20, #2026-09-30 08:00:00#);
"@ "Seeded Settings for KWASU"

    Exec-SQL @"
INSERT INTO tbl_InstitutionSettings 
(InstitutionID, AcademicSession, CurrentSemester, MaxSupervisorLoad, DualSupervisorForPostgrad, AutoAssignCoSupervisor, EnableAIPairing, AllowPublicStudentRegistration, AllowPublicLecturerRegistration, RequireAdminApproval, MinimumAbstractWordCount, PlagiarismCheckThreshold, UpdatedAt)
VALUES
(2, '2025/2026', 'Harmattan Semester', 12, True, True, True, True, True, True, 75, 15, #2026-09-30 08:00:00#);
"@ "Seeded Settings for UNILORIN"

    # Seed Faculties for KWASU
    Exec-SQL @"
INSERT INTO tbl_Faculties (InstitutionID, FacultyName, FacultyCode, DeanName, DeanEmail, CreatedAt)
VALUES (1, 'Faculty of Information and Communication Technology', 'FICT', 'Prof. A. S. Oladipo', 'dean_fict@kwasu.edu.ng', #2026-09-03 10:00:00#);
"@ "Seeded KWASU FICT"
    Exec-SQL @"
INSERT INTO tbl_Faculties (InstitutionID, FacultyName, FacultyCode, DeanName, DeanEmail, CreatedAt)
VALUES (1, 'Faculty of Pure and Applied Sciences', 'FPAS', 'Prof. M. K. Jimoh', 'dean_fpas@kwasu.edu.ng', #2026-09-03 10:30:00#);
"@ "Seeded KWASU FPAS"

    # Seed Departments for KWASU
    Exec-SQL @"
INSERT INTO tbl_Departments (InstitutionID, FacultyID, DepartmentName, DepartmentCode, HODName, HODEmail, CreatedAt)
VALUES (1, 1, 'Computer Science', 'CSC', 'Dr. B. R. Adebayo', 'hod_csc@kwasu.edu.ng', #2026-09-03 11:00:00#);
"@ "Seeded KWASU Computer Science"
    Exec-SQL @"
INSERT INTO tbl_Departments (InstitutionID, FacultyID, DepartmentName, DepartmentCode, HODName, HODEmail, CreatedAt)
VALUES (1, 1, 'Software Engineering', 'SWE', 'Dr. T. O. Bello', 'hod_swe@kwasu.edu.ng', #2026-09-03 11:15:00#);
"@ "Seeded KWASU Software Engineering"
    Exec-SQL @"
INSERT INTO tbl_Departments (InstitutionID, FacultyID, DepartmentName, DepartmentCode, HODName, HODEmail, CreatedAt)
VALUES (1, 1, 'Cyber Security', 'CYS', 'Dr. F. I. Aliyu', 'hod_cys@kwasu.edu.ng', #2026-09-03 11:30:00#);
"@ "Seeded KWASU Cyber Security"
    Exec-SQL @"
INSERT INTO tbl_Departments (InstitutionID, FacultyID, DepartmentName, DepartmentCode, HODName, HODEmail, CreatedAt)
VALUES (1, 1, 'Data Science', 'DTS', 'Dr. K. N. Ibrahim', 'hod_dts@kwasu.edu.ng', #2026-09-03 11:45:00#);
"@ "Seeded KWASU Data Science"

    # Seed Supervision Policies for KWASU
    Exec-SQL @"
INSERT INTO tbl_SupervisionPolicies (InstitutionID, DegreeLevel, SupervisorsRequired, CoSupervisorAssignmentMode, MaxChapters, MandatoryDefenseStages, DurationMonths)
VALUES (1, 'BSc', 1, 'Single_Supervisor', 5, 'Proposal, Final Defense', 9);
"@ "Seeded Policy: BSc"
    Exec-SQL @"
INSERT INTO tbl_SupervisionPolicies (InstitutionID, DegreeLevel, SupervisorsRequired, CoSupervisorAssignmentMode, MaxChapters, MandatoryDefenseStages, DurationMonths)
VALUES (1, 'PGD', 1, 'Single_Supervisor', 5, 'Proposal, Final Defense', 12);
"@ "Seeded Policy: PGD"
    Exec-SQL @"
INSERT INTO tbl_SupervisionPolicies (InstitutionID, DegreeLevel, SupervisorsRequired, CoSupervisorAssignmentMode, MaxChapters, MandatoryDefenseStages, DurationMonths)
VALUES (1, 'MSc', 2, 'Random_Or_Expertise', 5, 'Proposal, Internal Defense, External Defense', 18);
"@ "Seeded Policy: MSc (Dual Supervisor)"
    Exec-SQL @"
INSERT INTO tbl_SupervisionPolicies (InstitutionID, DegreeLevel, SupervisorsRequired, CoSupervisorAssignmentMode, MaxChapters, MandatoryDefenseStages, DurationMonths)
VALUES (1, 'PhD', 2, 'Domain_Expertise_Matching', 5, 'Proposal, Annual Seminars, Internal Defense, External Viva', 36);
"@ "Seeded Policy: PhD (Dual Supervisor)"

    # Seed Institutional Admins
    Exec-SQL @"
INSERT INTO tbl_InstitutionalAdmins (InstitutionID, FullName, Username, OfficialEmail, Phone, Designation, AdminRole, AdminApprovalCode, IsActive, CreatedAt)
VALUES (1, 'Dr. Abdullahi Musa', 'admin_kwasu', 'ict.admin@kwasu.edu.ng', '+2348031234567', 'Director of ICT', 'Institutional_SuperAdmin', 'KWASU-ADM-2026', True, #2026-09-01 09:00:00#);
"@ "Seeded KWASU Admin"

    Exec-SQL @"
INSERT INTO tbl_InstitutionalAdmins (InstitutionID, FullName, Username, OfficialEmail, Phone, Designation, AdminRole, AdminApprovalCode, IsActive, CreatedAt)
VALUES (2, 'Engr. Taiwo Adeleke', 'admin_unilorin', 'cit.head@unilorin.edu.ng', '+2348039876543', 'Director Centre for Information Technology', 'Institutional_SuperAdmin', 'UNILORIN-ADM-88', True, #2026-09-20 10:30:00#);
"@ "Seeded UNILORIN Admin"

    # Seed Tenant Databases
    Exec-SQL @"
INSERT INTO tbl_TenantDatabases (InstitutionID, IsolationModel, DatabaseHost, DatabaseName, SchemaName, StorageBucket, HealthStatus, LastHealthCheck)
VALUES (1, 'Shared_RowLevelSecurity', 'aws-0-eu-central-1.pooler.supabase.com', 'postgres', 'public', 'kwasu-spsems-storage', 'Healthy', #2026-10-01 08:00:00#);
"@ "Seeded Tenant DB: KWASU"

    Exec-SQL @"
INSERT INTO tbl_TenantDatabases (InstitutionID, IsolationModel, DatabaseHost, DatabaseName, SchemaName, StorageBucket, HealthStatus, LastHealthCheck)
VALUES (2, 'Dedicated_Schema', 'aws-0-eu-central-1.pooler.supabase.com', 'postgres', 'tenant_unilorin', 'unilorin-spsems-storage', 'Healthy', #2026-10-01 08:00:00#);
"@ "Seeded Tenant DB: UNILORIN"

    # Seed Data Imports (KWASU Batch Ingestion)
    Exec-SQL @"
INSERT INTO tbl_OnboardingDataImports (InstitutionID, BatchReference, ImportType, FileName, TotalRecords, SuccessCount, FailedCount, ImportStatus, ExecutedAt, LogDetails)
VALUES (1, 'BATCH-KWASU-FAC-01', 'Lecturers_CSV', 'kwasu_supervisors_2026.csv', 48, 48, 0, 'Completed', #2026-09-04 11:30:00#, 'Successfully imported all 48 faculty supervisors with academic ranks and research areas.');
"@ "Seeded Data Import: KWASU"

    # --------------------------------------------------------------------------
    # STEP 5: CREATING ACCESS VIEWS & QUERIES
    # --------------------------------------------------------------------------
    Write-Host "[5/6] Creating Pipeline Queries..." -ForegroundColor Cyan

    # Query 1: Schools Onboarding Overview
    $q1 = @"
SELECT 
    i.InstitutionID,
    i.InstitutionName,
    i.InstitutionCode,
    i.OfficialDomain,
    i.InstitutionType,
    i.OnboardingStatus,
    i.CurrentPipelineStage,
    i.PipelineProgressPercent,
    i.IsVerified,
    i.RegisteredAt
FROM tbl_Institutions AS i
ORDER BY i.PipelineProgressPercent DESC;
"@
    $db.CreateQueryDef("qry_SchoolsOnboardingProgress", $q1) | Out-Null
    Write-Host "      + Query: qry_SchoolsOnboardingProgress" -ForegroundColor Green

    # Query 2: Active Universities Directory
    $q2 = @"
SELECT 
    i.InstitutionName,
    i.InstitutionCode,
    i.OfficialDomain,
    i.City,
    i.StateOrProvince,
    i.ContactEmail,
    i.ContactPhone,
    s.AcademicSession,
    s.CurrentSemester,
    s.MaxSupervisorLoad,
    s.DualSupervisorForPostgrad
FROM tbl_Institutions AS i
INNER JOIN tbl_InstitutionSettings AS s ON i.InstitutionID = s.InstitutionID
WHERE i.OnboardingStatus = 'Active';
"@
    $db.CreateQueryDef("qry_ActiveInstitutionsDirectory", $q2) | Out-Null
    Write-Host "      + Query: qry_ActiveInstitutionsDirectory" -ForegroundColor Green

    # Query 3: Pending School Verifications
    $q3 = @"
SELECT 
    i.InstitutionID,
    i.InstitutionName,
    i.InstitutionCode,
    i.OfficialDomain,
    i.ContactEmail,
    i.ContactPhone,
    i.CurrentPipelineStage,
    i.RegisteredAt
FROM tbl_Institutions AS i
WHERE i.IsVerified = False OR i.OnboardingStatus = 'Pending_Verification';
"@
    $db.CreateQueryDef("qry_PendingSchoolVerifications", $q3) | Out-Null
    Write-Host "      + Query: qry_PendingSchoolVerifications" -ForegroundColor Green

    # Query 4: Department & Faculty Structure
    $q4 = @"
SELECT 
    i.InstitutionName,
    f.FacultyName,
    f.FacultyCode,
    d.DepartmentName,
    d.DepartmentCode,
    d.HODName,
    d.HODEmail
FROM (tbl_Institutions AS i
INNER JOIN tbl_Faculties AS f ON i.InstitutionID = f.InstitutionID)
INNER JOIN tbl_Departments AS d ON f.FacultyID = d.FacultyID
ORDER BY i.InstitutionName, f.FacultyName, d.DepartmentName;
"@
    $db.CreateQueryDef("qry_DepartmentsByInstitution", $q4) | Out-Null
    Write-Host "      + Query: qry_DepartmentsByInstitution" -ForegroundColor Green

    # Query 5: Supervision Rules & Policies
    $q5 = @"
SELECT 
    i.InstitutionName,
    p.DegreeLevel,
    p.SupervisorsRequired,
    p.CoSupervisorAssignmentMode,
    p.MaxChapters,
    p.MandatoryDefenseStages,
    p.DurationMonths
FROM tbl_Institutions AS i
INNER JOIN tbl_SupervisionPolicies AS p ON i.InstitutionID = p.InstitutionID
ORDER BY i.InstitutionName, p.DegreeLevel;
"@
    $db.CreateQueryDef("qry_InstitutionPolicies", $q5) | Out-Null
    Write-Host "      + Query: qry_InstitutionPolicies" -ForegroundColor Green

    Write-Host "[6/6] Database pipeline generation complete!" -ForegroundColor Green

} finally {
    if ($access) {
        $access.CloseCurrentDatabase()
        $access.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($access) | Out-Null
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }
}

Write-Host "`nSUCCESS: SPSEMS_MultiSchool_Pipeline.accdb is ready." -ForegroundColor Green
Write-Host "File location: $dbPath`n" -ForegroundColor Yellow

if ($LaunchAccess) {
    Write-Host "Launching Microsoft 365 Access..." -ForegroundColor Cyan
    $accessExe = "C:\Program Files\Microsoft Office\root\Office16\MSACCESS.EXE"
    if (Test-Path $accessExe) {
        Start-Process $accessExe -ArgumentList "`"$dbPath`""
    } else {
        Start-Process "MSACCESS.EXE" -ArgumentList "`"$dbPath`""
    }
}
