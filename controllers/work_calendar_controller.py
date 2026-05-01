"""
Controller untuk kalender kerja digital
"""
from datetime import date, datetime, timedelta
import calendar
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from models import db
from models.work_calendar_event import WorkCalendarEvent
from utils.decorators import login_required
from utils.audit_logger import AuditLogger

work_calendar_bp = Blueprint("work_calendar", __name__)

EVENT_TYPE_LABELS = {
    "hari_kerja": "Hari Kerja",
    "jadwal": "Jadwal",
    "deadline": "Deadline",
    "libur": "Libur",
}


@work_calendar_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Kalender kerja digital"""
    if request.method == "POST":
        event_date = request.form.get("event_date")
        title = request.form.get("title")
        event_type = request.form.get("event_type", "jadwal")
        description = request.form.get("description")

        if not event_date or not title:
            flash("Tanggal dan judul agenda wajib diisi.", "error")
            return redirect(url_for("work_calendar.index"))

        if event_type not in EVENT_TYPE_LABELS:
            flash("Tipe agenda tidak valid.", "error")
            return redirect(url_for("work_calendar.index"))

        event = WorkCalendarEvent(
            event_date=datetime.strptime(event_date, "%Y-%m-%d").date(),
            title=title,
            description=description,
            event_type=event_type,
            created_by_user_id=session.get("user_id"),
        )
        db.session.add(event)
        db.session.commit()

        AuditLogger.log_data_change(
            session.get("user_id"),
            session.get("username"),
            "create",
            "work_calendar_events",
            event.id,
            f"Created calendar event: {title}",
        )
        flash("Agenda kalender berhasil ditambahkan.", "success")
        return redirect(url_for("work_calendar.index", month=event.event_date.strftime("%Y-%m")))

    month_str = request.args.get("month", date.today().strftime("%Y-%m"))
    try:
        current_year, current_month = map(int, month_str.split("-"))
        current_date = date(current_year, current_month, 1)
    except ValueError:
        current_date = date.today().replace(day=1)

    first_day = current_date
    _, month_last_day = calendar.monthrange(current_date.year, current_date.month)
    last_day = current_date.replace(day=month_last_day)

    events = (
        WorkCalendarEvent.query
        .filter(WorkCalendarEvent.event_date >= first_day, WorkCalendarEvent.event_date <= last_day)
        .order_by(WorkCalendarEvent.event_date.asc(), WorkCalendarEvent.created_at.asc())
        .all()
    )

    events_by_date = {}
    for item in events:
        events_by_date.setdefault(item.event_date, []).append(item)

    cal = calendar.Calendar(firstweekday=0)
    month_weeks = []
    for week in cal.monthdatescalendar(current_date.year, current_date.month):
        row = []
        for day_item in week:
            row.append(
                {
                    "date": day_item,
                    "is_current_month": day_item.month == current_date.month,
                    "is_today": day_item == date.today(),
                    "is_weekend": day_item.weekday() >= 5,
                    "events": events_by_date.get(day_item, []),
                }
            )
        month_weeks.append(row)

    upcoming_events = (
        WorkCalendarEvent.query
        .filter(WorkCalendarEvent.event_date >= date.today(), WorkCalendarEvent.event_date <= (date.today() + timedelta(days=30)))
        .order_by(WorkCalendarEvent.event_date.asc())
        .limit(10)
        .all()
    )

    previous_month = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    next_month = (last_day + timedelta(days=1)).replace(day=1)

    return render_template(
        "work_calendar/index.html",
        month_weeks=month_weeks,
        current_date=current_date,
        previous_month=previous_month.strftime("%Y-%m"),
        next_month=next_month.strftime("%Y-%m"),
        today=date.today().strftime("%Y-%m-%d"),
        upcoming_events=upcoming_events,
        event_type_labels=EVENT_TYPE_LABELS,
    )
