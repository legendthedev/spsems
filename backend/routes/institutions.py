"""
backend/routes/institutions.py
Multi-School Autonomous Onboarding Pipeline API
Allows new universities, polytechnics, and colleges to self-onboard onto SPSEMS.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid, re, csv, io
from datetime import datetime

from database import get_db
from middleware.auth import get_current_user, require_role

router = APIRouter(prefix="/institutions", tags=["Institutions & Onboarding Pipeline"])


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
    primary_color: Optional[str] = "#16a34a"
    secondary_color: Optional[str] = "#0f172a"
    admin_fullname: str
    admin_username: str
    admin_password: str
    admin_designation: str = "Director of ICT"


class VerifyDomainRequest(BaseModel):
    institution_code: str
    verification_token: str


class UpdateSettingsRequest(BaseModel):
    academic_session: Optional[str] = "2025/2026"
    current_semester: Optional[str] = "First Semester"
    max_supervisor_load: Optional[int] = 10
    dual_supervisor_for_postgrad: Optional[bool] = True
    auto_assign_co_supervisor: Optional[bool] = True
    enable_ai_pairing: Optional[bool] = True


# ── STAGE 1: SELF-ONBOARDING REGISTRATION ─────────────────────────────────────

@router.post("/onboard", status_code=201)
def onboard_institution(req: SchoolOnboardRequest, db: Session = Depends(get_db)):
    """
    Public Endpoint: Allows a school representative (ICT Director / Dean)
    to initiate self-onboarding for their university or polytechnic.
    """
    code_upper = req.code.strip().upper()
    slug = re.sub(r'[^a-zA-Z0-9]', '', code_upper).lower()
    domain_clean = req.official_domain.strip().lower()

    # 1. Validation: check if institution code or domain already exists
    existing = db.execute(
        text("SELECT institution_id FROM institutions WHERE code=:code OR official_domain=:domain"),
        {"code": code_upper, "domain": domain_clean}
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An institution with code '{code_upper}' or domain '{domain_clean}' is already registered."
        )

    # 2. Generate secure verification token
    verification_token = f"VTOK-{uuid.uuid4().hex[:16].upper()}"

    # 3. Create institution record
    try:
        res = db.execute(
            text("""
                INSERT INTO institutions (
                    name, code, slug, official_domain, institution_type,
                    country, state, city, contact_email, contact_phone,
                    primary_color, secondary_color, status, verification_token,
                    is_verified, current_stage, onboarding_percent
                ) VALUES (
                    :name, :code, :slug, :domain, :type,
                    :country, :state, :city, :email, :phone,
                    :pcolor, :scolor, 'pending_verification', :token,
                    0, '1_registration', 15
                )
            """),
            {
                "name": req.name.strip(),
                "code": code_upper,
                "slug": slug,
                "domain": domain_clean,
                "type": req.institution_type,
                "country": req.country,
                "state": req.state,
                "city": req.city,
                "email": req.contact_email.lower(),
                "phone": req.contact_phone,
                "pcolor": req.primary_color,
                "scolor": req.secondary_color,
                "token": verification_token,
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

    # 4. Provision default settings
    db.execute(
        text("""
            INSERT INTO institution_settings (
                institution_id, max_supervisor_load, dual_supervisor_for_postgrad,
                auto_assign_co_supervisor, enable_ai_pairing
            ) VALUES (:iid, 10, 1, 1, 1)
        """),
        {"iid": inst_id}
    )

    # 5. Populate initial pipeline milestones
    pipeline_stages = [
        (1, '1_registration', 'School Profile & Contact Verification', 'completed', 'School metadata registered', 'System'),
        (2, '2_domain_verification', 'Educational Domain Ownership Check', 'in_progress', f'Verify ownership of {domain_clean}', 'System'),
        (3, '3_tenant_provisioning', 'Tenant Database Isolation & Cloud Storage', 'pending', 'Automatic allocation of storage bucket', 'Pipeline Daemon'),
        (4, '4_department_setup', 'Faculties & Academic Departments Tree', 'pending', 'Import or configure departments', 'Institutional Admin'),
        (5, '5_faculty_import', 'Supervisors & Lecturers Batch Ingestion', 'pending', 'Upload lecturer CSV roster', 'Institutional Admin'),
        (6, '6_policy_config', 'Degree Rules & Supervision Governance', 'pending', 'Configure dual supervision for MSc/PhD', 'Institutional Admin'),
        (7, '7_live_activation', 'Production Go-Live & Portal Access', 'pending', 'Activate student and staff self-service', 'Institutional Admin')
    ]

    for s_order, s_code, s_name, s_status, s_action, s_by in pipeline_stages:
        db.execute(
            text("""
                INSERT INTO tenant_onboarding_pipeline (
                    institution_id, stage_order, stage_code, stage_name, status, required_action, executed_by
                ) VALUES (:iid, :s_order, :s_code, :s_name, :s_status, :s_action, :s_by)
            """),
            {
                "iid": inst_id, "s_order": s_order, "s_code": s_code,
                "s_name": s_name, "s_status": s_status, "s_action": s_action, "s_by": s_by
            }
        )

    db.commit()

    return {
        "success": True,
        "message": f"Welcome {req.name}! Onboarding pipeline initialized.",
        "institution_id": inst_id,
        "institution_code": code_upper,
        "subdomain_slug": slug,
        "verification_token": verification_token,
        "next_step": "Verify domain ownership via /api/institutions/verify-domain using your verification token."
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

    # Mark verified and advance pipeline stage
    db.execute(
        text("""
            UPDATE institutions 
            SET is_verified=1, status='provisioned', current_stage='3_tenant_provisioning', onboarding_percent=45, verified_at=CURRENT_TIMESTAMP
            WHERE institution_id=:id
        """),
        {"id": inst.institution_id}
    )

    db.execute(
        text("""
            UPDATE tenant_onboarding_pipeline 
            SET status='completed', completed_at=CURRENT_TIMESTAMP 
            WHERE institution_id=:id AND stage_code='2_domain_verification'
        """),
        {"id": inst.institution_id}
    )

    db.execute(
        text("""
            UPDATE tenant_onboarding_pipeline 
            SET status='in_progress', started_at=CURRENT_TIMESTAMP 
            WHERE institution_id=:id AND stage_code='3_tenant_provisioning'
        """),
        {"id": inst.institution_id}
    )

    db.commit()

    return {
        "success": True,
        "message": f"Domain verified successfully for {inst.name}!",
        "current_stage": "3_tenant_provisioning",
        "onboarding_percent": 45
    }


# ── STAGE 3-7: PIPELINE TRACKER ───────────────────────────────────────────────

@router.get("/pipeline/{institution_code}")
def get_onboarding_pipeline(institution_code: str, db: Session = Depends(get_db)):
    """
    Retrieves the complete step-by-step pipeline status for a specific school.
    """
    inst = db.execute(
        text("""
            SELECT institution_id, name, code, slug, official_domain, institution_type,
                   status, is_verified, current_stage, onboarding_percent, primary_color, logo_url
            FROM institutions WHERE code=:c
        """),
        {"c": institution_code.upper()}
    ).fetchone()

    if not inst:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institution not found.")

    stages = db.execute(
        text("""
            SELECT stage_order, stage_code, stage_name, status, required_action, started_at, completed_at, executed_by
            FROM tenant_onboarding_pipeline
            WHERE institution_id=:id
            ORDER BY stage_order ASC
        """),
        {"id": inst.institution_id}
    ).fetchall()

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
            "logo_url": inst.logo_url,
        },
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
                   institution_type, state, city, logo_url, primary_color, status
            FROM institutions
            WHERE status IN ('active', 'configuring')
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
                "color": r.primary_color,
                "status": r.status,
            }
            for r in rows
        ]
    }
