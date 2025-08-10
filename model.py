from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, text
from database import Base
from sqlalchemy.orm import relationship

# --- Student ---
class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    profile_pic = Column(String(255))                 # NEW
    phone = Column(String(20))                        # NEW
    branch = Column(String(100))                      # NEW
    semester = Column(String(20))                     # NEW
    bio = Column(Text)                                # NEW
    skills_summary = Column(Text)                     # NEW
    resume_link = Column(String(255))                 # NEW
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

# --- Professor ---
class Professor(Base):
    __tablename__ = "professor"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    department = Column(String(100))
    office_location = Column(String(100))
    phone = Column(String(20))
    affiliation = Column(String(150))
    bio = Column(Text)
    expertise = Column(Text)
    research_interests = Column(Text)
    education = Column(Text)
    cv_link = Column(String(255))
    awards = Column(Text)
    publications = Column(Text)
    memberships = Column(Text)
    social_links = Column(Text)
    profile_pic = Column(String(255))
    pronouns = Column(String(50))
    pronunciation = Column(String(255))
    titles = Column(String(200))
    grants = Column(Text)
    news = Column(Text)
    other_info = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True, autoincrement=True)
    professor_id = Column(Integer, ForeignKey("professor.id"), nullable=False)
    title = Column(String(200), nullable=False)
    introduction = Column(Text)
    problem_definition = Column(Text)
    objective = Column(Text)
    methodology = Column(Text)
    scope = Column(Text)
    timeline = Column(Text)
    applications_open = Column(Boolean, default=True)
    status = Column(String(20), default="active")  # active/completed
    required_skills = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    applications = relationship("Application", back_populates="project")
    # Add other fields as needed...

class Application(Base):
    __tablename__ = "application"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    status = Column(String(20), default="pending")
    applied_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    project = relationship("Project", back_populates="applications")
    student = relationship("Student")
    # Add other fields as needed...