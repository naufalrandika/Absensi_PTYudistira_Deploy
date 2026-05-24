"""
Script untuk inisialisasi database
Membuat tabel dan user default
"""
import os
from dotenv import load_dotenv

# Load environment variables dari .env file
load_dotenv()

from app import create_app
from models import db
from models.user import User
from models.employee import Employee
from datetime import date

# Import semua models agar tabel dibuat
from models.attendance import Attendance
from models.leave_request import LeaveRequest
from models.overtime import Overtime
from models.notification import Notification
from models.audit_log import AuditLog
from models.office import Office
from models.time_worksheet import TimeWorksheet
from models.work_calendar_event import WorkCalendarEvent

app = create_app()

with app.app_context():
    # Create all tables
    print("Creating database tables...")
    db.create_all()
    print("[OK] Tables created successfully")
    
    # Create default admin employee
    admin_employee = Employee.query.filter_by(nik='ADMIN001').first()
    if not admin_employee:
        admin_employee = Employee(
            nik='ADMIN001',
            full_name='Administrator',
            email='admin@company.com',
            phone='081234567890',
            position='Administrator',
            division='IT',
            status='aktif',
            hire_date=date.today()
        )
        db.session.add(admin_employee)
        db.session.commit()
        print("[OK] Default admin employee created")
    else:
        print("[OK] Admin employee already exists")
    
    # Create default admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@company.com',
            role='admin',
            employee_id=admin_employee.id,
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("[OK] Default admin user created (username: admin, password: admin123)")
    else:
        print("[OK] Admin user already exists")
    
    # Create default HRD employee
    hrd_employee = Employee.query.filter_by(nik='HRD001').first()
    if not hrd_employee:
        hrd_employee = Employee(
            nik='HRD001',
            full_name='HRD Manager',
            email='hrd@company.com',
            phone='081234567891',
            position='HRD Manager',
            division='HRD',
            status='aktif',
            hire_date=date.today()
        )
        db.session.add(hrd_employee)
        db.session.commit()
        print("[OK] Default HRD employee created")
    else:
        print("[OK] HRD employee already exists")
    
    # Create default HRD user
    hrd_user = User.query.filter_by(username='hrd').first()
    if not hrd_user:
        hrd_user = User(
            username='hrd',
            email='hrd@company.com',
            role='hrd',
            employee_id=hrd_employee.id,
            is_active=True
        )
        hrd_user.set_password('hrd123')
        db.session.add(hrd_user)
        db.session.commit()
        print("[OK] Default HRD user created (username: hrd, password: hrd123)")
    else:
        print("[OK] HRD user already exists")
    
    print("\n" + "="*50)
    print("Database initialization completed!")
    print("="*50)
    print("\nDefault users:")
    print("  Admin: username='admin', password='admin123'")
    print("  HRD:   username='hrd',   password='hrd123'")
    print("\n[WARNING] IMPORTANT: Change default passwords after first login!")
    print("="*50)
