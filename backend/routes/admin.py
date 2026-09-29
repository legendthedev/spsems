import os
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from middleware.auth import require_role
from schemas.schemas import ManualAllocateRequest
from config import get_settings

router   = APIRouter(prefix="/admin", tags=["Admin"])
settings = get_settings()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), user: dict = Depends(require_role("admin"))):
    def scalar(q):
        return db.execute(text(q)).fetchone()[0]

    stats = {
        "total_students":     scalar("SELECT COUNT(*) FROM students"),
        "total_supervisors":  scalar("SELECT COUNT(*) FROM supervisors"),
        "total_projects":     scalar("SELECT COUNT(*) FROM projects"),
        "at_risk_count":      scalar("SELECT COUNT(*) FROM projects WHERE risk_label IN ('at_risk','critical')"),
        "pending_approvals":  scalar("SELECT COUNT(*) FROM projects WHERE status='pending'"),
        "completed_projects": scalar("SELECT COUNT(*) FROM projects WHERE status='completed'"),
        "unassigned":         scalar("SELECT COUNT(*) FROM projects WHERE supervisor_id IS NULL AND status='approved'"),
        "pending_users":      scalar("SELECT COUNT(*) FROM users WHERE is_active=0"),
    }
    dept_dist = db.execute(text("SELECT department AS dept, COUNT(*) AS count FROM students GROUP BY department")).fetchall()
    risk_dist = db.execute(text("SELECT COALESCE(risk_label,'unscanned') AS risk_label, COUNT(*) AS count FROM projects GROUP BY risk_label")).fetchall()
    recent    = db.execute(text("SELECT 'project' AS type, title AS label, submitted_at AS time FROM projects ORDER BY submitted_at DESC LIMIT 5")).fetchall()

    return JSONResponse(
        content={
            "success":         True,
            "stats":           stats,
            "dept_dist":       [dict(r._mapping) for r in dept_dist],
            "risk_dist":       [dict(r._mapping) for r in risk_dist],
            "recent_activity": [dict(r._mapping) for r in recent],
        },
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )


@router.get("/users")
def get_all_users(db: Session = Depends(get_db), user: dict = Depends(require_role("admin"))):
    rows = db.execute(
        text("""SELECT u.user_id, u.username, u.full_name, u.email, u.role,
                  u.is_active, u.phone, u.created_at,
                  s.supervisor_id, s.expertise_areas, s.max_load, s.current_load, s.department AS sup_dept,
                  st.student_id, st.matric_number, st.department AS stu_dept, st.level, st.research_domain,
                  st.supervisor_id, st.co_supervisor_id,
                  u_sup.full_name AS supervisor_name,
                  u_co.full_name AS co_supervisor_name
           FROM users u
           LEFT JOIN supervisors s        ON u.user_id=s.user_id
           LEFT JOIN students    st       ON u.user_id=st.user_id
           LEFT JOIN supervisors sup_main ON st.supervisor_id=sup_main.supervisor_id
           LEFT JOIN users       u_sup    ON sup_main.user_id=u_sup.user_id
           LEFT JOIN supervisors sup_co   ON st.co_supervisor_id=sup_co.supervisor_id
           LEFT JOIN users       u_co     ON sup_co.user_id=u_co.user_id
           ORDER BY u.created_at DESC""")
    ).fetchall()
    return {"success": True, "users": [dict(r._mapping) for r in rows]}



@router.get("/supervisors")
def get_supervisors(db: Session = Depends(get_db), user: dict = Depends(require_role("admin"))):
    rows = db.execute(
        text("""SELECT s.*, u.full_name, u.email, u.is_active,
             (SELECT COUNT(*) FROM projects p
              WHERE p.supervisor_id=s.supervisor_id
              AND p.status NOT IN ('completed','rejected')) AS active_projects
           FROM supervisors s
           JOIN users u ON s.user_id=u.user_id
           ORDER BY u.full_name""")
    ).fetchall()
    return {"success": True, "supervisors": [dict(r._mapping) for r in rows]}


