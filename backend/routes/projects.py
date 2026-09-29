import os, json, math
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from middleware.auth import get_current_user, require_role
from schemas.schemas import ProposalRequest, ProjectStatusUpdate, ChapterEnum
from config import get_settings

router   = APIRouter(tags=["Projects"])
settings = get_settings()


def _risk_fallback(f: dict) -> dict:
    score    = 0.0
    pressure = f["weeks_elapsed"] / max(f["total_weeks"], 1)
    days     = f["days_since_last_submission"]
    if   days > 21: score += 0.35
    elif days > 14: score += 0.20
    elif days > 7:  score += 0.08
    mcr = f["milestone_completion_rate"]
    if   mcr < 0.30: score += 0.30
    elif mcr < 0.50: score += 0.15
    score += min(f["overdue_milestones"] * 0.10, 0.25)
    gap = (pressure * 5) - (f["chapter_progress"] * 5)
    if   gap > 2: score += 0.25
    elif gap > 1: score += 0.12
    risk_prob = min(max(score, 0.0), 1.0)
    label = "critical" if risk_prob >= 0.65 else ("at_risk" if risk_prob >= 0.35 else "on_track")
    return {
        "final_label": label,
        "ensemble_risk_probability": round(risk_prob, 4),
        "xgboost":      {"risk_probability": risk_prob, "risk_label": label, "confidence": round(abs(risk_prob-0.5)*2, 4)},
        "random_forest": {"classification": label, "confidence": 0.6},
        "_source": "fallback_rule_engine",
    }


@router.get("/projects/dashboard")
def student_dashboard(db: Session = Depends(get_db), user: dict = Depends(require_role("student"))):
    """Single endpoint the student portal frontend expects."""
    proj = db.execute(
        text("""SELECT p.*,
             u_sup.full_name AS supervisor_name, u_sup.email AS supervisor_email,
             u_sup.user_id AS supervisor_user_id,
             s.expertise_areas, s.department AS sup_dept, s.supervisor_id,
             (SELECT COUNT(*) FROM submissions WHERE project_id=p.project_id) AS total_submissions,
             (SELECT COUNT(*) FROM milestones WHERE project_id=p.project_id AND status='completed') AS completed_milestones,
             (SELECT COUNT(*) FROM milestones WHERE project_id=p.project_id) AS total_milestones,
             (SELECT COUNT(*) FROM milestones WHERE project_id=p.project_id AND status='overdue') AS overdue_milestones,
             (SELECT supervisor_comment FROM submissions WHERE project_id=p.project_id
              AND supervisor_comment IS NOT NULL ORDER BY reviewed_at DESC LIMIT 1) AS feedback_latest
           FROM projects p
           JOIN students st ON p.student_id=st.student_id
           LEFT JOIN supervisors s ON p.supervisor_id=s.supervisor_id
           LEFT JOIN users u_sup ON s.user_id=u_sup.user_id
           WHERE st.user_id=:uid ORDER BY p.submitted_at DESC LIMIT 1"""),
        {"uid": user["user_id"]},
    ).fetchone()

    if not proj:
        return {"success": True, "project": None, "supervisor": None, "milestones": [], "submissions": []}

    p   = dict(proj._mapping)
    pid = p["project_id"]
    completed = int(p.get("completed_milestones") or 0)
    total     = int(p.get("total_milestones") or 5)

    p["chapter_progress"] = round(completed / max(total, 1), 2)
    p["current_chapter"]  = min(completed + 1, 5)

    supervisor = None
    if p.get("supervisor_name"):
        supervisor = {
            "full_name":       p["supervisor_name"],
            "email":           p.get("supervisor_email"),
            "expertise_areas": p.get("expertise_areas"),
            "department":      p.get("sup_dept"),
            "user_id":         p.get("supervisor_user_id"),
        }

    ms_rows = db.execute(
        text("SELECT * FROM milestones WHERE project_id=:pid ORDER BY due_date"), {"pid": pid}
    ).fetchall()
    milestones = []
    for m in ms_rows:
        md = dict(m._mapping)
        md["is_completed"] = md["status"] == "completed"
        md["is_overdue"]   = md["status"] == "overdue"
        milestones.append(md)

    subs = db.execute(
        text("SELECT * FROM submissions WHERE project_id=:pid ORDER BY COALESCE(submitted_at, uploaded_at) DESC LIMIT 10"), {"pid": pid}
    ).fetchall()

    return {
        "success":     True,
        "project":     p,
        "supervisor":  supervisor,
        "milestones":  milestones,
        "submissions": [dict(r._mapping) for r in subs],
    }


