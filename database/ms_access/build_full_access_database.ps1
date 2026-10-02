# ==============================================================================
# SPSEMS - Microsoft 365 Access Full Database Pipeline Builder
# Creates SPSEMS_Full_Database_Pipeline.accdb and SPSEMS_MultiSchool_Pipeline.accdb
# Full Schema: Onboarding, Gateways, Users, Projects, Milestones, Submissions, 
#              Evaluations, ML Telemetry, SIWES, and Hostel Allocations
# ==============================================================================

param(
    [string]$OutputDir = "$PSScriptRoot",
    [switch]$LaunchAccess = $true
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$dbPath = Join-Path $OutputDir "SPSEMS_Full_Database_Pipeline.accdb"
$legacyDbPath = Join-Path $OutputDir "SPSEMS_MultiSchool_Pipeline.accdb"

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  SPSEMS - MICROSOFT 365 ACCESS FULL DATABASE PIPELINE GENERATOR   " -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "[1/7] Target Access Database: $dbPath" -ForegroundColor Yellow

# Ensure no existing MSACCESS instance locks the file
Get-Process msaccess -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 800

# Remove old files if exist
if (Test-Path $dbPath) {
    Remove-Item $dbPath -Force
}
if (Test-Path $legacyDbPath) {
    Remove-Item $legacyDbPath -Force
}

# Initialize Access COM Engine
Write-Host "[2/7] Initializing Microsoft Access 365 COM Engine..." -ForegroundColor Cyan
$access = New-Object -ComObject Access.Application
$access.Visible = $false

try {
    $access.NewCurrentDatabase($dbPath)
    $db = $access.CurrentDb()
    Write-Host "      Database initialized successfully: $dbPath" -ForegroundColor Green

    function Exec-SQL([string]$sql, [string]$desc) {
        try {
            $db.Execute($sql, 128) # dbFailOnError
            Write-Host "      [+] $desc" -ForegroundColor Gray
        } catch {
            Write-Host "      [!] Failed: $desc -> $($_.Exception.Message)" -ForegroundColor Red
            throw $_
        }
    }

    # ==========================================================================
    # 1. INSTITUTIONS & ONBOARDING SCHEMAS
    # ==========================================================================
    Write-Host "`n[3/7] Building Core Multi-Tenant & Onboarding Tables..." -ForegroundColor Cyan

    Exec-SQL @"
CREATE TABLE tbl_Institutions (
    InstitutionID AUTOINCREMENT PRIMARY KEY,
    InstitutionName TEXT(150) NOT NULL,
    InstitutionCode TEXT(20) NOT NULL,
    OfficialDomain TEXT(100) NOT NULL,
    SubdomainSlug TEXT(50) NOT NULL,
    InstitutionType TEXT(50),
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

    Exec-SQL "CREATE UNIQUE INDEX idx_inst_code ON tbl_Institutions (InstitutionCode);" "Unique index InstitutionCode"
    Exec-SQL "CREATE UNIQUE INDEX idx_inst_domain ON tbl_Institutions (OfficialDomain);" "Unique index OfficialDomain"
    Exec-SQL "CREATE UNIQUE INDEX idx_inst_slug ON tbl_Institutions (SubdomainSlug);" "Unique index SubdomainSlug"

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

    # ==========================================================================
    # 2. MULTI-PORTAL GATEWAYS (SPSEMS, SIWES, HOSTEL)
    # ==========================================================================
    Write-Host "`n[4/7] Building 3-Portal Gateways & Routing Tables..." -ForegroundColor Cyan

    Exec-SQL @"
CREATE TABLE tbl_PortalGateways (
    PortalID AUTOINCREMENT PRIMARY KEY,
    PortalCode TEXT(30) NOT NULL,
    PortalName TEXT(100) NOT NULL,
    PortalCategory TEXT(50) NOT NULL,
    DefaultRoute TEXT(100) NOT NULL,
    Description MEMO,
    IsActive YESNO
);
"@ "Created tbl_PortalGateways"

    Exec-SQL "CREATE UNIQUE INDEX idx_portal_code ON tbl_PortalGateways (PortalCode);" "Unique index PortalCode"

    Exec-SQL @"
CREATE TABLE tbl_InstitutionPortals (
    InstitutionPortalID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    PortalID INTEGER NOT NULL,
    GatewayAccessUrl TEXT(200) NOT NULL,
    GatewayAuthToken TEXT(100) NOT NULL,
    IsEnabled YESNO,
    ActivatedAt DATETIME,
    LastAccessedAt DATETIME
);
"@ "Created tbl_InstitutionPortals"

    # ==========================================================================
    # 3. ACADEMIC ENTITIES: USERS, SUPERVISORS, STUDENTS, PROJECTS
    # ==========================================================================
    Write-Host "`n[5/7] Building Academic & Research Supervision Tables..." -ForegroundColor Cyan

    Exec-SQL @"
CREATE TABLE tbl_Users (
    UserID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    Username TEXT(50) NOT NULL,
    Email TEXT(100) NOT NULL,
    FullName TEXT(100) NOT NULL,
    Role TEXT(30) NOT NULL,
    Phone TEXT(30),
    IsActive YESNO,
    CreatedAt DATETIME
);
"@ "Created tbl_Users"

    Exec-SQL "CREATE UNIQUE INDEX idx_user_email ON tbl_Users (Email);" "Unique index User Email"

    Exec-SQL @"
CREATE TABLE tbl_Supervisors (
    SupervisorID AUTOINCREMENT PRIMARY KEY,
    UserID INTEGER NOT NULL,
    InstitutionID INTEGER NOT NULL,
    Department TEXT(100) NOT NULL,
    AcademicRank TEXT(50),
    ExpertiseAreas MEMO NOT NULL,
    MaxLoad INTEGER,
    CurrentLoad INTEGER,
    CanCoSupervise YESNO,
    CreatedAt DATETIME
);
"@ "Created tbl_Supervisors"

    Exec-SQL @"
CREATE TABLE tbl_Students (
    StudentID AUTOINCREMENT PRIMARY KEY,
    UserID INTEGER NOT NULL,
    InstitutionID INTEGER NOT NULL,
    MatricNumber TEXT(40) NOT NULL,
    Department TEXT(100) NOT NULL,
    DegreeLevel TEXT(20),
    StudyLevel TEXT(20),
    PrimarySupervisorID INTEGER,
    CoSupervisorID INTEGER,
    ResearchDomain TEXT(100),
    EnrollmentYear INTEGER,
    CreatedAt DATETIME
);
"@ "Created tbl_Students"

    Exec-SQL "CREATE UNIQUE INDEX idx_student_matric ON tbl_Students (MatricNumber);" "Unique index MatricNumber"

    Exec-SQL @"
CREATE TABLE tbl_Projects (
    ProjectID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    StudentID INTEGER NOT NULL,
    PrimarySupervisorID INTEGER,
    CoSupervisorID INTEGER,
    Title TEXT(255) NOT NULL,
    Abstract MEMO,
    ResearchDomain TEXT(100),
    DegreeLevel TEXT(20),
    Status TEXT(30),
    CurrentChapter TEXT(30),
    DuplicationScore REAL,
    RiskScore REAL,
    RiskLabel TEXT(30),
    FinalGrade REAL,
    GradeLetter TEXT(5),
    SubmittedAt DATETIME,
    ApprovedAt DATETIME,
    CompletedAt DATETIME
);
"@ "Created tbl_Projects"

    Exec-SQL @"
CREATE TABLE tbl_Milestones (
    MilestoneID AUTOINCREMENT PRIMARY KEY,
    ProjectID INTEGER NOT NULL,
    MilestoneOrder INTEGER,
    Title TEXT(120) NOT NULL,
    Description TEXT(255),
    DueDate DATETIME NOT NULL,
    CompletedDate DATETIME,
    Status TEXT(30),
    Weight REAL
);
"@ "Created tbl_Milestones"

    Exec-SQL @"
CREATE TABLE tbl_Submissions (
    SubmissionID AUTOINCREMENT PRIMARY KEY,
    ProjectID INTEGER NOT NULL,
    StudentID INTEGER NOT NULL,
    Chapter TEXT(30) NOT NULL,
    FileName TEXT(150),
    VersionNumber INTEGER,
    Status TEXT(30),
    PlagiarismScore REAL,
    SupervisorComment MEMO,
    StudentNotes MEMO,
    SubmittedAt DATETIME,
    ReviewedAt DATETIME
);
"@ "Created tbl_Submissions"

    Exec-SQL @"
CREATE TABLE tbl_Evaluations (
    EvaluationID AUTOINCREMENT PRIMARY KEY,
    ProjectID INTEGER NOT NULL,
    SupervisorID INTEGER NOT NULL,
    ProblemFormulation REAL,
    LiteratureReview REAL,
    Methodology REAL,
    ImplementationResult REAL,
    Documentation REAL,
    DefencePresentation REAL,
    TotalScore REAL,
    GradeLetter TEXT(5),
    FeedbackNotes MEMO,
    TurnaroundDays REAL,
    EvaluatedAt DATETIME
);
"@ "Created tbl_Evaluations"

    # ==========================================================================
    # 4. AI & ML PIPELINE TELEMETRY & TRAINING AUDIT
    # ==========================================================================
    Write-Host "`n[6/7] Building Live AI Telemetry & ML Pipeline Tables..." -ForegroundColor Cyan

    Exec-SQL @"
CREATE TABLE tbl_ML_Feature_Telemetry (
    TelemetryID AUTOINCREMENT PRIMARY KEY,
    ProjectID INTEGER NOT NULL,
    StudentID INTEGER NOT NULL,
    InstitutionCode TEXT(20),
    SubmissionRate REAL,
    DaysSinceLastSubmission INTEGER,
    MilestoneCompletionRate REAL,
    OverdueMilestones INTEGER,
    SupervisorFeedbackResponseDays REAL,
    ChapterProgress INTEGER,
    TimeProgressRatio REAL,
    StagnationZScore REAL,
    TotalSubmissions INTEGER,
    ChaptersRemaining INTEGER,
    GroundTruthRiskLabel TEXT(30),
    ExtractedAt DATETIME
);
"@ "Created tbl_ML_Feature_Telemetry"

    Exec-SQL @"
CREATE TABLE tbl_ML_Model_Predictions (
    PredictionID AUTOINCREMENT PRIMARY KEY,
    ProjectID INTEGER NOT NULL,
    ModelName TEXT(50) NOT NULL,
    PredictionType TEXT(50),
    InputFeaturesJson MEMO,
    PredictedRiskScore REAL,
    PredictedRiskLabel TEXT(30),
    Confidence REAL,
    PredictedAt DATETIME
);
"@ "Created tbl_ML_Model_Predictions"

    Exec-SQL @"
CREATE TABLE tbl_ML_Pipeline_Runs (
    RunID AUTOINCREMENT PRIMARY KEY,
    InstitutionCode TEXT(20),
    SourceType TEXT(40),
    ConnectionInfo TEXT(150),
    SamplesExtracted INTEGER,
    SamplesTrained INTEGER,
    XGBAccuracy REAL,
    XGBF1 REAL,
    RFAccuracy REAL,
    RFF1 REAL,
    Status TEXT(30),
    Summary MEMO,
    ExecutedAt DATETIME
);
"@ "Created tbl_ML_Pipeline_Runs"

    # ==========================================================================
    # 5. SUB-PORTALS: SIWES (IT PLACEMENT) & HOSTEL ALLOCATION
    # ==========================================================================
    Exec-SQL @"
CREATE TABLE tbl_SIWES_Placements (
    PlacementID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    StudentID INTEGER NOT NULL,
    CompanyName TEXT(150) NOT NULL,
    CompanyAddress TEXT(200),
    City TEXT(60),
    StateOrProvince TEXT(60),
    IndustrySupervisorName TEXT(100),
    IndustrySupervisorEmail TEXT(100),
    AcademicSupervisorID INTEGER,
    LogbooksSubmitted INTEGER,
    LogbooksVerified INTEGER,
    PerformanceScore REAL,
    PlacementStatus TEXT(30),
    CommencedAt DATETIME,
    CompletedAt DATETIME
);
"@ "Created tbl_SIWES_Placements"

    Exec-SQL @"
CREATE TABLE tbl_Hostel_Allocations (
    AllocationID AUTOINCREMENT PRIMARY KEY,
    InstitutionID INTEGER NOT NULL,
    StudentID INTEGER NOT NULL,
    AcademicSession TEXT(20),
    HostelHallName TEXT(100) NOT NULL,
    HostelBlock TEXT(20) NOT NULL,
    RoomNumber TEXT(20) NOT NULL,
    BedSpaceNumber TEXT(10) NOT NULL,
    AllocationStatus TEXT(30),
    FeeAmount REAL,
    PaymentStatus TEXT(30),
    CheckInDate DATETIME,
    CheckOutDate DATETIME
);
"@ "Created tbl_Hostel_Allocations"

    # ==========================================================================
    # 6. SEED COMPREHENSIVE PRODUCTION DATA
    # ==========================================================================
    Write-Host "`n[7/7] Seeding Production Relational Data Across All Systems..." -ForegroundColor Cyan

    # 1. Institutions
    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt, ActivatedAt)
VALUES
('Kwara State University', 'KWASU', 'kwasu.edu.ng', 'kwasu', 'State University', 'Nigeria', 'Kwara', 'Malete', 'ict@kwasu.edu.ng', '+2348030000001', '/kwasu.png', '#16a34a', '#080808', 'Active', True, '7_Live_Activation', 100, #2026-09-01 09:00:00#, #2026-09-06 14:00:00#);
"@ "Seeded Institution: KWASU (Active)"

    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt)
VALUES
('University of Ilorin', 'UNILORIN', 'unilorin.edu.ng', 'unilorin', 'Federal University', 'Nigeria', 'Kwara', 'Ilorin', 'director_citng@unilorin.edu.ng', '+2348030000002', '/unilorin.png', '#1d4ed8', '#0f172a', 'Configuring', True, '4_Department_Setup', 65, #2026-09-20 10:30:00#);
"@ "Seeded Institution: UNILORIN"

    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt)
VALUES
('University of Ibadan', 'UI', 'ui.edu.ng', 'ui', 'Federal University', 'Nigeria', 'Oyo', 'Ibadan', 'pgschool@ui.edu.ng', '+2348030000003', '/ui.png', '#b45309', '#1e293b', 'Pending_Verification', False, '2_Domain_Verification', 30, #2026-09-27 11:15:00#);
"@ "Seeded Institution: UI"

    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt)
VALUES
('Obafemi Awolowo University', 'OAU', 'oauife.edu.ng', 'oau', 'Federal University', 'Nigeria', 'Osun', 'Ile-Ife', 'dean_pg@oauife.edu.ng', '+2348030000004', '/oau.png', '#047857', '#0f172a', 'Provisioned', True, '3_Tenant_Provisioning', 45, #2026-09-25 08:45:00#);
"@ "Seeded Institution: OAU"

    Exec-SQL @"
INSERT INTO tbl_Institutions 
(InstitutionName, InstitutionCode, OfficialDomain, SubdomainSlug, InstitutionType, Country, StateOrProvince, City, ContactEmail, ContactPhone, LogoUrl, PrimaryColor, SecondaryColor, OnboardingStatus, IsVerified, CurrentPipelineStage, PipelineProgressPercent, RegisteredAt)
VALUES
('Kwara State Polytechnic', 'KWAPOLY', 'kwarapoly.edu.ng', 'kwapoly', 'State Polytechnic', 'Nigeria', 'Kwara', 'Ilorin', 'rector@kwarapoly.edu.ng', '+2348030000005', '/kwapoly.png', '#7c3aed', '#111827', 'Configuring', True, '5_Faculty_Import', 80, #2026-09-22 13:00:00#);
"@ "Seeded Institution: KWAPOLY"

    # 2. Portal Gateways (The 3 Gateways)
    Exec-SQL @"
INSERT INTO tbl_PortalGateways (PortalCode, PortalName, PortalCategory, DefaultRoute, Description, IsActive)
VALUES ('SPSEMS', 'Smart Project Supervision & Evaluation System', 'Academic Research', '/portal/spsems', 'Central thesis dissertation tracking, milestone pacing, plagiarism detection, and AI risk prediction.', True);
"@ "Seeded Gateway 1: SPSEMS"

    Exec-SQL @"
INSERT INTO tbl_PortalGateways (PortalCode, PortalName, PortalCategory, DefaultRoute, Description, IsActive)
VALUES ('SIWES', 'SIWES & IT Industrial Placement Portal', 'Internship & Fieldwork', '/portal/siwes', 'Industrial training placement coordination, weekly e-logbook verification, and supervisor field assessments.', True);
"@ "Seeded Gateway 2: SIWES"

    Exec-SQL @"
INSERT INTO tbl_PortalGateways (PortalCode, PortalName, PortalCategory, DefaultRoute, Description, IsActive)
VALUES ('HOSTEL', 'Hostel Bed Space Allocation Portal', 'Student Accommodation', '/portal/hostel', 'Campus residence management, real-time bed space reservations, clearance, and hall master check-ins.', True);
"@ "Seeded Gateway 3: HOSTEL"

    # Gateway Bindings for KWASU (Institution 1)
    Exec-SQL @"
INSERT INTO tbl_InstitutionPortals (InstitutionID, PortalID, GatewayAccessUrl, GatewayAuthToken, IsEnabled, ActivatedAt, LastAccessedAt)
VALUES (1, 1, 'https://kwasu.spsems.edu.ng/portal/spsems', 'GATEWAY-KWASU-SPSEMS-9981', True, #2026-09-06 14:00:00#, #2026-10-02 20:00:00#);
"@ "Seeded KWASU -> SPSEMS Gateway"

    Exec-SQL @"
INSERT INTO tbl_InstitutionPortals (InstitutionID, PortalID, GatewayAccessUrl, GatewayAuthToken, IsEnabled, ActivatedAt, LastAccessedAt)
VALUES (1, 2, 'https://kwasu.spsems.edu.ng/portal/siwes', 'GATEWAY-KWASU-SIWES-3312', True, #2026-09-10 10:00:00#, #2026-10-02 18:30:00#);
"@ "Seeded KWASU -> SIWES Gateway"

    Exec-SQL @"
INSERT INTO tbl_InstitutionPortals (InstitutionID, PortalID, GatewayAccessUrl, GatewayAuthToken, IsEnabled, ActivatedAt, LastAccessedAt)
VALUES (1, 3, 'https://kwasu.spsems.edu.ng/portal/hostel', 'GATEWAY-KWASU-HOSTEL-5541', True, #2026-09-12 11:00:00#, #2026-10-02 19:15:00#);
"@ "Seeded KWASU -> HOSTEL Gateway"

    # 3. Settings & Policies
    Exec-SQL @"
INSERT INTO tbl_InstitutionSettings 
(InstitutionID, AcademicSession, CurrentSemester, MaxSupervisorLoad, DualSupervisorForPostgrad, AutoAssignCoSupervisor, EnableAIPairing, AllowPublicStudentRegistration, AllowPublicLecturerRegistration, RequireAdminApproval, MinimumAbstractWordCount, PlagiarismCheckThreshold, UpdatedAt)
VALUES
(1, '2025/2026', 'First Semester', 10, True, True, True, True, True, True, 50, 20, #2026-10-01 08:00:00#);
"@ "Seeded Settings: KWASU"

    Exec-SQL @"
INSERT INTO tbl_SupervisionPolicies (InstitutionID, DegreeLevel, SupervisorsRequired, CoSupervisorAssignmentMode, MaxChapters, MandatoryDefenseStages, DurationMonths)
VALUES (1, 'BSc', 1, 'Single_Supervisor', 5, 'Proposal, Final Defense', 9);
"@ "Seeded Policy: BSc"

    Exec-SQL @"
INSERT INTO tbl_SupervisionPolicies (InstitutionID, DegreeLevel, SupervisorsRequired, CoSupervisorAssignmentMode, MaxChapters, MandatoryDefenseStages, DurationMonths)
VALUES (1, 'MSc', 2, 'Random_Or_Expertise', 5, 'Proposal, Internal Defense, External Defense', 18);
"@ "Seeded Policy: MSc (Dual Supervision)"

    Exec-SQL @"
INSERT INTO tbl_SupervisionPolicies (InstitutionID, DegreeLevel, SupervisorsRequired, CoSupervisorAssignmentMode, MaxChapters, MandatoryDefenseStages, DurationMonths)
VALUES (1, 'PhD', 2, 'Domain_Expertise_Matching', 5, 'Proposal, Annual Seminars, Internal Defense, External Viva', 36);
"@ "Seeded Policy: PhD (Dual Supervision)"

    # 4. Faculties & Departments
    Exec-SQL @"
INSERT INTO tbl_Faculties (InstitutionID, FacultyName, FacultyCode, DeanName, DeanEmail, CreatedAt)
VALUES (1, 'Faculty of Information and Communication Technology', 'FICT', 'Prof. A. S. Oladipo', 'dean_fict@kwasu.edu.ng', #2026-09-03 10:00:00#);
"@ "Seeded KWASU Faculty: FICT"

    Exec-SQL @"
INSERT INTO tbl_Departments (InstitutionID, FacultyID, DepartmentName, DepartmentCode, HODName, HODEmail, CreatedAt)
VALUES (1, 1, 'Computer Science', 'CSC', 'Dr. B. R. Adebayo', 'hod_csc@kwasu.edu.ng', #2026-09-03 11:00:00#);
"@ "Seeded KWASU Dept: Computer Science"

    Exec-SQL @"
INSERT INTO tbl_Departments (InstitutionID, FacultyID, DepartmentName, DepartmentCode, HODName, HODEmail, CreatedAt)
VALUES (1, 1, 'Software Engineering', 'SWE', 'Dr. T. O. Bello', 'hod_swe@kwasu.edu.ng', #2026-09-03 11:15:00#);
"@ "Seeded KWASU Dept: Software Engineering"

    # 5. Users, Supervisors & Students
    # Admins
    Exec-SQL @"
INSERT INTO tbl_Users (InstitutionID, Username, Email, FullName, Role, Phone, IsActive, CreatedAt)
VALUES (1, 'admin_kwasu', 'ict.admin@kwasu.edu.ng', 'Dr. Abdullahi Musa', 'admin', '+2348031234567', True, #2026-09-01 09:00:00#);
"@ "Seeded User: KWASU Admin"

    # Supervisors
    Exec-SQL @"
INSERT INTO tbl_Users (InstitutionID, Username, Email, FullName, Role, Phone, IsActive, CreatedAt)
VALUES (1, 'prof_oladipo', 'a.oladipo@kwasu.edu.ng', 'Prof. Abubakar S. Oladipo', 'supervisor', '+2348035550001', True, #2026-09-03 09:00:00#);
"@ "Seeded User: Prof Oladipo"

    Exec-SQL @"
INSERT INTO tbl_Supervisors (UserID, InstitutionID, Department, AcademicRank, ExpertiseAreas, MaxLoad, CurrentLoad, CanCoSupervise, CreatedAt)
VALUES (2, 1, 'Computer Science', 'Professor', 'Machine Learning, NLP, Distributed Systems', 10, 3, True, #2026-09-03 09:15:00#);
"@ "Seeded Supervisor 1"

    Exec-SQL @"
INSERT INTO tbl_Users (InstitutionID, Username, Email, FullName, Role, Phone, IsActive, CreatedAt)
VALUES (1, 'dr_adebayo', 'b.adebayo@kwasu.edu.ng', 'Dr. Beatrice R. Adebayo', 'supervisor', '+2348035550002', True, #2026-09-03 09:20:00#);
"@ "Seeded User: Dr Adebayo"

    Exec-SQL @"
INSERT INTO tbl_Supervisors (UserID, InstitutionID, Department, AcademicRank, ExpertiseAreas, MaxLoad, CurrentLoad, CanCoSupervise, CreatedAt)
VALUES (3, 1, 'Computer Science', 'Senior Lecturer', 'Cybersecurity, Cryptography, Network Protocols', 8, 4, True, #2026-09-03 09:30:00#);
"@ "Seeded Supervisor 2"

    Exec-SQL @"
INSERT INTO tbl_Users (InstitutionID, Username, Email, FullName, Role, Phone, IsActive, CreatedAt)
VALUES (1, 'dr_bello', 't.bello@kwasu.edu.ng', 'Dr. Tunde O. Bello', 'supervisor', '+2348035550003', True, #2026-09-03 09:40:00#);
"@ "Seeded User: Dr Bello"

    Exec-SQL @"
INSERT INTO tbl_Supervisors (UserID, InstitutionID, Department, AcademicRank, ExpertiseAreas, MaxLoad, CurrentLoad, CanCoSupervise, CreatedAt)
VALUES (4, 1, 'Software Engineering', 'Senior Lecturer', 'Cloud Computing, Microservices, Software Architecture', 8, 3, True, #2026-09-03 09:45:00#);
"@ "Seeded Supervisor 3"

    # Students (BSc, MSc, PhD)
    # Student 1: BSc (Single Supervisor)
    Exec-SQL @"
INSERT INTO tbl_Users (InstitutionID, Username, Email, FullName, Role, Phone, IsActive, CreatedAt)
VALUES (1, 'kwasu_std_01', 's.zainab@kwasu.edu.ng', 'Zainab Aminu Salihu', 'student', '+2348120000001', True, #2026-09-10 10:00:00#);
"@ "Seeded User: Student Zainab"

    Exec-SQL @"
INSERT INTO tbl_Students (UserID, InstitutionID, MatricNumber, Department, DegreeLevel, StudyLevel, PrimarySupervisorID, CoSupervisorID, ResearchDomain, EnrollmentYear, CreatedAt)
VALUES (5, 1, 'KWASU/2021/CSC/042', 'Computer Science', 'BSc', '400', 1, NULL, 'Artificial Intelligence', 2026, #2026-09-10 10:15:00#);
"@ "Seeded Student 1: Zainab (BSc)"

    # Student 2: MSc (Dual Supervision: Primary + Random Co-Supervisor)
    Exec-SQL @"
INSERT INTO tbl_Users (InstitutionID, Username, Email, FullName, Role, Phone, IsActive, CreatedAt)
VALUES (1, 'kwasu_std_02', 'i.fatai@kwasu.edu.ng', 'Fatai Ibrahim Olawale', 'student', '+2348120000002', True, #2026-09-11 11:00:00#);
"@ "Seeded User: Student Fatai"

    Exec-SQL @"
INSERT INTO tbl_Students (UserID, InstitutionID, MatricNumber, Department, DegreeLevel, StudyLevel, PrimarySupervisorID, CoSupervisorID, ResearchDomain, EnrollmentYear, CreatedAt)
VALUES (6, 1, 'KWASU/PG2025/MSc/018', 'Computer Science', 'MSc', 'Postgraduate', 1, 2, 'Applied Machine Learning in Healthcare', 2026, #2026-09-11 11:15:00#);
"@ "Seeded Student 2: Fatai (MSc Dual Supervisor)"

    # Student 3: PhD (Dual Supervision: Primary + Domain Matching Co-Supervisor)
    Exec-SQL @"
INSERT INTO tbl_Users (InstitutionID, Username, Email, FullName, Role, Phone, IsActive, CreatedAt)
VALUES (1, 'kwasu_std_03', 'e.chinedu@kwasu.edu.ng', 'Chinedu Emmanuel Okafor', 'student', '+2348120000003', True, #2026-09-12 12:00:00#);
"@ "Seeded User: Student Chinedu"

    Exec-SQL @"
INSERT INTO tbl_Students (UserID, InstitutionID, MatricNumber, Department, DegreeLevel, StudyLevel, PrimarySupervisorID, CoSupervisorID, ResearchDomain, EnrollmentYear, CreatedAt)
VALUES (7, 1, 'KWASU/PG2024/PhD/004', 'Computer Science', 'PhD', 'Doctoral', 2, 3, 'Zero-Trust Cloud Cryptography', 2026, #2026-09-12 12:15:00#);
"@ "Seeded Student 3: Chinedu (PhD Dual Supervisor)"

    # 6. Projects & Research
    Exec-SQL @"
INSERT INTO tbl_Projects 
(InstitutionID, StudentID, PrimarySupervisorID, CoSupervisorID, Title, Abstract, ResearchDomain, DegreeLevel, Status, CurrentChapter, DuplicationScore, RiskScore, RiskLabel, SubmittedAt, ApprovedAt)
VALUES
(1, 1, 1, NULL, 'Smart Project Supervision & Evaluation Management System using Predictive ML', 'This research develops an automated, ML-powered supervision tracker for university dissertations.', 'Machine Learning', 'BSc', 'in_progress', 'chapter3', 4.2, 0.12, 'on_track', #2026-09-15 14:00:00#, #2026-09-18 10:00:00#);
"@ "Seeded Project 1: Zainab"

    Exec-SQL @"
INSERT INTO tbl_Projects 
(InstitutionID, StudentID, PrimarySupervisorID, CoSupervisorID, Title, Abstract, ResearchDomain, DegreeLevel, Status, CurrentChapter, DuplicationScore, RiskScore, RiskLabel, SubmittedAt, ApprovedAt)
VALUES
(1, 2, 1, 2, 'Deep Learning Framework for Early Diabetic Retinopathy Detection in Rural Clinics', 'A multi-modal convolutional network designed for low-resource ophthalmic diagnostics.', 'Applied Machine Learning', 'MSc', 'in_progress', 'chapter2', 2.8, 0.45, 'at_risk', #2026-09-16 11:00:00#, #2026-09-20 09:30:00#);
"@ "Seeded Project 2: Fatai (MSc)"

    Exec-SQL @"
INSERT INTO tbl_Projects 
(InstitutionID, StudentID, PrimarySupervisorID, CoSupervisorID, Title, Abstract, ResearchDomain, DegreeLevel, Status, CurrentChapter, DuplicationScore, RiskScore, RiskLabel, SubmittedAt, ApprovedAt)
VALUES
(1, 3, 2, 3, 'Decentralized Zero-Knowledge Identity Verification for Multi-Tenant Academic Clouds', 'A mathematical and protocol study on privacy-preserving credential issuance.', 'Cryptography & Cloud', 'PhD', 'in_progress', 'chapter4', 1.5, 0.08, 'on_track', #2026-09-14 09:00:00#, #2026-09-17 11:00:00#);
"@ "Seeded Project 3: Chinedu (PhD)"

    # 7. Milestones & Submissions
    Exec-SQL @"
INSERT INTO tbl_Milestones (ProjectID, MilestoneOrder, Title, Description, DueDate, CompletedDate, Status, Weight)
VALUES (1, 1, 'Proposal Defense', 'Formal defense of problem formulation and scope', #2026-09-20#, #2026-09-19#, 'completed', 15);
"@ "Seeded Milestone 1"

    Exec-SQL @"
INSERT INTO tbl_Milestones (ProjectID, MilestoneOrder, Title, Description, DueDate, CompletedDate, Status, Weight)
VALUES (1, 2, 'Chapter 1 & 2: Literature Review', 'Comprehensive synthesis of relevant publications', #2026-09-28#, #2026-09-27#, 'completed', 20);
"@ "Seeded Milestone 2"

    Exec-SQL @"
INSERT INTO tbl_Milestones (ProjectID, MilestoneOrder, Title, Description, DueDate, CompletedDate, Status, Weight)
VALUES (1, 3, 'Chapter 3: System Methodology', 'System architecture, UML schemas, and data pipelines', #2026-10-15#, NULL, 'pending', 25);
"@ "Seeded Milestone 3"

    Exec-SQL @"
INSERT INTO tbl_Submissions (ProjectID, StudentID, Chapter, FileName, VersionNumber, Status, PlagiarismScore, SupervisorComment, StudentNotes, SubmittedAt, ReviewedAt)
VALUES (1, 1, 'chapter2', 'KWASU_CSC_042_Chapter2_Final.pdf', 2, 'approved', 3.8, 'Very thorough literature analysis. You may proceed to Chapter 3.', 'Incorporated supervisor suggestions on ML benchmarks.', #2026-09-26 16:30:00#, #2026-09-27 10:15:00#);
"@ "Seeded Submission 1"

    # 8. Evaluations
    Exec-SQL @"
INSERT INTO tbl_Evaluations (ProjectID, SupervisorID, ProblemFormulation, LiteratureReview, Methodology, ImplementationResult, Documentation, DefencePresentation, TotalScore, GradeLetter, FeedbackNotes, TurnaroundDays, EvaluatedAt)
VALUES (1, 1, 18.5, 19.0, 18.0, 17.5, 19.0, 18.5, 90.5, 'A', 'Outstanding performance, clearly defined research goals.', 1.8, #2026-09-27 10:15:00#);
"@ "Seeded Evaluation 1"

    # 9. ML Behavioral Telemetry & Retraining Audit
    Exec-SQL @"
INSERT INTO tbl_ML_Feature_Telemetry 
(ProjectID, StudentID, InstitutionCode, SubmissionRate, DaysSinceLastSubmission, MilestoneCompletionRate, OverdueMilestones, SupervisorFeedbackResponseDays, ChapterProgress, TimeProgressRatio, StagnationZScore, TotalSubmissions, ChaptersRemaining, GroundTruthRiskLabel, ExtractedAt)
VALUES
(1, 1, 'KWASU', 1.45, 5, 0.67, 0, 1.8, 3, 0.42, -0.65, 5, 2, 'on_track', #2026-10-02 20:00:00#);
"@ "Seeded ML Telemetry 1 (Zainab)"

    Exec-SQL @"
INSERT INTO tbl_ML_Feature_Telemetry 
(ProjectID, StudentID, InstitutionCode, SubmissionRate, DaysSinceLastSubmission, MilestoneCompletionRate, OverdueMilestones, SupervisorFeedbackResponseDays, ChapterProgress, TimeProgressRatio, StagnationZScore, TotalSubmissions, ChaptersRemaining, GroundTruthRiskLabel, ExtractedAt)
VALUES
(2, 2, 'KWASU', 0.55, 19, 0.33, 1, 4.2, 2, 0.65, 1.25, 2, 3, 'at_risk', #2026-10-02 20:00:00#);
"@ "Seeded ML Telemetry 2 (Fatai)"

    Exec-SQL @"
INSERT INTO tbl_ML_Model_Predictions (ProjectID, ModelName, PredictionType, InputFeaturesJson, PredictedRiskScore, PredictedRiskLabel, Confidence, PredictedAt)
VALUES (1, 'xgboost_risk_classifier', 'risk_score', '{""submission_rate"":1.45,""days_since_last_submission"":5}', 0.12, 'on_track', 0.96, #2026-10-02 20:10:00#);
"@ "Seeded ML Prediction"

    Exec-SQL @"
INSERT INTO tbl_ML_Pipeline_Runs 
(InstitutionCode, SourceType, ConnectionInfo, SamplesExtracted, SamplesTrained, XGBAccuracy, XGBF1, RFAccuracy, RFF1, Status, Summary, ExecutedAt)
VALUES
('KWASU', 'live_database', 'sqlite:///backend/spsems.db', 20, 50, 1.0, 1.0, 1.0, 1.0, 'completed', 'Trained on 20 authentic institutional student records with balanced distribution augmentation.', #2026-10-02 21:19:00#);
"@ "Seeded ML Pipeline Run Audit"

    # 10. Gateway 2: SIWES Placements
    Exec-SQL @"
INSERT INTO tbl_SIWES_Placements 
(InstitutionID, StudentID, CompanyName, CompanyAddress, City, StateOrProvince, IndustrySupervisorName, IndustrySupervisorEmail, AcademicSupervisorID, LogbooksSubmitted, LogbooksVerified, PerformanceScore, PlacementStatus, CommencedAt)
VALUES
(1, 1, 'MainOne Cables Nigeria Ltd', 'Victoria Island', 'Lagos', 'Lagos', 'Engr. K. Balogun', 'k.balogun@mainone.net', 1, 8, 8, 92.0, 'Completed', #2025-06-01 08:00:00#);
"@ "Seeded SIWES Placement"

    # 11. Gateway 3: Hostel Allocations
    Exec-SQL @"
INSERT INTO tbl_Hostel_Allocations 
(InstitutionID, StudentID, AcademicSession, HostelHallName, HostelBlock, RoomNumber, BedSpaceNumber, AllocationStatus, FeeAmount, PaymentStatus, CheckInDate)
VALUES
(1, 1, '2025/2026', 'Queen Amina Hall', 'Block B', 'B-104', 'Bed-2', 'Allocated', 45000.0, 'Paid', #2025-10-15 10:00:00#);
"@ "Seeded Hostel Allocation"

    # ==========================================================================
    # STEP 6: CREATING ACCESS VIEWS & QUERIES
    # ==========================================================================
    Write-Host "`nCreating Pre-Configured Relational Queries..." -ForegroundColor Cyan

    # Q1: Schools Onboarding Overview
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
    Write-Host "      [+] Query: qry_SchoolsOnboardingProgress" -ForegroundColor Green

    # Q2: Gateway Portals Directory (SPSEMS, SIWES, HOSTEL)
    $q2 = @"
SELECT 
    i.InstitutionName,
    i.InstitutionCode,
    g.PortalCode,
    g.PortalName,
    g.PortalCategory,
    p.GatewayAccessUrl,
    p.GatewayAuthToken,
    p.IsEnabled,
    p.LastAccessedAt
FROM (tbl_Institutions AS i
INNER JOIN tbl_InstitutionPortals AS p ON i.InstitutionID = p.InstitutionID)
INNER JOIN tbl_PortalGateways AS g ON p.PortalID = g.PortalID
ORDER BY i.InstitutionCode, g.PortalCode;
"@
    $db.CreateQueryDef("qry_PortalGatewayDirectory", $q2) | Out-Null
    Write-Host "      [+] Query: qry_PortalGatewayDirectory" -ForegroundColor Green

    # Q3: Full Project Supervision & Risk Status
    $q3 = @"
SELECT 
    p.ProjectID,
    i.InstitutionCode,
    s.MatricNumber,
    u.FullName AS StudentName,
    p.DegreeLevel,
    p.Title AS ProjectTitle,
    sup1.FullName AS PrimarySupervisor,
    p.CurrentChapter,
    p.RiskScore,
    p.RiskLabel,
    p.Status AS ProjectStatus
FROM (((tbl_Projects AS p
INNER JOIN tbl_Institutions AS i ON p.InstitutionID = i.InstitutionID)
INNER JOIN tbl_Students AS s ON p.StudentID = s.StudentID)
INNER JOIN tbl_Users AS u ON s.UserID = u.UserID)
LEFT JOIN tbl_Users AS sup1 ON p.PrimarySupervisorID = sup1.UserID;
"@
    $db.CreateQueryDef("qry_FullProjectSupervisionStatus", $q3) | Out-Null
    Write-Host "      [+] Query: qry_FullProjectSupervisionStatus" -ForegroundColor Green

    # Q4: Dual Supervisor Postgraduates (MSc / PhD)
    $q4 = @"
SELECT 
    s.MatricNumber,
    u.FullName AS StudentName,
    s.DegreeLevel,
    s.Department,
    s.ResearchDomain,
    u1.FullName AS PrimarySupervisor,
    u2.FullName AS CoSupervisor
FROM (((tbl_Students AS s
INNER JOIN tbl_Users AS u ON s.UserID = u.UserID)
LEFT JOIN tbl_Users AS u1 ON s.PrimarySupervisorID = u1.UserID)
LEFT JOIN tbl_Users AS u2 ON s.CoSupervisorID = u2.UserID)
WHERE s.DegreeLevel IN ('MSc', 'PhD');
"@
    $db.CreateQueryDef("qry_DualSupervisorPostgraduates", $q4) | Out-Null
    Write-Host "      [+] Query: qry_DualSupervisorPostgraduates" -ForegroundColor Green

    # Q5: Live AI / ML Behavioral Telemetry Matrix
    $q5 = @"
SELECT 
    t.TelemetryID,
    t.InstitutionCode,
    s.MatricNumber,
    p.Title AS ProjectTitle,
    t.SubmissionRate,
    t.DaysSinceLastSubmission,
    t.MilestoneCompletionRate,
    t.OverdueMilestones,
    t.SupervisorFeedbackResponseDays,
    t.ChapterProgress,
    t.TimeProgressRatio,
    t.StagnationZScore,
    t.TotalSubmissions,
    t.ChaptersRemaining,
    t.GroundTruthRiskLabel,
    t.ExtractedAt
FROM ((tbl_ML_Feature_Telemetry AS t
INNER JOIN tbl_Projects AS p ON t.ProjectID = p.ProjectID)
INNER JOIN tbl_Students AS s ON t.StudentID = s.StudentID)
ORDER BY t.ExtractedAt DESC;
"@
    $db.CreateQueryDef("qry_ML_LiveStudentRiskTelemetry", $q5) | Out-Null
    Write-Host "      [+] Query: qry_ML_LiveStudentRiskTelemetry" -ForegroundColor Green

    # Q6: Milestone Progress & Delays
    $q6 = @"
SELECT 
    p.ProjectID,
    p.Title,
    m.MilestoneOrder,
    m.Title AS MilestoneTitle,
    m.DueDate,
    m.CompletedDate,
    m.Status,
    m.Weight
FROM tbl_Milestones AS m
INNER JOIN tbl_Projects AS p ON m.ProjectID = p.ProjectID
ORDER BY p.ProjectID, m.MilestoneOrder;
"@
    $db.CreateQueryDef("qry_MilestoneProgressAndDelays", $q6) | Out-Null
    Write-Host "      [+] Query: qry_MilestoneProgressAndDelays" -ForegroundColor Green

    # Q7: Submissions & Supervisor Latency
    $q7 = @"
SELECT 
    p.Title AS ProjectTitle,
    sub.Chapter,
    sub.FileName,
    sub.VersionNumber,
    sub.PlagiarismScore,
    sub.Status,
    sub.SubmittedAt,
    sub.ReviewedAt,
    e.TurnaroundDays,
    e.TotalScore,
    e.GradeLetter
FROM (tbl_Submissions AS sub
INNER JOIN tbl_Projects AS p ON sub.ProjectID = p.ProjectID)
LEFT JOIN tbl_Evaluations AS e ON p.ProjectID = e.ProjectID
ORDER BY sub.SubmittedAt DESC;
"@
    $db.CreateQueryDef("qry_SubmissionsAndSupervisorLatency", $q7) | Out-Null
    Write-Host "      [+] Query: qry_SubmissionsAndSupervisorLatency" -ForegroundColor Green

    # Q8: SIWES Placements
    $q8 = @"
SELECT 
    i.InstitutionCode,
    s.MatricNumber,
    u.FullName AS StudentName,
    si.CompanyName,
    si.City,
    si.IndustrySupervisorName,
    si.LogbooksSubmitted,
    si.LogbooksVerified,
    si.PerformanceScore,
    si.PlacementStatus
FROM ((tbl_SIWES_Placements AS si
INNER JOIN tbl_Institutions AS i ON si.InstitutionID = i.InstitutionID)
INNER JOIN tbl_Students AS s ON si.StudentID = s.StudentID)
INNER JOIN tbl_Users AS u ON s.UserID = u.UserID;
"@
    $db.CreateQueryDef("qry_SIWES_PlacementDirectory", $q8) | Out-Null
    Write-Host "      [+] Query: qry_SIWES_PlacementDirectory" -ForegroundColor Green

    # Q9: Hostel Allocations
    $q9 = @"
SELECT 
    i.InstitutionCode,
    s.MatricNumber,
    u.FullName AS StudentName,
    h.AcademicSession,
    h.HostelHallName,
    h.HostelBlock,
    h.RoomNumber,
    h.BedSpaceNumber,
    h.FeeAmount,
    h.PaymentStatus,
    h.AllocationStatus
FROM ((tbl_Hostel_Allocations AS h
INNER JOIN tbl_Institutions AS i ON h.InstitutionID = i.InstitutionID)
INNER JOIN tbl_Students AS s ON h.StudentID = s.StudentID)
INNER JOIN tbl_Users AS u ON s.UserID = u.UserID;
"@
    $db.CreateQueryDef("qry_Hostel_AllocationSummary", $q9) | Out-Null
    Write-Host "      [+] Query: qry_Hostel_AllocationSummary" -ForegroundColor Green

    Write-Host "`nAll tables, relationships, seed records, and analytical queries built successfully!" -ForegroundColor Green

} finally {
    if ($access) {
        $access.CloseCurrentDatabase()
        $access.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($access) | Out-Null
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }
}

# Duplicate / Mirror to SPSEMS_MultiSchool_Pipeline.accdb as well
Copy-Item -Path $dbPath -Destination $legacyDbPath -Force
Write-Host "Mirrored full database to $legacyDbPath" -ForegroundColor Green

Write-Host "`n===================================================================" -ForegroundColor Green
Write-Host "  SUCCESS: FULL MICROSOFT 365 ACCESS DATABASE PIPELINE COMPLETED!  " -ForegroundColor Green
Write-Host "===================================================================" -ForegroundColor Green
Write-Host "Primary Database: $dbPath" -ForegroundColor Yellow
Write-Host "Mirrored Database: $legacyDbPath" -ForegroundColor Yellow

if ($LaunchAccess) {
    Write-Host "`nLaunching Microsoft 365 Access Desktop Application..." -ForegroundColor Cyan
    $accessExe = "C:\Program Files\Microsoft Office\root\Office16\MSACCESS.EXE"
    if (Test-Path $accessExe) {
        Start-Process $accessExe -ArgumentList "`"$dbPath`""
    } else {
        Start-Process "MSACCESS.EXE" -ArgumentList "`"$dbPath`""
    }
    Write-Host "Microsoft Access 365 is now OPEN on your desktop with the full database pipeline." -ForegroundColor Green
}
