"""
backend/init_db.py
Automatic database initialization and self-healing.
Ensures all required tables, columns, and initial demo accounts exist
on startup for both SQLite and PostgreSQL.
"""

import os
import sys
import json
from datetime import datetime
import bcrypt
from sqlalchemy import text
from database import engine

def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password[:72].encode(), bcrypt.gensalt()).decode()

SQLITE_TABLES = [
    ("institutions", """
        CREATE TABLE IF NOT EXISTS institutions (
          institution_id     INTEGER PRIMARY KEY AUTOINCREMENT,
          name               TEXT NOT NULL,
          code               TEXT NOT NULL UNIQUE,
          slug               TEXT NOT NULL UNIQUE,
          official_domain    TEXT NOT NULL UNIQUE,
          institution_type   TEXT DEFAULT 'State University',
          country            TEXT DEFAULT 'Nigeria',
          state              TEXT,
          city               TEXT,
          contact_email      TEXT NOT NULL,
          contact_phone      TEXT,
          logo_url           TEXT DEFAULT '/kwasu.png',
          primary_color      TEXT DEFAULT '#16a34a',
          secondary_color    TEXT DEFAULT '#080808',
          status             TEXT DEFAULT 'active',
          verification_token TEXT,
          is_verified        INTEGER DEFAULT 1,
          current_stage      TEXT DEFAULT '7_live_activation',
          onboarding_percent INTEGER DEFAULT 100,
          created_at         TEXT DEFAULT (datetime('now')),
          verified_at        TEXT,
          activated_at       TEXT
        )
    """),
    ("institution_settings", """
        CREATE TABLE IF NOT EXISTS institution_settings (
          setting_id                   INTEGER PRIMARY KEY AUTOINCREMENT,
          institution_id               INTEGER NOT NULL UNIQUE,
          academic_session             TEXT DEFAULT '2025/2026',
          current_semester             TEXT DEFAULT 'First Semester',
          max_supervisor_load          INTEGER DEFAULT 10,
          dual_supervisor_for_postgrad INTEGER DEFAULT 1,
          auto_assign_co_supervisor    INTEGER DEFAULT 1,
          enable_ai_pairing            INTEGER DEFAULT 1,
          allow_public_student_reg     INTEGER DEFAULT 1,
          allow_public_lecturer_reg    INTEGER DEFAULT 1,
          require_admin_approval       INTEGER DEFAULT 1,
          updated_at                   TEXT DEFAULT (datetime('now')),
          FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE
        )
    """),
    ("tenant_onboarding_pipeline", """
        CREATE TABLE IF NOT EXISTS tenant_onboarding_pipeline (
          pipeline_id     INTEGER PRIMARY KEY AUTOINCREMENT,
          institution_id  INTEGER NOT NULL,
          stage_order     INTEGER NOT NULL,
          stage_code      TEXT NOT NULL,
          stage_name      TEXT NOT NULL,
          status          TEXT DEFAULT 'pending',
          required_action TEXT,
          started_at      TEXT,
          completed_at    TEXT,
          executed_by     TEXT,
          error_message   TEXT,
          FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE
        )
    """),
    ("users", """
        CREATE TABLE IF NOT EXISTS users (
          user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
          username   TEXT    NOT NULL UNIQUE,
          email      TEXT    NOT NULL UNIQUE,
          password   TEXT    NOT NULL,
          role       TEXT    NOT NULL CHECK(role IN ('student','supervisor','admin')),
          full_name  TEXT    NOT NULL,
          phone      TEXT,
          is_active  INTEGER DEFAULT 1,
          avatar_url TEXT,
          created_at TEXT    DEFAULT (datetime('now')),
          updated_at TEXT    DEFAULT (datetime('now'))
        )
    """),
    ("supervisors", """
        CREATE TABLE IF NOT EXISTS supervisors (
          supervisor_id   INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id         INTEGER NOT NULL UNIQUE,
          department      TEXT    NOT NULL DEFAULT 'Computer Science',
          expertise_areas TEXT    NOT NULL,
          expertise_vector TEXT,
          max_load        INTEGER DEFAULT 5,
          current_load    INTEGER DEFAULT 0,
          bio             TEXT,
          created_at      TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """),
    ("students", """
        CREATE TABLE IF NOT EXISTS students (
          student_id       INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id          INTEGER NOT NULL UNIQUE,
          matric_number    TEXT    NOT NULL UNIQUE,
          department       TEXT    NOT NULL DEFAULT 'Computer Science',
          level            TEXT    DEFAULT '400',
          supervisor_id    INTEGER,
          co_supervisor_id INTEGER,
          project_id       INTEGER,
          research_domain  TEXT,
          enrollment_year  INTEGER,
          created_at       TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (user_id)          REFERENCES users(user_id)            ON DELETE CASCADE,
          FOREIGN KEY (supervisor_id)    REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
          FOREIGN KEY (co_supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE SET NULL
        )
    """),
    ("projects", """
        CREATE TABLE IF NOT EXISTS projects (
          project_id        INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id        INTEGER NOT NULL,
          supervisor_id     INTEGER,
          co_supervisor_id  INTEGER,
          title             TEXT    NOT NULL,
          abstract          TEXT,
          keywords          TEXT,
          keyword_vector    TEXT,
          status            TEXT    DEFAULT 'pending'   CHECK(status IN ('pending','approved','in_progress','completed','rejected')),
          duplication_score REAL    DEFAULT 0,
          risk_score        REAL    DEFAULT 0,
          risk_label        TEXT    DEFAULT 'on_track'  CHECK(risk_label IN ('on_track','at_risk','critical')),
          final_grade       REAL,
          grade_letter      TEXT,
          submitted_at      TEXT    DEFAULT (datetime('now')),
          approved_at       TEXT,
          completed_at      TEXT,
          updated_at        TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (student_id)       REFERENCES students(student_id)       ON DELETE CASCADE,
          FOREIGN KEY (supervisor_id)    REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
          FOREIGN KEY (co_supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE SET NULL
        )
    """),
    ("milestones", """
        CREATE TABLE IF NOT EXISTS milestones (
          milestone_id   INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id     INTEGER NOT NULL,
          title          TEXT    NOT NULL,
          description    TEXT,
          due_date       TEXT    NOT NULL,
          completed_date TEXT,
          status         TEXT    DEFAULT 'pending' CHECK(status IN ('pending','completed','overdue','missed')),
          weight         REAL    DEFAULT 10,
          created_at     TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        )
    """),
    ("submissions", """
        CREATE TABLE IF NOT EXISTS submissions (
          doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id         INTEGER NOT NULL,
          student_id         INTEGER NOT NULL,
          chapter            TEXT    NOT NULL CHECK(chapter IN ('proposal','chapter1','chapter2','chapter3','chapter4','chapter5','final')),
          file_name          TEXT,
          file_path          TEXT,
          file_size          INTEGER,
          version            INTEGER DEFAULT 1,
          status             TEXT    DEFAULT 'submitted' CHECK(status IN ('submitted','under_review','approved','revision_requested')),
          supervisor_comment TEXT,
          student_notes      TEXT,
          submitted_at       TEXT    DEFAULT (datetime('now')),
          uploaded_at        TEXT    DEFAULT (datetime('now')),
          reviewed_at        TEXT,
          FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
          FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
        )
    """),
    ("alerts", """
        CREATE TABLE IF NOT EXISTS alerts (
          alert_id     INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id      INTEGER NOT NULL,
          project_id   INTEGER,
          alert_type   TEXT    NOT NULL CHECK(alert_type IN ('deadline','inactivity','risk','feedback','system','ping','milestone_due','overdue','risk_detected','allocation')),
          title        TEXT    NOT NULL,
          message      TEXT    NOT NULL,
          severity     TEXT    DEFAULT 'info' CHECK(severity IN ('info','warning','critical')),
          is_read      INTEGER DEFAULT 0,
          triggered_at TEXT    DEFAULT (datetime('now')),
          created_at   TEXT    DEFAULT (datetime('now')),
          read_at      TEXT,
          FOREIGN KEY (user_id)    REFERENCES users(user_id)       ON DELETE CASCADE,
          FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL
        )
    """),
    ("messages", """
        CREATE TABLE IF NOT EXISTS messages (
          message_id  INTEGER PRIMARY KEY AUTOINCREMENT,
          msg_id      INTEGER,
          sender_id   INTEGER NOT NULL,
          receiver_id INTEGER NOT NULL,
          project_id  INTEGER,
          subject     TEXT,
          body        TEXT    NOT NULL,
          is_read     INTEGER DEFAULT 0,
          sent_at     TEXT    DEFAULT (datetime('now')),
          created_at  TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (sender_id)   REFERENCES users(user_id)       ON DELETE CASCADE,
          FOREIGN KEY (receiver_id) REFERENCES users(user_id)       ON DELETE CASCADE,
          FOREIGN KEY (project_id)  REFERENCES projects(project_id) ON DELETE SET NULL
        )
    """),
    ("evaluations", """
        CREATE TABLE IF NOT EXISTS evaluations (
          eval_id               INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id            INTEGER NOT NULL UNIQUE,
          supervisor_id         INTEGER NOT NULL,
          problem_formulation   REAL    DEFAULT 0,
          literature_review     REAL    DEFAULT 0,
          methodology           REAL    DEFAULT 0,
          implementation_result REAL    DEFAULT 0,
          documentation         REAL    DEFAULT 0,
          defence_presentation  REAL    DEFAULT 0,
          total_score           REAL    DEFAULT 0,
          grade_letter          TEXT,
          feedback_notes        TEXT,
          evaluated_at          TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (project_id)    REFERENCES projects(project_id)       ON DELETE CASCADE,
          FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE CASCADE
        )
    """),
    ("ml_predictions", """
        CREATE TABLE IF NOT EXISTS ml_predictions (
          pred_id         INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id      INTEGER NOT NULL,
          model_name      TEXT    NOT NULL CHECK(model_name IN ('xgboost','random_forest','cosine_similarity')),
          prediction_type TEXT    NOT NULL CHECK(prediction_type IN ('risk_score','classification','matching_score')),
          input_features  TEXT,
          output_value    REAL    NOT NULL,
          output_label    TEXT,
          confidence      REAL,
          predicted_at    TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        )
    """),
    ("allocation_history", """
        CREATE TABLE IF NOT EXISTS allocation_history (
          alloc_id          INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id        INTEGER NOT NULL,
          supervisor_id     INTEGER NOT NULL,
          match_score       REAL    DEFAULT 0,
          xgboost_score     REAL,
          rf_score          REAL,
          allocated_by      INTEGER,
          allocation_method TEXT    DEFAULT 'ai_auto' CHECK(allocation_method IN ('ai_auto','manual_admin')),
          allocated_at      TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (student_id)    REFERENCES students(student_id)       ON DELETE CASCADE,
          FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE CASCADE
        )
    """),
    ("audit_log", """
        CREATE TABLE IF NOT EXISTS audit_log (
          log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id    INTEGER,
          username   TEXT,
          role       TEXT,
          action     TEXT    NOT NULL,
          ip_address TEXT,
          user_agent TEXT,
          status     TEXT    DEFAULT 'success' CHECK(status IN ('success','failure')),
          logged_at  TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
        )
    """),
    ("ml_pipeline_runs", """
        CREATE TABLE IF NOT EXISTS ml_pipeline_runs (
          run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
          institution_code  TEXT NOT NULL DEFAULT 'GLOBAL',
          source_type       TEXT NOT NULL DEFAULT 'live_database',
          connection_info   TEXT,
          samples_extracted INTEGER DEFAULT 0,
          samples_trained   INTEGER DEFAULT 0,
          xgb_accuracy      REAL,
          xgb_f1            REAL,
          rf_accuracy       REAL,
          rf_f1             REAL,
          status            TEXT DEFAULT 'completed',
          summary           TEXT,
          executed_at       TEXT DEFAULT (datetime('now'))
        )
    """),
]

