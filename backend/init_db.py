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

    print("[*] Database verification complete.")
