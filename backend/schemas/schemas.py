from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Any
from enum import Enum


class RoleEnum(str, Enum):
    student    = "student"
    supervisor = "supervisor"
    admin      = "admin"

class ProjectStatusEnum(str, Enum):
    pending     = "pending"
    approved    = "approved"
    in_progress = "in_progress"
    completed   = "completed"
    rejected    = "rejected"

class ChapterEnum(str, Enum):
    proposal = "proposal"
    chapter1 = "chapter1"
    chapter2 = "chapter2"
    chapter3 = "chapter3"
    chapter4 = "chapter4"
    chapter5 = "chapter5"
    final    = "final"


# ── AUTH ──────────────────────────────────────────────────

class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str = Field(..., min_length=2)
    password: str = Field(..., min_length=1)
    verification_token: Optional[str] = None
    institution_slug:   Optional[str] = None

class VerifyTokenRequest(BaseModel):
    verification_token: str = Field(..., min_length=4)

class RegisterPublicRequest(BaseModel):
    role:       RoleEnum
    username:   str      = Field(..., min_length=4, max_length=100)
    email:      EmailStr
    password:   str      = Field(..., min_length=6)
    full_name:  str      = Field(..., min_length=2)
    phone:      Optional[str] = None
    # Institution
    institution_id:   Optional[int] = None
    institution_slug: Optional[str] = None
    # Student fields
    matric_number:   Optional[str] = None
    department:      Optional[str] = "Computer Science"
    level:           Optional[str] = "400"
    research_domain: Optional[str] = None
    enrollment_year: Optional[int] = None
    supervisor_id:      Optional[int] = None
    main_supervisor_id: Optional[int] = None
    # Supervisor fields
    expertise_areas: Optional[str] = None
    max_load:        Optional[int] = 5
    bio:             Optional[str] = None
    # Admin fields
    admin_code:      Optional[str] = None

class RegisterAdminRequest(RegisterPublicRequest):
    pass


# ── PROJECT ───────────────────────────────────────────────

class ProposalRequest(BaseModel):
    title:      str = Field(..., min_length=10, max_length=500)
    abstract:   str = Field(..., min_length=10)
    keywords:   Optional[str] = None
    objectives: Optional[str] = None

class ProjectStatusUpdate(BaseModel):
    status:           ProjectStatusEnum
    supervisor_id:    Optional[int] = None
    co_supervisor_id: Optional[int] = None


# ── SUBMISSION ────────────────────────────────────────────

class SubmitDocRequest(BaseModel):
    project_id: int
    chapter:    ChapterEnum


# ── SUPERVISOR ────────────────────────────────────────────

class ReviewRequest(BaseModel):
    status:             str
    supervisor_comment: Optional[str] = None

class EvaluationRequest(BaseModel):
    project_id:           int
    rubric_methodology:   float = Field(..., ge=0, le=20)
    rubric_literature:    float = Field(..., ge=0, le=20)
    rubric_analysis:      float = Field(..., ge=0, le=20)
    rubric_presentation:  float = Field(..., ge=0, le=20)
    rubric_originality:   float = Field(..., ge=0, le=20)
    comments:             Optional[str] = None

class MessageRequest(BaseModel):
    receiver_id: int
    project_id:  Optional[int] = None
    subject:     Optional[str] = None
    body:        str = Field(..., min_length=1)


# ── ADMIN ─────────────────────────────────────────────────

class ManualAllocateRequest(BaseModel):
    project_id:       int
    supervisor_id:    int
    co_supervisor_id: Optional[int] = None

class ToggleActiveRequest(BaseModel):
    is_active: bool


# ── GENERIC ───────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data:    Optional[Any] = None