@router.post("/projects/submit", status_code=201)
async def submit_proposal_form(
    title:     str        = Form(...),
    abstract:  str        = Form(...),
    keywords:  str        = Form(""),
    objectives:str        = Form(""),
    document:  UploadFile = File(None),
    db:        Session    = Depends(get_db),
    user:      dict       = Depends(require_role("student")),
):
    """Multipart alias for the proposal form in the student portal."""
    st = db.execute(
        text("SELECT student_id, project_id FROM students WHERE user_id=:user_id"),
        {"user_id": user["user_id"]},
    ).fetchone()
    if not st:
        raise HTTPException(404, "Student record not found.")
    if st.project_id:
        raise HTTPException(409, "You already have an active project.")

    dup_score = 0.0
    try:
        archive = db.execute(
            text("SELECT project_id AS id, title, keywords FROM projects WHERE status != 'rejected'")
        ).fetchall()
        resp = httpx.post(
            f"{settings.ml_service_url}/check/duplication",
            json={"title": title, "archive": [dict(r._mapping) for r in archive]},
            timeout=4.0,
        )
        d = resp.json()
        dup_score = d.get("duplication_score", 0.0)
        if d.get("is_duplicate"):
            raise HTTPException(409, detail={"message": "Project title too similar to an existing project.", "duplication_score": dup_score})
    except HTTPException:
        raise
    except Exception:
        pass

    kw_vector = json.dumps([k.strip().lower() for k in (keywords or title).split(",") if k.strip()])
    result = db.execute(
        text("""INSERT INTO projects (student_id,title,abstract,keywords,keyword_vector,duplication_score,status)
           VALUES (:sid,:title,:abstract,:keywords,:kw,:dup,'pending')"""),
        {"sid": st.student_id, "title": title, "abstract": abstract,
         "keywords": keywords or "", "kw": kw_vector, "dup": dup_score},
    )
    db.commit()
    project_id = getattr(result, "lastrowid", None)
    if not project_id:
        row = db.execute(text("SELECT project_id FROM projects WHERE student_id=:sid ORDER BY project_id DESC LIMIT 1"), {"sid": st.student_id}).fetchone()
        project_id = row[0] if row else None

    db.execute(
        text("UPDATE students SET project_id=:pid WHERE student_id=:sid"),
        {"pid": project_id, "sid": st.student_id},
    )

    now = datetime.now(timezone.utc)
    for title_m, weeks, weight in [
        ("Chapter 1 — Introduction", 3, 15),
        ("Chapter 2 — Literature Review", 6, 20),
        ("Chapter 3 — Methodology", 9, 20),
        ("Chapter 4 — Results & Analysis", 13, 25),
        ("Chapter 5 — Conclusion", 16, 20),
    ]:
        db.execute(
            text("INSERT INTO milestones (project_id,title,due_date,weight) VALUES (:pid,:title,:due,:weight)"),
            {"pid": project_id, "title": title_m, "due": (now + timedelta(weeks=weeks)).date(), "weight": weight},
        )

    if document and document.filename:
        ext = os.path.splitext(document.filename)[1].lower()
        if ext in {".pdf", ".doc", ".docx"}:
            os.makedirs(settings.upload_dir, exist_ok=True)
            fname = f"{project_id}_proposal_v1_{document.filename}"
            fpath = os.path.join(settings.upload_dir, fname)
            with open(fpath, "wb") as fout:
                fout.write(await document.read())
            db.execute(
                text("""INSERT INTO submissions (project_id,student_id,chapter,file_name,file_path,file_size,version)
                   VALUES (:pid,:sid,'proposal',:fname,:fpath,:fsize,1)"""),
                {"pid": project_id, "sid": st.student_id, "fname": document.filename,
                 "fpath": fpath, "fsize": os.path.getsize(fpath)},
            )

    for a in db.execute(text("SELECT user_id FROM users WHERE role='admin' AND is_active=1")).fetchall():
        db.execute(
            text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
               VALUES (:uid,:pid,'system','New Project Proposal',:msg,'info')"""),
            {"uid": a.user_id, "pid": project_id,
             "msg": f'"{title[:60]}" submitted — awaiting your review.'},
        )
    db.commit()
    return {"success": True, "message": "Proposal submitted. Awaiting HOD approval.", "project_id": project_id}


@router.post("/projects/upload-chapter", status_code=201)
async def upload_chapter(
    chapter:  str        = Form(...),
    notes:    str        = Form(""),
    document: UploadFile = File(...),
    db:       Session    = Depends(get_db),
    user:     dict       = Depends(require_role("student")),
):
    """Upload a chapter document — multipart alias used by the student portal."""
    st = db.execute(
        text("SELECT student_id, project_id FROM students WHERE user_id=:uid"), {"uid": user["user_id"]}
    ).fetchone()
    if not st or not st.project_id:
        raise HTTPException(404, "No active project found.")

    ext = os.path.splitext(document.filename or "")[1].lower()
    if ext not in {".pdf", ".doc", ".docx", ".ppt", ".pptx"}:
        raise HTTPException(400, "Only PDF, DOC, DOCX, PPT, PPTX files allowed.")

    chapter_val = f"chapter{chapter}" if not chapter.startswith("chapter") else chapter
    ver_row = db.execute(
        text("SELECT MAX(version) AS max_ver FROM submissions WHERE project_id=:pid AND chapter=:ch"),
        {"pid": st.project_id, "ch": chapter_val},
    ).fetchone()
    version = (ver_row.max_ver or 0) + 1

    os.makedirs(settings.upload_dir, exist_ok=True)
    fname    = f"{st.project_id}_{chapter_val}_v{version}_{document.filename}"
    fpath    = os.path.join(settings.upload_dir, fname)
    contents = await document.read()
    with open(fpath, "wb") as fout:
        fout.write(contents)

    db.execute(
        text("""INSERT INTO submissions (project_id,student_id,chapter,file_name,file_path,file_size,version,student_notes)
           VALUES (:pid,:sid,:ch,:fname,:fpath,:fsize,:ver,:notes)"""),
        {"pid": st.project_id, "sid": st.student_id, "ch": chapter_val,
         "fname": document.filename, "fpath": fpath, "fsize": len(contents),
         "ver": version, "notes": notes or None},
    )

    proj = db.execute(
        text("""SELECT s.user_id AS sup_uid FROM projects p
           JOIN supervisors s ON p.supervisor_id=s.supervisor_id WHERE p.project_id=:pid"""),
        {"pid": st.project_id},
    ).fetchone()
    if proj and proj.sup_uid:
        db.execute(
            text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
               VALUES (:uid,:pid,'feedback','New Chapter Submitted',:msg,'info')"""),
            {"uid": proj.sup_uid, "pid": st.project_id,
             "msg": f"{user['full_name']} submitted {chapter_val} (v{version}). Please review."},
        )
    db.commit()
    return {"success": True, "message": "Chapter uploaded successfully.", "version": version}


