from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from middleware.auth import get_current_user, require_role
from schemas.schemas import RegisterPublicRequest, ToggleActiveRequest
from config import get_settings
from routes.auth import _do_register

router   = APIRouter(tags=["Registration"])
settings = get_settings()


@router.post("/auth/register-public", status_code=201)
def register_public(body: RegisterPublicRequest, db: Session = Depends(get_db)):
    if body.role == "admin":
        if not body.admin_code or body.admin_code.strip() != settings.admin_reg_code:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid admin registration code.")

    # Force is_active=0 so HOD must approve
    orig_active = 1
    # patch _do_register — we override after insert
    user_id = _do_register(body, db)
    db.execute(text("UPDATE users SET is_active=0 WHERE user_id=:uid"), {"uid": user_id})
    db.commit()

    # Notify active admins
    admins = db.execute(
        text("SELECT user_id FROM users WHERE role='admin' AND is_active=1")
    ).fetchall()
    for admin in admins:
        db.execute(
            text("""INSERT INTO alerts (user_id,alert_type,title,message,severity)
               VALUES (:user_id,:alert_type,:title,:message,:severity)"""),
            {
                "user_id":    admin.user_id,
                "alert_type": "system",
                "title":      f"New {body.role.capitalize()} Registration",
                "message":    f"{body.full_name} (@{body.username}) registered as {body.role} — awaiting approval.",
                "severity":   "info",
            },
        )
    db.commit()
    return {
        "success": True,
        "message": (
            "Registration submitted. Your account is pending HOD/admin approval. "
            "You will be notified once activated."
        ),
        "user_id": user_id,
    }


@router.get("/admin/pending-users")
def get_pending_users(db: Session = Depends(get_db), user: dict = Depends(require_role("admin"))):
    rows = db.execute(
        text("""SELECT u.user_id,u.username,u.full_name,u.email,u.role,u.phone,u.created_at,
             s.expertise_areas, s.department AS sup_dept, s.max_load,
             st.matric_number, st.department AS stu_dept, st.level, st.research_domain
           FROM users u
           LEFT JOIN supervisors s  ON u.user_id=s.user_id
           LEFT JOIN students    st ON u.user_id=st.user_id
           WHERE u.is_active=0
           ORDER BY u.created_at DESC""")
    ).fetchall()
    return {"success": True, "pending": [dict(r._mapping) for r in rows]}


@router.patch("/admin/users/{user_id}/activate")
def toggle_user_active(
    user_id: int,
    body:    ToggleActiveRequest,
    db:      Session = Depends(get_db),
    user:    dict    = Depends(require_role("admin")),
):
    db.execute(
        text("UPDATE users SET is_active=:is_active WHERE user_id=:user_id"),
        {"is_active": 1 if body.is_active else 0, "user_id": user_id},
    )
    status_word = "activated" if body.is_active else "deactivated"
    db.execute(
        text("""INSERT INTO alerts (user_id,alert_type,title,message,severity)
           VALUES (:user_id,:alert_type,:title,:message,:severity)"""),
        {
            "user_id":    user_id,
            "alert_type": "system",
            "title":      f"Account {status_word.capitalize()}",
            "message":    (
                f"Your KWASU SPSEMS account has been {status_word} by the administrator. "
                + ("You can now log in." if body.is_active else "Contact the HOD for support.")
            ),
            "severity": "info" if body.is_active else "warning",
        },
    )
    db.commit()
    return {"success": True, "message": f"User {status_word}."}
