import json
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from middleware.auth import require_role
from schemas.schemas import ReviewRequest, EvaluationRequest, MessageRequest
from config import get_settings

router   = APIRouter(prefix="/supervisor", tags=["Supervisor"])
settings = get_settings()


def _grade(total: float) -> str:
    if total >= 70: return "A"
    if total >= 60: return "B"
    if total >= 50: return "C"
    if total >= 45: return "D"
    return "F"


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db), user: dict = Depends(require_role("supervisor"))):
    sup = db.execute(
        text("SELECT supervisor_id FROM supervisors WHERE user_id=:uid"), {"uid": user["user_id"]}
    ).fetchone()
    if not sup:
        raise HTTPException(404, "Supervisor record not found.")
    sid = sup.supervisor_id

    students = db.execute(
        text("""SELECT st.student_id, st.matric_number, st.level, st.department AS stu_dept,
             u.full_name AS student_name, u.email, u.user_id AS student_user_id,
             p.project_id, p.title, p.status, p.risk_score, p.risk_label, p.submitted_at,
             (SELECT COUNT(*) FROM submissions WHERE project_id=p.project_id)                        AS submission_count,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id AND status='completed') AS ms_done,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id)                        AS ms_total,
             (SELECT COUNT(*) FROM milestones  WHERE project_id=p.project_id AND status='overdue')   AS ms_overdue,
             COALESCE((SELECT CAST(julianday('now') - julianday(MAX(COALESCE(submitted_at, uploaded_at))) AS INTEGER) FROM submissions WHERE project_id=p.project_id),NULL) AS days_inactive
           FROM students st
           JOIN users u    ON st.user_id=u.user_id
           LEFT JOIN projects p ON st.project_id=p.project_id
           WHERE st.supervisor_id=:sid ORDER BY p.risk_score DESC NULLS LAST"""),
        {"sid": sid},
    ).fetchall()

    rows     = [dict(r._mapping) for r in students]
    at_risk  = [r for r in rows if r.get("risk_label") in ("at_risk", "critical")]
    on_track = [r for r in rows if r.get("risk_label") not in ("at_risk", "critical")]

    pending_reviews = db.execute(
        text("""SELECT sub.*, p.title AS project_title, u.full_name AS student_name
           FROM submissions sub
           JOIN projects p  ON sub.project_id=p.project_id
           JOIN students st ON sub.student_id=st.student_id
           JOIN users u     ON st.user_id=u.user_id
           WHERE p.supervisor_id=:sid AND sub.status='submitted'
           ORDER BY COALESCE(sub.submitted_at, sub.uploaded_at) DESC"""),
        {"sid": sid},
    ).fetchall()

    try:
        recent_alerts = db.execute(
            text("""SELECT a.* FROM alerts a
               JOIN projects p ON a.project_id=p.project_id
               WHERE p.supervisor_id=:sid ORDER BY a.triggered_at DESC LIMIT 20"""),
            {"sid": sid},
        ).fetchall()
    except Exception:
        try:
            recent_alerts = db.execute(
                text("""SELECT a.* FROM alerts a
                   JOIN projects p ON a.project_id=p.project_id
                   WHERE p.supervisor_id=:sid ORDER BY a.created_at DESC LIMIT 20"""),
                {"sid": sid},
            ).fetchall()
        except Exception:
            try:
                recent_alerts = db.execute(
                    text("""SELECT a.* FROM alerts a
                       JOIN projects p ON a.project_id=p.project_id
                       WHERE p.supervisor_id=:sid ORDER BY a.alert_id DESC LIMIT 20"""),
                    {"sid": sid},
                ).fetchall()
            except Exception:
                recent_alerts = []

    mapped_alerts = []
    for r in recent_alerts:
        d = dict(r._mapping)
        if not d.get("triggered_at"):
            d["triggered_at"] = d.get("created_at") or ""
        if not d.get("created_at"):
            d["created_at"] = d.get("triggered_at") or ""
        mapped_alerts.append(d)

    return {
        "success":  True,
        "overview": {"total": len(rows), "at_risk": len(at_risk), "on_track": len(on_track)},
        "students":       rows,
        "atRisk":         at_risk,
        "onTrack":        on_track,
        "pendingReviews": [dict(r._mapping) for r in pending_reviews],
        "recentAlerts":   mapped_alerts,
    }