@router.post("/projects/propose", status_code=201)
def submit_proposal(
    body: ProposalRequest,
    db:   Session = Depends(get_db),
    user: dict    = Depends(require_role("student")),
):
    st = db.execute(
        text("SELECT student_id, project_id FROM students WHERE user_id=:user_id"),
        {"user_id": user["user_id"]},
    ).fetchone()
    if not st:
        raise HTTPException(404, "Student record not found.")
    if st.project_id:
        raise HTTPException(409, "You already have an active project.")

    dup_score, is_dup = 0.0, False
    try:
        archive = db.execute(
            text("SELECT project_id AS id, title, keywords FROM projects WHERE status != 'rejected'")
        ).fetchall()
        resp = httpx.post(
            f"{settings.ml_service_url}/check/duplication",
            json={"title": body.title, "archive": [dict(r._mapping) for r in archive]},
            timeout=4.0,
        )
        d         = resp.json()
        dup_score = d.get("duplication_score", 0.0)
        is_dup    = d.get("is_duplicate", False)
    except Exception:
        pass

    if is_dup:
        raise HTTPException(409, detail={
            "message": "Project title too similar to an existing project.",
            "duplication_score": dup_score,
        })

    kw_vector = json.dumps([k.strip().lower() for k in (body.keywords or body.title).split(",") if k.strip()])
    result = db.execute(
        text("""INSERT INTO projects (student_id,title,abstract,keywords,keyword_vector,duplication_score,status)
           VALUES (:student_id,:title,:abstract,:keywords,:keyword_vector,:duplication_score,'pending')"""),
        {
            "student_id":        st.student_id,
            "title":             body.title,
            "abstract":          body.abstract,
            "keywords":          body.keywords or "",
            "keyword_vector":    kw_vector,
            "duplication_score": dup_score,
        },
    )
    db.commit()
    project_id = getattr(result, "lastrowid", None)
    if not project_id:
        row = db.execute(text("SELECT project_id FROM projects WHERE student_id=:student_id ORDER BY project_id DESC LIMIT 1"), {"student_id": st.student_id}).fetchone()
        project_id = row[0] if row else None

    db.execute(
        text("UPDATE students SET project_id=:project_id WHERE student_id=:student_id"),
        {"project_id": project_id, "student_id": st.student_id},
    )

    now = datetime.now(timezone.utc)
    for title, weeks, weight in [
        ("Chapter 1 — Introduction",       3,  15),
        ("Chapter 2 — Literature Review",  6,  20),
        ("Chapter 3 — Methodology",        9,  20),
        ("Chapter 4 — Results & Analysis", 13, 25),
        ("Chapter 5 — Conclusion",         16, 20),
    ]:
        due = (now + timedelta(weeks=weeks)).date()
        db.execute(
            text("INSERT INTO milestones (project_id,title,due_date,weight) VALUES (:project_id,:title,:due_date,:weight)"),
            {"project_id": project_id, "title": title, "due_date": due, "weight": weight},
        )

    for a in db.execute(text("SELECT user_id FROM users WHERE role='admin' AND is_active=1")).fetchall():
        db.execute(
            text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
               VALUES (:user_id,:project_id,'system','New Project Proposal',:message,'info')"""),
            {"user_id": a.user_id, "project_id": project_id,
             "message": f'"{body.title[:60]}" submitted — awaiting your review.'},
        )
    db.commit()
    return {"success": True, "message": "Proposal submitted. Awaiting HOD approval.", "project_id": project_id}


@router.get("/projects/my")
def get_student_project(db: Session = Depends(get_db), user: dict = Depends(require_role("student"))):
    proj = db.execute(
        text("""SELECT p.*, u.full_name AS supervisor_name, s.expertise_areas, s.department AS sup_dept, s.supervisor_id,
             (SELECT COUNT(*) FROM submissions WHERE project_id=p.project_id) AS total_submissions,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id AND status='completed') AS completed_milestones,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id) AS total_milestones,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id AND status='overdue')   AS overdue_milestones
           FROM projects p
           LEFT JOIN supervisors s ON p.supervisor_id=s.supervisor_id
           LEFT JOIN users u       ON s.user_id=u.user_id
           JOIN students st        ON p.student_id=st.student_id
           WHERE st.user_id=:user_id ORDER BY p.submitted_at DESC LIMIT 1"""),
        {"user_id": user["user_id"]},
    ).fetchone()

    if not proj:
        return {"success": True, "project": None, "milestones": [], "submissions": [], "alerts": [], "messages": []}

    pid = proj.project_id
    def rows(rs): return [dict(r._mapping) for r in rs]

    try:
        raw_alerts = rows(db.execute(text("SELECT * FROM alerts WHERE user_id=:uid ORDER BY triggered_at DESC LIMIT 20"), {"uid": user["user_id"]}).fetchall())
    except Exception:
        try:
            raw_alerts = rows(db.execute(text("SELECT * FROM alerts WHERE user_id=:uid ORDER BY created_at DESC LIMIT 20"), {"uid": user["user_id"]}).fetchall())
        except Exception:
            raw_alerts = []

    for a in raw_alerts:
        if not a.get("triggered_at"):
            a["triggered_at"] = a.get("created_at") or ""
        if not a.get("created_at"):
            a["created_at"] = a.get("triggered_at") or ""

    try:
        raw_messages = rows(db.execute(
            text("""SELECT m.*, u.full_name AS sender_name, u.role AS sender_role
               FROM messages m JOIN users u ON m.sender_id=u.user_id
               WHERE m.receiver_id=:uid OR m.sender_id=:uid ORDER BY m.sent_at DESC LIMIT 20"""),
            {"uid": user["user_id"]},
        ).fetchall())
    except Exception:
        try:
            raw_messages = rows(db.execute(
                text("""SELECT m.*, u.full_name AS sender_name, u.role AS sender_role
                   FROM messages m JOIN users u ON m.sender_id=u.user_id
                   WHERE m.receiver_id=:uid OR m.sender_id=:uid ORDER BY m.created_at DESC LIMIT 20"""),
                {"uid": user["user_id"]},
            ).fetchall())
        except Exception:
            raw_messages = []

    for m in raw_messages:
        if "message_id" not in m or m["message_id"] is None:
            m["message_id"] = m.get("msg_id")
        if "msg_id" not in m or m["msg_id"] is None:
            m["msg_id"] = m.get("message_id")
        if not m.get("sent_at"):
            m["sent_at"] = m.get("created_at") or ""
        if not m.get("created_at"):
            m["created_at"] = m.get("sent_at") or ""

    return {
        "success":     True,
        "project":     dict(proj._mapping),
        "milestones":  rows(db.execute(text("SELECT * FROM milestones  WHERE project_id=:pid ORDER BY due_date"), {"pid": pid}).fetchall()),
        "submissions": rows(db.execute(text("SELECT * FROM submissions WHERE project_id=:pid ORDER BY COALESCE(submitted_at, uploaded_at) DESC LIMIT 10"), {"pid": pid}).fetchall()),
        "alerts":      raw_alerts,
        "messages":    raw_messages,
    }


@router.post("/projects/submit-doc", status_code=201)
async def submit_document(
    project_id: int         = Form(...),
    chapter:    ChapterEnum = Form(...),
    file:       UploadFile  = File(...),
    db:         Session     = Depends(get_db),
    user:       dict        = Depends(require_role("student")),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".pdf", ".doc", ".docx", ".ppt", ".pptx"}:
        raise HTTPException(400, "Only PDF, DOC, DOCX, PPT, PPTX files allowed.")

    st = db.execute(text("SELECT student_id FROM students WHERE user_id=:uid"), {"uid": user["user_id"]}).fetchone()
    if not st:
        raise HTTPException(404, "Student not found.")

    ver_row = db.execute(
        text("SELECT MAX(version) AS max_ver FROM submissions WHERE project_id=:pid AND chapter=:chapter"),
        {"pid": project_id, "chapter": chapter},
    ).fetchone()
    version = (ver_row.max_ver or 0) + 1

    os.makedirs(settings.upload_dir, exist_ok=True)
    fname    = f"{project_id}_{chapter}_v{version}_{file.filename}"
    fpath    = os.path.join(settings.upload_dir, fname)
    contents = await file.read()
    with open(fpath, "wb") as fout:
        fout.write(contents)

    db.execute(
        text("""INSERT INTO submissions (project_id,student_id,chapter,file_name,file_path,file_size,version)
           VALUES (:project_id,:student_id,:chapter,:file_name,:file_path,:file_size,:version)"""),
        {"project_id": project_id, "student_id": st.student_id, "chapter": chapter,
         "file_name": file.filename, "file_path": fpath, "file_size": len(contents), "version": version},
    )

    proj = db.execute(
        text("""SELECT p.supervisor_id, s.user_id AS sup_uid FROM projects p
           JOIN supervisors s ON p.supervisor_id=s.supervisor_id WHERE p.project_id=:pid"""),
        {"pid": project_id},
    ).fetchone()
    if proj and proj.sup_uid:
        db.execute(
            text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
               VALUES (:user_id,:pid,'feedback','New Document Submitted',:message,'info')"""),
            {"user_id": proj.sup_uid, "pid": project_id,
             "message": f"{user['full_name']} submitted {chapter} (v{version}). Please review."},
        )
    db.commit()
    return {"success": True, "message": "Document submitted.", "version": version}


