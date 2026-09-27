"""
database/pipeline.py
SQLite database pipeline — creates tables, seeds demo users.
Run from project root: python database/pipeline.py
"""

import os, sys, json, sqlite3
from datetime import datetime
from pathlib import Path
import bcrypt

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "backend" / ".env")
except ImportError:
    pass

# ── CONFIG ────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.parent / "backend"
DB_PATH_ENV  = os.getenv("DB_PATH", "spsems.db")
DB_PATH      = Path(DB_PATH_ENV) if Path(DB_PATH_ENV).is_absolute() else BACKEND_DIR / DB_PATH_ENV
DB_PATH      = DB_PATH.resolve()

def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password[:72].encode(), bcrypt.gensalt()).decode()

def _verify_pw(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password[:72].encode(), hashed.encode())


# ── CONNECTION ────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── STEP 1: DATABASE FILE ─────────────────────────────────
def create_database():
    print(f"\n[Step 1] Initialising SQLite database at: {DB_PATH}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    conn.close()
    print("         Database file ready.")


# ── STEP 2: TABLES ────────────────────────────────────────
TABLES = [
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
          student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id         INTEGER NOT NULL UNIQUE,
          matric_number   TEXT    NOT NULL UNIQUE,
          department      TEXT    NOT NULL DEFAULT 'Computer Science',
          level           TEXT    DEFAULT '400',
          supervisor_id   INTEGER,
          project_id      INTEGER,
          research_domain TEXT,
          enrollment_year INTEGER,
          created_at      TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (user_id)       REFERENCES users(user_id)            ON DELETE CASCADE,
          FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE SET NULL
        )
    """),
    ("projects", """
        CREATE TABLE IF NOT EXISTS projects (
          project_id        INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id        INTEGER NOT NULL,
          supervisor_id     INTEGER,
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
          FOREIGN KEY (student_id)    REFERENCES students(student_id)       ON DELETE CASCADE,
          FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE SET NULL
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
          status             TEXT    DEFAULT 'submitted' CHECK(status IN ('submitted','reviewed','revision_needed','approved')),
          student_notes      TEXT,
          supervisor_comment TEXT,
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
          alert_type   TEXT    NOT NULL CHECK(alert_type IN ('ping','milestone_due','overdue','risk_detected','feedback','allocation','system')),
          title        TEXT    NOT NULL,
          message      TEXT    NOT NULL,
          severity     TEXT    DEFAULT 'info' CHECK(severity IN ('info','warning','critical')),
          is_read      INTEGER DEFAULT 0,
          triggered_at TEXT    DEFAULT (datetime('now')),
          read_at      TEXT,
          FOREIGN KEY (user_id)    REFERENCES users(user_id)       ON DELETE CASCADE,
          FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL
        )
    """),
    ("messages", """
        CREATE TABLE IF NOT EXISTS messages (
          message_id  INTEGER PRIMARY KEY AUTOINCREMENT,
          sender_id   INTEGER NOT NULL,
          receiver_id INTEGER NOT NULL,
          project_id  INTEGER,
          subject     TEXT,
          body        TEXT    NOT NULL,
          is_read     INTEGER DEFAULT 0,
          sent_at     TEXT    DEFAULT (datetime('now')),
          FOREIGN KEY (sender_id)   REFERENCES users(user_id) ON DELETE CASCADE,
          FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE,
          FOREIGN KEY (project_id)  REFERENCES projects(project_id) ON DELETE SET NULL
        )
    """),
    ("evaluations", """
        CREATE TABLE IF NOT EXISTS evaluations (
          eval_id              INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id           INTEGER NOT NULL,
          supervisor_id        INTEGER NOT NULL,
          rubric_methodology   REAL,
          rubric_literature    REAL,
          rubric_analysis      REAL,
          rubric_presentation  REAL,
          rubric_originality   REAL,
          total_score          REAL,
          grade_letter         TEXT,
          comments             TEXT,
          evaluated_at         TEXT    DEFAULT (datetime('now')),
          UNIQUE(project_id, supervisor_id),
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


def create_tables():
    print("\n[Step 2] Creating tables...")
    conn = get_conn()
    cur  = conn.cursor()
    for name, ddl in TABLES:
        cur.execute(ddl)
        print(f"         {name}")
    conn.commit()
    try:
        conn.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        conn.commit()
        print("         Migrated: added avatar_url to users.")
    except Exception:
        pass
    conn.close()
    print("         All tables ready.")


# ── STEP 3: SEED USERS ────────────────────────────────────
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


def seed_users():
    print("\n[Step 3] Seeding demo users...")
    conn   = get_conn()
    cur    = conn.cursor()
    seeded = []

    for s in SEED_USERS:
        cur.execute(
            "SELECT user_id FROM users WHERE username=? OR email=?",
            (s["username"], s["email"]),
        )
        existing = cur.fetchone()
        if existing:
            print(f"         Skipped (exists): {s['username']}")
            seeded.append({**s, "user_id": existing["user_id"], "skipped": True})
            continue

        hashed = _hash_pw(s["password"])
        cur.execute(
            "INSERT INTO users (username,email,password,role,full_name,phone,is_active) VALUES (?,?,?,?,?,?,1)",
            (s["username"], s["email"], hashed, s["role"], s["full_name"], s.get("phone")),
        )
        user_id = cur.lastrowid

        if s["role"] == "supervisor":
            ev = json.dumps([e.strip().lower() for e in s["expertise_areas"].split(",") if e.strip()])
            cur.execute(
                "INSERT INTO supervisors (user_id,department,expertise_areas,expertise_vector,max_load,bio) VALUES (?,?,?,?,?,?)",
                (user_id, s["department"], s["expertise_areas"], ev, s.get("max_load", 5), s.get("bio")),
            )
        elif s["role"] == "student":
            cur.execute(
                "INSERT INTO students (user_id,matric_number,department,level,research_domain,enrollment_year) VALUES (?,?,?,?,?,?)",
                (user_id, s["matric_number"], s["department"], s.get("level", "400"),
                 s.get("research_domain"), s.get("enrollment_year", datetime.now().year)),
            )

        print(f"         [{s['role']:10s}] {s['full_name']} — @{s['username']}")
        seeded.append({**s, "user_id": user_id, "skipped": False})

    conn.commit()
    conn.close()
    return seeded


# ── STEP 4: PRINT CREDENTIALS ─────────────────────────────
def print_credentials(users):
    W = 95
    print(f"\n{'='*W}")
    print("  CREDENTIAL REGISTRY — KWASU SPSEMS v2")
    print(f"{'='*W}")
    print(f"  {'Role':<14}{'Full Name':<28}{'Username':<18}{'Password':<16}{'Email'}")
    print(f"  {'-'*(W-2)}")
    for role in ("admin", "supervisor", "student"):
        group = [u for u in users if u["role"] == role]
        for u in group:
            print(f"  {u['role']:<14}{u['full_name'][:26]:<28}{u['username']:<18}{'password123':<16}{u['email']}")
    print(f"\n  Admin registration code : KWASU-HOD-2026")
    print(f"  Change passwords before going to production!\n")


# ── STEP 5: VERIFY ────────────────────────────────────────
def verify_tables():
    print("[Step 5] Verifying row counts...")
    conn = get_conn()
    cur  = conn.cursor()
    for name, _ in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {name}")
        count = cur.fetchone()[0]
        print(f"         {name:<26} {count} row(s)")
    conn.close()


# ── MAIN ──────────────────────────────────────────────────
def main():
    print("\n" + "="*54)
    print("   KWASU SPSEMS v2 — SQLite Database Pipeline")
    print("   Creates tables  *  Seeds credentials  *  Verifies")
    print("="*54)
    try:
        create_database()
        create_tables()
        seeded = seed_users()
        print_credentials(seeded)
        verify_tables()
        print("\nPipeline complete! Database is ready.")
        print("\nNext steps:")
        print("  1. cd backend && pip install -r requirements.txt")
        print("  2. uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("  3. cd ../ml-service && pip install -r requirements.txt")
        print("     uvicorn main:app --host 0.0.0.0 --port 8001 --reload")
        print("  4. cd ../frontend && npm install && npm start\n")
    except Exception as e:
        import traceback
        print(f"\nPipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