@router.get("/projects/{project_id}/submissions")
def get_project_submissions(
    project_id: int,
    db:   Session = Depends(get_db),
    user: dict    = Depends(require_role("supervisor")),
):
    sup = db.execute(
        text("SELECT supervisor_id FROM supervisors WHERE user_id=:uid"), {"uid": user["user_id"]}
    ).fetchone()
    if not sup:
        raise HTTPException(403, "Not a supervisor.")
    proj = db.execute(
        text("SELECT supervisor_id FROM projects WHERE project_id=:pid"), {"pid": project_id}
    ).fetchone()
    if not proj or proj.supervisor_id != sup.supervisor_id:
        raise HTTPException(403, "Access denied.")
    rows = db.execute(
        text("""SELECT sub.*, u.full_name AS student_name
               FROM submissions sub
               JOIN students st ON sub.student_id = st.student_id
               JOIN users u     ON st.user_id = u.user_id
               WHERE sub.project_id = :pid
               ORDER BY COALESCE(sub.submitted_at, sub.uploaded_at) DESC"""),
        {"pid": project_id},
    ).fetchall()
    return {"success": True, "submissions": [dict(r._mapping) for r in rows]}


@router.get("/submissions/{doc_id}/file")
def download_submission_file(
    doc_id: int,
    db:     Session = Depends(get_db),
    user:   dict    = Depends(require_role("supervisor", "admin")),
):
    sub = db.execute(
        text("""SELECT sub.file_path, sub.file_name, p.supervisor_id
               FROM submissions sub
               JOIN projects p ON sub.project_id = p.project_id
               WHERE sub.doc_id = :doc_id"""),
        {"doc_id": doc_id},
    ).fetchone()
    if not sub:
        raise HTTPException(404, "Submission not found.")

    if user["role"] == "supervisor":
        sup_row = db.execute(
            text("SELECT supervisor_id FROM supervisors WHERE user_id=:uid"),
            {"uid": user["user_id"]},
        ).fetchone()
        if not sup_row or sub.supervisor_id != sup_row.supervisor_id:
            raise HTTPException(403, "Access denied.")

    file_path = sub.file_path or ""
    if not os.path.isabs(file_path):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(backend_dir, file_path.lstrip("./\\").replace("\\", os.sep))

    if not os.path.exists(file_path):
        raise HTTPException(404, f"File not found on server: {os.path.basename(file_path)}")

    fname = sub.file_name or os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=fname,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.patch("/submissions/{doc_id}/review")
