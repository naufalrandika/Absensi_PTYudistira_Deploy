"""
Controller untuk Time Worksheet karyawan
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from models import db
from models.employee import Employee
from models.time_worksheet import TimeWorksheet
from utils.decorators import login_required
from utils.audit_logger import AuditLogger

time_worksheet_bp = Blueprint("time_worksheet", __name__)


def _calculate_duration_minutes(start_time_str, end_time_str):
    """Hitung durasi menit dari jam mulai dan selesai."""
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")
    if end_time <= start_time:
        end_time += timedelta(days=1)
    duration = int((end_time - start_time).total_seconds() // 60)
    return duration, start_time.time(), end_time.time()


@time_worksheet_bp.route("/")
@login_required
def index():
    """Daftar time worksheet"""
    role = session.get("role")
    employee_id = session.get("employee_id")

    query = TimeWorksheet.query
    if role == "karyawan":
        query = query.filter_by(employee_id=employee_id)
    elif role == "atasan":
        employee = Employee.query.get(employee_id)
        subordinate_ids = [item.id for item in employee.subordinates] if employee else []
        if subordinate_ids:
            query = query.filter(TimeWorksheet.employee_id.in_(subordinate_ids))
        else:
            query = query.filter(TimeWorksheet.id == -1)

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if start_date:
        query = query.filter(TimeWorksheet.activity_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(TimeWorksheet.activity_date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    worksheets = query.order_by(TimeWorksheet.activity_date.desc(), TimeWorksheet.start_time.desc()).all()
    total_minutes = sum(item.duration_minutes for item in worksheets)

    return render_template(
        "time_worksheet/index.html",
        worksheets=worksheets,
        role=role,
        total_minutes=total_minutes,
        start_date=start_date or "",
        end_date=end_date or "",
        today=date.today().strftime("%Y-%m-%d"),
    )


@time_worksheet_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Tambah aktivitas time worksheet"""
    if session.get("role") != "karyawan":
        flash("Fitur input lembar waktu kerja hanya untuk karyawan.", "warning")
        return redirect(url_for("time_worksheet.index"))

    employee_id = session.get("employee_id")
    if not employee_id:
        flash("Akun belum terhubung ke data karyawan.", "error")
        return redirect(url_for("time_worksheet.index"))

    if request.method == "POST":
        activity_date = request.form.get("activity_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        activity_title = request.form.get("activity_title")
        activity_description = request.form.get("activity_description")

        if not all([activity_date, start_time, end_time, activity_title]):
            flash("Tanggal, jam, dan judul aktivitas wajib diisi.", "error")
            return render_template("time_worksheet/create.html", today=date.today().strftime("%Y-%m-%d"))

        duration_minutes, parsed_start, parsed_end = _calculate_duration_minutes(start_time, end_time)
        if duration_minutes <= 0:
            flash("Durasi aktivitas harus lebih dari 0 menit.", "error")
            return render_template("time_worksheet/create.html", today=date.today().strftime("%Y-%m-%d"))

        worksheet = TimeWorksheet(
            employee_id=employee_id,
            activity_date=datetime.strptime(activity_date, "%Y-%m-%d").date(),
            start_time=parsed_start,
            end_time=parsed_end,
            duration_minutes=duration_minutes,
            activity_title=activity_title,
            activity_description=activity_description,
        )
        db.session.add(worksheet)
        db.session.commit()

        AuditLogger.log_data_change(
            session.get("user_id"),
            session.get("username"),
            "create",
            "time_worksheets",
            worksheet.id,
            f"Created worksheet activity: {activity_title}",
        )

        flash("Aktivitas harian berhasil dicatat.", "success")
        return redirect(url_for("time_worksheet.index"))

    return render_template("time_worksheet/create.html", today=date.today().strftime("%Y-%m-%d"))