@router.post("/projects/{project_id}/risk")
def run_risk_prediction(
    project_id: int,
    db:         Session = Depends(get_db),
    user:       dict    = Depends(require_role("admin", "supervisor")),
):
    row = db.execute(
        text("""SELECT p.*,
             (SELECT COUNT(*) FROM submissions WHERE project_id=p.project_id) AS total_submissions,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id AND status='completed') AS completed_milestones,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id) AS total_milestones,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id AND status='overdue')   AS overdue_milestones,
             COALESCE((SELECT CAST(julianday('now') - julianday(MAX(COALESCE(submitted_at, uploaded_at))) AS INTEGER) FROM submissions WHERE project_id=p.project_id),30) AS days_since_last_sub,
             COALESCE((SELECT AVG(julianday(reviewed_at) - julianday(COALESCE(submitted_at, uploaded_at))) FROM submissions WHERE project_id=p.project_id AND reviewed_at IS NOT NULL),5) AS avg_feedback_days
           FROM projects p WHERE p.project_id=:pid"""),
        {"pid": project_id},
    ).fetchone()

    if not row:
        raise HTTPException(404, "Project not found.")

    p            = dict(row._mapping)
    total_ms     = int(p.get("total_milestones")     or 5)
    done_ms      = int(p.get("completed_milestones") or 0)
    overdue_ms   = int(p.get("overdue_milestones")   or 0)
    total_subs   = int(p.get("total_submissions")    or 0)
    days_since   = float(p.get("days_since_last_sub") or 30)
    avg_feedback = float(p.get("avg_feedback_days")   or 5)

    submitted_at = p.get("submitted_at") or datetime.now(timezone.utc)
    if isinstance(submitted_at, str):
        submitted_at = datetime.fromisoformat(submitted_at)
    if submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=timezone.utc)

    weeks_elapsed = max(math.ceil((datetime.now(timezone.utc) - submitted_at).days / 7), 1)

    features = {
        "student_id":                        p["student_id"],
        "project_id":                        project_id,
        "days_since_last_submission":        days_since,
        "total_submissions":                 total_subs,
        "milestone_completion_rate":         done_ms / total_ms if total_ms else 0,
        "supervisor_feedback_response_days": avg_feedback,
        "overdue_milestones":                overdue_ms,
        "chapter_progress":                  min(done_ms / 5, 1),
        "weeks_elapsed":                     weeks_elapsed,
        "total_weeks":                       20,
    }

    ml_source = "python_ml_service"
    try:
        resp = httpx.post(f"{settings.ml_service_url}/predict/risk", json=features, timeout=6.0)
        pred = resp.json()
    except Exception as e:
        print(f"ML service offline — using fallback: {e}")
        pred      = _risk_fallback(features)
        ml_source = "fallback_rule_engine"

    final_label = pred["final_label"]
    risk_prob   = pred["ensemble_risk_probability"]

    try:
        db.execute(
            text("""INSERT INTO ml_predictions (project_id,model_name,prediction_type,input_features,output_value,output_label,confidence)
               VALUES (:pid,'xgboost','risk_score',:input,:output_value,:output_label,:confidence)"""),
            {"pid": project_id, "input": json.dumps(features),
             "output_value": risk_prob, "output_label": final_label,
             "confidence": pred.get("xgboost", {}).get("confidence", 0.5)},
        )
    except Exception:
        pass

    db.execute(
        text("UPDATE projects SET risk_score=:score, risk_label=:label, updated_at=CURRENT_TIMESTAMP WHERE project_id=:pid"),
        {"score": risk_prob, "label": final_label, "pid": project_id},
    )

    if final_label != "on_track":
        stu = db.execute(
            text("SELECT u.user_id FROM students st JOIN users u ON st.user_id=u.user_id WHERE st.student_id=:sid"),
            {"sid": p["student_id"]},
        ).fetchone()
        if stu:
            pct = f"{risk_prob * 100:.1f}"
            db.execute(
                text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
                   VALUES (:uid,:pid,'risk_detected',:title,:message,:severity)"""),
                {
                    "uid":  stu.user_id,
                    "pid":  project_id,
                    "title": f"Risk Alert — {'CRITICAL' if final_label=='critical' else 'AT RISK'}",
                    "message": f"Your project risk is {pct}%. {'Contact supervisor immediately.' if final_label=='critical' else 'Update your progress.'}",
                    "severity": "critical" if final_label == "critical" else "warning",
                },
            )
    db.commit()
    return {"success": True, "prediction": pred, "project_id": project_id, "ml_source": ml_source}


@router.get("/projects")
def get_all_projects(db: Session = Depends(get_db), user: dict = Depends(require_role("admin", "supervisor"))):
    base = """
      SELECT p.*, u_st.full_name AS student_name, st.matric_number, st.department AS student_dept, st.level,
             u_sup.full_name AS supervisor_name, sup.department AS supervisor_dept,
             (SELECT COUNT(*) FROM submissions WHERE project_id=p.project_id) AS submission_count,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id AND status='completed') AS ms_done,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id) AS ms_total,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id AND status='overdue')   AS ms_overdue
      FROM projects p
      JOIN students st ON p.student_id=st.student_id
      JOIN users u_st  ON st.user_id=u_st.user_id
      LEFT JOIN supervisors sup ON p.supervisor_id=sup.supervisor_id
      LEFT JOIN users u_sup     ON sup.user_id=u_sup.user_id
    """
    if user["role"] == "supervisor":
        sup_row = db.execute(
            text("SELECT supervisor_id FROM supervisors WHERE user_id=:uid"), {"uid": user["user_id"]}
        ).fetchone()
        if sup_row:
            rows = db.execute(
                text(base + " WHERE p.supervisor_id=:sid ORDER BY p.submitted_at DESC"),
                {"sid": sup_row.supervisor_id},
            ).fetchall()
        else:
            rows = []
    else:
        rows = db.execute(text(base + " ORDER BY p.submitted_at DESC")).fetchall()

    return {"success": True, "projects": [dict(r._mapping) for r in rows]}


@router.patch("/projects/{project_id}/status")
def update_project_status(
    project_id: int,
    body: ProjectStatusUpdate,
    db:   Session = Depends(get_db),
    user: dict    = Depends(require_role("admin")),
):
    set_parts = ["status=:status", "updated_at=CURRENT_TIMESTAMP"]
    params    = {"status": body.status, "project_id": project_id}
    if body.status == "approved":  set_parts.append("approved_at=CURRENT_TIMESTAMP")
    if body.status == "completed": set_parts.append("completed_at=CURRENT_TIMESTAMP")
    if body.supervisor_id:
        set_parts.append("supervisor_id=:supervisor_id")
        params["supervisor_id"] = body.supervisor_id

    db.execute(
        text(f"UPDATE projects SET {', '.join(set_parts)} WHERE project_id=:project_id"),
        params,
    )

    if body.supervisor_id:
        db.execute(
            text("UPDATE students SET supervisor_id=:sid WHERE project_id=:pid"),
            {"sid": body.supervisor_id, "pid": project_id},
        )
        db.execute(
            text("UPDATE supervisors SET current_load=current_load+1 WHERE supervisor_id=:sid"),
            {"sid": body.supervisor_id},
        )

    proj = db.execute(
        text("""SELECT u.user_id, p.title FROM projects p
           JOIN students st ON p.student_id=st.student_id JOIN users u ON st.user_id=u.user_id
           WHERE p.project_id=:pid"""),
        {"pid": project_id},
    ).fetchone()
    if proj:
        label = body.status.replace("_", " ").capitalize()
        db.execute(
            text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
               VALUES (:uid,:pid,'system',:title,:message,'info')"""),
            {
                "uid":   proj.user_id,
                "pid":   project_id,
                "title": f"Project {label}",
                "message": f'Your project "{(proj.title or "")[:60]}" has been {body.status}' +
                           (" and a supervisor assigned." if body.supervisor_id else "."),
            },
        )
    db.commit()
    return {"success": True, "message": f"Project marked as {body.status}."}