POSTGRES_TABLES = [
    ("users", """
        CREATE TABLE IF NOT EXISTS users (
          user_id    SERIAL PRIMARY KEY,
          username   VARCHAR(100) NOT NULL UNIQUE,
          email      VARCHAR(255) NOT NULL UNIQUE,
          password   VARCHAR(255) NOT NULL,
          role       VARCHAR(20)  NOT NULL CHECK(role IN ('student','supervisor','admin')),
          full_name  VARCHAR(255) NOT NULL,
          phone      VARCHAR(50),
          is_active  INTEGER DEFAULT 1,
          avatar_url TEXT,
          created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("supervisors", """
        CREATE TABLE IF NOT EXISTS supervisors (
          supervisor_id    SERIAL PRIMARY KEY,
          user_id          INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
          department       VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
          expertise_areas  TEXT NOT NULL,
          expertise_vector TEXT,
          max_load         INTEGER DEFAULT 5,
          current_load     INTEGER DEFAULT 0,
          bio              TEXT,
          created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("students", """
        CREATE TABLE IF NOT EXISTS students (
          student_id       SERIAL PRIMARY KEY,
          user_id          INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
          matric_number    VARCHAR(50) NOT NULL UNIQUE,
          department       VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
          level            VARCHAR(20) DEFAULT '400',
          supervisor_id    INTEGER REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
          co_supervisor_id INTEGER REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
          project_id       INTEGER,
          research_domain  TEXT,
          enrollment_year  INTEGER,
          created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("projects", """
        CREATE TABLE IF NOT EXISTS projects (
          project_id        SERIAL PRIMARY KEY,
          student_id        INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
          supervisor_id     INTEGER REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
          co_supervisor_id  INTEGER REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
          title             VARCHAR(255) NOT NULL,
          abstract          TEXT,
          keywords          TEXT,
          keyword_vector    TEXT,
          status            VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending','approved','in_progress','completed','rejected')),
          duplication_score DOUBLE PRECISION DEFAULT 0,
          risk_score        DOUBLE PRECISION DEFAULT 0,
          risk_label        VARCHAR(20) DEFAULT 'on_track' CHECK(risk_label IN ('on_track','at_risk','critical')),
          final_grade       DOUBLE PRECISION,
          grade_letter      VARCHAR(5),
          submitted_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
          approved_at       TIMESTAMPTZ,
          completed_at      TIMESTAMPTZ,
          updated_at        TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("milestones", """
        CREATE TABLE IF NOT EXISTS milestones (
          milestone_id   SERIAL PRIMARY KEY,
          project_id     INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
          title          VARCHAR(255) NOT NULL,
          description    TEXT,
          due_date       DATE NOT NULL,
          completed_date DATE,
          status         VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending','completed','overdue','missed')),
          weight         DOUBLE PRECISION DEFAULT 10,
          created_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("submissions", """
        CREATE TABLE IF NOT EXISTS submissions (
          doc_id             SERIAL PRIMARY KEY,
          project_id         INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
          student_id         INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
          chapter            VARCHAR(20) NOT NULL CHECK(chapter IN ('proposal','chapter1','chapter2','chapter3','chapter4','chapter5','final')),
          file_name          VARCHAR(255),
          file_path          VARCHAR(500),
          file_size          INTEGER,
          version            INTEGER DEFAULT 1,
          status             VARCHAR(30) DEFAULT 'submitted' CHECK(status IN ('submitted','under_review','approved','revision_requested')),
          supervisor_comment TEXT,
          student_notes      TEXT,
          submitted_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
          uploaded_at        TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
          reviewed_at        TIMESTAMPTZ
        )
    """),
    ("alerts", """
        CREATE TABLE IF NOT EXISTS alerts (
          alert_id     SERIAL PRIMARY KEY,
          user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
          project_id   INTEGER REFERENCES projects(project_id) ON DELETE SET NULL,
          alert_type   VARCHAR(50) NOT NULL CHECK(alert_type IN ('deadline','inactivity','risk','feedback','system','ping','milestone_due','overdue','risk_detected','allocation')),
          title        VARCHAR(255) NOT NULL,
          message      TEXT NOT NULL,
          severity     VARCHAR(20) DEFAULT 'info' CHECK(severity IN ('info','warning','critical')),
          is_read      INTEGER DEFAULT 0,
          triggered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
          created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
          read_at      TIMESTAMPTZ
        )
    """),
    ("messages", """
        CREATE TABLE IF NOT EXISTS messages (
          message_id  SERIAL PRIMARY KEY,
          msg_id      INTEGER,
          sender_id   INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
          receiver_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
          project_id  INTEGER REFERENCES projects(project_id) ON DELETE SET NULL,
          subject     VARCHAR(255),
          body        TEXT NOT NULL,
          is_read     INTEGER DEFAULT 0,
          sent_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
          created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("evaluations", """
        CREATE TABLE IF NOT EXISTS evaluations (
          eval_id               SERIAL PRIMARY KEY,
          project_id            INTEGER NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
          supervisor_id         INTEGER NOT NULL REFERENCES supervisors(supervisor_id) ON DELETE CASCADE,
          problem_formulation   DOUBLE PRECISION DEFAULT 0,
          literature_review     DOUBLE PRECISION DEFAULT 0,
          methodology           DOUBLE PRECISION DEFAULT 0,
          implementation_result DOUBLE PRECISION DEFAULT 0,
          documentation         DOUBLE PRECISION DEFAULT 0,
          defence_presentation  DOUBLE PRECISION DEFAULT 0,
          total_score           DOUBLE PRECISION DEFAULT 0,
          grade_letter          VARCHAR(5),
          feedback_notes        TEXT,
          evaluated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("ml_predictions", """
        CREATE TABLE IF NOT EXISTS ml_predictions (
          pred_id         SERIAL PRIMARY KEY,
          project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
          model_name      VARCHAR(50)  NOT NULL CHECK(model_name IN ('xgboost','random_forest','cosine_similarity')),
          prediction_type VARCHAR(50)  NOT NULL CHECK(prediction_type IN ('risk_score','classification','matching_score')),
          input_features  TEXT,
          output_value    DOUBLE PRECISION NOT NULL,
          output_label    VARCHAR(50),
          confidence      DOUBLE PRECISION,
          predicted_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("allocation_history", """
        CREATE TABLE IF NOT EXISTS allocation_history (
          alloc_id          SERIAL PRIMARY KEY,
          student_id        INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
          supervisor_id     INTEGER NOT NULL REFERENCES supervisors(supervisor_id) ON DELETE CASCADE,
          match_score       DOUBLE PRECISION DEFAULT 0,
          xgboost_score     DOUBLE PRECISION,
          rf_score          DOUBLE PRECISION,
          allocated_by      INTEGER,
          allocation_method VARCHAR(50) DEFAULT 'ai_auto' CHECK(allocation_method IN ('ai_auto','manual_admin')),
          allocated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("audit_log", """
        CREATE TABLE IF NOT EXISTS audit_log (
          log_id     SERIAL PRIMARY KEY,
          user_id    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
          username   VARCHAR(100),
          role       VARCHAR(20),
          action     VARCHAR(255) NOT NULL,
          ip_address VARCHAR(50),
          user_agent TEXT,
          status     VARCHAR(20) DEFAULT 'success' CHECK(status IN ('success','failure')),
          logged_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("ml_pipeline_runs", """
        CREATE TABLE IF NOT EXISTS ml_pipeline_runs (
          run_id            SERIAL PRIMARY KEY,
          institution_code  VARCHAR(50) NOT NULL DEFAULT 'GLOBAL',
          source_type       VARCHAR(50) NOT NULL DEFAULT 'live_database',
          connection_info   TEXT,
          samples_extracted INTEGER DEFAULT 0,
          samples_trained   INTEGER DEFAULT 0,
          xgb_accuracy      DOUBLE PRECISION,
          xgb_f1            DOUBLE PRECISION,
          rf_accuracy       DOUBLE PRECISION,
          rf_f1             DOUBLE PRECISION,
          status            VARCHAR(20) DEFAULT 'completed',
          summary           TEXT,
          executed_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """),
]

SEED_USERS = [
    dict(role="admin", username="admin", email="hod@kwasu.edu.ng",
         password="password123", full_name="Dr. Jumoke Ajao (HOD)", phone="08012340001",
         department="Computer Science"),

    dict(role="supervisor", username="supervisor1", email="shakirat@kwasu.edu.ng",
         password="password123", full_name="Dr. Mrs. Shakirat Yusuff", phone="08012340002",
         department="Computer Science", max_load=5,
         expertise_areas="machine learning, neural networks, deep learning, computer vision, pattern recognition",
         bio="Specialises in applied ML and intelligent systems for educational contexts."),

    dict(role="supervisor", username="supervisor2", email="isiaka@kwasu.edu.ng",
         password="password123", full_name="Dr. Rafiu M. Isiaka", phone="08012340003",
         department="Computer Science", max_load=5,
         expertise_areas="cybersecurity, network security, cryptography, blockchain, intrusion detection",
         bio="Research focus on secure systems, ethical hacking and digital forensics."),

    dict(role="supervisor", username="supervisor3", email="afolabi@kwasu.edu.ng",
         password="password123", full_name="Dr. Blessing Afolabi", phone="08012340004",
         department="Computer Science", max_load=4,
         expertise_areas="natural language processing, text mining, information retrieval, chatbots, sentiment analysis",
         bio="Expert in NLP and computational linguistics with focus on low-resource languages."),

    dict(role="supervisor", username="supervisor4", email="adewale.sup@kwasu.edu.ng",
         password="password123", full_name="Mr. Adewale Ogundimu", phone="08012340005",
         department="Computer Science", max_load=6,
         expertise_areas="mobile computing, android development, IoT, embedded systems, cloud computing",
         bio="Passionate about mobile and edge computing for African contexts."),

    dict(role="student", username="student1", email="student1@kwasu.edu.ng",
         password="password123", full_name="Adewale Ibrahim", phone="08098760001",
         matric_number="CSC/2021/001", department="Computer Science", level="400",
         research_domain="machine learning, student performance prediction, educational data mining",
         enrollment_year=2021),

    dict(role="student", username="student2", email="student2@kwasu.edu.ng",
         password="password123", full_name="Fatima Bello", phone="08098760002",
         matric_number="CSC/2021/002", department="Computer Science", level="400",
         research_domain="cybersecurity, network intrusion detection, anomaly detection",
         enrollment_year=2021),

    dict(role="student", username="student3", email="student3@kwasu.edu.ng",
         password="password123", full_name="Emeka Okonkwo", phone="08098760003",
         matric_number="CSC/2021/003", department="Computer Science", level="400",
         research_domain="natural language processing, Yoruba language, text classification",
         enrollment_year=2021),

    dict(role="student", username="student4", email="student4@kwasu.edu.ng",
         password="password123", full_name="Aisha Musa", phone="08098760004",
         matric_number="CSC/2021/004", department="Computer Science", level="400",
         research_domain="IoT, smart agriculture, embedded systems, sensor networks",
         enrollment_year=2021),

    dict(role="student", username="student5", email="student5@kwasu.edu.ng",
         password="password123", full_name="David Osei", phone="08098760005",
         matric_number="CSC/2021/005", department="Computer Science", level="400",
         research_domain="blockchain, smart contracts, decentralised finance, cryptocurrency",
         enrollment_year=2021),
]

def auto_init_database():
    """Checks database tables and automatically initializes schema and seed accounts if needed."""
    db_url = os.getenv("DATABASE_URL", "")
    is_postgres = db_url.startswith("postgres://") or db_url.startswith("postgresql://")
    tables = POSTGRES_TABLES if is_postgres else SQLITE_TABLES

    print(f"[*] Checking database schema ({'PostgreSQL' if is_postgres else 'SQLite'})...")

    with engine.begin() as conn:
        # 1. Create tables
        for name, ddl in tables:
            try:
                conn.execute(text(ddl))
            except Exception as e:
                print(f"    Warning creating table {name}: {e}")

        # 2. Check if users are seeded
        try:
            count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        except Exception:
            count = 0

        if count == 0:
            print("[*] Empty database detected. Seeding demo accounts...")
            for s in SEED_USERS:
                try:
                    hashed = _hash_pw(s["password"])
                    res = conn.execute(
                        text("""INSERT INTO users (username,email,password,role,full_name,phone,is_active)
                                VALUES (:username,:email,:password,:role,:full_name,:phone,1)"""),
                        {
                            "username":  s["username"],
                            "email":     s["email"],
                            "password":  hashed,
                            "role":      s["role"],
                            "full_name": s["full_name"],
                            "phone":     s.get("phone"),
                        },
                    )
                    user_id = getattr(res, "lastrowid", None)
                    if not user_id:
                        user_row = conn.execute(
                            text("SELECT user_id FROM users WHERE username=:u"),
                            {"u": s["username"]},
                        ).fetchone()
                        user_id = user_row[0] if user_row else None

                    if s["role"] == "supervisor":
                        ev = json.dumps([e.strip().lower() for e in s["expertise_areas"].split(",") if e.strip()])
                        conn.execute(
                            text("""INSERT INTO supervisors (user_id,department,expertise_areas,expertise_vector,max_load,bio)
                                    VALUES (:uid,:dept,:areas,:vec,:max_load,:bio)"""),
                            {
                                "uid":      user_id,
                                "dept":     s["department"],
                                "areas":    s["expertise_areas"],
                                "vec":      ev,
                                "max_load": s.get("max_load", 5),
                                "bio":      s.get("bio"),
                            },
                        )
                    elif s["role"] == "student":
                        conn.execute(
                            text("""INSERT INTO students (user_id,matric_number,department,level,research_domain,enrollment_year)
                                    VALUES (:uid,:matric,:dept,:level,:domain,:year)"""),
                            {
                                "uid":    user_id,
                                "matric": s["matric_number"],
                                "dept":   s["department"],
                                "level":  s.get("level", "400"),
                                "domain": s.get("research_domain"),
                                "year":   s.get("enrollment_year", datetime.now().year),
                            },
                        )
                except Exception as e:
                    print(f"    Warning seeding user {s['username']}: {e}")
            print("[*] Successfully seeded demo accounts (admin, supervisors, students)!")
        else:
            print(f"[*] Database already initialized ({count} users found).")

        # 3. Safe column migrations
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE submissions ADD COLUMN student_notes TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE submissions ADD COLUMN uploaded_at TEXT"))
            conn.execute(text("UPDATE submissions SET uploaded_at = submitted_at WHERE uploaded_at IS NULL"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE submissions ADD COLUMN submitted_at TEXT"))
            conn.execute(text("UPDATE submissions SET submitted_at = uploaded_at WHERE submitted_at IS NULL"))
        except Exception:
            pass

        # Alerts migrations
        try:
            conn.execute(text("ALTER TABLE alerts ADD COLUMN triggered_at TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("UPDATE alerts SET triggered_at = created_at WHERE triggered_at IS NULL"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE alerts ADD COLUMN created_at TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("UPDATE alerts SET created_at = triggered_at WHERE created_at IS NULL"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE alerts ADD COLUMN read_at TEXT"))
        except Exception:
            pass

        # Messages migrations
        try:
            conn.execute(text("ALTER TABLE messages ADD COLUMN message_id INTEGER"))
        except Exception:
            pass
        try:
            conn.execute(text("UPDATE messages SET message_id = msg_id WHERE message_id IS NULL"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE messages ADD COLUMN msg_id INTEGER"))
        except Exception:
            pass
        try:
            conn.execute(text("UPDATE messages SET msg_id = message_id WHERE msg_id IS NULL"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE messages ADD COLUMN sent_at TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("UPDATE messages SET sent_at = created_at WHERE sent_at IS NULL"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE messages ADD COLUMN created_at TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("UPDATE messages SET created_at = sent_at WHERE created_at IS NULL"))
        except Exception:
            pass

        # Co-supervisor migrations
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN co_supervisor_id INTEGER"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE projects ADD COLUMN co_supervisor_id INTEGER"))
        except Exception:
            pass

        # Multi-tenant migrations
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN institution_id INTEGER"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN institution_id INTEGER"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE supervisors ADD COLUMN institution_id INTEGER"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE projects ADD COLUMN institution_id INTEGER"))
        except Exception:
            pass

        # Seed KWASU institution #1 if empty
        try:
            inst_count = conn.execute(text("SELECT count(*) FROM institutions")).fetchone()[0]
            if inst_count == 0:
                conn.execute(text("""
                    INSERT INTO institutions (
                        institution_id, name, code, slug, official_domain,
                        institution_type, state, city, contact_email, contact_phone,
                        logo_url, primary_color, secondary_color, status,
                        is_verified, current_stage, onboarding_percent
                    ) VALUES (
                        1, 'Kwara State University', 'KWASU', 'kwasu', 'kwasu.edu.ng',
                        'State University', 'Kwara', 'Malete', 'ict@kwasu.edu.ng', '+2348030000001',
                        '/kwasu.png', '#16a34a', '#080808', 'active',
                        1, '7_live_activation', 100
                    )
                """))
                conn.execute(text("""
                    INSERT INTO institution_settings (
                        institution_id, academic_session, current_semester, max_supervisor_load,
                        dual_supervisor_for_postgrad, auto_assign_co_supervisor, enable_ai_pairing
                    ) VALUES (1, '2025/2026', 'First Semester', 10, 1, 1, 1)
                """))
                conn.execute(text("UPDATE users SET institution_id = 1 WHERE institution_id IS NULL"))
                conn.execute(text("UPDATE students SET institution_id = 1 WHERE institution_id IS NULL"))
                conn.execute(text("UPDATE supervisors SET institution_id = 1 WHERE institution_id IS NULL"))
                conn.execute(text("UPDATE projects SET institution_id = 1 WHERE institution_id IS NULL"))
                print("[*] Seeded primary tenant: Kwara State University (KWASU)")

            # Ensure KWASU has all 7 pipeline stages marked as completed
            pipe_count = conn.execute(text("SELECT count(*) FROM tenant_onboarding_pipeline WHERE institution_id=1")).fetchone()[0]
            if pipe_count == 0:
                kwasu_stages = [
                    (1, '1_registration', 'School Profile & Contact Verification', 'completed', 'Kwara State University registered and validated', 'Institutional Admin', '2026-09-01 08:00:00', '2026-09-01 08:30:00'),
                    (2, '2_domain_verification', 'Educational Domain Ownership Check', 'completed', 'Domain kwasu.edu.ng verified via DNS TXT record', 'System', '2026-09-01 08:30:00', '2026-09-01 09:00:00'),
                    (3, '3_tenant_provisioning', 'Tenant Database Isolation & Cloud Storage', 'completed', 'Isolated database schema & storage provisioned', 'Pipeline Daemon', '2026-09-01 09:00:00', '2026-09-01 09:15:00'),
                    (4, '4_department_setup', 'Faculties & Academic Departments Tree', 'completed', 'Computer Science and allied departments mapped', 'Institutional Admin', '2026-09-01 09:15:00', '2026-09-01 10:00:00'),
                    (5, '5_faculty_import', 'Supervisors & Lecturers Batch Ingestion', 'completed', 'Faculty roster uploaded and supervisor accounts active', 'Institutional Admin', '2026-09-01 10:00:00', '2026-09-01 11:00:00'),
                    (6, '6_policy_config', 'Degree Rules & Supervision Governance', 'completed', 'Postgraduate dual-supervision rules & load limits set', 'Institutional Admin', '2026-09-01 11:00:00', '2026-09-01 11:30:00'),
                    (7, '7_live_activation', 'Production Go-Live & Portal Access', 'completed', 'Full production launch: student & faculty self-service live', 'System & Admin', '2026-09-01 12:00:00', '2026-09-01 12:00:00'),
                ]
                for s_order, s_code, s_name, s_status, s_action, s_by, s_start, s_end in kwasu_stages:
                    conn.execute(text("""
                        INSERT INTO tenant_onboarding_pipeline (
                            institution_id, stage_order, stage_code, stage_name, status,
                            required_action, executed_by, started_at, completed_at
                        ) VALUES (1, :s_order, :s_code, :s_name, :s_status, :s_action, :s_by, :s_start, :s_end)
                    """), {
                        "s_order": s_order, "s_code": s_code, "s_name": s_name,
                        "s_status": s_status, "s_action": s_action, "s_by": s_by,
                        "s_start": s_start, "s_end": s_end
                    })
                print("[*] Seeded KWASU pipeline milestone records (100% completed)")
            # Seed Projects, Milestones, and Submissions if empty
            proj_count = conn.execute(text("SELECT count(*) FROM projects")).fetchone()[0]
            if proj_count == 0:
                print("[*] Seeding live student projects, milestones, and submissions for KWASU...")
                # 1. Projects for primary demo students (1 to 5)
                demo_projects = [
                    (1, 1, 1, None, "Autonomous Multi-Agent AI Framework for Higher Institution Dissertation Evaluation",
                     "An automated agentic ecosystem integrating deep learning and NLP to supervise undergraduate dissertations.",
                     "machine learning, multi-agent systems, natural language processing", "in_progress", "on_track", 0.12),
                    (2, 2, 2, None, "Deep Learning Based Network Intrusion Detection for Academic Campus Infrastructure",
                     "Implementation of convolutional neural networks and LSTM networks to detect zero-day cyber threats in campus intranets.",
                     "cybersecurity, deep learning, anomaly detection, network security", "in_progress", "at_risk", 0.58),
                    (3, 3, 1, 3, "Low-Resource African NLP: Cross-Lingual Translation & Sentiment Analysis for Yoruba",
                     "Transformer architectures fine-tuned for low-resource West African language sentiment extraction.",
                     "natural language processing, transformers, yoruba language", "completed", "on_track", 0.05),
                    (4, 4, 3, None, "IoT-Enabled Precision Agriculture Sensor Array and Smart Irrigation Control System",
                     "Deployment of ESP32 sensor clusters transmitting soil moisture and weather telemetry to cloud dashboards.",
                     "iot, embedded systems, smart agriculture, sensor networks", "in_progress", "critical", 0.88),
                    (5, 5, 4, None, "Decentralized Credential Verification Protocol for Academic Degree Transcripts",
                     "A tamper-proof smart contract architecture on EVM blockchain to prevent degree certificate forgery.",
                     "blockchain, smart contracts, cryptography, decentralized finance", "in_progress", "on_track", 0.18),
                ]

                for p_id, s_id, sup_id, co_id, title, abstract, kw, status, r_label, r_score in demo_projects:
                    conn.execute(text("""
                        INSERT INTO projects (
                            project_id, student_id, supervisor_id, co_supervisor_id,
                            title, abstract, keywords, status, risk_label, risk_score, institution_id
                        ) VALUES (
                            :p_id, :s_id, :sup_id, :co_id, :title, :abstract, :kw, :status, :r_label, :r_score, 1
                        )
                    """), {
                        "p_id": p_id, "s_id": s_id, "sup_id": sup_id, "co_id": co_id,
                        "title": title, "abstract": abstract, "kw": kw, "status": status,
                        "r_label": r_label, "r_score": r_score
                    })
                    conn.execute(text("UPDATE students SET project_id = :p_id, supervisor_id = :sup_id WHERE student_id = :s_id"),
                                 {"p_id": p_id, "sup_id": sup_id, "s_id": s_id})

                # Milestones for Project 1 (On track)
                p1_milestones = [
                    (1, "Topic Proposal & Problem Formulation", "Define system goals and scope", "2026-08-01", "2026-08-05", "completed"),
                    (1, "Literature Review & Existing Systems Analysis", "Comprehensive survey of state of the art", "2026-08-25", "2026-08-22", "completed"),
                    (1, "System Architecture & ML Modeling", "Design pipeline data flow and models", "2026-09-15", "2026-09-14", "completed"),
                    (1, "Full Implementation & Testing", "Develop working prototype with test suite", "2026-10-15", None, "pending"),
                ]
                for p_id, m_title, m_desc, m_due, m_done, m_stat in p1_milestones:
                    conn.execute(text("""
                        INSERT INTO milestones (project_id, title, description, due_date, completed_date, status)
                        VALUES (:p_id, :m_title, :m_desc, :m_due, :m_done, :m_stat)
                    """), {"p_id": p_id, "m_title": m_title, "m_desc": m_desc, "m_due": m_due, "m_done": m_done, "m_stat": m_stat})

                # Submissions for Project 1
                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (1, 1, 'proposal', 'Proposal_Sulaiman.pdf', 'approved', '2026-08-04 10:00:00', '2026-08-06 14:00:00', 'Good research questions.')
                """))
                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (1, 1, 'chapter1', 'Chapter1_Sulaiman.pdf', 'approved', '2026-08-21 09:30:00', '2026-08-23 11:00:00', 'Clear background and problem statement.')
                """))
                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (1, 1, 'chapter2', 'Chapter2_Sulaiman.pdf', 'under_review', '2026-09-28 16:00:00', None, None)
                """))

                # Milestones for Project 2 (At Risk - overdue milestone)
                p2_milestones = [
                    (2, "Proposal Defense", "Approved by departmental panel", "2026-08-01", "2026-08-03", "completed"),
                    (2, "Dataset Acquisition & Preprocessing", "Acquire CICIDS2017 dataset and normalize", "2026-08-20", "2026-08-18", "completed"),
                    (2, "Neural Network Architecture Design", "Build CNN-LSTM model in PyTorch", "2026-09-10", None, "overdue"),
                    (2, "Ablation Studies & Defense", "Benchmark against baseline models", "2026-10-20", None, "pending"),
                ]
                for p_id, m_title, m_desc, m_due, m_done, m_stat in p2_milestones:
                    conn.execute(text("""
                        INSERT INTO milestones (project_id, title, description, due_date, completed_date, status)
                        VALUES (:p_id, :m_title, :m_desc, :m_due, :m_done, :m_stat)
                    """), {"p_id": p_id, "m_title": m_title, "m_desc": m_desc, "m_due": m_due, "m_done": m_done, "m_stat": m_stat})

                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (2, 2, 'proposal', 'Proposal_Fatima.pdf', 'approved', '2026-08-02 12:00:00', '2026-08-07 10:00:00', 'Approved.')
                """))
                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (2, 2, 'chapter1', 'Chapter1_Fatima.pdf', 'revision_requested', '2026-09-02 14:00:00', '2026-09-10 16:00:00', 'Need clearer citation on modern botnets.')
                """))

                # Milestones for Project 3 (Completed with Grade 88.5)
                for i in range(1, 6):
                    conn.execute(text(f"""
                        INSERT INTO milestones (project_id, title, description, due_date, completed_date, status)
                        VALUES (3, 'Milestone Phase {i}', 'Phase {i} deliverables', '2026-08-{i*5:02d}', '2026-08-{i*5-1:02d}', 'completed')
                    """))
                for ch in ['proposal', 'chapter1', 'chapter2', 'chapter3', 'chapter4', 'final']:
                    conn.execute(text(f"""
                        INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                        VALUES (3, 3, '{ch}', '{ch}_Emeka.pdf', 'approved', '2026-08-15 11:00:00', '2026-08-17 15:00:00', 'Excellent submission.')
                    """))
                conn.execute(text("""
                    INSERT INTO evaluations (
                        project_id, supervisor_id, problem_formulation, literature_review,
                        methodology, implementation_result, documentation, defence_presentation,
                        total_score, grade_letter, feedback_notes
                    ) VALUES (
                        3, 1, 18.0, 17.5, 18.5, 19.0, 8.0, 7.5, 88.5, 'A', 'Distinction level research work.'
                    )
                """))
                conn.execute(text("UPDATE projects SET final_grade = 88.5, grade_letter = 'A' WHERE project_id = 3"))

                # Milestones for Project 4 (Critical - 2 overdue milestones, long inactivity)
                p4_milestones = [
                    (4, "Proposal Formulation", "Project concept paper", "2026-07-20", "2026-07-22", "completed"),
                    (4, "Hardware Prototyping", "Assemble soil moisture sensors", "2026-08-10", None, "overdue"),
                    (4, "Firmware Programming", "Implement MQTT telemetry", "2026-08-30", None, "overdue"),
                    (4, "Deployment & Documentation", "Field testing in campus farm", "2026-10-10", None, "pending"),
                ]
                for p_id, m_title, m_desc, m_due, m_done, m_stat in p4_milestones:
                    conn.execute(text("""
                        INSERT INTO milestones (project_id, title, description, due_date, completed_date, status)
                        VALUES (:p_id, :m_title, :m_desc, :m_due, :m_done, :m_stat)
                    """), {"p_id": p_id, "m_title": m_title, "m_desc": m_desc, "m_due": m_due, "m_done": m_done, "m_stat": m_stat})

                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (4, 4, 'proposal', 'Proposal_Aisha.pdf', 'approved', '2026-07-21 10:00:00', '2026-07-25 10:00:00', 'Approved.')
                """))

                # Milestones for Project 5 (On track)
                p5_milestones = [
                    (5, "Proposal & Protocol Architecture", "Whitepaper specifications", "2026-08-10", "2026-08-08", "completed"),
                    (5, "Smart Contract Solidity Engineering", "ERC-721 soulbound token design", "2026-08-30", "2026-08-28", "completed"),
                    (5, "Frontend Web3 Integration", "Ethers.js and IPFS verification", "2026-09-25", "2026-09-24", "completed"),
                    (5, "Security Audit & Final Defense", "Formal verification and gas optimization", "2026-10-25", None, "pending"),
                ]
                for p_id, m_title, m_desc, m_due, m_done, m_stat in p5_milestones:
                    conn.execute(text("""
                        INSERT INTO milestones (project_id, title, description, due_date, completed_date, status)
                        VALUES (:p_id, :m_title, :m_desc, :m_due, :m_done, :m_stat)
                    """), {"p_id": p_id, "m_title": m_title, "m_desc": m_desc, "m_due": m_due, "m_done": m_done, "m_stat": m_stat})

                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (5, 5, 'proposal', 'Proposal_David.pdf', 'approved', '2026-08-07 10:00:00', '2026-08-09 10:00:00', 'Solid protocol design.')
                """))
                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (5, 5, 'chapter1', 'Chapter1_David.pdf', 'approved', '2026-08-27 10:00:00', '2026-08-29 14:00:00', 'Approved.')
                """))
                conn.execute(text("""
                    INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                    VALUES (5, 5, 'chapter2', 'Chapter2_David.pdf', 'approved', '2026-09-23 15:00:00', '2026-09-25 11:00:00', 'Approved.')
                """))

                # 2. Add 15 Historical Cohort Records for rich institutional ML dataset
                historical_cohort = [
                    ("Computer Vision Framework for Automated Traffic Density Estimation in Ilorin", "computer vision, yolo, deep learning", "completed", "on_track", 0.08, 82.0, "A"),
                    ("Predictive Maintenance for Telecommunication Base Stations using Random Forest", "machine learning, iot, predictive maintenance", "completed", "on_track", 0.10, 78.5, "A"),
                    ("Cloud-Native Electronic Health Record Management with Role-Based Access Control", "cloud computing, healthcare, security, rbac", "completed", "on_track", 0.12, 74.0, "B"),
                    ("Automated Essay Scoring System using RoBERTa and Semantic Vector Alignment", "nlp, education technology, deep learning", "completed", "on_track", 0.06, 85.0, "A"),
                    ("Solar Energy Generation Forecasting using Long Short-Term Memory Networks", "time series, lstm, renewable energy", "completed", "on_track", 0.15, 71.0, "B"),
                    ("DDoS Attack Mitigation using Software-Defined Networking and Flow Analytics", "networking, sdn, cybersecurity", "completed", "at_risk", 0.42, 63.5, "C"),
                    ("Face Recognition Attendance System for University Lecture Auditoriums", "computer vision, opencv, biometrics", "completed", "on_track", 0.14, 76.0, "B"),
                    ("Decentralized Autonomous Organization (DAO) Voting System on Polygon Network", "blockchain, governance, smart contracts", "completed", "on_track", 0.11, 79.0, "A"),
                    ("Phishing URL Detection using XGBoost and Lexical Feature Extraction", "cybersecurity, machine learning, web security", "completed", "on_track", 0.09, 81.5, "A"),
                    ("Federated Learning Framework for Multi-Hospital Privacy-Preserving Diagnostics", "federated learning, privacy, medical imaging", "completed", "on_track", 0.05, 91.0, "A"),
                    ("Smart Grid Load Balancing using Multi-Agent Reinforcement Learning", "reinforcement learning, smart grid, multi-agent", "rejected", "critical", 0.92, 42.0, "F"),
                    ("Fingerprint Biometric Authentication API with Template Protection", "biometrics, security, cryptography", "completed", "at_risk", 0.51, 60.0, "C"),
                    ("Hybrid Recommendation Engine for Academic Course Advising and Career Pathways", "recommender systems, collaborative filtering", "completed", "on_track", 0.13, 75.0, "B"),
                    ("Speech Recognition Model for Low-Resource Hausa Dialects", "speech recognition, nlp, deep learning", "completed", "at_risk", 0.48, 64.0, "C"),
                    ("Autonomous Quadcopter Navigation using SLAM and LiDAR Sensor Fusion", "robotics, slam, sensor fusion", "completed", "at_risk", 0.55, 58.0, "C"),
                ]

                base_pid = 6
                for h_idx, (h_title, h_kw, h_status, h_risk, h_score, h_grade, h_letter) in enumerate(historical_cohort):
                    h_pid = base_pid + h_idx
                    # Pick student 1..5 round robin as dummy relation
                    s_id = (h_idx % 5) + 1
                    sup_id = (h_idx % 4) + 1
                    conn.execute(text("""
                        INSERT INTO projects (
                            project_id, student_id, supervisor_id, title, abstract,
                            keywords, status, risk_label, risk_score, final_grade, grade_letter, institution_id
                        ) VALUES (
                            :p_id, :s_id, :sup_id, :title, 'Archival cohort dissertation record.',
                            :kw, :status, :r_label, :r_score, :grade, :letter, 1
                        )
                    """), {
                        "p_id": h_pid, "s_id": s_id, "sup_id": sup_id, "title": h_title,
                        "kw": h_kw, "status": h_status, "r_label": h_risk, "r_score": h_score,
                        "grade": h_grade, "letter": h_letter
                    })

                    # Seed submission & milestone trace for each historical project
                    is_bad = (h_risk in ('critical', 'at_risk'))
                    num_subs = 1 if is_bad and h_score > 0.8 else (3 if is_bad else 6)
                    for c_idx, ch in enumerate(['proposal', 'chapter1', 'chapter2', 'chapter3', 'chapter4', 'final'][:num_subs]):
                        conn.execute(text(f"""
                            INSERT INTO submissions (project_id, student_id, chapter, file_name, status, submitted_at, reviewed_at, supervisor_comment)
                            VALUES ({h_pid}, {s_id}, '{ch}', '{ch}_historical.pdf', 'approved', '2025-0{c_idx+2}-10 10:00:00', '2025-0{c_idx+2}-14 12:00:00', 'Satisfactory.')
                        """))

                    # Milestones
                    m_overdue = 2 if h_risk == 'critical' else (1 if h_risk == 'at_risk' else 0)
                    for m_idx in range(4):
                        m_stat = 'overdue' if (m_idx >= 4 - m_overdue) else 'completed'
                        conn.execute(text(f"""
                            INSERT INTO milestones (project_id, title, description, due_date, completed_date, status)
                            VALUES ({h_pid}, 'Milestone {m_idx+1}', 'Phase deliverable', '2025-0{m_idx+3}-15', {'NULL' if m_stat == 'overdue' else "'2025-0'+str(m_idx+3)+'-14'"}, '{m_stat}')
                        """))

                print("[*] Successfully seeded 20 authentic project, milestone, and submission traces for KWASU!")
        except Exception as e:
            print(f"[*] Note on projects seed: {e}")

    print("[*] Database verification complete.")


if __name__ == "__main__":
    auto_init_database()
