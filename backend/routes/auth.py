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
    if not plain or not hashed:
        return False
    # 1. Exact match
    try:
        if _bcrypt.checkpw(plain[:72].encode(), hashed.encode()):
            return True
    except Exception:
        pass
    # 2. Case-insensitive surname variations (lowercase, uppercase, capitalized, stripped)
    variants = [plain.strip(), plain.lower(), plain.upper(), plain.capitalize()]
    for var in variants:
        try:
            if _bcrypt.checkpw(var[:72].encode(), hashed.encode()):
                return True
        except Exception:
            pass
    return False


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
    uname = body.username.strip().lower()
    rows = db.execute(
        text("""SELECT u.*,
             inst.name AS institution_name, inst.code AS institution_code, inst.slug AS institution_slug,
             inst.logo_url AS institution_logo, inst.primary_color AS institution_primary_color,
             inst.verification_token AS inst_verification_token, inst.is_verified AS inst_is_verified, inst.status AS inst_status,
             s.supervisor_id, s.expertise_areas, s.max_load, s.current_load, s.department AS sup_dept,
             st.student_id, st.matric_number, st.department AS stu_dept, st.level, st.project_id,
             st.supervisor_id AS student_sup_id, st.co_supervisor_id
           FROM users u
           LEFT JOIN institutions inst ON u.institution_id=inst.institution_id
           LEFT JOIN supervisors s  ON u.user_id=s.user_id
           LEFT JOIN students    st ON u.user_id=st.user_id
           WHERE (LOWER(u.username)=:uname OR LOWER(u.email)=:uname OR (u.role='student' AND LOWER(st.matric_number)=:uname))
             AND u.is_active=1"""),
        {"uname": uname},
    ).fetchall()

    ip = request.client.host if request.client else "unknown"

    if not rows:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")

    # Match institution if slug provided
    row = None
    if body.institution_slug:
        req_slug = body.institution_slug.strip().lower()
        for r in rows:
            u_inst_slug = (r.institution_slug or "").strip().lower()
            if u_inst_slug == req_slug or (req_slug == "kwasu" and not u_inst_slug):
                row = dict(r._mapping)
                break
    if not row:
        row = dict(rows[0]._mapping)

    ok = _verify_pw(body.password, row["password"])
    _audit(db, row["user_id"], row["username"], row["role"], "login", ip, ok)

    if not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")

    # Verification token handling & node activation
    token_submitted = (body.verification_token or "").strip()
    inst_token = (row.get("inst_verification_token") or "").strip()
    is_verified = bool(row.get("inst_is_verified"))
    inst_status = row.get("inst_status") or "active"

    if token_submitted:
        if inst_token and token_submitted.upper() != inst_token.upper():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Invalid institution verification token. Please check the token provided during onboarding."
            )
        if (not is_verified or inst_status != "active") and row.get("institution_id"):
            db.execute(
                text("""UPDATE institutions 
                       SET is_verified=1, status='active',
                           verified_at=COALESCE(verified_at, CURRENT_TIMESTAMP),
                           activated_at=COALESCE(activated_at, CURRENT_TIMESTAMP)
                       WHERE institution_id=:iid"""),
                {"iid": row["institution_id"]}
            )
            db.commit()
            row["inst_is_verified"] = 1
            row["inst_status"] = "active"
    elif inst_status == "pending_verification" and not is_verified and row.get("role") == "admin":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This institution portal is pending domain verification. Please enter the verification token generated during onboarding to activate."
        )

    payload = {
        "user_id":          row["user_id"],
        "username":         row["username"],
        "role":             row["role"],
        "full_name":        row["full_name"],
        "email":            row["email"],
        "supervisor_id":    row.get("supervisor_id") or row.get("student_sup_id"),
        "co_supervisor_id": row.get("co_supervisor_id"),
        "student_id":       row.get("student_id"),
    }
    token = create_access_token(payload)
    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            **payload,
            "institution_id":            row.get("institution_id"),
            "institution_name":          row.get("institution_name") or "Kwara State University",
            "institution_code":          row.get("institution_code") or "KWASU",
            "institution_slug":          row.get("institution_slug") or "kwasu",
            "institution_logo":          row.get("institution_logo") or ("/kwasu.png" if (row.get("institution_slug") or "kwasu") == "kwasu" else None),
            "institution_primary_color": row.get("institution_primary_color") or "#16a34a",
            "sup_dept":                  row.get("sup_dept"),
            "stu_dept":                  row.get("stu_dept"),
            "matric_number":             row.get("matric_number"),
            "level":                     row.get("level"),
            "project_id":                row.get("project_id"),
            "expertise_areas":           row.get("expertise_areas"),
            "max_load":                  row.get("max_load"),
            "current_load":              row.get("current_load"),
            "co_supervisor_id":          row.get("co_supervisor_id"),
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
             u.institution_id, inst.name AS institution_name, inst.code AS institution_code,
             inst.slug AS institution_slug, inst.logo_url AS institution_logo,
             inst.primary_color AS institution_primary_color,
             s.supervisor_id,s.expertise_areas,s.max_load,s.current_load,s.department AS sup_dept,s.bio,
             st.student_id,st.matric_number,st.department AS stu_dept,st.level,st.project_id,st.research_domain,
             st.supervisor_id AS student_sup_id, st.co_supervisor_id
           FROM users u
           LEFT JOIN institutions inst ON u.institution_id=inst.institution_id
           LEFT JOIN supervisors s  ON u.user_id=s.user_id
           LEFT JOIN students    st ON u.user_id=st.user_id
           WHERE u.user_id=:user_id"""),
        {"user_id": current["user_id"]},
    ).fetchone()
    if not row:
        raise HTTPException(404, "User not found.")
    u_dict = dict(row._mapping)
    if not u_dict.get("institution_name"):
        u_dict["institution_name"] = "Kwara State University"
        u_dict["institution_code"] = "KWASU"
        u_dict["institution_slug"] = "kwasu"
        u_dict["institution_logo"] = "/kwasu.png"
        u_dict["institution_primary_color"] = "#16a34a"
    elif not u_dict.get("institution_logo") and u_dict.get("institution_slug") == "kwasu":
        u_dict["institution_logo"] = "/kwasu.png"
    return {"success": True, "user": u_dict}


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

    # Resolve institution
    inst_id = getattr(body, "institution_id", None)
    inst_slug = getattr(body, "institution_slug", None)
    if not inst_id and inst_slug:
        inst_row = db.execute(
            text("SELECT institution_id FROM institutions WHERE LOWER(slug)=:s OR UPPER(code)=:c"),
            {"s": inst_slug.lower().strip(), "c": inst_slug.upper().strip()}
        ).fetchone()
        if inst_row:
            inst_id = inst_row[0]
    if not inst_id:
        inst_id = 1  # KWASU default

    hashed = _hash_pw(body.password)
    result = db.execute(
        text("""INSERT INTO users (username,email,password,role,full_name,phone,is_active,institution_id)
           VALUES (:username,:email,:password,:role,:full_name,:phone,:is_active,:institution_id)"""),
        {
            "username":       body.username,
            "email":          body.email.lower(),
            "password":       hashed,
            "role":           body.role,
            "full_name":      body.full_name,
            "phone":          body.phone,
            "is_active":      1,
            "institution_id": inst_id,
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
        import random
        from datetime import datetime

        level_str = (body.level or "400").strip()
        level_clean = level_str.lower()
        is_postgrad = level_clean in ("msc", "phd", "masters", "doctorate")

        main_sup_id = getattr(body, "main_supervisor_id", None) or getattr(body, "supervisor_id", None)
        co_sup_id = None

        if is_postgrad:
            dept = body.department or "Computer Science"
            dept_sups = db.execute(
                text("""SELECT s.supervisor_id FROM supervisors s
                        JOIN users u ON s.user_id=u.user_id
                        WHERE u.is_active=1 AND s.department=:dept
                          AND (u.institution_id=:inst_id OR u.institution_id IS NULL)"""),
                {"dept": dept, "inst_id": inst_id}
            ).fetchall()
            all_sups = [r[0] for r in dept_sups]

            if not all_sups:
                fallback_sups = db.execute(
                    text("""SELECT s.supervisor_id FROM supervisors s
                            JOIN users u ON s.user_id=u.user_id
                            WHERE u.is_active=1 AND (u.institution_id=:inst_id OR u.institution_id IS NULL)"""),
                    {"inst_id": inst_id}
                ).fetchall()
                all_sups = [r[0] for r in fallback_sups]

            if not all_sups:
                fallback_sups = db.execute(
                    text("""SELECT s.supervisor_id FROM supervisors s
                            JOIN users u ON s.user_id=u.user_id
                            WHERE u.is_active=1""")
                ).fetchall()
                all_sups = [r[0] for r in fallback_sups]

            if all_sups:
                # 1. Main Supervisor: use student's choice if valid, else least-loaded supervisor
                if main_sup_id and main_sup_id in all_sups:
                    pass
                else:
                    if len(all_sups) == 1:
                        main_sup_id = all_sups[0]
                    else:
                        placeholders = ",".join([f":sid_{i}" for i in range(len(all_sups))])
                        params = {f"sid_{i}": sid for i, sid in enumerate(all_sups)}
                        least_loaded = db.execute(
                            text(f"""SELECT s.supervisor_id FROM supervisors s
                                    JOIN users u ON s.user_id=u.user_id
                                    WHERE u.is_active=1 AND s.supervisor_id IN ({placeholders})
                                    ORDER BY s.current_load ASC LIMIT 1"""),
                            params
                        ).fetchone()
                        main_sup_id = least_loaded[0] if least_loaded else all_sups[0]

                # 2. Co-Supervisor: MUST be assigned at random from remaining supervisors
                pool_for_co = [sid for sid in all_sups if sid != main_sup_id]
                if pool_for_co:
                    co_sup_id = random.choice(pool_for_co)
                else:
                    # If no other supervisor in the same department, pick at random from other departments
                    other_sups = db.execute(
                        text("""SELECT s.supervisor_id FROM supervisors s
                                JOIN users u ON s.user_id=u.user_id
                                WHERE u.is_active=1 AND s.supervisor_id != :main_id"""),
                        {"main_id": main_sup_id}
                    ).fetchall()
                    if other_sups:
                        co_sup_id = random.choice([r[0] for r in other_sups])

        db.execute(
            text("""INSERT INTO students (user_id,matric_number,department,level,supervisor_id,co_supervisor_id,research_domain,enrollment_year)
               VALUES (:user_id,:matric_number,:department,:level,:supervisor_id,:co_supervisor_id,:research_domain,:enrollment_year)"""),
            {
                "user_id":          user_id,
                "matric_number":    body.matric_number or "",
                "department":       body.department or "Computer Science",
                "level":            level_str,
                "supervisor_id":    main_sup_id,
                "co_supervisor_id": co_sup_id,
                "research_domain":  body.research_domain,
                "enrollment_year":  body.enrollment_year or datetime.now().year,
            },
        )

        # Notify supervisors and increment load
        if main_sup_id:
            try:
                db.execute(text("UPDATE supervisors SET current_load=current_load+1 WHERE supervisor_id=:sid"), {"sid": main_sup_id})
                sup_user = db.execute(text("SELECT user_id FROM supervisors WHERE supervisor_id=:sid"), {"sid": main_sup_id}).fetchone()
                if sup_user:
                    db.execute(
                        text("""INSERT INTO alerts (user_id,alert_type,title,message,severity)
                               VALUES (:uid,'system',:title,:msg,'info')"""),
                        {
                            "uid": sup_user[0],
                            "title": f"New Supervisee: {body.full_name} ({level_str})",
                            "msg": f"You have been assigned as the Main Supervisor for {body.full_name} ({body.matric_number or body.username}, {level_str} in {body.department}).",
                        }
                    )
            except Exception:
                pass

        if co_sup_id:
            try:
                db.execute(text("UPDATE supervisors SET current_load=current_load+1 WHERE supervisor_id=:sid"), {"sid": co_sup_id})
                co_user = db.execute(text("SELECT user_id FROM supervisors WHERE supervisor_id=:sid"), {"sid": co_sup_id}).fetchone()
                if co_user:
                    db.execute(
                        text("""INSERT INTO alerts (user_id,alert_type,title,message,severity)
                               VALUES (:uid,'system',:title,:msg,'info')"""),
                        {
                            "uid": co_user[0],
                            "title": f"New Co-Supervisee (Random Allocation): {body.full_name}",
                            "msg": f"You have been assigned at random as Co-Supervisor for {body.full_name} ({body.matric_number or body.username}, {level_str} in {body.department}).",
                        }
                    )
            except Exception:
                pass

    db.commit()
    return user_id
