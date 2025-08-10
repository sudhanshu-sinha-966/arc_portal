from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# ---- Registration/Login ----
class StudentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

class ProfessorRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "student" or "professor"

# ---- Profile Update ----
class ProfessorUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    office_location: Optional[str] = None
    phone: Optional[str] = None
    affiliation: Optional[str] = None
    bio: Optional[str] = None
    expertise: Optional[str] = None
    research_interests: Optional[str] = None
    education: Optional[str] = None
    cv_link: Optional[str] = None
    awards: Optional[str] = None
    publications: Optional[str] = None
    memberships: Optional[str] = None
    social_links: Optional[str] = None
    profile_pic: Optional[str] = None
    pronouns: Optional[str] = None
    pronunciation: Optional[str] = None
    titles: Optional[str] = None
    grants: Optional[str] = None
    news: Optional[str] = None
    other_info: Optional[str] = None


class StudentUpdateRequest(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None      # Use str for parsing from web form
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mailing_address: Optional[str] = None
    previous_school: Optional[str] = None
    graduation_date: Optional[str] = None  # str, will parse to DateTime
    gpa: Optional[str] = None
    intended_major: Optional[str] = None
    current_year: Optional[str] = None
    bio: Optional[str] = None
    medical_info: Optional[str] = None
    extracurricular_activities: Optional[str] = None
    social_profiles: Optional[str] = None
    honors_awards: Optional[str] = None
    skills_summary: Optional[str] = None
    profile_pic: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_email: Optional[str] = None
    emergency_relationship: Optional[str] = None
    resume_link: Optional[str] = None

#to send project create request

class ProjectCreateRequest(BaseModel):
    title: str
    introduction: Optional[str] = None
    problem_definition: Optional[str] = None
    objective: Optional[str] = None
    methodology: Optional[str] = None
    scope: Optional[str] = None
    timeline: Optional[str] = None
    applications_open: Optional[bool] = True
    status: Optional[str] = "active"
    required_skills: Optional[str] = None
