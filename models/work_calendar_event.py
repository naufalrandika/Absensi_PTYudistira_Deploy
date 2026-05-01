"""
Model kalender kerja digital
"""
from datetime import datetime
from models import db


class WorkCalendarEvent(db.Model):
    """Model event untuk kalender kerja digital"""
    __tablename__ = "work_calendar_events"

    id = db.Column(db.Integer, primary_key=True)
    event_date = db.Column(db.Date, nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_type = db.Column(db.String(20), nullable=False, default="jadwal")
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship("User", backref="work_calendar_events")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "created_by_user_id": self.created_by_user_id,
            "created_by": self.creator.username if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
