-- ============================================================
-- KWASU SPSEMS — PostgreSQL Schema for Supabase Migration
-- ============================================================

-- Drop existing tables if re-running
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS allocation_history CASCADE;
DROP TABLE IF EXISTS ml_predictions CASCADE;
DROP TABLE IF EXISTS evaluations CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS submissions CASCADE;
DROP TABLE IF EXISTS milestones CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS supervisors CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. USERS
CREATE TABLE users (
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
);

-- 2. SUPERVISORS
CREATE TABLE supervisors (
  supervisor_id    SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
  department       VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
  expertise_areas  TEXT NOT NULL,
  expertise_vector TEXT,
  max_load         INTEGER DEFAULT 5,
  current_load     INTEGER DEFAULT 0,
  bio              TEXT,
  created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. STUDENTS
CREATE TABLE students (
  student_id      SERIAL PRIMARY KEY,
  user_id         INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
  matric_number   VARCHAR(50) NOT NULL UNIQUE,
  department      VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
  level           VARCHAR(20) DEFAULT '400',
  supervisor_id   INTEGER REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
  co_supervisor_id INTEGER REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
  project_id      INTEGER,
  research_domain TEXT,
  enrollment_year INTEGER,
  created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. PROJECTS
CREATE TABLE projects (
  project_id        SERIAL PRIMARY KEY,
  student_id        INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
  supervisor_id     INTEGER REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
  co_supervisor_id  INTEGER REFERENCES supervisors(supervisor_id) ON DELETE SET NULL,
  title             VARCHAR(500) NOT NULL,
  abstract          TEXT,
  keywords          TEXT,
  keyword_vector    TEXT,
  status            VARCHAR(30) DEFAULT 'pending' CHECK(status IN ('pending','approved','in_progress','completed','rejected')),
  duplication_score DOUBLE PRECISION DEFAULT 0,
  risk_score        DOUBLE PRECISION DEFAULT 0,
  risk_label        VARCHAR(30) DEFAULT 'on_track' CHECK(risk_label IN ('on_track','at_risk','critical')),
  final_grade       DOUBLE PRECISION,
  grade_letter      VARCHAR(5),
  submitted_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  approved_at       TIMESTAMPTZ,
  completed_at      TIMESTAMPTZ,
  updated_at        TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Foreign key linking students back to projects
ALTER TABLE students ADD CONSTRAINT fk_students_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL;

-- 5. MILESTONES
CREATE TABLE milestones (
  milestone_id   SERIAL PRIMARY KEY,
  project_id     INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  title          VARCHAR(255) NOT NULL,
  description    TEXT,
  due_date       VARCHAR(50) NOT NULL,
  completed_date VARCHAR(50),
  status         VARCHAR(30) DEFAULT 'pending' CHECK(status IN ('pending','completed','overdue','missed')),
  weight         DOUBLE PRECISION DEFAULT 10,
  created_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. SUBMISSIONS
CREATE TABLE submissions (
  doc_id             SERIAL PRIMARY KEY,
  project_id         INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  student_id         INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
  chapter            VARCHAR(30) NOT NULL CHECK(chapter IN ('proposal','chapter1','chapter2','chapter3','chapter4','chapter5','final')),
  file_name          VARCHAR(255),
  file_path          TEXT,
  file_size          BIGINT,
  version            INTEGER DEFAULT 1,
  status             VARCHAR(30) DEFAULT 'submitted' CHECK(status IN ('submitted','reviewed','revision_needed','approved')),
  student_notes      TEXT,
  supervisor_comment TEXT,
  uploaded_at        TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  reviewed_at        TIMESTAMPTZ
);

-- 7. ALERTS
CREATE TABLE alerts (
  alert_id     SERIAL PRIMARY KEY,
  user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  project_id   INTEGER REFERENCES projects(project_id) ON DELETE SET NULL,
  alert_type   VARCHAR(50) NOT NULL CHECK(alert_type IN ('ping','milestone_due','overdue','risk_detected','feedback','allocation','system')),
  title        VARCHAR(255) NOT NULL,
  message      TEXT NOT NULL,
  severity     VARCHAR(20) DEFAULT 'info' CHECK(severity IN ('info','warning','critical')),
  is_read      INTEGER DEFAULT 0,
  triggered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  read_at      TIMESTAMPTZ
);

-- 8. MESSAGES
CREATE TABLE messages (
  message_id  SERIAL PRIMARY KEY,
  sender_id   INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  receiver_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  project_id  INTEGER REFERENCES projects(project_id) ON DELETE SET NULL,
  subject     VARCHAR(255),
  body        TEXT NOT NULL,
  is_read     INTEGER DEFAULT 0,
  sent_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 9. EVALUATIONS
CREATE TABLE evaluations (
  eval_id              SERIAL PRIMARY KEY,
  project_id           INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  supervisor_id        INTEGER NOT NULL REFERENCES supervisors(supervisor_id) ON DELETE CASCADE,
  rubric_methodology   DOUBLE PRECISION,
  rubric_literature    DOUBLE PRECISION,
  rubric_analysis      DOUBLE PRECISION,
  rubric_presentation  DOUBLE PRECISION,
  rubric_originality   DOUBLE PRECISION,
  total_score          DOUBLE PRECISION,
  grade_letter         VARCHAR(5),
  comments             TEXT,
  evaluated_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(project_id, supervisor_id)
);

-- 10. ML_PREDICTIONS
CREATE TABLE ml_predictions (
  pred_id         SERIAL PRIMARY KEY,
  project_id      INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  model_name      VARCHAR(50) NOT NULL CHECK(model_name IN ('xgboost','random_forest','cosine_similarity')),
  prediction_type VARCHAR(50) NOT NULL CHECK(prediction_type IN ('risk_score','classification','matching_score')),
  input_features  TEXT,
  output_value    DOUBLE PRECISION NOT NULL,
  output_label    VARCHAR(50),
  confidence      DOUBLE PRECISION,
  predicted_at    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 11. ALLOCATION_HISTORY
CREATE TABLE allocation_history (
  alloc_id          SERIAL PRIMARY KEY,
  student_id        INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
  supervisor_id     INTEGER NOT NULL REFERENCES supervisors(supervisor_id) ON DELETE CASCADE,
  match_score       DOUBLE PRECISION DEFAULT 0,
  xgboost_score     DOUBLE PRECISION,
  rf_score          DOUBLE PRECISION,
  allocated_by      INTEGER,
  allocation_method VARCHAR(50) DEFAULT 'ai_auto' CHECK(allocation_method IN ('ai_auto','manual_admin')),
  allocated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 12. AUDIT_LOG
CREATE TABLE audit_log (
  log_id     SERIAL PRIMARY KEY,
  user_id    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
  username   VARCHAR(100),
  role       VARCHAR(20),
  action     VARCHAR(255) NOT NULL,
  ip_address VARCHAR(50),
  user_agent TEXT,
  status     VARCHAR(20) DEFAULT 'success' CHECK(status IN ('success','failure')),
  logged_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- SEED DEMO ACCOUNTS (Default password for all: password123)
-- ============================================================

INSERT INTO users (username, email, password, role, full_name, phone, is_active)
VALUES
  ('admin', 'hod@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'admin', 'Dr. Jumoke Ajao (HOD)', '08012340001', 1),
  ('supervisor1', 'shakirat@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'supervisor', 'Dr. Mrs. Shakirat Yusuff', '08012340002', 1),
  ('supervisor2', 'isiaka@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'supervisor', 'Dr. Rafiu M. Isiaka', '08012340003', 1),
  ('supervisor3', 'afolabi@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'supervisor', 'Dr. Blessing Afolabi', '08012340004', 1),
  ('supervisor4', 'adewale.sup@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'supervisor', 'Mr. Adewale Ogundimu', '08012340005', 1),
  ('student1', 'student1@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'student', 'Adewale Ibrahim', '08098760001', 1),
  ('student2', 'student2@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'student', 'Fatima Bello', '08098760002', 1),
  ('student3', 'student3@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'student', 'Emeka Okonkwo', '08098760003', 1),
  ('student4', 'student4@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'student', 'Aisha Musa', '08098760004', 1),
  ('student5', 'student5@kwasu.edu.ng', '$2b$12$zBq9O1Yx3YqT9zD5Q7J4vO0K8wS1lG5h3jE9vP2uT7bY4fC8mX9K.', 'student', 'David Osei', '08098760005', 1)
ON CONFLICT (username) DO NOTHING;

INSERT INTO supervisors (user_id, department, expertise_areas, expertise_vector, max_load, bio)
SELECT user_id, 'Computer Science', 'machine learning, neural networks, deep learning, computer vision, pattern recognition', '["machine learning", "neural networks", "deep learning", "computer vision", "pattern recognition"]', 5, 'Specialises in applied ML and intelligent systems for educational contexts.'
FROM users WHERE username = 'supervisor1' ON CONFLICT (user_id) DO NOTHING;

INSERT INTO supervisors (user_id, department, expertise_areas, expertise_vector, max_load, bio)
SELECT user_id, 'Computer Science', 'cybersecurity, network security, cryptography, blockchain, intrusion detection', '["cybersecurity", "network security", "cryptography", "blockchain", "intrusion detection"]', 5, 'Research focus on secure systems, ethical hacking and digital forensics.'
FROM users WHERE username = 'supervisor2' ON CONFLICT (user_id) DO NOTHING;

INSERT INTO supervisors (user_id, department, expertise_areas, expertise_vector, max_load, bio)
SELECT user_id, 'Computer Science', 'natural language processing, text mining, information retrieval, chatbots, sentiment analysis', '["natural language processing", "text mining", "information retrieval", "chatbots", "sentiment analysis"]', 4, 'Expert in NLP and computational linguistics with focus on low-resource languages.'
FROM users WHERE username = 'supervisor3' ON CONFLICT (user_id) DO NOTHING;

INSERT INTO supervisors (user_id, department, expertise_areas, expertise_vector, max_load, bio)
SELECT user_id, 'Computer Science', 'mobile computing, android development, IoT, embedded systems, cloud computing', '["mobile computing", "android development", "iot", "embedded systems", "cloud computing"]', 6, 'Passionate about mobile and edge computing for African contexts.'
FROM users WHERE username = 'supervisor4' ON CONFLICT (user_id) DO NOTHING;

INSERT INTO students (user_id, matric_number, department, level, research_domain, enrollment_year)
SELECT user_id, 'CSC/2021/001', 'Computer Science', '400', 'machine learning, student performance prediction, educational data mining', 2021
FROM users WHERE username = 'student1' ON CONFLICT (user_id) DO NOTHING;

INSERT INTO students (user_id, matric_number, department, level, research_domain, enrollment_year)
SELECT user_id, 'CSC/2021/002', 'Computer Science', '400', 'cybersecurity, network intrusion detection, anomaly detection', 2021
FROM users WHERE username = 'student2' ON CONFLICT (user_id) DO NOTHING;

INSERT INTO students (user_id, matric_number, department, level, research_domain, enrollment_year)
SELECT user_id, 'CSC/2021/003', 'Computer Science', '400', 'natural language processing, Yoruba language, text classification', 2021
FROM users WHERE username = 'student3' ON CONFLICT (user_id) DO NOTHING;

INSERT INTO students (user_id, matric_number, department, level, research_domain, enrollment_year)
SELECT user_id, 'CSC/2021/004', 'Computer Science', '400', 'IoT, smart agriculture, embedded systems, sensor networks', 2021
FROM users WHERE username = 'student4' ON CONFLICT (user_id) DO NOTHING;

INSERT INTO students (user_id, matric_number, department, level, research_domain, enrollment_year)
SELECT user_id, 'CSC/2021/005', 'Computer Science', '400', 'blockchain, smart contracts, decentralised finance, cryptocurrency', 2021
FROM users WHERE username = 'student5' ON CONFLICT (user_id) DO NOTHING;
