"""
backend/routes/institutions.py
Multi-School Autonomous Onboarding Pipeline API
Allows new universities, polytechnics, and colleges to self-onboard onto SPSEMS.
Includes automatic logo upload, color scheme preservation, academic policy tuning,
and tenant super-admin credential provisioning.
"""

import os
import re
import uuid
import base64
from datetime import datetime
from typing import Optional, List

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db

router = APIRouter(prefix="/institutions", tags=["Institutions & Onboarding Pipeline"])
settings = get_settings()


def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password[:72].encode(), bcrypt.gensalt()).decode()


# ── SCHEMAS ───────────────────────────────────────────────────────────────────

class SchoolOnboardRequest(BaseModel):
    name: str                       # e.g. "University of Ilorin"
    code: str                       # e.g. "UNILORIN"
    official_domain: str            # e.g. "unilorin.edu.ng"
    institution_type: str = "Federal University"
    country: str = "Nigeria"
    state: Optional[str] = "Kwara"
    city: Optional[str] = "Ilorin"
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = "#16a34a"
    secondary_color: Optional[str] = "#080808"
    accent_color: Optional[str] = "#22c55e"
    admin_fullname: str
    admin_username: str
    admin_password: str
    admin_designation: str = "Director of ICT / Dean"
    academic_session: Optional[str] = "2025/2026"
    current_semester: Optional[str] = "First Semester"
    max_supervisor_load: Optional[int] = 10
    dual_supervisor_for_postgrad: Optional[bool] = True
    auto_assign_co_supervisor: Optional[bool] = True
    enable_ai_pairing: Optional[bool] = True
    instant_live_activation: Optional[bool] = True


class VerifyDomainRequest(BaseModel):
    institution_code: str
    verification_token: str


class VerifyTokenRequest(BaseModel):
    verification_token: str


class UpdateSettingsRequest(BaseModel):
    academic_session: Optional[str] = "2025/2026"
    current_semester: Optional[str] = "First Semester"
    max_supervisor_load: Optional[int] = 10
    dual_supervisor_for_postgrad: Optional[bool] = True
    auto_assign_co_supervisor: Optional[bool] = True
    enable_ai_pairing: Optional[bool] = True


class UpdateBrandingRequest(BaseModel):
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


# ── LOGO UPLOAD ENDPOINT ─────────────────────────────────────────────────────