@router.post("/placement-engine")
def run_placement_engine(db: Session = Depends(get_db), user: dict = Depends(require_role("admin"))):
    unassigned = db.execute(
        text("""SELECT p.project_id, p.title, p.keywords, p.keyword_vector,
                  p.student_id, u.full_name AS student_name
           FROM projects p
           JOIN students st ON p.student_id=st.student_id
           JOIN users u     ON st.user_id=u.user_id
           WHERE p.status='approved' AND p.supervisor_id IS NULL""")
    ).fetchall()

    if not unassigned:
        return {"success": True, "message": "No unassigned approved projects.", "allocations": []}

    supervisors = db.execute(
        text("""SELECT s.supervisor_id AS id, s.expertise_areas, s.expertise_vector,
                  s.max_load, s.current_load, s.department, u.full_name AS name
           FROM supervisors s
           JOIN users u ON s.user_id=u.user_id
           WHERE s.current_load < s.max_load AND u.is_active=1""")
    ).fetchall()

    if not supervisors:
        return {"success": True, "message": "No supervisors with available capacity.", "allocations": []}

    sup_list = []
    for s in supervisors:
        ev = s.expertise_vector
        try:
            ev = json.loads(ev) if ev else []
        except Exception:
            ev = [e.strip().lower() for e in (s.expertise_areas or "").split(",") if e.strip()]
        sup_list.append({
            "id": s.id, "name": s.name, "department": s.department,
            "expertise_areas": s.expertise_areas, "expertise_vector": ev,
            "current_load": s.current_load, "max_load": s.max_load,
        })

    load_tracker = {s["id"]: s["current_load"] for s in sup_list}
    allocations  = []

    for proj in unassigned:
        p = dict(proj._mapping)
        try:
            kw = json.loads(p.get("keyword_vector") or "[]")
        except Exception:
            kw = [k.strip().lower() for k in (p.get("keywords") or p["title"]).split(",") if k.strip()]

        available = [s for s in sup_list if load_tracker[s["id"]] < s["max_load"]]
        if not available:
            break

        match_data = None
        try:
            resp = httpx.post(
                f"{settings.ml_service_url}/match/supervisors",
                json={"student_keywords": kw, "supervisors": available},
                timeout=8.0,
            )
            match_data = resp.json()
        except Exception:
            def _overlap(sup):
                sup_kws = set(sup["expertise_vector"])
                return len(sup_kws & set(kw)) / max(len(sup_kws | set(kw)), 1)
            ranked     = sorted(available, key=_overlap, reverse=True)
            if not ranked:
                continue
            best       = ranked[0]
            score      = round(_overlap(best), 4)
            match_data = {
                "top_match": {**best, "cosine_similarity": score, "workload_available": True},
                "matches":   [{**s, "cosine_similarity": round(_overlap(s), 4)} for s in ranked[:3]],
            }

        top = match_data.get("top_match")
        if not top:
            continue

        best_id   = top.get("supervisor_id") or top.get("id")
        cos_score = top.get("cosine_similarity", 0.0)

        try:
            db.execute(
                text("UPDATE projects SET supervisor_id=:sid, status='in_progress' WHERE project_id=:pid"),
                {"sid": best_id, "pid": p["project_id"]},
            )
            db.execute(
                text("UPDATE students SET supervisor_id=:sid WHERE student_id=:student_id"),
                {"sid": best_id, "student_id": p["student_id"]},
            )
            db.execute(
                text("UPDATE supervisors SET current_load=current_load+1 WHERE supervisor_id=:sid"),
                {"sid": best_id},
            )
            db.execute(
                text("""INSERT INTO allocation_history
                     (student_id,supervisor_id,match_score,allocated_by,allocation_method)
                   VALUES (:student_id,:sid,:score,:by,'ai_auto')"""),
                {"student_id": p["student_id"], "sid": best_id, "score": cos_score, "by": user["user_id"]},
            )
            stu_user = db.execute(
                text("SELECT u.user_id FROM students st JOIN users u ON st.user_id=u.user_id WHERE st.student_id=:sid"),
                {"sid": p["student_id"]},
            ).fetchone()
            if stu_user:
                db.execute(
                    text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
                       VALUES (:uid,:pid,'allocation','Supervisor Assigned',:message,'info')"""),
                    {
                        "uid": stu_user.user_id, "pid": p["project_id"],
                        "message": f"Matched with {top.get('name','your supervisor')} ({top.get('department','')}). Match Score: {cos_score*100:.1f}%.",
                    },
                )
            db.commit()
            load_tracker[best_id] += 1
            allocations.append({
                "project_id":      p["project_id"],
                "project_title":   p["title"],
                "student_name":    p["student_name"],
                "supervisor_id":   best_id,
                "supervisor_name": top.get("name"),
                "match_score":     cos_score,
                "all_matches":     match_data.get("matches", [])[:3],
            })
        except Exception as e:
            db.rollback()
            print(f"Allocation error for project {p['project_id']}: {e}")

    return {
        "success":     True,
        "message":     f"Placement engine complete. {len(allocations)} student(s) matched.",
        "allocations": allocations,
    }


@router.post("/manual-allocate")
def manual_allocate(
    body: ManualAllocateRequest,
    db:   Session = Depends(get_db),
    user: dict    = Depends(require_role("admin")),
):
    sup = db.execute(
        text("SELECT * FROM supervisors WHERE supervisor_id=:sid"), {"sid": body.supervisor_id}
    ).fetchone()
    if not sup:
        raise HTTPException(404, "Supervisor not found.")
    if sup.current_load >= sup.max_load:
        raise HTTPException(400, "Supervisor has reached maximum student capacity.")

    proj = db.execute(
        text("SELECT * FROM projects WHERE project_id=:pid"), {"pid": body.project_id}
    ).fetchone()
    if not proj:
        raise HTTPException(404, "Project not found.")

    db.execute(
        text("UPDATE projects SET supervisor_id=:sid, status='in_progress', approved_at=CURRENT_TIMESTAMP WHERE project_id=:pid"),
        {"sid": body.supervisor_id, "pid": body.project_id},
    )
    db.execute(
        text("UPDATE students SET supervisor_id=:sid WHERE student_id=:student_id"),
        {"sid": body.supervisor_id, "student_id": proj.student_id},
    )
    db.execute(
        text("UPDATE supervisors SET current_load=current_load+1 WHERE supervisor_id=:sid"),
        {"sid": body.supervisor_id},
    )
    db.execute(
        text("""INSERT INTO allocation_history (student_id,supervisor_id,match_score,allocated_by,allocation_method)
           VALUES (:student_id,:sid,0,:by,'manual_admin')"""),
        {"student_id": proj.student_id, "sid": body.supervisor_id, "by": user["user_id"]},
    )

    if body.co_supervisor_id:
        co_sup = db.execute(text("SELECT * FROM supervisors WHERE supervisor_id=:sid"), {"sid": body.co_supervisor_id}).fetchone()
        if co_sup:
            db.execute(
                text("UPDATE projects SET co_supervisor_id=:sid WHERE project_id=:pid"),
                {"sid": body.co_supervisor_id, "pid": body.project_id},
            )
            db.execute(
                text("UPDATE students SET co_supervisor_id=:sid WHERE student_id=:student_id"),
                {"sid": body.co_supervisor_id, "student_id": proj.student_id},
            )
            db.execute(
                text("UPDATE supervisors SET current_load=current_load+1 WHERE supervisor_id=:sid"),
                {"sid": body.co_supervisor_id},
            )
            co_sup_user = db.execute(text("SELECT user_id FROM supervisors WHERE supervisor_id=:sid"), {"sid": body.co_supervisor_id}).fetchone()
            if co_sup_user:
                db.execute(
                    text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
                       VALUES (:uid,:pid,'allocation','Co-Supervisor Assignment',:msg,'info')"""),
                    {"uid": co_sup_user.user_id, "pid": body.project_id, "msg": f'You have been assigned as co-supervisor for project: "{proj.title[:60]}"'},
                )

    stu = db.execute(
        text("SELECT u.user_id FROM students st JOIN users u ON st.user_id=u.user_id WHERE st.student_id=:sid"),
        {"sid": proj.student_id},
    ).fetchone()
    if stu:
        sup_user = db.execute(
            text("SELECT full_name FROM users WHERE user_id=(SELECT user_id FROM supervisors WHERE supervisor_id=:sid)"),
            {"sid": body.supervisor_id},
        ).fetchone()
        db.execute(
            text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
               VALUES (:uid,:pid,'allocation','Supervisor Assigned (Manual)',:message,'info')"""),
            {
                "uid": stu.user_id, "pid": body.project_id,
                "message": f"The HOD has manually assigned {sup_user.full_name if sup_user else 'a supervisor'} to your project.",
            },
        )

    db.commit()
    return {"success": True, "message": "Manual allocation successful."}


@router.get("/ml-metrics")
def get_ml_metrics(user: dict = Depends(require_role("admin"))):
    try:
        resp = httpx.get(f"{settings.ml_service_url}/metrics", timeout=25.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise HTTPException(503, "ML service is offline. Start the ML service on port 8001.")
    except Exception as e:
        raise HTTPException(503, f"ML service error: {str(e)}")


@router.post("/ml-retrain/{model_name}")
def retrain_ml_model(model_name: str, user: dict = Depends(require_role("admin"))):
    allowed = {"xgboost", "random_forest"}
    if model_name not in allowed:
        raise HTTPException(400, f"Unknown model. Valid: {', '.join(allowed)}")
    try:
        resp = httpx.post(f"{settings.ml_service_url}/retrain/{model_name}", timeout=60.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise HTTPException(503, "ML service is offline.")
    except Exception as e:
        raise HTTPException(503, f"Retrain failed: {str(e)}")


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db), user: dict = Depends(require_role("admin"))):
    def scalar(q, params=None):
        try:
            row = db.execute(text(q), params or {}).fetchone()
            return row[0] if (row and row[0] is not None) else 0
        except Exception:
            return 0

    is_postgres = bool(os.getenv("DATABASE_URL") and ("postgres" in os.getenv("DATABASE_URL")))

    # ── Project status funnel ──────────────────────────────────────────────
    try:
        status_rows = db.execute(text(
            "SELECT status, COUNT(*) AS cnt FROM projects GROUP BY status"
        )).fetchall()
        status_dist = [dict(r._mapping) for r in status_rows]
    except Exception:
        status_dist = []

    # ── Submissions per week (last 8 weeks) ───────────────────────────────
    weekly_subs = []
    try:
        if is_postgres:
            sql = """SELECT to_char(COALESCE(submitted_at, uploaded_at, CURRENT_TIMESTAMP), 'YYYY-"W"IW') AS week, COUNT(*) AS cnt
                     FROM submissions
                     WHERE COALESCE(submitted_at, uploaded_at) >= CURRENT_TIMESTAMP - INTERVAL '56 days'
                     GROUP BY week ORDER BY week"""
        else:
            sql = """SELECT strftime('%Y-W%W', COALESCE(submitted_at, uploaded_at, datetime('now'))) AS week, COUNT(*) AS cnt
                     FROM submissions
                     WHERE COALESCE(submitted_at, uploaded_at, datetime('now')) >= date('now','-56 days')
                     GROUP BY week ORDER BY week"""
        weekly_rows = db.execute(text(sql)).fetchall()
        weekly_subs = [dict(r._mapping) for r in weekly_rows]
    except Exception:
        weekly_subs = []

    # ── Submission chapter breakdown ──────────────────────────────────────
    try:
        chapter_rows = db.execute(text(
            "SELECT COALESCE(chapter,'unknown') AS chapter, COUNT(*) AS cnt FROM submissions GROUP BY chapter"
        )).fetchall()
        chapter_dist = [dict(r._mapping) for r in chapter_rows]
    except Exception:
        chapter_dist = []

    # ── Avg review turnaround per supervisor (days) ───────────────────────
    turnaround = []
    try:
        if is_postgres:
            sql = """SELECT u.full_name AS supervisor_name,
                            COUNT(*) AS total_reviewed,
                            ROUND(CAST(AVG(EXTRACT(EPOCH FROM (sub.reviewed_at - COALESCE(sub.submitted_at, sub.uploaded_at))) / 86400) AS NUMERIC), 1) AS avg_days
                     FROM submissions sub
                     JOIN projects p ON sub.project_id=p.project_id
                     JOIN supervisors s ON p.supervisor_id=s.supervisor_id
                     JOIN users u ON s.user_id=u.user_id
                     WHERE sub.reviewed_at IS NOT NULL
                     GROUP BY u.full_name ORDER BY avg_days"""
        else:
            sql = """SELECT u.full_name AS supervisor_name,
                            COUNT(*) AS total_reviewed,
                            ROUND(AVG(CAST(julianday(sub.reviewed_at) - julianday(COALESCE(sub.submitted_at, sub.uploaded_at)) AS REAL)),1) AS avg_days
                     FROM submissions sub
                     JOIN projects p ON sub.project_id=p.project_id
                     JOIN supervisors s ON p.supervisor_id=s.supervisor_id
                     JOIN users u ON s.user_id=u.user_id
                     WHERE sub.reviewed_at IS NOT NULL
                     GROUP BY u.full_name ORDER BY avg_days"""
        turnaround_rows = db.execute(text(sql)).fetchall()
        turnaround = [dict(r._mapping) for r in turnaround_rows]
    except Exception:
        turnaround = []

    # ── Supervisor workload ───────────────────────────────────────────────
    try:
        workload_rows = db.execute(text(
            """SELECT u.full_name AS name, s.current_load, s.max_load,
                      ROUND(CAST(s.current_load AS REAL)/MAX(s.max_load,1)*100,0) AS pct
               FROM supervisors s JOIN users u ON s.user_id=u.user_id
               WHERE u.is_active=1
               ORDER BY pct DESC"""
        )).fetchall()
        workload = [dict(r._mapping) for r in workload_rows]
    except Exception:
        workload = []

    # ── Milestone completion ──────────────────────────────────────────────
    ms_total     = scalar("SELECT COUNT(*) FROM milestones")
    ms_completed = scalar("SELECT COUNT(*) FROM milestones WHERE status='completed'")
    ms_overdue   = scalar("SELECT COUNT(*) FROM milestones WHERE status='overdue'")
    ms_pending   = ms_total - ms_completed - ms_overdue

    # ── Login activity (last 7 days) ──────────────────────────────────────
    login_activity = []
    try:
        if is_postgres:
            sql = """SELECT to_char(logged_at, 'YYYY-MM-DD') AS day, COUNT(*) AS cnt
                     FROM audit_log
                     WHERE action='login' AND status='success'
                       AND logged_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
                     GROUP BY day ORDER BY day"""
        else:
            sql = """SELECT strftime('%Y-%m-%d', logged_at) AS day, COUNT(*) AS cnt
                     FROM audit_log
                     WHERE action='login' AND status='success'
                       AND logged_at >= date('now','-7 days')
                     GROUP BY day ORDER BY day"""
        login_rows = db.execute(text(sql)).fetchall()
        login_activity = [dict(r._mapping) for r in login_rows]
    except Exception:
        login_activity = []

    # ── Alert severity distribution ───────────────────────────────────────
    try:
        alert_rows = db.execute(text(
            "SELECT severity, COUNT(*) AS cnt FROM alerts GROUP BY severity"
        )).fetchall()
        alert_dist = [dict(r._mapping) for r in alert_rows]
    except Exception:
        alert_dist = []

    # ── Submission status breakdown ───────────────────────────────────────
    try:
        sub_status_rows = db.execute(text(
            "SELECT status, COUNT(*) AS cnt FROM submissions GROUP BY status"
        )).fetchall()
        sub_status_dist = [dict(r._mapping) for r in sub_status_rows]
    except Exception:
        sub_status_dist = []

    # ── Top-level KPIs ────────────────────────────────────────────────────
    total_submissions  = scalar("SELECT COUNT(*) FROM submissions")
    try:
        avg_chapters_done = round(
            scalar("SELECT AVG(chapter_count) FROM (SELECT project_id, COUNT(DISTINCT chapter) AS chapter_count FROM submissions GROUP BY project_id)") or 0,
            1,
        )
    except Exception:
        avg_chapters_done = 0.0

    return {
        "success": True,
        "kpis": {
            "total_submissions":  total_submissions,
            "avg_chapters_done":  avg_chapters_done,
            "ms_total":           ms_total,
            "ms_completed":       ms_completed,
            "ms_overdue":         ms_overdue,
            "ms_pending":         ms_pending,
            "ms_completion_pct":  round(ms_completed / max(ms_total, 1) * 100, 1) if ms_total > 0 else 0,
        },
        "status_dist":    status_dist,
        "weekly_subs":    weekly_subs,
        "chapter_dist":   chapter_dist,
        "turnaround":     turnaround,
        "workload":       workload,
        "login_activity": login_activity,
        "alert_dist":     alert_dist,
        "sub_status_dist": sub_status_dist,
    }


@router.get("/allocation-history")
def get_allocation_history(db: Session = Depends(get_db), user: dict = Depends(require_role("admin"))):
    rows = db.execute(
        text("""SELECT ah.*, u_st.full_name AS student_name, st.matric_number,
                  u_sup.full_name AS supervisor_name, sup.department,
                  p.title AS project_title
           FROM allocation_history ah
           JOIN students    st    ON ah.student_id=st.student_id
           JOIN users       u_st  ON st.user_id=u_st.user_id
           JOIN supervisors sup   ON ah.supervisor_id=sup.supervisor_id
           JOIN users       u_sup ON sup.user_id=u_sup.user_id
           LEFT JOIN projects p   ON st.project_id=p.project_id
           ORDER BY ah.allocated_at DESC""")
    ).fetchall()
    return {"success": True, "history": [dict(r._mapping) for r in rows]}