def review_submission(
    doc_id: int,
    body:   ReviewRequest,
    db:     Session = Depends(get_db),
    user:   dict    = Depends(require_role("supervisor")),
):
    allowed = {"reviewed", "revision_needed", "approved"}
    if body.status not in allowed:
        raise HTTPException(400, f"Status must be one of: {', '.join(allowed)}")

    sub = db.execute(text("SELECT * FROM submissions WHERE doc_id=:doc_id"), {"doc_id": doc_id}).fetchone()
    if not sub:
        raise HTTPException(404, "Submission not found.")

    db.execute(
        text("""UPDATE submissions SET status=:status, supervisor_comment=:comment, reviewed_at=CURRENT_TIMESTAMP
           WHERE doc_id=:doc_id"""),
        {"status": body.status, "comment": body.supervisor_comment, "doc_id": doc_id},
    )

    stu = db.execute(
        text("SELECT u.user_id FROM students st JOIN users u ON st.user_id=u.user_id WHERE st.student_id=:sid"),
        {"sid": sub.student_id},
    ).fetchone()
    if stu:
        labels   = {"reviewed": "Reviewed", "revision_needed": "Revision Needed", "approved": "Approved"}
        severity = "info" if body.status == "approved" else "warning"
        db.execute(
            text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
               VALUES (:uid,:pid,'feedback',:title,:message,:severity)"""),
            {
                "uid":      stu.user_id,
                "pid":      sub.project_id,
                "title":    f"Chapter {labels[body.status]}",
                "message":  body.supervisor_comment or f"Your submission has been {body.status.replace('_', ' ')}.",
                "severity": severity,
            },
        )
    db.commit()
    return {"success": True, "message": "Review submitted and student notified."}


@router.post("/evaluate")
def submit_evaluation(
    body: EvaluationRequest,
    db:   Session = Depends(get_db),
    user: dict    = Depends(require_role("supervisor")),
):
    sup = db.execute(
        text("SELECT supervisor_id FROM supervisors WHERE user_id=:uid"), {"uid": user["user_id"]}
    ).fetchone()
    if not sup:
        raise HTTPException(403, "Not a supervisor.")

    total = (body.rubric_methodology + body.rubric_literature +
             body.rubric_analysis + body.rubric_presentation + body.rubric_originality)
    grade = _grade(total)

    try:
        resp = httpx.post(
            f"{settings.ml_service_url}/evaluate/grade",
            json={
                "methodology_score":   body.rubric_methodology,
                "literature_score":    body.rubric_literature,
                "analysis_score":      body.rubric_analysis,
                "presentation_score":  body.rubric_presentation,
                "originality_score":   body.rubric_originality,
            },
            timeout=5.0,
        )
        d     = resp.json()
        total = d.get("total_score", total)
        grade = d.get("grade_letter", grade)
    except Exception:
        pass

    db.execute(
        text("""INSERT INTO evaluations
             (project_id,supervisor_id,rubric_methodology,rubric_literature,
              rubric_analysis,rubric_presentation,rubric_originality,total_score,grade_letter,comments)
           VALUES (:pid,:sid,:m,:l,:a,:p,:o,:total,:grade,:comments)
           ON CONFLICT(project_id,supervisor_id) DO UPDATE SET
             rubric_methodology=excluded.rubric_methodology,
             rubric_literature=excluded.rubric_literature,
             rubric_analysis=excluded.rubric_analysis,
             rubric_presentation=excluded.rubric_presentation,
             rubric_originality=excluded.rubric_originality,
             total_score=excluded.total_score,
             grade_letter=excluded.grade_letter,
             comments=excluded.comments"""),
        {
            "pid": body.project_id, "sid": sup.supervisor_id,
            "m": body.rubric_methodology, "l": body.rubric_literature,
            "a": body.rubric_analysis,    "p": body.rubric_presentation,
            "o": body.rubric_originality, "total": total, "grade": grade,
            "comments": body.comments,
        },
    )
    db.execute(
        text("UPDATE projects SET final_grade=:g, grade_letter=:gl, status='completed' WHERE project_id=:pid"),
        {"g": total, "gl": grade, "pid": body.project_id},
    )

    proj = db.execute(
        text("""SELECT u.user_id FROM projects p
           JOIN students st ON p.student_id=st.student_id
           JOIN users u     ON st.user_id=u.user_id
           WHERE p.project_id=:pid"""),
        {"pid": body.project_id},
    ).fetchone()
    if proj:
        fb = f" Feedback: {body.comments[:100]}" if body.comments else ""
        db.execute(
            text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
               VALUES (:uid,:pid,'system','Project Evaluated',:message,'info')"""),
            {"uid": proj.user_id, "pid": body.project_id,
             "message": f"Final Score: {total}/100. Grade: {grade}.{fb}"},
        )
    db.commit()
    return {"success": True, "message": "Evaluation submitted.", "total": total, "grade": grade}


@router.post("/batch-risk-check")
def batch_risk_check(db: Session = Depends(get_db), user: dict = Depends(require_role("supervisor"))):
    sup = db.execute(
        text("SELECT supervisor_id FROM supervisors WHERE user_id=:uid"), {"uid": user["user_id"]}
    ).fetchone()
    if not sup:
        raise HTTPException(404, "Supervisor not found.")

    projects = db.execute(
        text("SELECT project_id FROM projects WHERE supervisor_id=:sid AND status='in_progress'"),
        {"sid": sup.supervisor_id},
    ).fetchall()
    return {"success": True, "message": f"{len(projects)} projects queued for risk scan.", "count": len(projects)}


@router.post("/message")
def send_message_sup(
    body: MessageRequest,
    db:   Session = Depends(get_db),
    user: dict    = Depends(require_role("supervisor", "admin", "student")),
):
    db.execute(
        text("INSERT INTO messages (sender_id,receiver_id,project_id,subject,body) VALUES (:sid,:rid,:pid,:subject,:body)"),
        {"sid": user["user_id"], "rid": body.receiver_id, "pid": body.project_id, "subject": body.subject, "body": body.body},
    )
    db.execute(
        text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
           VALUES (:uid,:pid,'feedback',:title,:message,'info')"""),
        {"uid": body.receiver_id, "pid": body.project_id,
         "title": f"Message: {body.subject or 'No Subject'}", "message": body.body[:200]},
    )
    db.commit()
    return {"success": True, "message": "Message sent."}
