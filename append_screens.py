import os
import sys

# Load build_and_deploy_70_screens.py and append the full metadata and execution logic
with open(r"C:\Users\legen\OneDrive\Desktop\proj contd\spsems\build_and_deploy_70_screens.py", "a", encoding="utf-8") as f:
    f.write('''
# ─────────────────────────────────────────────────────────────────────────────
# COMPLETE 70 SCREEN SPECIFICATION CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────

ALL_SCREENS = [
    # ── CATEGORY 1: PLATFORM FRONT DOOR & ONBOARDING (1 - 6) ──
    {
        "id": "CS-01", "title": "Main Landing Page Hero", "portal": "CampusSphere", "role": "Public Visitor", "route": "/",
        "db": "tbl_Institutions", "color": "#8B5CF6", "compliance": "NUC Accreditation Baseline §1.0", "archetype": "dashboard",
        "subtitle": "Unified Higher Education Operating System Front-Door",
        "metrics": [("Active Universities", "42 Verified", "+8 this term"), ("Enrolled Scholars", "85,420 Active", "99.8% Uptime"), ("Research Throughput", "₦4.8B Managed", "TETFund Compliant")],
        "table_title": "Accredited Higher Institution Network (Active Gateways)",
        "table_headers": ["Institution", "State", "Active Portals", "Accreditation", "Actions"],
        "table_rows": [
            ["Kwara State University (KWASU)", "Kwara", "SPSEMS • SIWES • HOSTEL", "NUC Full 2024", "Enter Portal →"],
            ["University of Ilorin (UNILORIN)", "Kwara", "SPSEMS • SIWES", "NUC Full 2024", "Enter Portal →"],
            ["Federal University Lokoja (FUL)", "Kogi", "SPSEMS Only", "NUC Full 2023", "Enter Portal →"],
            ["Landmark University (LU)", "Kwara", "HOSTEL • SIWES", "NUC Full 2024", "Provisioning →"]
        ]
    },
    {
        "id": "CS-02", "title": "Institutional Directory Side Panel", "portal": "CampusSphere", "role": "Public Visitor", "route": "/directory",
        "db": "tbl_Institutions", "color": "#8B5CF6", "compliance": "Federal Education Registry Audit §2.4", "archetype": "dashboard",
        "subtitle": "Accredited University Subdomain Directory & Search",
        "metrics": [("Federal Campuses", "18 Connected", "NUC Validated"), ("State Campuses", "16 Connected", "Full Compliance"), ("Private Campuses", "8 Connected", "ISO Certified")],
        "table_title": "Directory Search & Filtering Index",
        "table_headers": ["Code", "Institution Name", "Vice-Chancellor / Contact", "Domain Route", "Actions"],
        "table_rows": [
            ["KWASU", "Kwara State University, Malete", "Prof. M. M. Akanbi (VC)", "kwasu.campussphere.edu.ng", "Select Tenant →"],
            ["UNILORIN", "University of Ilorin", "Prof. W. O. Egbewole (VC)", "unilorin.campussphere.edu.ng", "Select Tenant →"],
            ["OAU", "Obafemi Awolowo University", "Prof. A. S. Bamire (VC)", "oau.campussphere.edu.ng", "Select Tenant →"],
            ["ABU", "Ahmadu Bello University", "Prof. K. Bala (VC)", "abu.campussphere.edu.ng", "Select Tenant →"]
        ]
    },
    {
        "id": "CS-03", "title": "Clean-Slate Zero State", "portal": "CampusSphere", "role": "System Admin", "route": "/directory/clean-slate",
        "db": "tbl_Institutions", "color": "#8B5CF6", "compliance": "Zero-Tenant Isolation Initial State", "archetype": "clean_slate",
        "subtitle": "Pioneer Institution Onboarding Launchpad (0 Institutions Registered)"
    },
    {
        "id": "CS-04", "title": "Onboarding Step 1: Profile & Domain", "portal": "Onboarding", "role": "University Registrar", "route": "/onboard/step-1",
        "db": "tbl_Institutions", "color": "#8B5CF6", "compliance": "NUC Identity Gazette Validation", "archetype": "auth",
        "subtitle": "University Identity, Official Emblem & DNS Subdomain Reservation",
        "auth_headline": "Pioneer Institution Onboarding",
        "auth_description": "Establish your university identity on the national higher education operating system.",
        "form_title": "Register University Profile",
        "form_subtitle": "Step 1 of 4: Primary Identity & Subdomain Allocation",
        "form_inputs": [
            ("Official University Name (Gazette)", "Kwara State University, Malete"),
            ("Institutional Acronym & Subdomain Slug", "kwasu (.campussphere.edu.ng)"),
            ("Registrar Official Verification Email", "registrar@kwasu.edu.ng")
        ],
        "btn_label": "Save Profile & Proceed to Step 2 →"
    },
    {
        "id": "CS-05", "title": "Onboarding Step 2: Academic Hierarchy", "portal": "Onboarding", "role": "Academic Planning", "route": "/onboard/step-2",
        "db": "tbl_Faculties", "color": "#8B5CF6", "compliance": "NUC Benchmark Minimum Academic Standards (BMAS)", "archetype": "dashboard",
        "subtitle": "Faculties, Departments & Postgraduate Degree Program Seeding",
        "metrics": [("Faculties Seeded", "8 Faculties", "BMAS Aligned"), ("Departments", "42 Departments", "Postgrad Active"), ("Degree Programs", "18 MSc / 12 PhD", "NUC Approved")],
        "table_title": "Configured Academic Faculties & Quotas",
        "table_headers": ["Faculty Name", "Departments Count", "Postgraduate Degrees", "Dean of Faculty", "Actions"],
        "table_rows": [
            ["Faculty of Information & Comm. Tech", "4 Departments", "MSc CS, PhD CS, MSc Cyber", "Prof. I. A. Bello", "Configure Depts →"],
            ["Faculty of Engineering & Technology", "6 Departments", "MEng Mechanical, Civil, Electrical", "Prof. K. A. Adeleke", "Configure Depts →"],
            ["Faculty of Pure & Applied Sciences", "8 Departments", "MSc Biochemistry, Microbiology", "Prof. H. O. Salami", "Configure Depts →"],
            ["Faculty of Management & Social Sciences", "7 Departments", "MSc Accounting, MBA, PhD Econ", "Prof. S. O. Balogun", "Configure Depts →"]
        ]
    },
    {
        "id": "CS-06", "title": "Onboarding Step 3 & 4: Policies & Portals", "portal": "Onboarding", "role": "University Registrar", "route": "/onboard/step-3",
        "db": "tbl_InstitutionSettings", "color": "#8B5CF6", "compliance": "Senate Regulations & Multi-Portal Licensure", "archetype": "dashboard",
        "subtitle": "Turnitin Cutoff Limits, Supervisor Quotas & Portal Activation Toggles",
        "metrics": [("SPSEMS Portal", "ACTIVATED (Tier 1)", "Dissertations Active"), ("SIWES Portal", "PENDING INTEGRATION", "Beta License"), ("HOSTEL Portal", "PENDING INTEGRATION", "Staging Matrix")],
        "table_title": "Enforced Academic Policy Thresholds",
        "table_headers": ["Parameter", "Configured Limit", "Regulatory Baseline", "Enforcement Engine", "Actions"],
        "table_rows": [
            ["Turnitin Similarity Limit", "15% Maximum Overlap", "NUC Guideline <= 20%", "Automated Document Lock", "Adjust Limit"],
            ["Max Supervisees Per Professor", "5 Postgraduate Scholars", "Senate Policy 2024", "AI Quota Enforcement", "Adjust Quota"],
            ["Defense Grading Rubric", "100-Point Standard", "Postgraduate Board", "Digital Examination Panel", "Edit Rubric"],
            ["Plagiarism Action Threshold", "Auto-Reject on 3rd Submission", "Academic Integrity Council", "Disciplinary Committee Flag", "View Policy"]
        ]
    },

    # ── CATEGORY 2: TENANT GATEWAYS (7 - 10) ──
    {
        "id": "GW-01", "title": "University Multi-Portal Selection Hub", "portal": "Gateway", "role": "Institutional Member", "route": "/login/:slug",
        "db": "tbl_Institutions", "color": "#3B82F6", "compliance": "Federated Multi-Portal Routing Framework", "archetype": "dashboard",
        "subtitle": "Kwara State University Central Access Hub & Gateway Selector",
        "metrics": [("Active Session", "2024/2025 Harmattan", "Live"), ("Campus Users", "18,420 Enrolled", "SSO Active"), ("Security Tier", "ISO 27001 Certified", "MFA Enforced")],
        "table_title": "Available University Portals & Service Workstations",
        "table_headers": ["Portal Designation", "Service Domain", "Target Demographics", "Access Clearance", "Actions"],
        "table_rows": [
            ["PORTAL 01: SPSEMS", "Postgraduate Dissertation & Thesis Defense", "PG Students, Supervisors, Dean", "ACTIVE & INTEGRATED", "Enter SPSEMS Gateway →"],
            ["PORTAL 02: SIWES", "Industrial Attachment & Placement Logbook", "Undergraduates, Industry Staff, Coord.", "ACTIVE & INTEGRATED", "Enter SIWES Gateway →"],
            ["PORTAL 03: HOSTEL", "Hall Accommodation & 3D Bed Matrix", "All Students, Wardens, Housing Dir.", "ACTIVE & INTEGRATED", "Enter HOSTEL Gateway →"],
            ["CENTRAL SSO", "Unified Identity & Active Directory", "All University Staff & Students", "ACTIVE & VERIFIED", "Manage Profile →"]
        ]
    },
    {
        "id": "GW-02", "title": "University Single-Sign-On Gateway", "portal": "Gateway", "role": "All Users", "route": "/login/:slug/sso",
        "db": "tbl_Users", "color": "#3B82F6", "compliance": "OAuth 2.0 / OpenID Connect Enterprise Protocol", "archetype": "auth",
        "subtitle": "Centralized Active Directory & Microsoft 365 Authentication",
        "auth_headline": "University Central SSO Gateway",
        "auth_description": "Sign in once with your official university credentials to access SPSEMS, SIWES, and HOSTEL.",
        "form_title": "Institutional Single Sign-On",
        "form_subtitle": "Microsoft 365 & Google Workspace Unified Authentication",
        "form_inputs": [
            ("Institutional Email Address", "username@kwasu.edu.ng"),
            ("Campus Password", "••••••••••••••••"),
            ("Two-Factor Authentication Code", "481 920")
        ],
        "btn_label": "Authenticate Session →"
    },
    {
        "id": "GW-03", "title": "Institution Portal Provisioning Hub", "portal": "Gateway", "role": "ICT Director", "route": "/admin/:slug/portals",
        "db": "tbl_InstitutionSettings", "color": "#3B82F6", "compliance": "Semester Lifecycle & Module Governance", "archetype": "dashboard",
        "subtitle": "Tenant Licensing & Semester-by-Semester Portal Enablement",
        "metrics": [("Active Modules", "3 / 3 Portals Live", "All Verified"), ("API Latency", "14 ms Mean", "Zero Drift"), ("Database Health", "16 Tables Synced", "ADODB Bridge")],
        "table_title": "Campus Portal Enablement & Module Lifecycle",
        "table_headers": ["Module Name", "License Tier", "Concurrency Limit", "Health Telemetry", "Actions"],
        "table_rows": [
            ["SPSEMS Dissertation Supervision", "Enterprise Unlimited", "1,500 Concurrent Defenses", "Healthy (11ms)", "Module Settings →"],
            ["SIWES Industrial Work Scheme", "Campus Enterprise", "3,500 Active Trainees", "Healthy (14ms)", "Module Settings →"],
            ["HOSTEL Smart Residential Matrix", "Campus Enterprise", "8,500 Managed Beds", "Healthy (9ms)", "Module Settings →"],
            ["Access ADODB Two-Way Sync Engine", "Core Background Worker", "16 Relational Tables", "100% Consistent", "Force Resync →"]
        ]
    },
    {
        "id": "GW-04", "title": "Cross-Portal Identity Switcher", "portal": "Gateway", "role": "Student / Staff", "route": "/user/account-switcher",
        "db": "tbl_Users", "color": "#3B82F6", "compliance": "Identity Token Federation (JWT RSA-256)", "archetype": "dashboard",
        "subtitle": "Seamless Session Switching Across SPSEMS, SIWES, and HOSTEL",
        "metrics": [("Active Identities", "2 Connected Profiles", "Single Sign-On"), ("Current Token", "JWT RSA-256", "Valid 8h"), ("Security Posture", "Fingerprint Verified", "Malete, Nigeria")],
        "table_title": "Active Federated Portal Workspaces",
        "table_headers": ["Portal Designation", "Associated Identity", "Primary Role", "Department / Unit", "Actions"],
        "table_rows": [
            ["SPSEMS Dissertation Portal", "Adeyemi Bashir (20/52CS/0084)", "MSc Candidate", "Computer Science", "Switch Workspace →"],
            ["HOSTEL Accommodation Portal", "Adeyemi Bashir (20/52CS/0084)", "Resident Scholar", "Hall A, Room 104, Bunk A", "Switch Workspace →"],
            ["SIWES Industrial Portal (Archive)", "Adeyemi Bashir (18/52CS/0012)", "Completed Trainee", "TotalEnergies Placement", "View Logbook →"],
            ["University Bursary Account", "Adeyemi Bashir (Student Account)", "Tuition Verified", "University Bursary", "View Receipts →"]
        ]
    },

    # ── CATEGORY 3: SPSEMS PORTAL (11 - 28) ──
    # Student Pathway (11 - 18)
    {
        "id": "SP-ST-01", "title": "Student SPSEMS Login", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/:slug/login/student",
        "db": "tbl_Students", "color": "#10B981", "compliance": "Postgraduate Matriculation Authentication Standard", "archetype": "auth",
        "subtitle": "Postgraduate Scholar Dissertation Workstation Access",
        "auth_headline": "SPSEMS Scholar Workstation",
        "auth_description": "Access your dissertation draft, split-screen feedback, Turnitin reports, and defense scheduling.",
        "form_title": "Sign in as Postgraduate Scholar",
        "form_subtitle": "Enter your Postgraduate Matriculation Number & Security PIN",
        "form_inputs": [
            ("Postgraduate Matriculation Number", "20/52CS/0084"),
            ("Dissertation Security Key / PIN", "••••••••••••••••"),
            ("Current Academic Session", "2024/2025 Harmattan Semester")
        ],
        "btn_label": "Enter Dissertation Workspace →"
    },
    {
        "id": "SP-ST-02", "title": "Dissertation Command Center", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/dashboard",
        "db": "tbl_Projects", "color": "#10B981", "compliance": "NUC 5-Stage Dissertation Progression Framework", "archetype": "dashboard",
        "subtitle": "5-Stage Milestone Tracker, Supervisor Allocation & Turnitin Telemetry",
        "metrics": [("Milestone Progress", "Stage 4 of 5", "Results & Discussion"), ("Turnitin Similarity", "11.4% Overlap", "Threshold <= 15%"), ("Assigned Supervisor", "Prof. I. A. Bello", "Feedback Logged")],
        "table_title": "Dissertation Milestone Progression Tracker",
        "table_headers": ["Milestone Stage", "Deliverable Scope", "Submission Date", "Review State", "Actions"],
        "table_rows": [
            ["Stage 1: Proposal & Concept Note", "Problem formulation and research domain", "12-JAN-2024", "Senate Approved", "View Certificate →"],
            ["Stage 2: Literature Synthesis", "Chapter 2 theoretical review & prior art", "15-APR-2024", "Approved by Supervisor", "View Diffs →"],
            ["Stage 3: Research Methodology", "Chapter 3 mathematical formulation & design", "02-JUL-2024", "Approved by Supervisor", "View Diffs →"],
            ["Stage 4: Experimental Results", "Chapter 4 benchmark evaluation & data", "14-OCT-2024", "Under Active Review", "Open Annotator →"],
            ["Stage 5: Oral Viva Defense", "Final dissertation defense before external panel", "PENDING", "Awaiting Clearance", "Pre-Defense Prep →"]
        ]
    },
    {
        "id": "SP-ST-03", "title": "Topic & Concept Note Studio", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/proposal",
        "db": "tbl_Projects", "color": "#10B981", "compliance": "Postgraduate Board Research Vetting Policy", "archetype": "dashboard",
        "subtitle": "Research Title Registration, Abstract Submission & Keyword Vector Tagging",
        "metrics": [("Topic Status", "APPROVED BY HOD", "Computer Science"), ("Research Domain", "Artificial Intelligence", "Multi-Agent Systems"), ("Vector Match Score", "96.4% Cosine", "Supervisor Aligned")],
        "table_title": "Submitted Research Proposals & Revision History",
        "table_headers": ["Submission Ref", "Proposed Research Topic", "Submission Date", "Committee Verdict", "Actions"],
        "table_rows": [
            ["PROP-2024-0084-v2", "Autonomous Multi-Agent Orchestration for Higher Education Systems", "12-JAN-2024", "APPROVED AS SUBMITTED", "View Approval Form →"],
            ["PROP-2024-0084-v1", "Multi-Agent Systems in University Management", "10-DEC-2023", "REVISE & RESUBMIT", "View Comments →"]
        ]
    },
    {
        "id": "SP-ST-04", "title": "Chapter Vault & Version Diffs", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/chapters",
        "db": "tbl_Submissions", "color": "#10B981", "compliance": "Document Immutability & Git-Style Differential Tracking", "archetype": "annotator",
        "subtitle": "Chapter 1 to 5 Digital Repository with Cryptographic Hash History"
    },
    {
        "id": "SP-ST-05", "title": "Split-Screen Thesis Annotator", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/feedback",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "Double-Blind Digital Thesis Annotation Standard", "archetype": "annotator",
        "subtitle": "Interactive PDF Reader with Real-Time Supervisor Comments & Revision Threads"
    },
    {
        "id": "SP-ST-06", "title": "Plagiarism Similarity Audit", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/plagiarism",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "NUC 15% Maximum Similarity Threshold Mandate", "archetype": "turnitin",
        "subtitle": "Turnitin Integration Engine, Matched Source Repositories & Excerpt Highlighter"
    },
    {
        "id": "SP-ST-07", "title": "Defense Timetable & Panel", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/defense",
        "db": "tbl_Projects", "color": "#10B981", "compliance": "Senate Postgraduate Examination Regulations", "archetype": "defense_rubric",
        "subtitle": "Final Oral Viva Timetable, Examination Panel & Slide Presentation Uploader"
    },
    {
        "id": "SP-ST-08", "title": "Final Archival & Clearance", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/clearance",
        "db": "tbl_Projects", "color": "#10B981", "compliance": "University Senate Final Degree Award Policy", "archetype": "dashboard",
        "subtitle": "Final Hardbound Copy Deposition, Library Clearance & Graduation Pass-List",
        "metrics": [("Defense Result", "PASSED (DISTINCTION)", "Grade A (93.0)"), ("Library Deposition", "VERIFIED (ARCHIVE)", "e-Library ID #8841"), ("Senate Approval", "RECOMMENDED", "Order Paper Ready")],
        "table_title": "Institutional Graduation Clearance Stations",
        "table_headers": ["Clearance Unit", "Required Verification", "Certifying Officer", "Status", "Actions"],
        "table_rows": [
            ["Departmental Clearance", "All revisions completed and certified", "Dr. A. M. Jimoh (HOD)", "PASSED & SIGNED", "View Endorsement →"],
            ["Postgraduate School", "Turnitin <=15% and defense rubric verified", "Dean PG School", "PASSED & SIGNED", "View Endorsement →"],
            ["University Library", "Final bound dissertation deposited", "University Librarian", "PASSED & SIGNED", "View Receipt →"],
            ["University Bursary", "All postgraduate tuition and defense fees cleared", "University Bursar", "PASSED & SIGNED", "View Receipt →"]
        ]
    },

    # Supervisor Pathway (19 - 23)
    {
        "id": "SP-SV-01", "title": "Supervisor Authentication", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/:slug/login/supervisor",
        "db": "tbl_Supervisors", "color": "#10B981", "compliance": "Staff Multi-Factor Authentication Protocol", "archetype": "auth",
        "subtitle": "Senior Academic Supervisor & Professorial Workstation Sign-In",
        "auth_headline": "Academic Supervisor Portal",
        "auth_description": "Review candidate chapter submissions, annotate drafts, and issue cryptographic milestone sign-offs.",
        "form_title": "Sign in as Academic Supervisor",
        "form_subtitle": "Enter your University Staff ID & Faculty Token",
        "form_inputs": [
            ("University Staff ID Number", "STAFF/KWASU/CS/042"),
            ("Faculty Security Token / PIN", "••••••••••••••••"),
            ("Selected Academic Session", "2024/2025 Harmattan Semester")
        ],
        "btn_label": "Enter Supervisory Workstation →"
    },
    {
        "id": "SP-SV-02", "title": "Supervision Caseload Radar", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/supervisor/dashboard",
        "db": "tbl_Supervisors", "color": "#10B981", "compliance": "Senate Workload Ratio (Max 5 Supervisees)", "archetype": "dashboard",
        "subtitle": "Active Candidates Overview, Pending Chapter Reviews & Quota Health",
        "metrics": [("Active Supervisees", "4 Active Scholars", "Senate Quota: 5 Max"), ("Pending Chapter Drafts", "2 Drafts Awaiting Review", "Average Turnaround 3d"), ("Milestones Signed", "12 Approved", "Cryptographic Sign-Off")],
        "table_title": "Assigned Postgraduate Supervisees Caseload",
        "table_headers": ["Candidate Name", "Degree Program", "Current Milestone", "Submission Date", "Actions"],
        "table_rows": [
            ["Adeyemi Bashir (20/52CS/0084)", "MSc Computer Science", "Chapter 4: Results & Discussion", "14-OCT-2024", "Review Draft →"],
            ["Fatima Garba (21/52CS/0012)", "PhD Cyber Security", "Chapter 3: Methodology", "10-OCT-2024", "Review Draft →"],
            ["Chukwuma Obi (20/52CS/0091)", "MSc Data Science", "Chapter 2: Lit Review", "05-OCT-2024", "Review Draft →"],
            ["Zainab Aliyu (21/52CS/0034)", "MSc Artificial Intelligence", "Concept Proposal", "01-OCT-2024", "Approved →"]
        ]
    },
    {
        "id": "SP-SV-03", "title": "Document Annotation Studio", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/supervisor/review/:id",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "Digital Thesis Annotation & Revision Mandate", "archetype": "annotator",
        "subtitle": "In-Depth PDF Markup, Inline Sticky Notes & Correction Guidance Studio"
    },
    {
        "id": "SP-SV-04", "title": "Milestone Sign-Off Studio", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/supervisor/milestones",
        "db": "tbl_Milestones", "color": "#10B981", "compliance": "Cryptographic Non-Repudiation Electronic Sign-Off", "archetype": "dashboard",
        "subtitle": "Digital Approval Keys & Progression Authorization for Senate Pass-List",
        "metrics": [("Awaiting Sign-Off", "1 Candidate Ready", "Chapter 4 Certified"), ("Signed This Semester", "8 Milestones", "100% On Time"), ("Average Turnaround", "3.2 Days", "Benchmark < 5d")],
        "table_title": "Milestones Ready for Formal Supervisory Endorsement",
        "table_headers": ["Candidate", "Milestone Stage", "Turnitin Index", "Supervisor Verdict", "Actions"],
        "table_rows": [
            ["Adeyemi Bashir (20/52CS/0084)", "Stage 4: Results & Discussion", "11.4% (Passed)", "REVISIONS CERTIFIED", "Affix Digital Key →"],
            ["Fatima Garba (21/52CS/0012)", "Stage 3: Formal Methodology", "8.9% (Passed)", "APPROVED FOR DEFENSE", "Affix Digital Key →"]
        ]
    },
    {
        "id": "SP-SV-05", "title": "Pre-Defense Evaluation Rubric", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/supervisor/defense-grading",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "Postgraduate Examination Board Standard 100-Point Rubric", "archetype": "defense_rubric",
        "subtitle": "Methodology Rigor, Originality, Literature Mastery & Viva Readiness Grading"
    },

    # Admin / Dean Pathway (24 - 28)
    {
        "id": "SP-AD-01", "title": "PG School Command Center", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/dashboard",
        "db": "tbl_Institutions", "color": "#10B981", "compliance": "Institutional Research Governance & Quality Assurance", "archetype": "dashboard",
        "subtitle": "University-Wide Dissertation Velocity, Defense Radar & Faculty Analytics",
        "metrics": [("Total Dissertations", "184 Active", "Across 8 Faculties"), ("Average Turnitin", "11.8% Clean", "Threshold <= 15%"), ("Scheduled Defenses", "28 Defenses", "This Quarter")],
        "table_title": "Faculty Postgraduate Research Overview",
        "table_headers": ["Faculty", "Active Dissertations", "Supervisors Engaged", "Mean Turnitin %", "Actions"],
        "table_rows": [
            ["Information & Comm. Technology", "42 Dissertations", "14 Supervisors", "10.4%", "View Faculty →"],
            ["Engineering & Technology", "54 Dissertations", "18 Supervisors", "11.2%", "View Faculty →"],
            ["Pure & Applied Sciences", "48 Dissertations", "16 Supervisors", "12.1%", "View Faculty →"],
            ["Management & Social Sciences", "40 Dissertations", "12 Supervisors", "13.4%", "View Faculty →"]
        ]
    },
    {
        "id": "SP-AD-02", "title": "AI Supervisor Allocation Engine", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/allocation",
        "db": "tbl_AllocationHistory", "color": "#10B981", "compliance": "Algorithmic Fairness & Workload Distribution Directive", "archetype": "ai_allocation",
        "subtitle": "Cosine Similarity Vector Matching & Supervisee Quota Optimization Engine"
    },
    {
        "id": "SP-AD-03", "title": "Defense Board & Panel Builder", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/defense-panels",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "External Examiner Accreditation Criteria", "archetype": "defense_rubric",
        "subtitle": "External & Internal Examiner Assignment, Zoom Integration & Timetabling"
    },
    {
        "id": "SP-AD-04", "title": "Academic Policy Configuration", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/settings",
        "db": "tbl_InstitutionSettings", "color": "#10B981", "compliance": "Senate Regulations Update Authority", "archetype": "dashboard",
        "subtitle": "Turnitin Cutoff (15%), Supervisor Load (5:1) & Resubmission Penalties",
        "metrics": [("Plagiarism Limit", "15% Max Overlap", "Enforced Strict"), ("Supervisor Ratio", "5 Supervisees Max", "Enforced Strict"), ("Turnaround SLA", "5 Business Days", "Automated Alerts")],
        "table_title": "Senate Policy Parameters Registry",
        "table_headers": ["Policy Directive", "Configured Baseline", "Enforcement Rule", "Audit Status", "Actions"],
        "table_rows": [
            ["Turnitin Maximum Similarity Limit", "15% Maximum", "Block defense booking if > 15%", "VERIFIED SENATE 2024", "Modify Value →"],
            ["Faculty Supervisor Quota", "5 Candidates Max", "AI engine skips staff with 5 loads", "VERIFIED SENATE 2024", "Modify Value →"],
            ["External Examiner Honorarium", "Approved Scale", "Bursary Remita automated disbursement", "VERIFIED SENATE 2024", "Modify Value →"]
        ]
    },
    {
        "id": "SP-AD-05", "title": "SPSEMS System Audit Trail", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/audit",
        "db": "tbl_AuditLog", "color": "#10B981", "compliance": "Tamper-Evident SHA-256 Ledger Requirement", "archetype": "dashboard",
        "subtitle": "Cryptographic Event Log of Submissions, Reviews, Scores & Endorsements",
        "metrics": [("Total Audited Events", "148,200 Events", "Zero Gaps"), ("Cryptographic Integrity", "SHA-256 Verified", "100% Immutable"), ("Failed Auth Attempts", "0 Security Breaches", "Firewall Active")],
        "table_title": "Real-Time Telemetry & Event Audit Ledger",
        "table_headers": ["Timestamp", "Officer / User", "Event Description", "Cryptographic Hash", "Actions"],
        "table_rows": [
            ["14-OCT-2024 14:35:12", "Prof. I. A. Bello", "Approved Chapter 4 Milestone for Adeyemi Bashir", "sha256:7f8a9b2...", "Verify Signature →"],
            ["14-OCT-2024 11:20:05", "Turnitin Engine", "Generated 11.4% Similarity Report for Draft v4.1", "sha256:3c4d5e6...", "Inspect Hash →"],
            ["12-OCT-2024 09:15:44", "Dean PG School", "Ratified External Examiner for Oral Defense Panel", "sha256:1a2b3c4...", "Inspect Hash →"]
        ]
    }
]

# Write remainder of 70 screens (SIWES 29-46, HOSTEL 47-65, ENGINES 66-70)
print(f"Loaded initial {len(ALL_SCREENS)} screens metadata.")
''')

print("Appended first batch of screens.")
