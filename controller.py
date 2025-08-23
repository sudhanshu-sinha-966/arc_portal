from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from service import register_student, create_project
from schemas import StudentRegisterRequest, ProfessorUpdateRequest, ProjectCreateRequest
from service import register_professor, update_professor_profile, update_student_profile
from schemas import ProfessorRegisterRequest, StudentUpdateRequest
from model import Professor, Project, Application
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import Response, Cookie
from fastapi import status
from utils import decode_access_token
from schemas import LoginRequest
import service  # or from service import authenticate_user, create_user_jwt ...
from fastapi import HTTPException, status, Depends
from fastapi.responses import RedirectResponse
import os
from uuid import uuid4
from sqlalchemy import func


from model import Student

templates = Jinja2Templates(directory="templates")
router = APIRouter()

# Create tables on startup (safe to run repeatedly)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register/student", response_class=HTMLResponse)
async def register_student_endpoint(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Construct Pydantic schema
    data = StudentRegisterRequest(
        name=name,
        email=email,
        password=password,
        confirm_password=confirm_password
    )
    error = register_student(db, data)
    if error:
        # Show form again with error
        return templates.TemplateResponse("landing.html",
            {"request": request, "register_student_error": error})
    # Registration successful, show success message and redirect to login
    return templates.TemplateResponse("landing.html",
            {"request": request, "register_student_success": "Registration successful! Please login."})


@router.post("/register/professor", response_class=HTMLResponse)
async def register_professor_endpoint(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    data = ProfessorRegisterRequest(
        name=name,
        email=email,
        password=password,
        confirm_password=confirm_password
    )
    error = register_professor(db, data)
    if error:
        return templates.TemplateResponse(
            "landing.html", {"request": request, "register_professor_error": error}
        )
    return templates.TemplateResponse(
        "landing.html", {"request": request, "register_professor_message": "Registration successful. Please log in!"}
    )

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),  # "student" or "professor"
    db: Session = Depends(get_db),
):
    user = service.authenticate_user(db, email, password, role)
    if not user:
        # Return landing page with error
        return templates.TemplateResponse("landing.html", {"request": request, "login_error": "Invalid credentials or role."})
    token = service.create_user_jwt(user, role)
    response = RedirectResponse(url=f"/dashboard/{role}", status_code=status.HTTP_302_FOUND)
    # Set HTTPOnly cookie for the token (demo style; can use secure/session for prod)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.get("/dashboard/student", response_class=HTMLResponse)
async def student_dashboard(request: Request, user = Depends(get_current_user)):
    if user["role"] != "student":
        return RedirectResponse(url="/", status_code=303)
    # Render dashboard template and pass user info
    return templates.TemplateResponse("student_dashboard.html", {"request": request, "user": user})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)  # Go to landing page
    # Remove the access_token cookie
    response.delete_cookie("access_token")
    return response

