from sqlalchemy.orm import Session
from model import Student
from schemas import StudentRegisterRequest, StudentUpdateRequest
from model import Professor, Project, Student
from schemas import ProfessorRegisterRequest, ProfessorUpdateRequest, ProjectCreateRequest
from utils import hash_password, create_access_token, check_password
from sqlalchemy.orm import Session
from datetime import datetime


def register_student(db: Session, data: StudentRegisterRequest) -> str:
    if data.password != data.confirm_password:
        return "Passwords do not match."
    if db.query(Student).filter(Student.email == data.email).first():
        return "Email already registered."
    hashed_pw = hash_password(data.password)
    new_student = Student(name=data.name, email=data.email, password=hashed_pw)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return None  # Success


def register_professor(db: Session, data: ProfessorRegisterRequest) -> str:
    if data.password != data.confirm_password:
        return "Passwords do not match."
    if db.query(Professor).filter(Professor.email == data.email).first():
        return "Email already registered."
    hashed_pw = hash_password(data.password)
    new_prof = Professor(name=data.name, email=data.email, password=hashed_pw)
    db.add(new_prof)
    db.commit()
    db.refresh(new_prof)
    return None  # Success

def authenticate_user(db: Session, email: str, password: str, role: str):
    UserModel = Student if role == "student" else Professor
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user and check_password(password, user.password):
        return user
    return None

def create_user_jwt(user, role: str):
    # Minimal user-id and role in token; add more claims if needed
    data = {"sub": str(user.id), "role": role, "id": user.id, "email": user.email, "name": user.name}
    return create_access_token(data)

def update_professor_profile(db: Session, professor_id: int, update_data: ProfessorUpdateRequest) -> str:
    prof = db.query(Professor).filter(Professor.id == professor_id).first()
    if not prof:
        return "Professor not found."

    updated = False
    for field, value in update_data.dict(exclude_unset=True).items():
        if hasattr(prof, field):
            setattr(prof, field, value)
            updated = True
    if updated:
        db.commit()
        return None  # Success
    else:
        return "No fields to update."
    
def create_project(db: Session, professor_id: int, project_data: ProjectCreateRequest):
    new_project = Project(
        professor_id=professor_id,
        title=project_data.title,
        introduction=project_data.introduction,
        problem_definition=project_data.problem_definition,
        objective=project_data.objective,
        methodology=project_data.methodology,
        scope=project_data.scope,
        timeline=project_data.timeline,
        applications_open=project_data.applications_open,
        status=project_data.status,
        required_skills=project_data.required_skills
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

#update student profile

def update_student_profile(db: Session, student_id: int, update: StudentUpdateRequest):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return "Student not found"

    for field, value in update.dict(exclude_unset=True).items():
        if value is None:
            continue

        # Handle date parsing for DOB and graduation_date
        if field in ["dob", "graduation_date"]:
            try:
                if value:
                    setattr(student, field, datetime.strptime(value, "%Y-%m-%d"))
            except Exception:
                continue  # Bad date → skip update
        else:
            setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return None
