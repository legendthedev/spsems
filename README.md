# KWASU SPSEMS — Smart Project Supervision & Evaluation Management System

A full-stack web application for managing final-year student project supervision at Kwara State University (KWASU). The system handles project proposals, supervisor allocation, chapter-by-chapter reviews, AI risk assessment, and final grading — all in one platform.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Demo Credentials](#demo-credentials)
- [API Reference](#api-reference)
- [ML Service Endpoints](#ml-service-endpoints)
- [User Roles](#user-roles)
- [Environment Variables](#environment-variables)

---

## Features

### Student
- Register and submit research proposals
- Upload chapter documents (PDF)
- Track project status and milestone progress
- View supervisor feedback in real time
- Receive risk alerts and notifications

### Supervisor
- View all assigned students and their project status
- Review and provide feedback on chapter submissions
- Trigger per-student AI risk checks
- Submit final evaluation using a 5-criteria rubric (100-point scale)
- Message students directly

### Admin / HOD
- Approve or deactivate user accounts
- Run the **AI Placement Engine** — automatically assigns unassigned projects to supervisors using keyword cosine similarity and workload balancing
- Perform **manual allocation** overrides
- View full allocation history
- Monitor system-wide statistics: risk distribution, department breakdown, pending approvals

### AI / ML Features
- **Risk Prediction** — XGBoost + Random Forest ensemble scores each student's project as `on_track`, `at_risk`, or `critical`
- **Supervisor Matching** — TF-IDF cosine similarity between student keywords and supervisor expertise areas, weighted by workload
- **Duplication Detection** — flags new proposals with high similarity to existing archived titles
- **Grade Evaluation** — maps five rubric scores to a final letter grade (A–F)

---

## Architecture

```
┌─────────────────┐     HTTP/REST      ┌──────────────────────┐
│  React Frontend │ ─────────────────► │  FastAPI Backend      │
│  (port 3000)    │ ◄───────────────── │  (port 8000)          │
└─────────────────┘     JSON           │  SQLite database      │
                                       └──────────┬───────────┘
                                                  │ internal HTTP
                                                  ▼
                                       ┌──────────────────────┐
                                       │  FastAPI ML Service   │
                                       │  (port 8001)          │
                                       │  XGBoost / RF / TF-IDF│
                                       └──────────────────────┘
```

The backend proxies ML requests to the microservice. If the ML service is unavailable, the backend falls back to built-in heuristic engines so the system keeps running.

---

## Tech Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Frontend   | React 18, React Router v6, Axios, react-hot-toast |
| Backend    | FastAPI, SQLAlchemy (SQLite), python-jose (JWT) |
| ML Service | FastAPI, XGBoost, scikit-learn, TF-IDF          |
| Database   | SQLite (file-based, no server required)         |
| Auth       | JWT Bearer tokens, bcrypt password hashing      |

---

## Project Structure

```
spsems-v2/
│
├── backend/                        # FastAPI backend (port 8000)
│   ├── main.py                     # App entry point, router registration
│   ├── config.py                   # Settings via pydantic-settings
│   ├── database.py                 # SQLAlchemy engine + session
│   ├── requirements.txt
│   ├── .env                        # Environment overrides
│   ├── middleware/
│   │   └── auth.py                 # JWT creation, verification, role guards
│   ├── routes/
│   │   ├── auth.py                 # Login, register (admin/supervisor), profile
│   │   ├── register.py             # Public student self-registration
│   │   ├── projects.py             # Proposal submit, chapter upload, dashboard
│   │   ├── supervisor.py           # Review, evaluate, risk-check, dashboard
│   │   ├── admin.py                # Stats, users, placement engine, allocation
│   │   └── alerts.py               # Alerts and messages
│   └── schemas/
│       └── schemas.py              # All Pydantic request/response models
│
├── database/
│   └── pipeline.py                 # Creates all 12 tables and seeds demo data
│
├── ml-service/                     # FastAPI ML microservice (port 8001)
│   ├── main.py                     # ML API endpoints
│   ├── ml_engine.py                # XGBoost, Random Forest, cosine matcher
│   └── requirements.txt
│
├── frontend/                       # React SPA (port 3000)
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js
│       ├── App.js                  # Routes + auth guards
│       ├── context/
│       │   └── AuthContext.js      # Global auth state (login/logout/refresh)
│       ├── services/
│       │   └── api.js              # Axios instance with JWT interceptor
│       └── pages/
│           ├── LandingPage.js      # Login page
│           ├── RegisterPage.js     # Student self-registration
│           ├── StudentPortal.js    # Student dashboard + proposal + progress
│           ├── SupervisorPortal.js # Supervisor dashboard + review + evaluate
│           └── AdminPortal.js      # Admin dashboard + placement + allocation
│
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- No database server required (SQLite is file-based)

---

### Step 1 — Initialize the Database

```bash
cd spsems-v2/database
python pipeline.py
```

This creates `spsems-v2/backend/spsems.db` with all 12 tables and seeds 10 demo users (1 admin, 4 supervisors, 5 students).

---

### Step 2 — Start the Backend

```bash
cd spsems-v2/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API available at: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

### Step 3 — Start the ML Service

```bash
cd spsems-v2/ml-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

ML service available at: `http://localhost:8001`

> The ML service trains its models on first startup using synthetic data (~1 second). Trained models are cached in `ml-service/models/` for subsequent runs.

---

### Step 4 — Start the Frontend

```bash
cd spsems-v2/frontend
npm install
npm start
```

App available at: `http://localhost:3000`

---

## Demo Credentials

All demo accounts use the password: **`password123`**

| Role         | Username         | Notes                            |
|--------------|------------------|----------------------------------|
| Admin / HOD  | `admin_kwasu`    | Full system access               |
| Supervisor   | `dr_ahmed`       | Computer Science dept.           |
| Supervisor   | `prof_adesanya`  | Software Engineering dept.       |
| Supervisor   | `dr_okafor`      | Data Science dept.               |
| Supervisor   | `dr_ibrahim`     | Cyber Security dept.             |
| Student      | `student_alice`  | Has a submitted proposal         |
| Student      | `student_bob`    | Has a submitted proposal         |
| Student      | `student_carol`  | Has a submitted proposal         |
| Student      | `student_dave`   | New student                      |
| Student      | `student_eve`    | New student                      |

> Students registered through the public `/register` page start as **inactive** and must be activated by the admin before they can log in.

---

## API Reference

All endpoints are prefixed with `/api`. JWT token required (except login and public register).

### Auth

| Method | Endpoint              | Description                          | Auth |
|--------|-----------------------|--------------------------------------|------|
| POST   | `/api/auth/login`     | Login — returns JWT token            | No   |
| POST   | `/api/auth/register`  | Register admin or supervisor         | No   |
| GET    | `/api/auth/profile`   | Get current user profile             | Yes  |

### Public Registration

| Method | Endpoint                  | Description                  | Auth |
|--------|---------------------------|------------------------------|------|
| POST   | `/api/register/student`   | Student self-registration    | No   |

### Projects (Student)

| Method | Endpoint                         | Description                    |
|--------|----------------------------------|--------------------------------|
| GET    | `/api/projects/dashboard`        | Student dashboard + project    |
| POST   | `/api/projects/submit`           | Submit research proposal       |
| POST   | `/api/projects/upload-chapter`   | Upload a chapter document      |
| GET    | `/api/projects/all`              | List all projects (admin use)  |

### Supervisor

| Method | Endpoint                           | Description                         |
|--------|------------------------------------|-------------------------------------|
| GET    | `/api/supervisor/dashboard`        | Supervisor dashboard + students     |
| POST   | `/api/supervisor/review`           | Submit chapter review + feedback    |
| POST   | `/api/supervisor/evaluate`         | Submit final evaluation (rubric)    |
| POST   | `/api/supervisor/batch-risk-check` | Trigger ML risk check on projects   |
| POST   | `/api/supervisor/message`          | Send message to student             |

### Admin

| Method | Endpoint                            | Description                            |
|--------|-------------------------------------|----------------------------------------|
| GET    | `/api/admin/stats`                  | System-wide statistics                 |
| GET    | `/api/admin/users`                  | All users with details                 |
| PATCH  | `/api/admin/users/{id}/toggle-active` | Activate or deactivate a user        |
| GET    | `/api/admin/supervisors`            | All supervisors with load info         |
| POST   | `/api/admin/placement-engine`       | Run AI auto-allocation                 |
| POST   | `/api/admin/manual-allocate`        | Manually assign supervisor to project  |
| GET    | `/api/admin/allocation-history`     | Full allocation log                    |

### Alerts & Messages

| Method | Endpoint                        | Description                     |
|--------|---------------------------------|---------------------------------|
| GET    | `/api/alerts`                   | Get user notifications          |
| PATCH  | `/api/alerts/{id}/read`         | Mark one alert as read          |
| PATCH  | `/api/alerts/read-all`          | Mark all alerts as read         |
| GET    | `/api/messages`                 | Get inbox/outbox messages       |
| POST   | `/api/messages`                 | Send a message                  |
| PATCH  | `/api/messages/{id}/read`       | Mark message as read            |

---

## ML Service Endpoints

Base URL: `http://localhost:8001`

### `POST /predict/risk`
Predicts student project risk using XGBoost + Random Forest ensemble.

**Request:**
```json
{
  "student_id": 1,
  "project_id": 1,
  "days_since_last_submission": 14,
  "total_submissions": 3,
  "milestone_completion_rate": 0.6,
  "supervisor_feedback_response_days": 3,
  "overdue_milestones": 0,
  "chapter_progress": 0.4,
  "weeks_elapsed": 8,
  "total_weeks": 20
}
```

**Response:**
```json
{
  "final_label": "on_track",
  "ensemble_risk_probability": 0.21,
  "xgboost": { "risk_label": "on_track", "risk_probability": 0.21, "confidence": 0.58 },
  "random_forest": { "category": "On Track", "confidence": 0.84 }
}
```

---

### `POST /check/duplication`
Checks a new proposal title against an archive of existing titles using TF-IDF cosine similarity.

**Request:**
```json
{
  "title": "Deep Learning for Medical Image Segmentation",
  "archive": [
    { "id": 1, "title": "Neural Networks in Medical Imaging" }
  ]
}
```

**Response:**
```json
{
  "duplication_score": 0.62,
  "is_duplicate": false,
  "similar_titles": [
    { "id": 1, "title": "Neural Networks in Medical Imaging", "score": 0.62 }
  ]
}
```

---

### `POST /match/supervisors`
Ranks supervisors by keyword match score (cosine similarity) combined with workload availability.

**Request:**
```json
{
  "student_keywords": ["machine learning", "classification", "neural networks"],
  "supervisors": [
    { "id": 1, "name": "Dr. Ahmed", "expertise_vector": ["machine learning", "deep learning"], "current_load": 2, "max_load": 5 }
  ]
}
```

**Response:**
```json
{
  "top_match": { "id": 1, "name": "Dr. Ahmed", "cosine_similarity": 0.81, "final_score": 0.73 },
  "matches": [ ... ]
}
```

---

### `POST /evaluate/grade`
Converts five rubric scores (each out of 20) into a total score and letter grade.

**Request:**
```json
{
  "methodology_score": 16,
  "literature_score": 14,
  "analysis_score": 15,
  "presentation_score": 13,
  "originality_score": 12
}
```

**Response:**
```json
{
  "total_score": 70.0,
  "grade_letter": "A"
}
```

**Grading scale:** A ≥ 70 · B ≥ 60 · C ≥ 50 · D ≥ 45 · F < 45

---

## User Roles

| Role       | Register via         | Requires Approval | Access Level               |
|------------|----------------------|-------------------|----------------------------|
| Student    | `/register` page     | Yes (by admin)    | Own project only           |
| Supervisor | `/api/auth/register` | No                | All assigned students      |
| Admin/HOD  | `/api/auth/register` + `ADMIN_REG_CODE` | No | Full system |

---

## Environment Variables

Located in `backend/.env`:

| Variable         | Default                        | Description                              |
|------------------|--------------------------------|------------------------------------------|
| `DB_PATH`        | `spsems.db`                    | SQLite file path (relative to backend/)  |
| `JWT_SECRET`     | `kwasu_spsems_jwt_secret_2026` | Secret key for signing JWT tokens        |
| `JWT_EXPIRE_HOURS` | `24`                         | Token expiry in hours                    |
| `APP_HOST`       | `0.0.0.0`                      | Backend bind host                        |
| `APP_PORT`       | `8000`                         | Backend port                             |
| `ML_SERVICE_URL` | `http://localhost:8001`        | ML microservice base URL                 |
| `UPLOAD_DIR`     | `./uploads`                    | Directory for uploaded chapter files     |
| `ADMIN_REG_CODE` | `KWASU-HOD-2026`               | Code required to register as admin/HOD   |
| `FRONTEND_URL`   | `http://localhost:3000`        | Allowed CORS origin                      |

---

## Database Schema

The SQLite database contains 12 tables:

- **users** — all accounts (student, supervisor, admin)
- **students** — student profile linked to users
- **supervisors** — supervisor profile with expertise and load tracking
- **projects** — research proposals with status lifecycle
- **chapters** — individual chapter submissions with file paths
- **reviews** — supervisor feedback per chapter
- **evaluations** — final rubric scores and grades
- **milestones** — per-project milestone tracking
- **alerts** — in-app notifications
- **messages** — user-to-user messaging
- **allocation_history** — log of all supervisor–student assignments
- **project_archive** — reference titles for duplication checking

---

## Notes

- The ML service trains models on first launch using synthetic data. This takes about 1–2 seconds. Trained models are saved to `ml-service/models/` and reused on subsequent startups.
- If the ML service is offline, the backend automatically falls back to built-in heuristic logic — the system will not crash.
- All file uploads are stored in `backend/uploads/` organized by project and chapter.
- The frontend proxies all `/api` requests to `http://localhost:8000` via the `proxy` field in `package.json`.