@router.post("/upload-logo")
async def upload_institution_logo(file: UploadFile = File(...)):
    """
    Accepts official school emblem / logo and saves it to static uploads directory.
    Returns both static relative URL and Base64 data URL for cross-environment compatibility.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Only image files (.png, .jpg, .svg, .webp) are accepted as official school logo."
        )

    inst_dir = os.path.join(settings.upload_dir, "institutions")
    os.makedirs(inst_dir, exist_ok=True)
    fname = f"logo_{uuid.uuid4().hex[:12]}{ext}"
    fpath = os.path.join(inst_dir, fname)

    contents = await file.read()
    with open(fpath, "wb") as fout:
        fout.write(contents)

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".gif": "image/gif",
    }
    mime = mime_map.get(ext, "image/png")
    b64_str = base64.b64encode(contents).decode("utf-8")
    data_url = f"data:{mime};base64,{b64_str}"
    logo_url = f"/uploads/institutions/{fname}"

    return {
        "success": True,
        "message": "Logo uploaded successfully.",
        "logo_url": logo_url,
        "data_url": data_url
    }


# ── STAGE 1: SELF-ONBOARDING REGISTRATION ─────────────────────────────────────

@router.post("/onboard", status_code=201)
def onboard_institution(req: SchoolOnboardRequest, db: Session = Depends(get_db)):
    """
    Public Endpoint: Allows an authorized university/polytechnic representative
    to register their institution, define their branding & color scheme,
    set degree supervision rules, and instantiate their institutional lead administrator.
    """
    code_upper = req.code.strip().upper()
    slug = re.sub(r'[^a-zA-Z0-9]', '', code_upper).lower()
    domain_clean = req.official_domain.strip().lower()
    admin_uname = req.admin_username.strip().lower()
    admin_email = req.contact_email.strip().lower()

    # 1. Validation: check if institution code or domain already exists
    existing = db.execute(
        text("SELECT institution_id, name FROM institutions WHERE code=:code OR official_domain=:domain"),
        {"code": code_upper, "domain": domain_clean}
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An institution with code '{code_upper}' or domain '{domain_clean}' is already registered ({existing.name})."
        )

    # 2. Validation: check if admin username or email already exists in users table
    existing_user = db.execute(
        text("SELECT user_id FROM users WHERE username=:u OR email=:e"),
        {"u": admin_uname, "e": admin_email}
    ).fetchone()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with username '{admin_uname}' or email '{admin_email}' already exists. Please choose a different administrative username."
        )

    # 3. Generate secure verification token
    verification_token = f"VTOK-{uuid.uuid4().hex[:16].upper()}"

    # Determine activation mode
    is_live = bool(req.instant_live_activation)
    inst_status = "active" if is_live else "pending_verification"
    is_verified = 1 if is_live else 0
    current_stage = "7_live_activation" if is_live else "2_domain_verification"
    onboarding_percent = 100 if is_live else 25

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 4. Create institution record
    try:
        db.execute(
            text("""
                INSERT INTO institutions (
                    name, code, slug, official_domain, institution_type,
                    country, state, city, contact_email, contact_phone,
                    logo_url, primary_color, secondary_color, status, verification_token,
                    is_verified, current_stage, onboarding_percent,
                    created_at, verified_at, activated_at
                ) VALUES (
                    :name, :code, :slug, :domain, :type,
                    :country, :state, :city, :email, :phone,
                    :logo_url, :pcolor, :scolor, :status, :token,
                    :is_verified, :current_stage, :percent,
                    :now_str, :verified_at, :activated_at
                )
            """),
            {
                "name": req.name.strip(),
                "code": code_upper,
                "slug": slug,
                "domain": domain_clean,
                "type": req.institution_type,
                "country": req.country,
                "state": req.state or "",
                "city": req.city or "",
                "email": admin_email,
                "phone": req.contact_phone,
                "logo_url": req.logo_url.strip() if (req.logo_url and req.logo_url.strip()) else ("/kwasu.png" if slug == "kwasu" else None),
                "pcolor": req.primary_color or "#16a34a",
                "scolor": req.secondary_color or "#080808",
                "status": inst_status,
                "token": verification_token,
                "is_verified": is_verified,
                "current_stage": current_stage,
                "percent": onboarding_percent,
                "now_str": now_str,
                "verified_at": now_str if is_live else None,
                "activated_at": now_str if is_live else None,
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Registration failed: {str(e)}")

    # Fetch inserted ID
    inst_row = db.execute(
        text("SELECT institution_id FROM institutions WHERE code=:code"),
        {"code": code_upper}
    ).fetchone()
    inst_id = inst_row[0]

    # 5. Provision institutional settings & supervision rules
    db.execute(
        text("""
            INSERT INTO institution_settings (
                institution_id, academic_session, current_semester,
                max_supervisor_load, dual_supervisor_for_postgrad,
                auto_assign_co_supervisor, enable_ai_pairing,
                allow_public_student_reg, allow_public_lecturer_reg, require_admin_approval
            ) VALUES (
                :iid, :session, :semester,
                :max_load, :dual_sup,
                :auto_co, :ai_pair,
                1, 1, 1
            )
        """),
        {
            "iid": inst_id,
            "session": req.academic_session or "2025/2026",
            "semester": req.current_semester or "First Semester",
            "max_load": req.max_supervisor_load or 10,
            "dual_sup": 1 if req.dual_supervisor_for_postgrad else 0,
            "auto_co": 1 if req.auto_assign_co_supervisor else 0,
            "ai_pair": 1 if req.enable_ai_pairing else 0,
        }
    )

    # 6. Create initial Super Admin / ICT Director account
    hashed_pw = _hash_pw(req.admin_password)
    db.execute(
        text("""
            INSERT INTO users (
                username, email, password, role, full_name, phone, institution_id, is_active, created_at
            ) VALUES (
                :username, :email, :password, 'admin', :full_name, :phone, :institution_id, 1, :now_str
            )
        """),
        {
            "username": admin_uname,
            "email": admin_email,
            "password": hashed_pw,
            "full_name": req.admin_fullname.strip(),
            "phone": req.contact_phone,
            "institution_id": inst_id,
            "now_str": now_str,
        }
    )

    # 7. Populate onboarding pipeline milestones
    if is_live:
        pipeline_stages = [
            (1, '1_registration', 'School Profile & Contact Verification', 'completed', 'School metadata registered and validated', 'Institutional Admin', now_str, now_str),
            (2, '2_domain_verification', 'Educational Domain Ownership Check', 'completed', f'Domain {domain_clean} verified', 'System', now_str, now_str),
            (3, '3_tenant_provisioning', 'Tenant Database Isolation & Cloud Storage', 'completed', 'Database tenant partition & storage allocated', 'Pipeline Daemon', now_str, now_str),
            (4, '4_department_setup', 'Faculties & Academic Departments Tree', 'completed', 'Default institutional departments initialized', 'Institutional Admin', now_str, now_str),
            (5, '5_faculty_import', 'Supervisors & Lecturers Batch Ingestion', 'completed', 'Faculty onboarding workflow ready', 'Institutional Admin', now_str, now_str),
            (6, '6_policy_config', 'Degree Rules & Supervision Governance', 'completed', 'Supervision load & dual-supervisor policies configured', 'Institutional Admin', now_str, now_str),
            (7, '7_live_activation', 'Production Go-Live & Portal Access', 'completed', 'Institutional portal live for staff & students', 'Institutional Admin', now_str, now_str)
        ]
    else:
        pipeline_stages = [
            (1, '1_registration', 'School Profile & Contact Verification', 'completed', 'School metadata registered', 'System', now_str, now_str),
            (2, '2_domain_verification', 'Educational Domain Ownership Check', 'in_progress', f'Verify DNS TXT or meta token for {domain_clean}', 'System', now_str, None),
            (3, '3_tenant_provisioning', 'Tenant Database Isolation & Cloud Storage', 'pending', 'Allocation of cloud storage & isolated namespace', 'Pipeline Daemon', None, None),
            (4, '4_department_setup', 'Faculties & Academic Departments Tree', 'pending', 'Configure academic departments and degrees', 'Institutional Admin', None, None),
            (5, '5_faculty_import', 'Supervisors & Lecturers Batch Ingestion', 'pending', 'Upload lecturer and supervisor CSV roster', 'Institutional Admin', None, None),
            (6, '6_policy_config', 'Degree Rules & Supervision Governance', 'pending', 'Finalize supervisor ratios and PG dual supervision', 'Institutional Admin', None, None),
            (7, '7_live_activation', 'Production Go-Live & Portal Access', 'pending', 'Activate portal self-service for students', 'Institutional Admin', None, None)
        ]

    for s in pipeline_stages:
        db.execute(
            text("""
                INSERT INTO tenant_onboarding_pipeline (
                    institution_id, stage_order, stage_code, stage_name, status,
                    required_action, executed_by, started_at, completed_at
                ) VALUES (
                    :iid, :s_order, :s_code, :s_name, :s_status,
                    :s_action, :s_by, :s_start, :s_end
                )
            """),
            {
                "iid": inst_id,
                "s_order": s[0],
                "s_code": s[1],
                "s_name": s[2],
                "s_status": s[3],
                "s_action": s[4],
                "s_by": s[5],
                "s_start": s[6],
                "s_end": s[7],
            }
        )

    db.commit()

    return {
        "success": True,
        "message": f"Congratulations! {req.name} ({code_upper}) has been successfully onboarded and activated.",
        "institution_id": inst_id,
        "institution_name": req.name.strip(),
        "institution_code": code_upper,
        "subdomain_slug": slug,
        "status": inst_status,
        "is_verified": is_verified,
        "onboarding_percent": onboarding_percent,
        "logo_url": req.logo_url or ("/kwasu.png" if slug == "kwasu" else None),
        "primary_color": req.primary_color or "#16a34a",
        "secondary_color": req.secondary_color or "#080808",
        "admin_username": admin_uname,
        "verification_token": verification_token,
        "portal_login_path": f"/login",
    }


# ── STAGE 2: DOMAIN VERIFICATION ──────────────────────────────────────────────

@router.post("/verify-domain")
def verify_institution_domain(req: VerifyDomainRequest, db: Session = Depends(get_db)):
    """
    Confirms domain ownership to activate tenant provisioning.
    """
    inst = db.execute(
        text("SELECT institution_id, name, verification_token, is_verified FROM institutions WHERE code=:c"),
        {"c": req.institution_code.upper()}
    ).fetchone()

    if not inst:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institution not found.")

    if inst.is_verified:
        return {"success": True, "message": "Institution domain already verified."}

    if inst.verification_token != req.verification_token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid verification token.")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Mark verified and advance pipeline stage
    db.execute(
        text("""
            UPDATE institutions 
            SET is_verified=1, status='active', current_stage='7_live_activation',
                onboarding_percent=100, verified_at=:now_str, activated_at=:now_str
            WHERE institution_id=:id
        """),
        {"id": inst.institution_id, "now_str": now_str}
    )

    db.execute(
        text("""
            UPDATE tenant_onboarding_pipeline 
            SET status='completed', completed_at=:now_str
            WHERE institution_id=:id
        """),
        {"id": inst.institution_id, "now_str": now_str}
    )

    db.commit()

    return {
        "success": True,
        "message": f"Domain verified and live activation enabled for {inst.name}!",
        "current_stage": "7_live_activation",
        "onboarding_percent": 100
    }


# ── LIVE ACTIVATION ──────────────────────────────────────────────────────────

@router.post("/activate-live/{institution_code}")
def activate_institution_live(institution_code: str, db: Session = Depends(get_db)):
    """
    Activates an institution for full live production access.
    """
    inst = db.execute(
        text("SELECT institution_id, name, code, status FROM institutions WHERE code=:c"),
        {"c": institution_code.upper()}
    ).fetchone()

    if not inst:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institution not found.")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.execute(
        text("""
            UPDATE institutions 
            SET is_verified=1, status='active', current_stage='7_live_activation',
                onboarding_percent=100, activated_at=:now_str
            WHERE institution_id=:id
        """),
        {"id": inst.institution_id, "now_str": now_str}
    )

    db.execute(
        text("""
            UPDATE tenant_onboarding_pipeline 
            SET status='completed', completed_at=:now_str
            WHERE institution_id=:id
        """),
        {"id": inst.institution_id, "now_str": now_str}
    )

    db.commit()

    return {
        "success": True,
        "message": f"{inst.name} ({inst.code}) is now LIVE and fully active!",
        "status": "active",
        "onboarding_percent": 100
    }


# ── PIPELINE TRACKER ──────────────────────────────────────────────────────────

@router.get("/pipeline/{institution_code}")
def get_onboarding_pipeline(institution_code: str, db: Session = Depends(get_db)):
    """
    Retrieves the complete step-by-step pipeline status for a specific school.
    """
    inst = db.execute(
        text("""
            SELECT institution_id, name, code, slug, official_domain, institution_type,
                   status, is_verified, current_stage, onboarding_percent, primary_color,
                   secondary_color, logo_url, created_at, verified_at, activated_at
            FROM institutions WHERE code=:c
        """),
        {"c": institution_code.upper()}
    ).fetchone()

    if not inst:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Institution with code '{institution_code}' not found.")

    stages = db.execute(
        text("""
            SELECT stage_order, stage_code, stage_name, status, required_action, started_at, completed_at, executed_by
            FROM tenant_onboarding_pipeline
            WHERE institution_id=:id
            ORDER BY stage_order ASC
        """),
        {"id": inst.institution_id}
    ).fetchall()

    settings_row = db.execute(
        text("SELECT * FROM institution_settings WHERE institution_id=:id"),
        {"id": inst.institution_id}
    ).fetchone()

    return {
        "institution": {
            "id": inst.institution_id,
            "name": inst.name,
            "code": inst.code,
            "slug": inst.slug,
            "domain": inst.official_domain,
            "type": inst.institution_type,
            "status": inst.status,
            "is_verified": bool(inst.is_verified),
            "current_stage": inst.current_stage,
            "progress_percent": inst.onboarding_percent,
            "primary_color": inst.primary_color,
            "secondary_color": inst.secondary_color,
            "logo_url": inst.logo_url,
            "created_at": str(inst.created_at) if inst.created_at else None,
            "verified_at": str(inst.verified_at) if inst.verified_at else None,
            "activated_at": str(inst.activated_at) if inst.activated_at else None,
        },
        "settings": dict(settings_row._mapping) if settings_row else {},
        "pipeline_stages": [
            {
                "order": s.stage_order,
                "code": s.stage_code,
                "name": s.stage_name,
                "status": s.status,
                "action": s.required_action,
                "started_at": str(s.started_at) if s.started_at else None,
                "completed_at": str(s.completed_at) if s.completed_at else None,
                "executed_by": s.executed_by,
            }
            for s in stages
        ]
    }


# ── PUBLIC DIRECTORY: MULTI-SCHOOL PICKER ─────────────────────────────────────

@router.get("/directory")
def get_institutions_directory(db: Session = Depends(get_db)):
    """
    Returns list of all active/verified institutions for user login & school switcher.
    """
    rows = db.execute(
        text("""
            SELECT institution_id, name, code, slug, official_domain,
                   institution_type, state, city, logo_url, primary_color, secondary_color,
                   status, onboarding_percent
            FROM institutions
            ORDER BY name ASC
        """)
    ).fetchall()

    return {
        "total": len(rows),
        "institutions": [
            {
                "id": r.institution_id,
                "name": r.name,
                "code": r.code,
                "slug": r.slug,
                "domain": r.official_domain,
                "type": r.institution_type,
                "location": f"{r.city or ''}, {r.state or ''}".strip(", "),
                "logo": r.logo_url,
                "primary_color": r.primary_color,
                "secondary_color": r.secondary_color,
                "status": r.status,
                "progress_percent": r.onboarding_percent,
            }
            for r in rows
        ]
    }


# ── INSTITUTION BY SLUG (FOR CUSTOM PORTAL THEME) ─────────────────────────────

@router.get("/by-slug/{slug}")
def get_institution_by_slug(slug: str, db: Session = Depends(get_db)):
    """
    Retrieves public branding profile and policies for a specific institution slug.
    """
    row = db.execute(
        text("""
            SELECT i.institution_id, i.name, i.code, i.slug, i.official_domain,
                   i.institution_type, i.state, i.city, i.contact_email, i.logo_url,
                   i.primary_color, i.secondary_color, i.status, i.is_verified, i.verification_token,
                   s.academic_session, s.current_semester, s.dual_supervisor_for_postgrad
            FROM institutions i
            LEFT JOIN institution_settings s ON i.institution_id = s.institution_id
            WHERE i.slug = :s OR LOWER(i.code) = :s
        """),
        {"s": slug.lower().strip()}
    ).fetchone()

    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Institution '{slug}' not found.")

    return {
        "id": row.institution_id,
        "name": row.name,
        "code": row.code,
        "slug": row.slug,
        "domain": row.official_domain,
        "contact_email": row.contact_email,
        "type": row.institution_type,
        "location": f"{row.city or ''}, {row.state or ''}".strip(", "),
        "logo_url": row.logo_url,
        "primary_color": row.primary_color,
        "secondary_color": row.secondary_color,
        "status": row.status,
        "is_verified": bool(row.is_verified),
        "has_verification_token": bool(row.verification_token),
        "session": row.academic_session,
        "semester": row.current_semester,
        "dual_supervisor_for_postgrad": bool(row.dual_supervisor_for_postgrad),
    }


# ── VERIFY INSTITUTION TOKEN ─────────────────────────────────────────────────

@router.post("/{slug_or_code}/verify-token")
def verify_institution_token(slug_or_code: str, body: VerifyTokenRequest, db: Session = Depends(get_db)):
    target = slug_or_code.lower().strip()
    row = db.execute(
        text("""SELECT institution_id, name, code, slug, verification_token, is_verified, status 
                FROM institutions 
                WHERE LOWER(slug)=:t OR UPPER(code)=:c"""),
        {"t": target, "c": target.upper()}
    ).fetchone()

    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Institution '{slug_or_code}' not found.")

    expected = (row.verification_token or "").strip()
    submitted = (body.verification_token or "").strip()

    if expected and submitted.upper() != expected.upper():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Invalid verification token. Please enter the token generated during onboarding."
        )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        text("""UPDATE institutions 
               SET is_verified=1, status='active',
                   verified_at=COALESCE(verified_at, :now_str),
                   activated_at=COALESCE(activated_at, :now_str)
               WHERE institution_id=:iid"""),
        {"iid": row.institution_id, "now_str": now_str}
    )
    db.commit()

    return {
        "success": True,
        "message": f"Verification successful! {row.name} ({row.code}) portal node is now verified and active.",
        "institution_id": row.institution_id,
        "institution_code": row.code,
        "status": "active",
        "is_verified": True,
    }


# ── UPDATE INSTITUTION LOGO & BRANDING ────────────────────────────────────────

@router.post("/{slug_or_code}/update-logo")
def update_institution_logo(
    slug_or_code: str,
    body: UpdateBrandingRequest,
    db: Session = Depends(get_db)
):
    """
    Updates the official submitted logo and brand colors for a specific school.
    Accepts Base64 data URL or static URL.
    """
    clean = slug_or_code.strip()
    inst = db.execute(
        text("SELECT institution_id, name, code, slug FROM institutions WHERE LOWER(slug)=:s OR UPPER(code)=:c"),
        {"s": clean.lower(), "c": clean.upper()}
    ).fetchone()

    if not inst:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Institution '{clean}' not found.")

    updates = []
    params = {"id": inst.institution_id}

    if body.logo_url:
        updates.append("logo_url = :logo_url")
        params["logo_url"] = body.logo_url.strip()
    if body.primary_color:
        updates.append("primary_color = :pcolor")
        params["pcolor"] = body.primary_color.strip()
    if body.secondary_color:
        updates.append("secondary_color = :scolor")
        params["scolor"] = body.secondary_color.strip()

    if updates:
        sql = f"UPDATE institutions SET {', '.join(updates)} WHERE institution_id = :id"
        db.execute(text(sql), params)
        db.commit()

    updated = db.execute(
        text("SELECT institution_id, name, code, slug, logo_url, primary_color, secondary_color FROM institutions WHERE institution_id=:id"),
        {"id": inst.institution_id}
    ).fetchone()

    return {
        "success": True,
        "message": f"Official logo and branding for {inst.name} ({inst.code}) updated successfully.",
        "institution": {
            "id": updated.institution_id,
            "name": updated.name,
            "code": updated.code,
            "slug": updated.slug,
            "logo_url": updated.logo_url,
            "primary_color": updated.primary_color,
            "secondary_color": updated.secondary_color,
        }
    }


@router.post("/{slug_or_code}/upload-and-update-logo")
async def upload_and_update_institution_logo(
    slug_or_code: str,
    file: UploadFile = File(...),
    primary_color: Optional[str] = Form(None),
    secondary_color: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts direct image file upload and updates the school's logo immediately.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Only image files (.png, .jpg, .svg, .webp) are accepted."
        )

    clean = slug_or_code.strip()
    inst = db.execute(
        text("SELECT institution_id, name, code, slug FROM institutions WHERE LOWER(slug)=:s OR UPPER(code)=:c"),
        {"s": clean.lower(), "c": clean.upper()}
    ).fetchone()

    if not inst:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Institution '{clean}' not found.")

    inst_dir = os.path.join(settings.upload_dir, "institutions")
    os.makedirs(inst_dir, exist_ok=True)
    fname = f"logo_{inst.slug}_{uuid.uuid4().hex[:8]}{ext}"
    fpath = os.path.join(inst_dir, fname)

    contents = await file.read()
    with open(fpath, "wb") as fout:
        fout.write(contents)

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".gif": "image/gif",
    }
    mime = mime_map.get(ext, "image/png")
    b64_str = base64.b64encode(contents).decode("utf-8")
    data_url = f"data:{mime};base64,{b64_str}"

    updates = ["logo_url = :logo_url"]
    params = {"id": inst.institution_id, "logo_url": data_url}

    if primary_color:
        updates.append("primary_color = :pcolor")
        params["pcolor"] = primary_color
    if secondary_color:
        updates.append("secondary_color = :scolor")
        params["scolor"] = secondary_color

    sql = f"UPDATE institutions SET {', '.join(updates)} WHERE institution_id = :id"
    db.execute(text(sql), params)
    db.commit()

    return {
        "success": True,
        "message": f"Official logo for {inst.name} ({inst.code}) updated successfully.",
        "logo_url": data_url,
        "static_url": f"/uploads/institutions/{fname}"
    }

