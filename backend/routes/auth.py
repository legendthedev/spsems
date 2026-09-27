import os
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import bcrypt as _bcrypt
from datetime import datetime

from database import get_db
from middleware.auth import create_access_token, get_current_user, require_role
from schemas.schemas import LoginRequest, RegisterAdminRequest
from config import get_settings

router   = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()

def _hash_pw(password: str) -> str:
    return _bcrypt.hashpw(password[:72].encode(), _bcrypt.gensalt()).decode()

def _verify_pw(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain[:72].encode(), hashed.encode())


def _audit(db: Session, user_id, username, role, action, ip, ok: bool):
    try:
        db.execute(
            text("""INSERT INTO audit_log (user_id,username,role,action,ip_address,status)
                   VALUES (:user_id,:username,:role,:action,:ip,:status)"""),
            {"user_id": user_id, "username": username, "role": role,
             "action": action, "ip": ip, "status": "success" if ok else "failure"},
        )
        db.commit()
    except Exception:
        pass


@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    rows = db.execute(
        text("""SELECT u.*,
             s.supervisor_id, s.expertise_areas, s.max_load, s.current_load, s.department AS sup_dept,
             st.student_id, st.matric_number, st.department AS stu_dept, st.level, st.project_id
           FROM users u
           LEFT JOIN supervisors s  ON u.user_id=s.user_id
           LEFT JOIN students    st ON u.user_id=st.user_id
           WHERE u.username=:username AND u.is_active=1"""),
        {"username": body.username},
    ).fetchall()

    ip = request.client.host if request.client else "unknown"

    if not rows:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")

    row = dict(rows[0]._mapping)
    ok = _verify_pw(body.password, row["password"])
    _audit(db, row["user_id"], row["username"], row["role"], "login", ip, ok)

    if not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")

    payload = {
        "user_id":       row["user_id"],
        "username":      row["username"],
        "role":          row["role"],
        "full_name":     row["full_name"],
        "email":         row["email"],
        "supervisor_id": row.get("supervisor_id"),
        "student_id":    row.get("student_id"),
    }
    token = create_access_token(payload)
    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            **payload,
            "sup_dept":        row.get("sup_dept"),
            "stu_dept":        row.get("stu_dept"),
            "matric_number":   row.get("matric_number"),
            "level":           row.get("level"),
            "project_id":      row.get("project_id"),
            "expertise_areas": row.get("expertise_areas"),
            "max_load":        row.get("max_load"),
            "current_load":    row.get("current_load"),
        },
    }


@router.post("/register", status_code=201)
def register(
    body: RegisterAdminRequest,
    db:   Session = Depends(get_db),
    user: dict    = Depends(require_role("admin")),
):
    _do_register(body, db)
    return {"success": True, "message": f"{body.role} registered successfully."}


@router.get("/profile")
def profile(current: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.execute(
        text("""SELECT u.user_id,u.username,u.email,u.full_name,u.role,u.phone,u.avatar_url,u.created_at,
             s.supervisor_id,s.expertise_areas,s.max_load,s.current_load,s.department AS sup_dept,s.bio,
             st.student_id,st.matric_number,st.department AS stu_dept,st.level,st.project_id,st.research_domain
           FROM users u
           LEFT JOIN supervisors s  ON u.user_id=s.user_id
           LEFT JOIN students    st ON u.user_id=st.user_id
           WHERE u.user_id=:user_id"""),
        {"user_id": current["user_id"]},
    ).fetchone()
    if not row:
        raise HTTPException(404, "User not found.")
    return {"success": True, "user": dict(row._mapping)}


@router.patch("/profile/avatar")
async def upload_avatar(
    file: UploadFile  = File(...),
    db:   Session     = Depends(get_db),
    user: dict        = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        raise HTTPException(400, "Only JPG, PNG, GIF, WEBP images are allowed.")
    avatar_dir = os.path.join(settings.upload_dir, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    fname = f"{user['user_id']}{ext}"
    fpath = os.path.join(avatar_dir, fname)
    contents = await file.read()
    with open(fpath, "wb") as fout:
        fout.write(contents)
    avatar_url = f"/uploads/avatars/{fname}"
    db.execute(
        text("UPDATE users SET avatar_url=:url, updated_at=CURRENT_TIMESTAMP WHERE user_id=:uid"),
        {"url": avatar_url, "uid": user["user_id"]},
    )
    db.commit()
    return {"success": True, "avatar_url": avatar_url}


def _do_register(body, db: Session) -> int:
    existing = db.execute(
        text("SELECT user_id FROM users WHERE username=:username OR email=:email"),
        {"username": body.username, "email": body.email},
    ).fetchone()
    if existing:
        raise HTTPException(409, "Username or email already exists.")

    if body.role == "student" and body.matric_number:
        dup = db.execute(
            text("SELECT student_id FROM students WHERE matric_number=:m"),
            {"m": body.matric_number},
        ).fetchone()
        if dup:
            raise HTTPException(409, "Matric number already registered.")

    hashed = _hash_pw(body.password)
    result = db.execute(
        text("""INSERT INTO users (username,email,password,role,full_name,phone,is_active)
           VALUES (:username,:email,:password,:role,:full_name,:phone,:is_active)"""),
        {
            "username":  body.username,
            "email":     body.email.lower(),
            "password":  hashed,
            "role":      body.role,
            "full_name": body.full_name,
            "phone":     body.phone,
            "is_active": 1,
        },
    )
    db.commit()
    user_id = getattr(result, "lastrowid", None)
    if not user_id:
        row = db.execute(text("SELECT user_id FROM users WHERE username=:username"), {"username": body.username}).fetchone()
        user_id = row[0] if row else None

    if body.role == "supervisor":
        import json
        ev = json.dumps([e.strip().lower() for e in (body.expertise_areas or "").split(",") if e.strip()])
        db.execute(
            text("""INSERT INTO supervisors (user_id,department,expertise_areas,expertise_vector,max_load,bio)
               VALUES (:user_id,:department,:expertise_areas,:expertise_vector,:max_load,:bio)"""),
            {
                "user_id":          user_id,
                "department":       body.department or "Computer Science",
                "expertise_areas":  body.expertise_areas or "",
                "expertise_vector": ev,
                "max_load":         body.max_load or 5,
                "bio":              body.bio,
            },
        )
    elif body.role == "student":
        db.execute(
            text("""INSERT INTO students (user_id,matric_number,department,level,research_domain,enrollment_year)
               VALUES (:user_id,:matric_number,:department,:level,:research_domain,:enrollment_year)"""),
            {
                "user_id":         user_id,
                "matric_number":   body.matric_number or "",
                "department":      body.department or "Computer Science",
                "level":           body.level or "400",
                "research_domain": body.research_domain,
                "enrollment_year": body.enrollment_year or datetime.now().year,
            },
        )
    db.commit()
    return user_id
