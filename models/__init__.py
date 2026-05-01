"""
Database Models
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.employee import Employee
from models.attendance import Attendance
from models.leave_request import LeaveRequest
from models.overtime import Overtime
from models.notification import Notification
from models.audit_log import AuditLog
from models.office import Office
from models.time_worksheet import TimeWorksheet
from models.work_calendar_event import WorkCalendarEvent