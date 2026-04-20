"""
GovScheme Advisor — Database Models & Configuration
MongoDB document schemas for schemes, users, and analytics.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ──────────────────────────────────────────────
# ENUMS
# ──────────────────────────────────────────────

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class CasteCategory(str, Enum):
    SC = "sc"
    ST = "st"
    OBC = "obc"
    GENERAL = "general"
    EWS = "ews"

class AreaType(str, Enum):
    RURAL = "rural"
    URBAN = "urban"
    BOTH = "both"

class EmploymentStatus(str, Enum):
    EMPLOYED = "employed"
    UNEMPLOYED = "unemployed"
    SELF_EMPLOYED = "self_employed"
    STUDENT = "student"

class SchemeCategory(str, Enum):
    SCHOLARSHIP = "scholarship"
    PENSION = "pension"
    WOMEN = "women"
    STUDENT = "student"
    FARMER = "farmer"
    EMPLOYMENT = "employment"
    HEALTH = "health"
    HOUSING = "housing"
    STARTUP = "startup"
    SOCIAL_SECURITY = "social_security"
    INSURANCE = "insurance"
    SKILL_DEVELOPMENT = "skill_development"
    OTHER = "other"


# ──────────────────────────────────────────────
# SCHEME MODEL
# ──────────────────────────────────────────────

class SchemeEligibility(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[List[str]] = None          # ["male","female","other"] or None=all
    caste_categories: Optional[List[str]] = None # ["sc","st","obc","general","ews"] or None=all
    bpl_required: Optional[bool] = None
    max_annual_income: Optional[int] = None
    states: Optional[List[str]] = None           # None = all India
    area_type: Optional[str] = None              # "rural","urban","both" or None
    education_levels: Optional[List[str]] = None
    is_student: Optional[bool] = None
    is_farmer: Optional[bool] = None
    is_employed: Optional[bool] = None
    is_disabled: Optional[bool] = None
    is_widow: Optional[bool] = None
    is_senior_citizen: Optional[bool] = None
    is_minority: Optional[bool] = None
    marital_status: Optional[List[str]] = None
    special_categories: Optional[List[str]] = None  # orphan, single_mother, etc.
    eligibility_text: Optional[str] = ""


class SchemeModel(BaseModel):
    scheme_id: Optional[str] = None
    name: str
    name_hindi: Optional[str] = ""
    description: str
    description_hindi: Optional[str] = ""
    category: str = "other"
    ministry: Optional[str] = ""
    eligibility: SchemeEligibility = SchemeEligibility()
    eligibility_text: str = ""
    benefits: str = ""
    benefits_hindi: Optional[str] = ""
    documents_required: List[str] = []
    how_to_apply: str = ""
    apply_link: Optional[str] = ""
    official_website: Optional[str] = ""
    state: Optional[str] = "All India"
    last_date: Optional[str] = ""
    status: str = "active"
    tags: List[str] = []
    source_url: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ──────────────────────────────────────────────
# USER PROFILE (form input)
# ──────────────────────────────────────────────

class UserProfile(BaseModel):
    # Personal
    full_name: str = ""
    gender: str = ""
    age: int = 0
    marital_status: str = ""
    disability_status: bool = False

    # Social Category
    caste_category: str = ""
    minority_status: bool = False
    bpl_status: bool = False

    # Education
    highest_qualification: str = ""
    is_student: bool = False
    current_course: str = ""

    # Employment
    occupation: str = ""
    employment_status: str = ""
    monthly_income: int = 0
    annual_family_income: int = 0

    # Agriculture
    is_farmer: bool = False
    land_ownership: str = ""

    # Location
    state: str = ""
    district: str = ""
    area_type: str = ""

    # Special Categories
    is_widow: bool = False
    is_senior_citizen: bool = False
    is_single_mother: bool = False
    is_orphan: bool = False
    special_category: str = ""


# ──────────────────────────────────────────────
# RECOMMENDATION RESULT
# ──────────────────────────────────────────────

class RecommendationResult(BaseModel):
    scheme_id: str
    name: str
    name_hindi: Optional[str] = ""
    category: str
    eligibility_score: float = 0.0
    nlp_relevance_score: float = 0.0
    total_score: float = 0.0
    why_eligible: str = ""
    why_eligible_hindi: Optional[str] = ""
    benefits: str = ""
    how_to_apply: str = ""
    documents_required: List[str] = []
    apply_link: str = ""
    state: str = ""


# ──────────────────────────────────────────────
# AUTH MODELS
# ──────────────────────────────────────────────

class UserAuth(BaseModel):
    email: str
    password: str

class UserInDB(BaseModel):
    email: str
    hashed_password: str
    role: str = "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ──────────────────────────────────────────────
# SEARCH QUERY
# ──────────────────────────────────────────────

class SearchQuery(BaseModel):
    query: str
    language: str = "en"  # "en" or "hi"
