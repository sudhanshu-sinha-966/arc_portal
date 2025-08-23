import sys
sys.path.append('.')

from database import SessionLocal
from model import Student, Professor, Project, Application

def check_database():
    db = SessionLocal()
    try:
        students = db.query(Student).count()
        professors = db.query(Professor).count()
        projects = db.query(Project).count()
        applications = db.query(Application).count()
        
        print(f"Database Status:")
        print(f"Students: {students}")
        print(f"Professors: {professors}")
        print(f"Projects: {projects}")
        print(f"Applications: {applications}")
        
        if students > 0:
            print("\nStudent details:")
            for student in db.query(Student).all():
                print(f"  ID: {student.id}, Name: {student.name}, Email: {student.email}")
        
        if applications > 0:
            print("\nApplication details:")
            for app in db.query(Application).all():
                print(f"  Student ID: {app.student_id}, Project ID: {app.project_id}, Status: {app.status}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