@router.get("/profile/professor", response_class=HTMLResponse)
async def get_professor_profile(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user["role"] != "professor":
        return RedirectResponse(url="/", status_code=303)
    prof = db.query(Professor).filter(Professor.id == user["id"]).first()
    if not prof:
        return RedirectResponse(url="/logout")
    return templates.TemplateResponse("professor_profile.html", {"request": request, "prof": prof})


@router.post("/profile/professor/update", response_class=HTMLResponse)
async def update_professor_profile_endpoint(
    request: Request,
    name: str = Form(None),
    email: str = Form(None),
    department: str = Form(None),
    office_location: str = Form(None),
    phone: str = Form(None),
    affiliation: str = Form(None),
    bio: str = Form(None),
    expertise: str = Form(None),
    research_interests: str = Form(None),
    education: str = Form(None),
    cv_link: str = Form(None),
    awards: str = Form(None),
    publications: str = Form(None),
    memberships: str = Form(None),
    social_links: str = Form(None),
    profile_pic: UploadFile = File(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # Role check
    if user.get("role") != "professor":
        return RedirectResponse(url="/", status_code=303)

    # --- Handle file upload ---
    photo_url = None
    if profile_pic and profile_pic.filename:
        ext = os.path.splitext(profile_pic.filename)[1]
        filename = f"{uuid4().hex}{ext}"
        save_dir = "static/profile_photos"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        with open(save_path, "wb") as f:
            f.write(await profile_pic.read())
        photo_url = f"/static/profile_photos/{filename}"

    # --- Build schema for update ---
    from schemas import ProfessorUpdateRequest
    update_data = ProfessorUpdateRequest(
        name=name,
        email=email,
        department=department,
        office_location=office_location,
        phone=phone,
        affiliation=affiliation,
        bio=bio,
        expertise=expertise,
        research_interests=research_interests,
        education=education,
        cv_link=cv_link,
        awards=awards,
        publications=publications,
        memberships=memberships,
        social_links=social_links,
        profile_pic=photo_url,  # <--- Pass file path string, or None
    )

    # --- Perform update ---
    error = update_professor_profile(db, int(user.get("id") or user.get("sub")), update_data)
    prof = db.query(Professor).filter(Professor.id == int(user.get("id") or user.get("sub"))).first()

    if error:
        return templates.TemplateResponse("professor_profile.html", {"request": request, "prof": prof, "error": error})

    return templates.TemplateResponse("professor_profile.html", {
        "request": request,
        "prof": prof,
        "message": "Profile updated successfully!"
    })

@router.get("/dashboard/professor", response_class=HTMLResponse)
async def professor_dashboard(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.get("role") != "professor":
        return RedirectResponse(url="/", status_code=303)
    professor_id = int(user.get("id") or user.get("sub"))
    
    # Total projects
    total_projects = db.query(func.count(Project.id)).filter(Project.professor_id == professor_id).scalar() or 0
    # Active projects
    active_projects = db.query(func.count(Project.id)).filter(Project.professor_id == professor_id, Project.status == "active").scalar() or 0
    # Students applied (count of applications to professor's projects)
    student_applied = db.query(Application).join(Project, Application.project_id == Project.id)\
        .filter(Project.professor_id == professor_id).count() or 0

     # Recent projects (5 latest updated)
    recent_projects = db.query(Project).filter(Project.professor_id == professor_id).order_by(Project.updated_at.desc()).limit(5).all()

    # Recent applications (5 latest, with join)
    recent_applications = (
        db.query(Application, Student, Project)
        .join(Project, Application.project_id == Project.id)
        .join(Student, Application.student_id == Student.id)
        .filter(Project.professor_id == professor_id)
        .order_by(Application.applied_at.desc())
        .limit(5)
        .all()
    )

    return templates.TemplateResponse(
        "professor_dashboard.html",
        {
            "request": request,
            "user": user,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "student_applied": student_applied,
            "recent_projects": recent_projects,
            "recent_applications": recent_applications,
        }
    )

#to get the post a new project page

@router.get("/professor/post-project", response_class=HTMLResponse)
async def get_post_project_form(request: Request, user=Depends(get_current_user)):
    if user.get("role") != "professor":
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("professor_postproject.html", {"request": request, "user": user})

#to actually post a new project

@router.post("/professor/post-project", response_class=HTMLResponse)
async def submit_new_project(
    request: Request,
    title: str = Form(...),
    introduction: str = Form(None),
    problem_definition: str = Form(None),
    objective: str = Form(None),
    methodology: str = Form(None),
    scope: str = Form(None),
    timeline: str = Form(None),
    applications_open: bool = Form(True),
    status: str = Form("active"),
    required_skills: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.get("role") != "professor":
        return RedirectResponse(url="/", status_code=303)

    project_data = ProjectCreateRequest(
        title=title,
        introduction=introduction,
        problem_definition=problem_definition,
        objective=objective,
        methodology=methodology,
        scope=scope,
        timeline=timeline,
        applications_open=applications_open,
        status=status,
        required_skills=required_skills
    )

    new_project = create_project(db, int(user.get("id") or user.get("sub")), project_data)

    return templates.TemplateResponse(
        "professor_postproject.html",
        {"request": request, "user": user, "message": "Project posted successfully!", "project": new_project}
    )

#to view the project details which open a pop up
@router.get("/api/professor/project/{project_id}")
async def get_project_detail(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.get("role") != "professor":
        return {"error": "Unauthorized"}, 401
    professor_id = int(user.get("id") or user.get("sub"))
    project = db.query(Project).filter(Project.id == project_id, Project.professor_id == professor_id).first()
    if not project:
        return {"error": "Not found"}, 404
    # Return only relevant fields
    return {
        "id": project.id,
        "title": project.title,
        "status": project.status,
        "introduction": project.introduction,
        "problem_definition": project.problem_definition,
        "objective": project.objective,
        "methodology": project.methodology,
        "scope": project.scope,
        "timeline": project.timeline,
        "updated_at": project.updated_at.strftime("%b %d, %Y") if project.updated_at else "",
        "applications_count": len(project.applications) if hasattr(project, "applications") else None,
        "required_skills": project.required_skills,
    }

#to show projects when my projects is clicked from professor

@router.get("/professor/my-projects", response_class=HTMLResponse)
async def my_projects(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.get("role") != "professor":
        return RedirectResponse(url="/", status_code=303)
    professor_id = int(user.get("id") or user.get("sub"))

    projects = (
        db.query(Project)
        .filter(Project.professor_id == professor_id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "professor_myprojects.html",
        {"request": request, "user": user, "projects": projects}
    )

@router.get("/dashboard/student", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.get("role") != "student":
        return RedirectResponse(url="/", status_code=303)

    student_id = int(user.get("id") or user.get("sub"))
    total_applications = db.query(Application).filter(Application.student_id == student_id).count() or 0
    accepted = db.query(Application).filter(Application.student_id == student_id, Application.status == "accepted").count() or 0
    shortlisted = db.query(Application).filter(Application.student_id == student_id, Application.status == "shortlisted").count() or 0
    pending = db.query(Application).filter(Application.student_id == student_id, Application.status == "pending").count() or 0
    rejected = db.query(Application).filter(Application.student_id == student_id, Application.status == "rejected").count() or 0

    # Recent applications: join Application, Project, and Professor; order by apply time
    recent_applications = (
        db.query(Application, Project, Professor)
        .join(Project, Application.project_id == Project.id)
        .join(Professor, Project.professor_id == Professor.id)
        .filter(Application.student_id == student_id)
        .order_by(Application.applied_at.desc())
        .limit(5)
        .all()
    )

    student = db.query(Student).filter(Student.id == student_id).first()
    skills = (student.skills_summary.split(',') if student and student.skills_summary else [])

    return templates.TemplateResponse("student_dashboard.html", {
        "request": request,
        "user": user,
        "total_applications": total_applications,
        "accepted": accepted,
        "shortlisted": shortlisted,
        "pending": pending,
        "rejected": rejected,
        "skills": skills,
        "recent_applications": recent_applications
    })

#to get the student profile page 

@router.get("/profile/student", response_class=HTMLResponse)
async def get_student_profile(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.get("role") != "student":
        return RedirectResponse(url="/", status_code=303)

    student_id = int(user.get("id") or user.get("sub"))
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return RedirectResponse(url="/logout")

    return templates.TemplateResponse("student_profile.html", {
        "request": request,
        "student": student,
        "user": user
    })

#to update the student's profile

@router.post("/profile/student/update", response_class=HTMLResponse)
async def update_student_profile_endpoint(
    request: Request,
    name: str = Form(None),
    gender: str = Form(None),
    dob: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    mailing_address: str = Form(None),
    previous_school: str = Form(None),
    graduation_date: str = Form(None),
    gpa: str = Form(None),
    intended_major: str = Form(None),
    current_year: str = Form(None),
    bio: str = Form(None),
    medical_info: str = Form(None),
    extracurricular_activities: str = Form(None),
    social_profiles: str = Form(None),
    honors_awards: str = Form(None),
    skills_summary: str = Form(None),
    emergency_contact_name: str = Form(None),
    emergency_phone: str = Form(None),
    emergency_email: str = Form(None),
    emergency_relationship: str = Form(None),
    resume_link: str = Form(None),
    profile_pic: UploadFile = File(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.get("role") != "student":
        return RedirectResponse(url="/", status_code=303)

    photo_url = None
    if profile_pic and profile_pic.filename:
        import os
        from uuid import uuid4
        _, ext = os.path.splitext(profile_pic.filename)
        filename = f"{uuid4().hex}{ext}"
        save_dir = "static/profile_photos"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        with open(save_path, "wb") as f:
            f.write(await profile_pic.read())
        photo_url = f"/static/profile_photos/{filename}"

    update_data = StudentUpdateRequest(
        name=name,
        gender=gender,
        dob=dob,
        email=email,
        phone=phone,
        mailing_address=mailing_address,
        previous_school=previous_school,
        graduation_date=graduation_date,
        gpa=gpa,
        intended_major=intended_major,
        current_year=current_year,
        bio=bio,
        medical_info=medical_info,
        extracurricular_activities=extracurricular_activities,
        social_profiles=social_profiles,
        honors_awards=honors_awards,
        skills_summary=skills_summary,
        emergency_contact_name=emergency_contact_name,
        emergency_phone=emergency_phone,
        emergency_email=emergency_email,
        emergency_relationship=emergency_relationship,
        resume_link=resume_link,
        profile_pic=photo_url
    )
    student_id = int(user.get("id") or user.get("sub"))
    error = update_student_profile(db, student_id, update_data)
    student = db.query(Student).filter(Student.id == student_id).first()
    if error:
        return templates.TemplateResponse("student_profile.html", {"request": request, "student": student, "user": user, "error": error})

    return templates.TemplateResponse("student_profile.html", {"request": request, "student": student, "user": user, "message": "Profile updated successfully!"})

#to get the browse project page for the student 

@router.get("/student/browse-projects", response_class=HTMLResponse)
async def browse_projects_student(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from model import Project, Professor, Application  # import your models

    # For filters, you can process query params here (not covered in this step)
    projects = (
        db.query(Project, Professor)
        .join(Professor, Project.professor_id == Professor.id)
        .filter(Project.status == "active", Project.applications_open == True)
        .all()
    )

    # Professors list for filter dropdowns (optional)
    professors = db.query(Professor).all()

    return templates.TemplateResponse("student_browseproject.html", {
        "request": request,
        "user": user,
        "projects": projects,
        "professors": professors,
    })

#handles the logic wen apply is clicked on the browse project page in any project

@router.post("/student/apply-project", response_class=HTMLResponse)
async def apply_project_student(
    request: Request,
    project_id: int = Form(...),
    message: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    from model import Application, Project

    if user.get("role") != "student":
        return RedirectResponse(url="/login", status_code=303)
    student_id = int(user.get("id") or user.get("sub"))

    # Check not already applied
    exists = db.query(Application).filter(
        Application.student_id == student_id,
        Application.project_id == project_id
    ).first()
    if exists:
        # Get projects and professors data for the template
        projects = (
            db.query(Project, Professor)
            .join(Professor, Project.professor_id == Professor.id)
            .filter(Project.status == "active", Project.applications_open == True)
            .all()
        )
        professors = db.query(Professor).all()
        return templates.TemplateResponse("student_browseproject.html", {
            "request": request,
            "user": user,
            "projects": projects,
            "professors": professors,
            "error": "You have already applied to this project."
        })

    application = Application(
        student_id=student_id,
        project_id=project_id,
        status="pending",
    )
    db.add(application)
    db.commit()

    # Success - return to browse page with a message
    return RedirectResponse("/student/browse-projects", status_code=303)


#to get the applications tab in professor

@router.get("/professor/applications", response_class=HTMLResponse)
async def professor_applications(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from model import Professor, Project, Application, Student
    professor_id = int(user.get("id") or user.get("sub"))
    # Get all projects owned by this professor
    projects = db.query(Project).filter(Project.professor_id == professor_id).all()
    project_ids = [proj.id for proj in projects]
    # Get all applications for those projects with student and project info
    applications = (
        db.query(Application, Student, Project)
        .join(Student, Application.student_id == Student.id)
        .join(Project, Application.project_id == Project.id)
        .filter(Application.project_id.in_(project_ids))
        .order_by(Application.applied_at.desc())
        .all()
    )
    return templates.TemplateResponse("professor_applications.html", {
        "request": request,
        "user": user,
        "applications": applications
    })

#to handle the status change of recieved applications

@router.post("/professor/application/update-status", response_class=HTMLResponse)
async def update_application_status(request: Request, application_id: int = Form(...), status: str = Form(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    from model import Application
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        return RedirectResponse("/professor/applications", status_code=303)
    app.status = status
    db.commit()
    return RedirectResponse("/professor/applications", status_code=303)

#API endpoint for students to view project details
@router.get("/api/student/project/{project_id}")
async def get_student_project_detail(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.get("role") != "student":
        return {"error": "Unauthorized"}, 401
    
    project = db.query(Project).filter(Project.id == project_id, Project.status == "active", Project.applications_open == True).first()
    if not project:
        return {"error": "Project not found or not available"}, 404
    
    return {
        "id": project.id,
        "title": project.title,
        "status": project.status,
        "introduction": project.introduction,
        "problem_definition": project.problem_definition,
        "objective": project.objective,
        "methodology": project.methodology,
        "scope": project.scope,
        "timeline": project.timeline,
        "updated_at": project.updated_at.strftime("%b %d, %Y") if project.updated_at else "",
        "required_skills": project.required_skills,
    }

#when professor clicks view profile for an applicant this works

@router.get("/professor/student-profile")
async def professor_student_profile(student_id: int, db: Session = Depends(get_db)):
    from model import Student
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return JSONResponse({"error": "Student not found"}, status_code=404)
    # Return all useful profile fields
    student_data = {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "gender": student.gender,
        "dob": student.dob.strftime('%Y-%m-%d') if student.dob else "",
        "branch": getattr(student, "branch", ""),  # if you have branch field
        "semester": getattr(student, "semester", ""),
        "bio": student.bio or "",
        "skills_summary": student.skills_summary or "",
        "profile_pic": student.profile_pic or "",
        "mailing_address": student.mailing_address or "",
        "previous_school": student.previous_school or "",
        "gpa": student.gpa or "",
        "intended_major": student.intended_major or "",
        "current_year": student.current_year or "",
        "extracurricular_activities": student.extracurricular_activities or "",
        "honors_awards": student.honors_awards or "",
        "medical_info": student.medical_info or "",
        "resume_link": student.resume_link or "",
        "emergency_contact_name": getattr(student, "emergency_contact_name", ""),
        "emergency_relationship": getattr(student, "emergency_relationship", ""),
        "emergency_phone": getattr(student, "emergency_phone", ""),
        "emergency_email": getattr(student, "emergency_email", ""),
    }
    return JSONResponse(student_data)

#to get the my applications of student 

@router.get("/student/my-applications", response_class=HTMLResponse)
async def student_my_applications(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from model import Application, Project, Professor
    student_id = int(user.get("id") or user.get("sub"))
    # Get all applications submitted by this student
    applications = (
        db.query(Application, Project, Professor)
        .join(Project, Application.project_id == Project.id)
        .join(Professor, Project.professor_id == Professor.id)
        .filter(Application.student_id == student_id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return templates.TemplateResponse("student_myapps.html", {
        "request": request,
        "user": user,
        "applications": applications
    })


