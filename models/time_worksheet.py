"""
Model Time Worksheet untuk aktivitas harian karyawan
"""
from datetime import datetime
from models import db


class TimeWorksheet(db.Model):
    """Model untuk mencatat aktivitas kerja harian beserta durasinya"""
    __tablename__ = "time_worksheets"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    activity_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    activity_title = db.Column(db.String(150), nullable=False)
    activity_description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = db.relationship("Employee", backref="time_worksheets")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.full_name if self.employee else None,
            "activity_date": self.activity_date.isoformat() if self.activity_date else None,
            "start_time": self.start_time.strftime("%H:%M") if self.start_time else None,
            "end_time": self.end_time.strftime("%H:%M") if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "duration_hours": round(self.duration_minutes / 60, 2),
            "activity_title": self.activity_title,
            "activity_description": self.activity_description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
